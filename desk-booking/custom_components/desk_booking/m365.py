"""Lifecycle, local cache and serialized M365 synchronization."""
from .records import records_of_type, update_record, add_record

import asyncio
from datetime import timedelta
import logging
from types import MappingProxyType

from homeassistant.config_entries import ConfigSubentry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN, PROFILE, DESK, GROUP, ROOM, update_signal
from .groups import group_updates
from .directory import profile_updates
from .places import desk_updates, desk_identity, resource_users, room_updates
from .graph import GraphClient, GraphError
from .profile import ProfileError, identity, profile_title

_LOGGER = logging.getLogger(__name__)


class DirectorySync:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.config = dict(entry.data.get("m365", {}))
        self.store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.directory")
        self.cache = {}
        self.state = "not_configured"
        self.error = None
        self.lock = asyncio.Lock()
        self.task = None
        self.cancel_timer = None
        self.client = GraphClient(async_get_clientsession(hass), self.config) if self.config else None

    def notify(self):
        async_dispatcher_send(self.hass, update_signal(self.entry.entry_id))

    async def start(self):
        self.cache = await self.store.async_load() or {}
        if self.client:
            if "places" in self.cache and all(self.cache.get(k) == self.config.get(k) for k in ("tenant_id", "client_id")):
                try:
                    self.apply(self.cache)
                except (GraphError, ProfileError, ValueError, KeyError, TypeError):
                    self.cache = {}
            self.state = "cached" if self.cache else "idle"
            self.cancel_timer = async_track_time_interval(self.hass, self.scheduled, timedelta(minutes=self.config.get("sync_interval", 15)))
            self.task = self.hass.async_create_task(self.sync(), "Desk Booking M365 initial sync")

    def plan(self, snapshot):
        group_updates(list(records_of_type(self.entry, GROUP)), snapshot)
        room_updates(list(records_of_type(self.entry, ROOM)), snapshot)
        desks = list(records_of_type(self.entry, DESK))
        profiles = list(records_of_type(self.entry, PROFILE))
        desk_changes = desk_updates(desks, profiles, snapshot)
        migrated = {current.subentry_id for current, _ in desk_changes if current and current.subentry_type == PROFILE}
        # Remember retired resource accounts even after Places deletes the object.
        excluded = {d.data.get("object_id") for d in desks if d.data.get("source") == "places"}
        excluded |= {r.data.get("object_id") for r in records_of_type(self.entry, ROOM) if r.data.get("source") == "places"}
        profile_changes = profile_updates([p for p in profiles if p.subentry_id not in migrated], snapshot, excluded)
        return desk_changes, profile_changes

    def apply(self, snapshot):
        desk_changes, changes = self.plan(snapshot)
        group_changes = group_updates(list(records_of_type(self.entry, GROUP)), snapshot)
        registry = dr.async_get(self.hass)
        for current, data in room_updates(list(records_of_type(self.entry, ROOM)), snapshot):
            if current:
                update_record(self.hass, self.entry, current, data=data, title=data["name"])
                device = registry.async_get_device_by_identifier((DOMAIN, current.subentry_id), self.entry.entry_id)
                if device and device.name != data["name"]:
                    registry.async_update_device(device.id, name=data["name"])
            else:
                add_record(self.hass, self.entry, ConfigSubentry(
                    data=MappingProxyType(data), subentry_type=ROOM, title=data["name"],
                    unique_id=desk_identity(data["tenant_id"], data["place_id"])))
        for current, data in group_changes:
            if current:
                update_record(self.hass, self.entry, current, data=data, title=data["name"])
                device = registry.async_get_device_by_identifier((DOMAIN, current.subentry_id), self.entry.entry_id)
                if device and device.name != data["name"]:
                    registry.async_update_device(device.id, name=data["name"])
            else:
                add_record(self.hass, self.entry, ConfigSubentry(
                    data=MappingProxyType(data), subentry_type=GROUP, title=data["name"],
                    unique_id=f"group:{data['tenant_id']}:{data['object_id']}"))
        for current, data in desk_changes:
            title = data["name"]
            if current and current.subentry_type == DESK:
                update_record(self.hass, self.entry, current, data=data, title=title)
            else:
                # The managed add API replaces an existing subentry ID without
                # clearing its registry associations. A new unique ID represents
                # the confirmed Places identity; the opaque subentry ID survives.
                kwargs = {"subentry_id": current.subentry_id} if current else {}
                add_record(self.hass, self.entry, ConfigSubentry(
                    **kwargs, data=MappingProxyType(data), subentry_type=DESK, title=title,
                    unique_id=desk_identity(data["tenant_id"], data["place_id"])))
                if current:
                    entities = er.async_get(self.hass)
                    for entity in er.async_entries_for_config_entry(entities, self.entry.entry_id):
                        if entity.unique_id in {f"{current.subentry_id}_{key}" for key in ("sitting_height", "standing_height", "active", "directory_status")} and entity.disabled_by is None:
                            # Retain registry IDs and recorder history, disable only
                            # obsolete employee controls. Never delete registry data.
                            entities.async_update_entity(entity.entity_id, disabled_by=er.RegistryEntryDisabler.INTEGRATION)
            if current:
                device = registry.async_get_device_by_identifier((DOMAIN, current.subentry_id), self.entry.entry_id)
                if device:
                    registry.async_update_device(device.id, name=title, model="Desk")
        for current, data in changes:
            if current:
                update_record(self.hass, self.entry, current, data=data, title=profile_title(data))
                device = registry.async_get_device_by_identifier((DOMAIN, current.subentry_id), self.entry.entry_id)
                if device and device.name != profile_title(data):
                    registry.async_update_device(device.id, name=profile_title(data))
            else:
                add_record(self.hass, self.entry, ConfigSubentry(
                    data=MappingProxyType(data), subentry_type=PROFILE,
                    title=profile_title(data), unique_id=identity(data)))

    async def scheduled(self, now):
        if not self.task or self.task.done():
            self.task = self.hass.async_create_task(self.sync(), "Desk Booking M365 sync")

    async def stop(self):
        if self.cancel_timer:
            self.cancel_timer()
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        # Manual calls are tracked as the current task while running as well.

    async def sync(self):
        if not self.client or self.lock.locked():
            return
        self.task = asyncio.current_task()
        async with self.lock:
            self.state, self.error = "syncing", None
            self.notify()
            try:
                cache = self.cache
                if any(cache.get(k) != self.config.get(k) for k in ("tenant_id", "client_id")):
                    cache = {}
                async with asyncio.timeout(600):
                    snapshot = await self.client.snapshot(cache)
                # Validate every profile before writing anything. Projection reads
                # the latest local values after the network calls, without yielding.
                self.plan(snapshot)
                snapshot["last_success"] = dt_util.utcnow().isoformat()
                # Write complete snapshot first. Cursors are replay-safe if profile
                # application is interrupted; cached users are projected every run.
                await self.store.async_save(snapshot)
                self.apply(snapshot)
                self.cache = snapshot
                self.state = "ok"
            except GraphError as err:
                self.state, self.error = "error", err.code
                _LOGGER.warning("M365 sync failed: %s", err.code)
            except (ProfileError, ValueError, KeyError, TypeError):
                self.state, self.error = "error", "invalid_response"
                _LOGGER.warning("M365 directory validation failed; retained local profiles")
            except (OSError, asyncio.TimeoutError):
                self.state, self.error = "error", "cannot_connect"
            finally:
                self.notify()

    @property
    def status(self):
        resources = set(resource_users(self.cache)) if "users" in self.cache else set()
        resources |= {d.data.get("object_id") for d in records_of_type(self.entry, DESK) if d.data.get("source") == "places"}
        resources |= {r.data.get("object_id") for r in records_of_type(self.entry, ROOM) if r.data.get("source") == "places"}
        return {"last_success": self.cache.get("last_success"), "error": self.error,
                "users": sum(oid not in resources and u.get("accountEnabled") is True and u.get("userType") == "Member" for oid, u in self.cache.get("users", {}).items()),
                "places_desks": sum(p.get("kind") == "desk" for p in self.cache.get("places", {}).values()),
                "places_rooms": sum(p.get("kind") == "room" for p in self.cache.get("places", {}).values()),
                "places_workspaces": sum(p.get("kind") == "workspace" for p in self.cache.get("places", {}).values()),
                "resource_accounts": len(resources - {None}),
                "groups": len(self.cache.get("groups", {})), "interval_minutes": self.config.get("sync_interval", 15)}
