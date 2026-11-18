"""Authenticated floorplan API; public static path contains code only."""
import asyncio
import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
import secrets

import probatio as vol
from homeassistant.components import websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.storage import Store
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.util import dt as dt_util

from .const import DOMAIN, DESK, ROOM, PROFILE
from .records import records_of_type
from .floorplan_model import validate_plan, day_window, day_events
from .graph import GraphError
from .floorplan_settings import DEFAULT_BOOKING_URL, verify_password

KEY = DOMAIN + "_floorplan"


class Floorplans:
    def __init__(self, hass):
        self.hass = hass
        self.store = Store(hass, 1, KEY, private=True)
        self.photo_store = Store(hass, 1, KEY + "_photos", private=True)
        self.plans, self.photos = {}, {}
        self.lock, self.photo_lock = asyncio.Lock(), asyncio.Lock()
        self.entries = {}
        self.edit_tokens = {}
        self.auth_attempts = {}
        self.auth_lock = asyncio.Lock()

    def settings(self):
        return next((e.options.get('floorplan', {}) for e in self.entries.values()), {})

    def can_save(self, user, token):
        stored = self.settings().get('password_hash')
        if not stored:
            return True
        authorization = self.edit_tokens.get(token)
        return bool(authorization and authorization[:2] == (user.id, stored) and authorization[2] > time.monotonic())

    async def authorize(self, user, password):
        # Serialize expensive hashing and throttle authenticated users before hashing.
        async with self.auth_lock:
            now = time.monotonic()
            attempts = [t for t in self.auth_attempts.get(user.id, []) if t > now - 60]
            self.auth_attempts[user.id] = attempts
            if len(attempts) >= 5:
                raise ValueError('Rate limited')
            attempts.append(now)
            stored = self.settings().get('password_hash')
            if stored and not await self.hass.async_add_executor_job(verify_password, password, stored):
                raise ValueError('Invalid password')
            token = secrets.token_urlsafe(32)
            self.edit_tokens[token] = (user.id, stored, now + 3600)
            # Tokens are single-save, expire after one hour and invalidate on password changes.
            if len(self.edit_tokens) > 100:
                self.edit_tokens.pop(next(iter(self.edit_tokens)))
            return {'token': token}

    async def load(self):
        self.plans = (await self.store.async_load() or {}).get("plans", {})
        self.photos = (await self.photo_store.async_load() or {}).get("photos", {})

    def resources(self):
        return {r.subentry_id: (entry, r) for entry in self.entries.values()
                for kind in (DESK, ROOM) for r in records_of_type(entry, kind)}

    def readable(self, user, record, key):
        entity_id = er.async_get(self.hass).async_get_entity_id("sensor", DOMAIN, f"{record.subentry_id}_{key}")
        return bool(entity_id and user.permissions.check_entity(entity_id, POLICY_READ))

    def people(self, entry, user):
        tenant = entry.data.get("m365", {}).get("tenant_id")
        return {p.data["object_id"]: p for p in records_of_type(entry, PROFILE)
                if not p.data.get('hidden') and p.data.get("tenant_id") == tenant and p.data.get("object_id") and self.readable(user, p, "directory_status")}

    def person(self, entry, record):
        if not record:
            return None
        device = dr.async_get(self.hass).async_get_device_by_identifier((DOMAIN, record.subentry_id), entry.entry_id)
        return {"id": record.subentry_id, "name": record.data["name"], "device_id": device.id if device else None}

    def snapshot(self, selected, user):
        now = dt_util.utcnow()
        zone = self.hass.config.time_zone
        day, start, end = day_window(selected, now, zone)
        output = []
        for rid, (entry, resource) in self.resources().items():
            if resource.data.get('hidden') or not self.readable(user, resource, "next_booking"):
                continue
            people = self.people(entry, user)
            by_id = {p.subentry_id:p for p in people.values()}
            sync = entry.runtime_data.bookings
            cached = sync.cache.get(rid, {})
            info = sync.info(rid)
            def project(event):
                person = self.person(entry, people.get(event.get("booker_object_id")))
                return {"id":event["id"], "start":event["start"], "end":event["end"],
                    "person":person, "name":person["name"] if person else "Nicht zugeordnet",
                    "identity_status":event.get("identity_status")}
            events = [project(e) for e in day_events(cached.get("events", []), start, end)]
            following = next((project(e) for e in cached.get("events", []) if datetime.fromisoformat(e["start"]) >= end),None)
            occupant = self.person(entry, by_id.get(resource.data.get("occupant")))
            output.append({"id":rid,"name":resource.title,"kind":resource.subentry_type,
                "active":resource.data.get("active",True), "fresh":info["fresh"], "last_success":info["last_success"],
                "error":info["error"], "events":events, "following":following,
                "checked_in":resource.subentry_type == DESK and resource.data.get("status") == "checked_in",
                "occupant":occupant, "checkin_at":resource.data.get('checkin_at')})
        return {"date":day.isoformat(),"today":now.astimezone(dt_util.get_time_zone(zone)).date().isoformat(),
                "timezone":zone,"now":now.isoformat(),"day_start":start.isoformat(),"day_end":end.isoformat(),"resources":output,
                "plans":[{k:p[k] for k in ("id","name","revision")} for p in self.plans.values()],
                "can_edit":user.is_admin, "edit_password_required":bool(self.settings().get('password_hash')),
                "booking_url":self.settings().get('booking_url', DEFAULT_BOOKING_URL)}

    async def save(self, payload):
        async with self.lock:
            plan = validate_plan(payload, self.resources())
            old = self.plans.get(plan["id"])
            if payload.get("revision", 0) != (old or {}).get("revision", 0):
                raise ValueError("Der Plan wurde zwischenzeitlich geändert. Bitte abbrechen und neu öffnen.")
            if not old and len(self.plans) >= 20:
                raise ValueError("Maximal 20 Pläne.")
            plan["revision"] = (old or {}).get("revision", 0) + 1
            updated = {**self.plans, plan["id"]:plan}
            await self.store.async_save({"plans":updated})
            self.plans = updated
            return deepcopy(plan)

    async def photo(self, rid, user):
        for entry in self.entries.values():
            person = next((p for p in self.people(entry,user).values() if p.subentry_id == rid),None)
            if person:
                break
        else:
            raise ValueError("Mitarbeiter nicht verfügbar.")
        key = f"{person.data['tenant_id']}:{person.data['object_id']}"
        async with self.photo_lock:
            old = self.photos.get(key, {})
            if old.get("retry_at", 0) > time.time():
                return {"image":old.get("image"),"status":old.get("status","cached")}
            client = entry.runtime_data.directory.client
            try:
                if not client:
                    raise GraphError("not_configured")
                data, mime = await client.profile_photo(person.data["object_id"])
                value = {"image":f"data:{mime};base64,"+base64.b64encode(data).decode(),
                         "status":"ok", "retry_at":time.time()+86400}
            except GraphError as err:
                image = None if err.code in ("not_found","insufficient_permissions") else old.get("image")
                value = {"image":image,"status":err.code,
                         "retry_at":time.time()+(86400 if err.code == "not_found" else max(300,err.retry_after))}
            updated = {**self.photos,key:value}
            await self.photo_store.async_save({"photos":updated})
            self.photos = updated
            return {"image":value["image"],"status":value["status"]}


