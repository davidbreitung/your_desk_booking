"""Central display settings and explicit broadcast commands, scoped to mapped desks."""
from .records import records, records_of_type

import asyncio
import logging

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event

from .const import DESK, DISPLAY_DEFAULTS, update_signal
from .groups import recipient_devices

_LOGGER = logging.getLogger(__name__)
SETTING_TARGETS = {"display_brightness": "Display Helligkeit",
                   "standby_brightness": "Display Standby Helligkeit",
                   "standby_timeout": "Display Standby Wartezeit"}


def endpoint(hass, device, domain, name):
    matches = [e.entity_id for e in er.async_entries_for_device(er.async_get(hass), device)
               if e.platform == "esphome" and e.domain == domain
               and e.original_name == name and not e.disabled_by]
    if len(matches) != 1:
        raise ServiceValidationError(f"Display-Funktion nicht verfügbar: {name}")
    return matches[0]


class DisplayFleet:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.tasks, self.unsubs = set(), []
        self.locks = {}
        self.settings = self.current_settings()

    def current_settings(self):
        return {k: self.entry.options.get(k, v) for k, v in DISPLAY_DEFAULTS.items()}

    def spawn(self, coro):
        task = self.hass.async_create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    def devices(self):
        return list(dict.fromkeys(d.data["display_device"] for d in records_of_type(self.entry, DESK) if d.data.get("display_device")))

    @callback
    def start(self):
        watched = []
        for device in self.devices():
            watched.extend(e.entity_id for e in er.async_entries_for_device(er.async_get(self.hass), device)
                           if e.platform == "esphome" and e.domain in ("number", "switch"))
        if watched:
            self.unsubs.append(async_track_state_change_event(self.hass, watched, self.changed))
        self.spawn(self.sync_settings())

    @callback
    def changed(self, event):
        old, new = event.data.get("old_state"), event.data.get("new_state")
        if new and new.state not in ("unknown", "unavailable") and (
                old is None or old.state in ("unknown", "unavailable")):
            # Reapply settings only to the endpoint that just returned, without
            # replaying power, notifications, or actuator commands.
            for device in self.devices():
                for key, name in SETTING_TARGETS.items():
                    try:
                        target = endpoint(self.hass, device, "number", name)
                    except ServiceValidationError:
                        continue
                    if target == event.data["entity_id"]:
                        self.spawn(self._sync_one(device, key))
        async_dispatcher_send(self.hass, update_signal(self.entry.entry_id))

    async def settings_updated(self):
        values = self.current_settings()
        changed = [k for k in SETTING_TARGETS if values[k] != self.settings[k]]
        self.settings = values
        await self.sync_settings(changed)

    async def _call(self, device, domain, name, service, data, context=None):
        target = endpoint(self.hass, device, domain, name)
        state = self.hass.states.get(target)
        # Buttons have no state before their first press; empty ESPHome text
        # inputs can also start as unknown while fully connected.
        if state is None or state.state == "unavailable" or (state.state == "unknown" and domain not in ("button", "text", "select")):
            raise HomeAssistantError(f"Display nicht erreichbar: {name}")
        async with asyncio.timeout(15):
            await self.hass.services.async_call(domain, service, {"entity_id": target, **data},
                                                blocking=True, context=context)

    async def _sync_one(self, device, key):
        try:
            target = endpoint(self.hass, device, "number", SETTING_TARGETS[key])
            state = self.hass.states.get(target)
            value = self.entry.options.get(key, DISPLAY_DEFAULTS[key])
            if state and state.state not in ("unknown", "unavailable") and float(state.state) != value:
                await self._call(device, "number", SETTING_TARGETS[key], "set_value", {"value": value})
        except (HomeAssistantError, ValueError, TimeoutError):
            _LOGGER.warning("Zentrale Displayeinstellung konnte nicht übertragen werden: %s", key)

    async def sync_settings(self, keys=None):
        await asyncio.gather(*(self._sync_one(d, k) for d in self.devices()
                               for k in (SETTING_TARGETS if keys is None else keys)))

    async def broadcast(self, action):
        devices = self.devices()
        if not devices:
            raise ServiceValidationError("Keine Schreibtisch-Displays zugeordnet.")
        results = await asyncio.gather(*(action(d) for d in devices), return_exceptions=True)
        failed = sum(isinstance(r, BaseException) for r in results)
        if failed:
            raise HomeAssistantError(f"{failed} von {len(devices)} Displays konnten nicht erreicht werden; übrige Displays wurden bedient.")

    async def power(self, enabled, context):
        await self.broadcast(lambda d: self._call(d, "switch", "Display Aktiv",
                             "turn_on" if enabled else "turn_off", {}, context))

    async def brightness(self, value, context):
        # Persist the central default and explicitly fan out, even if unchanged.
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, "display_brightness": value})
        await self.broadcast(lambda d: self._call(d, "number", "Display Helligkeit", "set_value", {"value": value}, context))

    async def send_one(self, device, text, priority, duration, context, booking=False):
        async with self.locks.setdefault(device, asyncio.Lock()):
            await self._call(device, "text", "Nachricht Text", "set_value", {"value": text}, context)
            if not booking:
                await self._call(device, "select", "Nachricht Prioritaet", "select_option", {"option": str(priority)}, context)
                await self._call(device, "number", "Nachrichten Anzeigedauer", "set_value", {"value": duration}, context)
            await self._call(device, "button", "Check-in Nachricht senden" if booking else "Nachricht senden", "press", {}, context)

    async def notify(self, text, priority, duration, context):
        if not text.strip() or len(text) > 255 or str(priority) not in ("1", "2", "3") or not 1 <= duration <= 300:
            raise ServiceValidationError("Nachricht: 1–255 Zeichen, Priorität 1–3, Dauer 1–300 Sekunden.")
        await self.broadcast(lambda d: self.send_one(d, text, priority, duration, context))

    async def notify_target(self, subentry_id, context):
        target = records(self.entry)[subentry_id]
        data = target.data
        text, priority, duration = data.get("message_text", ""), str(data.get("message_priority", "3")), data.get("message_duration", 15)
        if not text.strip() or len(text) > 255 or priority not in ("1", "2", "3") or not 1 <= duration <= 300:
            raise ServiceValidationError("Nachricht: 1–255 Zeichen, Priorität 1–3, Dauer 1–300 Sekunden.")
        if target.subentry_type == "group":
            devices = recipient_devices(self.entry, subentry_id, self.entry.runtime_data.directory.cache)
        else:
            devices = [data["display_device"]] if data.get("display_device") else []
        if not devices:
            raise ServiceValidationError("Keine zugeordneten Displays mit passenden angemeldeten Mitarbeitern erreichbar.")
        results = await asyncio.gather(*(self.send_one(d, text, priority, duration, context) for d in devices), return_exceptions=True)
        failed = sum(isinstance(r, BaseException) for r in results)
        if failed:
            raise HomeAssistantError(f"{failed} von {len(devices)} Displays konnten nicht erreicht werden.")

    async def checkout_all(self, context):
        failed = []
        for desk in list(records_of_type(self.entry, DESK)):
            try:
                await self.entry.runtime_data.check_out(desk.subentry_id, context)
            except (HomeAssistantError, TimeoutError):
                failed.append(desk.title)
        if failed:
            raise HomeAssistantError("Nicht abgemeldet (Wiederherstellung ausstehend): " + ", ".join(failed))

    async def stop(self):
        for unsub in self.unsubs:
            unsub()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
