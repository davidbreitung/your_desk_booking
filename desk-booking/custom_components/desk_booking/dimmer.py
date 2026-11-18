"""Desk display controls a configured light without user automations."""
from .records import records_of_type

import asyncio
import logging
import math
from datetime import datetime, timezone

from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .const import DESK
from .const import update_signal
from .fleet import endpoint
from homeassistant.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)
INVALID = ("unknown", "unavailable")


def dimmer_targets(hass, device_id, slot=1):
    entries = er.async_entries_for_device(er.async_get(hass), device_id)
    targets = {}
    for domain, name in (("number", "Dimmer Regelwert"), ("event", "Dimmer Taster")):
        if slot > 1:
            name += f" {slot}"
        matches = [e.entity_id for e in entries if e.platform == "esphome"
                   and e.domain == domain and e.original_name == name and not e.disabled_by]
        if len(matches) != 1:
            raise ServiceValidationError("Das Display benötigt Dimmer Regelwert und Dimmer Taster.")
        targets[domain] = matches[0]
    return targets


def validate_light(hass, entity_id, display):
    state = hass.states.get(entity_id)
    registered = er.async_get(hass).async_get(entity_id)
    if not entity_id.startswith("light.") or state is None:
        raise ServiceValidationError("Bitte ein vorhandenes dimmbares Licht auswählen.")
    if display and registered and registered.device_id == display:
        raise ServiceValidationError("Die Displaybeleuchtung darf nicht als Arbeitsplatzlicht verwendet werden.")
    modes = set(state.attributes.get("supported_color_modes", []))
    if not modes - {"onoff", "unknown"}:
        raise ServiceValidationError("Das ausgewählte Licht unterstützt keine Helligkeitsregelung.")


def brightness_change(old, new):
    """Ignore initial/reconnected states, attribute-only updates and bad values."""
    if (old is None or new is None or old.state in INVALID or new.state in INVALID
            or old.state == new.state or old.attributes.get("restored") or new.attributes.get("restored")):
        return None
    try:
        value = float(new.state)
    except (ValueError, TypeError):
        return None
    return int(value + 0.5) if math.isfinite(value) and 0 <= value <= 100 else None