@websocket_api.websocket_command({"type":"desk_booking/floorplan", "action":str,
                                  vol.Optional("payload", default=dict):dict})
@websocket_api.async_response
async def websocket_floorplan(hass, connection, msg):
    manager = hass.data[KEY]
    action, payload = msg["action"], msg["payload"]
    if action in ("save", "authorize") and not connection.user.is_admin:
        connection.send_error(msg["id"],"unauthorized","Nur Administratoren dürfen Pläne bearbeiten.")
        return
    try:
        if action == "snapshot":
            result = manager.snapshot(payload.get("date"),connection.user)
        elif action == "get":
            result = deepcopy(manager.plans[payload["id"]])
        elif action == "authorize":
            result = await manager.authorize(connection.user, payload.get('password', ''))
        elif action == "save":
            token = payload.get('edit_token', '')
            if not manager.can_save(connection.user, token):
                connection.send_error(msg['id'], 'password_required', 'Kennwort erforderlich. Bitte Bearbeitung neu öffnen.')
                return
            result = await manager.save({k:v for k,v in payload.items() if k != 'edit_token'})
            manager.edit_tokens.pop(token, None)
        elif action == "photo":
            result = await manager.photo(payload["id"],connection.user)
        else:
            raise ValueError("Unbekannte Aktion.")
        connection.send_result(msg["id"],result)
    except (ValueError, KeyError, TypeError, AttributeError):
        # Avoid returning raw values (e.g. names or payloads) in exception messages.
        connection.send_error(msg["id"],"invalid_request","Ungültige Daten oder geänderter Plan. Bitte Eingaben prüfen und gegebenenfalls neu laden.")
    except (OSError, TimeoutError):
        connection.send_error(msg["id"],"storage_error","Daten konnten nicht geladen oder gespeichert werden.")


async def async_setup_floorplan(hass, entry):
    if KEY not in hass.data:
        manager = Floorplans(hass)
        await manager.load()
        await hass.http.async_register_static_paths([StaticPathConfig(
            "/desk_booking_static",str(Path(__file__).parent / "frontend"),False)])
        hass.data[KEY] = manager
        websocket_api.async_register_command(hass,websocket_floorplan)
    hass.data[KEY].entries[entry.entry_id] = entry


def unload_floorplan(hass, entry):
    if KEY in hass.data:
        hass.data[KEY].entries.pop(entry.entry_id,None)
