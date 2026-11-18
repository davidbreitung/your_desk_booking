"""Independent calendar polling and minute-accurate local display refresh."""
from .records import records, records_of_type

import asyncio
import json
from datetime import timedelta, datetime, timezone

from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DESK, ROOM, PROFILE, update_signal
from .booking import project_events, next_event, active_event, booking_presentation
from .graph import GraphError
from .checkin_policy import decide, protected_events, no_show, warning_key


class BookingSync:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.interval = entry.options.get("booking_interval", 5)
        self.store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.bookings")
        self.cache, self.errors, self.sent = {}, {}, {}
        self.lock, self.task, self.timers = asyncio.Lock(), None, []
        self.state = "idle"
        self.refresh_tasks = set()
        self.refresh_lock = asyncio.Lock()

    async def start(self):
        saved = await self.store.async_load() or {}
        if saved.get("tenant_id") == self.entry.data.get("m365", {}).get("tenant_id"):
            self.cache = saved.get("desks", {})
        self.timers = [async_track_time_interval(self.hass, self.scheduled, timedelta(minutes=self.interval)),
                       async_track_time_interval(self.hass, self.refresh, timedelta(seconds=30))]
        self.task = self.hass.async_create_task(self.sync(), "Desk Booking calendar initial sync")

    async def scheduled(self, now):
        if not self.task or self.task.done():
            self.task = self.hass.async_create_task(self.sync(), "Desk Booking calendar sync")

    async def sync(self):
        if self.lock.locked():
            return
        self.task = asyncio.current_task()
        async with self.lock:
            client = self.entry.runtime_data.directory.client
            if client is None:
                self.state = "not_configured"
                return
            self.state = "syncing"
            now = dt_util.utcnow()
            resources = list(records_of_type(self.entry, DESK)) + list(records_of_type(self.entry, ROOM))
            ids = {d.subentry_id for d in resources}
            self.cache = {k: v for k, v in self.cache.items() if k in ids}
            self.errors = {k: v for k, v in self.errors.items() if k in ids}
            for desk in resources:
                async with self.entry.runtime_data.lock:
                    await self._read_desk(desk, now)
            self.state = "error" if self.errors else "ok"
            try:
                await self.store.async_save({"tenant_id": self.entry.data.get("m365", {}).get("tenant_id"), "desks": self.cache})
            except OSError:
                self.state = "cache_error"
            await self.refresh()

    async def _read_desk(self, desk, now):
        mailbox = desk.data.get("calendar_mailbox") or desk.data.get("object_id") or desk.data.get("places_email")
        if not desk.data.get("active", True):
            # Retirement is expected inventory state, not a failed calendar poll.
            # Keep cached history, but never contact its former mailbox.
            self.errors.pop(desk.subentry_id, None)
            return False
        if not mailbox:
            self.errors[desk.subentry_id] = "no_resource_mailbox"
            return False
        client = self.entry.runtime_data.directory.client
        if client is None:
            self.errors[desk.subentry_id] = "not_configured"
            return False
        try:
            async with asyncio.timeout(60):
                # Keep the complete local day for the floorplan's day timeline.
                local_start = now.astimezone(getattr(dt_util, "DEFAULT_TIME_ZONE", timezone.utc)).replace(hour=0, minute=0, second=0, microsecond=0)
                raw = await client.calendar_view(mailbox, local_start.astimezone(timezone.utc), now + timedelta(days=365))
            events = project_events(raw, self.entry.runtime_data.directory.cache.get("users", {}))
            old = self.cache.get(desk.subentry_id, {})
            # Retain attendance and notification history across syncs/restarts.
            self.cache[desk.subentry_id] = {**old, "events": events, "last_success": dt_util.utcnow().isoformat(),
                "window_end": (now + timedelta(days=365)).isoformat(), "mailbox": mailbox}
            self.errors.pop(desk.subentry_id, None)
            return True
        except GraphError as err:
            self.errors[desk.subentry_id] = err.code
        except (OSError, TimeoutError):
            self.errors[desk.subentry_id] = "cannot_connect"
        except (ValueError, KeyError, TypeError, AttributeError):
            self.errors[desk.subentry_id] = "invalid_response"
        return False

    async def _save(self):
        try:
            await self.store.async_save({"tenant_id": self.entry.data.get("m365", {}).get("tenant_id"), "desks":self.cache})
            return True
        except OSError:
            self.state = "cache_error"
            return False

    async def mark_attended(self, desk_id, event):
        if event:
            self.cache.setdefault(desk_id, {}).setdefault('attended', {})[event['id']] = event['end']
            await self._save()

    def _observe_occupant(self, desk, now):
        if desk.data.get('status') != 'checked_in':
            return None
        person = records(self.entry).get(desk.data.get('occupant'))
        if not person or person.data.get('tenant_id') != self.entry.data.get('m365', {}).get('tenant_id'):
            return None
        matches = [e for e in protected_events(self.cache.get(desk.subentry_id, {}).get('events', []), now)
                   if e.get('booker_object_id') == person.data.get('object_id')]
        if not matches:
            return None
        event = matches[0]
        if desk.data.get('checkin_reservation') != event:
            self.entry.runtime_data.update(desk, checkin_reservation=event)
        self.cache[desk.subentry_id].setdefault('attended', {})[event['id']] = event['end']
        return event

    async def check_in_decision(self, desk, person):
        # Called with the shared transaction lock; re-read the calendar directly
        # before granting access instead of trusting a five-minute-old snapshot.
        if desk.data.get('status') == 'checked_in' and desk.data.get('occupant') == person.subentry_id:
            return 'already_checked_in', None
        if person.data.get('tenant_id') != self.entry.data.get('m365', {}).get('tenant_id'):
            return 'reserved', None
        fresh = await self._read_desk(desk, dt_util.utcnow())
        if fresh:
            self._observe_occupant(desk, dt_util.utcnow())
        desk = records(self.entry)[desk.subentry_id]
        return decide(desk.data, person, self.cache.get(desk.subentry_id, {}).get('events', []), dt_util.utcnow(), fresh)

    async def _automation(self, desk):
        # Caller holds DeskManager.lock. No-show and check-in cannot race.
        if getattr(desk, "subentry_type", DESK) != DESK:
            return  # Room calendars are strictly read-only, including future callers.
        now = dt_util.utcnow()
        info = self.info(desk.subentry_id)
        if not info['fresh']:
            return
        item = self.cache[desk.subentry_id]
        attended = item.setdefault('attended', {})
        event = self._observe_occupant(desk, now)
        if event:
            key = warning_key(event, now)
            if key and key not in item.setdefault('warned', []):
                if await self.entry.runtime_data.alert(desk, 'Achtung, Reservierung endet bald. Bitte nachbuchen, falls benötigt...'):
                    item['warned'].append(key)
                    item['warned'] = item['warned'][-500:]
        # Persist attendance before any remote deletion. On storage failure fail
        # closed, retaining bookings instead of forgetting a prior check-in.
        if not await self._save():
            return
        if desk.data.get('status', 'free') != 'free':
            return
        candidates = [e for e in item.get('events', []) if no_show(e, now, False, attended)]
        if not candidates:
            return
        client = self.entry.runtime_data.directory.client
        try:
            if not await client.has_calendar_write():
                self.errors[desk.subentry_id] = 'calendar_write_permission_missing'
                return
            for candidate in candidates:
                # Fresh event + ETag prevents deleting an extension or changed
                # booking based on an earlier calendar snapshot.
                raw = await client.resource_event(item['mailbox'], candidate['id'])
                projected = project_events([raw], self.entry.runtime_data.directory.cache.get('users', {}))
                if not projected or not no_show(projected[0], dt_util.utcnow(), False, attended):
                    continue
                if any(projected[0].get(k) != candidate.get(k) for k in ('start','end','booker_object_id')):
                    continue
                await client.delete_resource_event(item['mailbox'], raw)
                item['last_no_show_release'] = dt_util.utcnow().isoformat()
                item['no_show_releases'] = item.get('no_show_releases', 0) + 1
                # Do not locally assume that a successful DELETE freed the desk.
                await self._read_desk(desk, dt_util.utcnow())
            await self._save()
        except GraphError as err:
            self.errors[desk.subentry_id] = err.code
        except (OSError, TimeoutError):
            self.errors[desk.subentry_id] = 'cannot_connect'

    def info(self, desk_id, *, current=False):
        now = dt_util.utcnow()
        record = self.cache.get(desk_id, {})
        last = record.get("last_success")
        try:
            fresh = bool(last and 0 <= (now - datetime.fromisoformat(last)).total_seconds() <= max(900, self.interval * 120 + 60))
        except (TypeError, ValueError):
            fresh = False
        error = self.errors.get(desk_id)
        desk = records(self.entry).get(desk_id)
        if desk and not desk.data.get("active", True):
            error = "inactive"
        event = (active_event if current else next_event)(record.get("events", []), now)
        profile = None
        if event and event.get("booker_object_id"):
            tenant = self.entry.data.get("m365", {}).get("tenant_id")
            profile = next((p for p in records_of_type(self.entry, PROFILE)
                if p.data.get("tenant_id") == tenant and p.data.get("object_id") == event["booker_object_id"]), None)
        name = profile.data["name"] if profile else (event.get("organizer_name") or "Nicht zugeordnet") if event else ""
        device = dr.async_get(self.hass).async_get_device_by_identifier((DOMAIN, profile.subentry_id), self.entry.entry_id) if profile else None
        entity_id = er.async_get(self.hass).async_get_entity_id("sensor", DOMAIN, f"{profile.subentry_id}_directory_status") if profile else None
        presentation = booking_presentation(event, now, dt_util.DEFAULT_TIME_ZONE)
        active = active_event(record.get("events", []), now)
        active_name = ""
        active_label = ""
        if active:
            tenant = self.entry.data.get("m365", {}).get("tenant_id")
            person = next((p for p in records_of_type(self.entry, PROFILE)
                if p.data.get("tenant_id") == tenant and p.data.get("object_id") == active.get("booker_object_id")), None)
            active_name = person.data["name"] if person else active.get("organizer_name") or "Nicht zugeordnet"
            active_label = "Reserviert bis " + datetime.fromisoformat(active["end"]).astimezone(dt_util.DEFAULT_TIME_ZONE).strftime("%d.%m. %H:%M")
        return {"event": event, "name": name, "employee_subentry_id": profile.subentry_id if profile else None,
                "active_event": active, "active_name": active_name, "active_label": active_label,
                "employee_device_id": device.id if device else None, "employee_entity_id": entity_id,
                "fresh": fresh and not error, "error": error, "last_success": last, "window_end": record.get("window_end"),
                **presentation}

    async def refresh(self, now=None):
        if self.refresh_lock.locked():
            return
        async with self.refresh_lock:
            await self._refresh()

    async def _refresh(self):
        task = asyncio.current_task()
        self.refresh_tasks.add(task)
        try:
            if hasattr(self.entry.runtime_data, 'mail'):
                await self.entry.runtime_data.mail.tick()
            async_dispatcher_send(self.hass, update_signal(self.entry.entry_id))
            for desk in list(records_of_type(self.entry, DESK)):
                async with self.entry.runtime_data.lock:
                    desk = records(self.entry)[desk.subentry_id]
                    await self._automation(desk)
                device = desk.data.get("display_device")
                if not device:
                    continue
                info = self.info(desk.subentry_id)
                # A single text entity makes dynamic desk/display mappings possible;
                # no hard-coded HA entity IDs in the booking firmware are required.
                active = bool(info["active_event"] and info["fresh"])
                data = {"time": (info["active_label"] if active else info["label"]) if info["fresh"] else "Buchungen nicht aktuell",
                    "who": (info["active_name"] if active else info["name"])[:80] if info["fresh"] else "",
                    "warn": info["warning"] and info["fresh"] and not active, "active": active}
                payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                while len(payload.encode("utf-8")) > 255 and data["who"]:
                    data["who"] = data["who"][:-1]
                    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                try:
                    # Refresh heartbeat every 30 seconds; display clears stale hints
                    # after HA disconnects. This never sends a notification or motor command.
                    await self.entry.runtime_data.fleet._call(device, "text", "Naechste Buchung", "set_value", {"value": payload})
                except (HomeAssistantError, TimeoutError):
                    pass  # Older display firmware can be upgraded independently.
            if self.state != 'cache_error':
                current_records = records(self.entry)
                self.errors = {key: value for key, value in self.errors.items()
                               if key in current_records and current_records[key].data.get('active', True)}
                self.state = 'error' if self.errors else 'ok'
            async_dispatcher_send(self.hass, update_signal(self.entry.entry_id))
        finally:
            self.refresh_tasks.discard(task)

    async def stop(self):
        for cancel in self.timers:
            cancel()
        tasks = set(self.refresh_tasks)
        if self.task and not self.task.done():
            tasks.add(self.task)
        tasks.discard(asyncio.current_task())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
