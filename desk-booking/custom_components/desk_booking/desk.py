"""Local check-in transactions. Only the two known ESPHome favorites are writable."""
from .records import records, records_of_type, update_record


import asyncio
from decimal import Decimal, ROUND_HALF_UP
import math
from datetime import datetime, timezone

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DESK, DOMAIN, PROFILE, update_signal


def display_targets(hass, device_id):
    registry = er.async_get(hass)
    targets = {}
    for key, original in (("sitting_height", "Favorit Sitzen"), ("standing_height", "Favorit Stehen")):
        matches = [e for e in er.async_entries_for_device(registry, device_id)
                   if e.platform == "esphome" and e.domain == "number"
                   and e.original_name == original and not e.disabled_by
                   and e.unique_id.endswith(f"/number/{original}")]
        if len(matches) != 1:
            raise ServiceValidationError("Das Display muss die bekannten Favoriten Sitzen und Stehen bereitstellen.")
        targets[key] = matches[0].entity_id
    return targets


def fit_value(value, attributes):
    """Round to the device step; reject unsafe ranges, never clamp."""
    minimum, maximum = float(attributes["min"]), float(attributes["max"])
    step = float(attributes["step"])
    if not all(math.isfinite(v) for v in (value, minimum, maximum, step)) or step <= 0:
        raise ServiceValidationError("Ungültiger Höhenbereich am Display.")
    if not minimum <= value <= maximum:
        raise ServiceValidationError("Die Profilhöhe liegt außerhalb des Displaybereichs.")
    ticks = ((Decimal(str(value)) - Decimal(str(minimum))) / Decimal(str(step))).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP)
    result = float(Decimal(str(minimum)) + ticks * Decimal(str(step)))
    if not minimum <= result <= maximum:
        raise ServiceValidationError("Die gerundete Profilhöhe liegt außerhalb des Displaybereichs.")
    return result