class DeskDimmer:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.unsubscribers = []
        self.tasks = set()
        self.pending = {}
        self.locks = {}
        self.started_at = datetime.now(timezone.utc)

    @callback
    def start(self):
        for desk in records_of_type(self.entry, DESK):
            if not desk.data.get("display_device"):
                continue
            for slot, light in enumerate(desk.data.get("light_entities", []), 1):
                self._bind(desk, slot, light)
            self._bind_accessories(desk)

    def _bind_accessories(self, desk):
        device = desk.data["display_device"]
        cover, switch = desk.data.get("cover_entity"), desk.data.get("switch_entity")
        for target, domain, name, service, parameter, feature in (
            (cover, "event", "Rollo Position Befehl", "set_cover_position", "position", 4),
            (cover, "event", "Lamellen Position Befehl", "set_cover_tilt_position", "tilt_position", 128),
            (switch, "event", "Schaltkanal Taster", None, None, 0)):
            if not target:
                continue
            try:
                source = endpoint(self.hass, device, domain, name)
                value_source = endpoint(self.hass, device, "number", "Rollo Position Sollwert" if parameter == "position" else "Lamellen Position Sollwert") if service else None
            except ServiceValidationError:
                _LOGGER.warning("Display benötigt aktualisierte Firmware für %s", name)
                continue
            key = (desk.subentry_id, name)
            self.locks[key] = asyncio.Lock()
            @callback
            def changed(event, dst=target, command=service, arg=parameter, mask=feature, lock=key, number=value_source):
                old, new = event.data.get("old_state"), event.data.get("new_state")
                if command:
                    if not self._live_command(old, new, ("apply",)):
                        return
                    current = self.hass.states.get(number)
                    try:
                        value = float(current.state) if current else float("nan")
                    except (ValueError, TypeError):
                        return
                    if not math.isfinite(value) or not 0 <= value <= 100:
                        return
                    value = round(value)
                    pending = self.pending.pop(lock, None)
                    if pending:
                        pending.cancel()
                    task = self._spawn(self._accessory(lock, dst, command, {arg: value}, mask, event.context, True))
                    self.pending[lock] = task
                elif self._live_command(old, new):
                    self._spawn(self._accessory(lock, dst, new.attributes["event_type"], {}, 0, event.context))
            self.unsubscribers.append(async_track_state_change_event(self.hass, [source], changed))
        targets = [x for x in (cover, switch) if x]
        if targets:
            @callback
            def feedback(event):
                async_dispatcher_send(self.hass, update_signal(self.entry.entry_id))
            self.unsubscribers.append(async_track_state_change_event(self.hass, targets, feedback))

    async def _accessory(self, key, entity, service, data, feature, context, debounce=False):
        if debounce:
            await asyncio.sleep(.25)
            self.pending.pop(key, None)
        async with self.locks[key]:
            state = self.hass.states.get(entity)
            if state is None or state.state in INVALID:
                return
            if feature and not int(state.attributes.get("supported_features", 0)) & feature:
                return
            try:
                await self.hass.services.async_call(entity.split(".")[0], service,
                    {"entity_id": entity, **data}, blocking=True, context=context)
            except HomeAssistantError:
                _LOGGER.warning("Arbeitsplatzgerät %s konnte nicht bedient werden", entity)

    @callback
    def _bind(self, desk, slot, light):
        try:
            targets = dimmer_targets(self.hass, desk.data["display_device"], slot)
        except ServiceValidationError:
            _LOGGER.warning("Dimmer-Anbindung für %s nicht verfügbar", desk.title)
            return
        key = (desk.subentry_id, slot)
        self.locks[key] = asyncio.Lock()
        @callback
        def changed(event, desk_id=key, light_id=light, endpoints=targets):
            old, new = event.data.get("old_state"), event.data.get("new_state")
            if event.data["entity_id"] == endpoints["number"]:
                value = brightness_change(old, new)
                if value is None:
                    return
                previous = self.pending.get(desk_id)
                if previous:
                    previous.cancel()
                task = self._spawn(self._brightness(desk_id, light_id, value, event.context))
                self.pending[desk_id] = task
            elif self._live_command(old, new):
                pending = self.pending.pop(desk_id, None)
                if pending:
                    pending.cancel()
                self._spawn(self._call(desk_id, light_id, new.attributes["event_type"], {}, event.context))
        self.unsubscribers.append(async_track_state_change_event(self.hass, list(targets.values()), changed))

    def _live_command(self, old, new, allowed=("turn_on", "turn_off")):
        if (new is None or new.state in INVALID or (old is not None and old.state == new.state)
                or new.attributes.get("event_type") not in allowed
                or new.attributes.get("restored")):
            return False
        try:
            timestamp = datetime.fromisoformat(new.state)
            return timestamp >= self.started_at
        except (ValueError, TypeError):
            return False

    def _spawn(self, coro):
        task = self.hass.async_create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def _brightness(self, desk_id, light, value, context):
        await asyncio.sleep(0.15)
        # Only debounce waiting commands; don't cancel a service already sent.
        self.pending.pop(desk_id, None)
        await self._call(desk_id, light, "turn_on" if value else "turn_off",
                         {"brightness_pct": value} if value else {}, context)

    async def _call(self, desk_id, light, service, data, context):
        async with self.locks[desk_id]:
            state = self.hass.states.get(light)
            if state is None or state.state in INVALID:
                return
            try:
                await self.hass.services.async_call("light", service, {"entity_id": light, **data},
                                                    blocking=True, context=context)
            except HomeAssistantError:
                _LOGGER.warning("Arbeitsplatzlicht %s konnte nicht geschaltet werden", light)

    async def stop(self):
        for unsubscribe in self.unsubscribers:
            unsubscribe()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
