"""Local check-in/out buttons; no motor actions."""
from .records import records_of_type, category_id

from homeassistant.components.button import ButtonEntity
from .const import DESK, GROUP
from .entity import EmployeeEntity, CentralEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([CentralButton(entry, "checkout_all", "Alle Mitarbeiter abmelden"),
                        SyncButton(entry, "sync_m365", "Microsoft 365 synchronisieren"),
                        CentralButton(entry, "notify_all", "Nachricht an alle Displays senden")])
    for desk in records_of_type(entry, DESK):
        async_add_entities([DeskButton(entry, desk, key) for key in ("check_in", "check_out")], config_subentry_id=category_id(entry, desk))
    async_add_entities([BookingSyncButton(entry, "sync_bookings", "Buchungen aktualisieren")])
    for kind in (DESK, GROUP):
        for record in records_of_type(entry, kind):
            async_add_entities([TargetNotify(entry, record, "send_message")], config_subentry_id=category_id(entry, record))


class TargetNotify(EmployeeEntity, ButtonEntity):
    _attr_name = "Nachricht senden"
    _attr_entity_category = None

    async def async_press(self):
        await self.entry.runtime_data.fleet.notify_target(self.subentry_id, self._context)


class BookingSyncButton(CentralEntity, ButtonEntity):
    async def async_press(self):
        await self.entry.runtime_data.bookings.sync()


class DeskButton(EmployeeEntity, ButtonEntity):
    _attr_entity_category = None

    async def async_press(self):
        action = getattr(self.entry.runtime_data, self.key)
        await action(self.subentry_id, self._context)


class SyncButton(CentralEntity, ButtonEntity):
    async def async_press(self):
        await self.entry.runtime_data.directory.sync()


class CentralButton(CentralEntity, ButtonEntity):
    async def async_press(self):
        if self.key == "checkout_all":
            await self.fleet.checkout_all(self._context)
        else:
            options = self.entry.options
            await self.fleet.notify(options.get("message_text", ""), options.get("message_priority", "3"),
                                    options.get("message_duration", 15), self._context)