class DeskManager:
    def __init__(self, hass, entry, structure):
        self.hass, self.entry, self.structure = hass, entry, structure
        # Preserve mutual exclusion even if a profile rename causes a reload
        # while a device action is awaiting its state confirmation.
        self.lock = hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, asyncio.Lock())

    def update(self, desk, **changes):
        # Re-read after awaits: cloud sync or an earlier transaction stage may
        # already have replaced this immutable record snapshot.
        current = records(self.entry)[desk.subentry_id]
        update_record(self.hass, self.entry, current, data={**current.data, **changes})
        async_dispatcher_send(self.hass, update_signal(self.entry.entry_id))

    def choices(self):
        profiles = records_of_type(self.entry, PROFILE)
        counts = {}
        result = {"—": ""}
        for profile in profiles:
            if not profile.data.get("active", True) or profile.data.get("resource_account") or profile.data.get('hidden'):
                continue
            counts[profile.title] = counts.get(profile.title, 0) + 1
            index = counts[profile.title]
            label = profile.title if index == 1 else f"{profile.title} ({index})"
            while label in result:
                label += " ·"
            result[label] = profile.subentry_id
        return result

    def _snapshot(self, targets):
        result = {}
        for key, entity_id in targets.items():
            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("unknown", "unavailable"):
                raise ServiceValidationError("Das Display ist nicht erreichbar.")
            try:
                value = float(state.state)
                if not math.isfinite(value):
                    raise ValueError
            except ValueError as err:
                raise ServiceValidationError("Das Display meldet keine gültige Favoritenhöhe.") from err
            result[key] = value
        return result

    async def _write(self, targets, values, context):
        for key, entity_id in targets.items():
            await self.hass.services.async_call("number", "set_value",
                {"entity_id": entity_id, "value": values[key]}, blocking=True, context=context)
        # ESPHome state reports may follow the action response asynchronously.
        for _ in range(40):
            if all((state := self.hass.states.get(entity_id)) is not None
                   and state.state not in ("unknown", "unavailable")
                   and math.isclose(float(state.state), values[key], abs_tol=0.01)
                   for key, entity_id in targets.items()):
                return
            await asyncio.sleep(0.25)
        raise HomeAssistantError("Die Favoritenübertragung wurde vom Display nicht bestätigt.")

    async def check_in(self, desk_id, context):
        async with self.lock:
            desk = records(self.entry)[desk_id]
            if not desk.data.get("active", True):
                raise ServiceValidationError("Der Schreibtisch ist in Microsoft Places nicht verfügbar.")
            if not desk.data.get("display_device"):
                raise ServiceValidationError("Bitte zuerst in der Schreibtisch-Konfiguration ein Display zuordnen.")
            profile_id = desk.data.get("selected_profile", "")
            profile = records(self.entry).get(profile_id)
            if profile is None or profile.subentry_type != PROFILE:
                raise ServiceValidationError("Zuerst einen Mitarbeiter auswählen.")
            if not profile.data["active"]:
                raise ServiceValidationError("Das Mitarbeiterprofil ist gesperrt.")
            reservation = None
            if hasattr(self, 'bookings'):
                action, reservation = await self.bookings.check_in_decision(desk, profile)
                desk = records(self.entry)[desk_id]
                if action == 'already_checked_in':
                    return
                if action not in ('allow', 'replace'):
                    message = 'Buchungen nicht aktuell. Bitte erneut versuchen...' if action == 'calendar_unavailable' else 'Bereits gebucht...'
                    await self.alert(desk, message, context)
                    raise ServiceValidationError(message)
            elif desk.data.get('status', 'free') != 'free':
                raise ServiceValidationError('Der Tisch ist belegt. Zuerst auschecken.')
            if any(p.subentry_id != desk_id and p.data.get("occupant") == profile_id and p.data.get("status", "free") != "free"
                   for p in records_of_type(self.entry, DESK)):
                raise ServiceValidationError("Der Mitarbeiter ist bereits an einem Tisch eingecheckt.")
            targets = display_targets(self.hass, desk.data["display_device"])
            snapshot = self._snapshot(targets)
            replacing = desk.data.get('status', 'free') != 'free'
            previous = desk.data.get('previous') if replacing else snapshot
            if not previous:
                raise HomeAssistantError('Gespeicherte Displayfavoriten fehlen; Wechsel gesperrt.')
            original = {key: desk.data.get(key, default) for key, default in
                (('status','free'),('occupant',''),('previous',{}),('applied',{}),('checkin_reservation',None))}
            values = {key: fit_value(profile.data[key], self.hass.states.get(entity_id).attributes)
                      for key, entity_id in targets.items()}
            if values["sitting_height"] >= values["standing_height"]:
                raise ServiceValidationError("Die gerundete Sitzhöhe muss kleiner als die Stehhöhe sein.")
            # Keep the old occupant until successful acknowledgement; this also
            # prevents group messages being routed to the prospective occupant.
            self.update(desk, status="applying", previous=previous)
            try:
                async with asyncio.timeout(20):
                    await self._write(targets, values, context)
                # Profile may have been disabled/removed while waiting for ESPHome.
                current = records(self.entry).get(profile_id)
                if current is None or not current.data["active"]:
                    raise HomeAssistantError("Das Profil wurde während des Check-ins gesperrt oder entfernt.")
            except (HomeAssistantError, TimeoutError):
                try:
                    async with asyncio.timeout(20):
                        await self._write(targets, snapshot, context)
                except (HomeAssistantError, TimeoutError):
                    self.update(desk, status="error")
                    raise HomeAssistantError("Übertragung fehlgeschlagen. Tisch gesperrt; Auschecken erneut versuchen.") from None
                self.update(desk, **original)
                raise HomeAssistantError("Check-in fehlgeschlagen; vorherige Displayfavoriten wiederhergestellt.") from None
            self.update(desk, status="checked_in", occupant=profile_id, previous=previous,
                        applied=values, checkin_reservation=reservation, checkin_at=datetime.now(timezone.utc).isoformat())
            if hasattr(self, 'bookings'):
                await self.bookings.mark_attended(desk_id, reservation)
            await self._message(desk, f"Willkommen, {current.data['name']}", context)

    async def check_out(self, desk_id, context, expected_occupant=None):
        async with self.lock:
            desk = records(self.entry)[desk_id]
            if expected_occupant is not None and desk.data.get('occupant', '') != expected_occupant:
                return
            if desk.data.get("status", "free") == "free":
                return
            targets = display_targets(self.hass, desk.data["display_device"])
            previous = desk.data.get("previous", {})
            if not previous:
                raise HomeAssistantError("Gespeicherte Displayfavoriten fehlen; Zuordnung bleibt gesperrt.")
            self.update(desk, status="applying")
            try:
                async with asyncio.timeout(20):
                    await self._write(targets, previous, context)
            except (HomeAssistantError, TimeoutError):
                self.update(desk, status="error")
                raise HomeAssistantError("Auschecken nicht abgeschlossen. Displayverbindung prüfen und erneut versuchen.") from None
            self.update(desk, status="free", occupant="", previous={}, applied={}, checkin_reservation=None, checkin_at=None)
            await self._message(desk, "Ausgecheckt - Tisch frei", context)

    async def alert(self, desk, message, context=None):
        if getattr(self, 'fleet', None) and desk.data.get('display_device'):
            try:
                # Normal priority 1 messages already have a red animated ring.
                await self.fleet.send_one(desk.data['display_device'], message, '1', 30, context)
                return True
            except (HomeAssistantError, TimeoutError):
                return False
        return False

    async def _message(self, desk, message, context):
        if hasattr(self, "fleet"):
            try:
                await self.fleet.send_one(desk.data["display_device"], message, "3", 15, context, booking=True)
            except (HomeAssistantError, TimeoutError):
                pass
            return
        # Optional UI feedback via known same-device text and button entities.
        entries = er.async_entries_for_device(er.async_get(self.hass), desk.data["display_device"])
        text = next((e.entity_id for e in entries if e.platform == "esphome" and
                     e.domain == "text" and e.original_name == "Nachricht Text" and not e.disabled_by), None)
        button = None
        for name in ("Check-in Nachricht senden", "Nachricht senden"):
            button = next((e.entity_id for e in entries if e.platform == "esphome" and
                           e.domain == "button" and e.original_name == name and not e.disabled_by), None)
            if button:
                break
        if text and button:
            try:
                async with asyncio.timeout(10):
                    await self.hass.services.async_call("text", "set_value", {"entity_id": text, "value": message}, blocking=True, context=context)
                    await self.hass.services.async_call("button", "press", {"entity_id": button}, blocking=True, context=context)
            except (HomeAssistantError, TimeoutError):
                # A missing toast does not undo a verified check-in.
                pass
