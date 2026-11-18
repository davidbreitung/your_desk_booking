"""Shared employee device and entity lifecycle."""
from .records import records, update_record


from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity, EntityCategory

from .const import DOMAIN, update_signal


class EmployeeEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, subentry, key):
        self.entry = entry
        self.subentry_id = subentry.subentry_id
        self.key = key
        # Use the internal opaque subentry ID, keeping Entra and NFC IDs out
        # of entity/device identifiers and public state attributes.
        self._attr_unique_id = f"{subentry.subentry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="Desk Booking",
            model=("Room" if subentry.subentry_type == "room" else "Group" if subentry.subentry_type == "group" else "Desk" if subentry.subentry_type == "desk" else
                   "Test employee profile" if subentry.data["test_profile"] else "Employee profile"),
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def profile(self):
        subentry = records(self.entry).get(self.subentry_id)
        if subentry is None:
            raise HomeAssistantError("Employee profile no longer exists")
        return subentry.data

    @property
    def available(self):
        return self.subentry_id in records(self.entry)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(
            self.hass, update_signal(self.entry.entry_id), self._updated
        ))

    @callback
    def _updated(self):
        self.async_write_ha_state()

    @callback
    def update_profile(self, **updates):
        subentry = records(self.entry).get(self.subentry_id)
        if subentry is None:
            raise HomeAssistantError("Employee profile no longer exists")
        update_record(self.hass, self.entry, subentry, data={**subentry.data, **updates})
        self.async_write_ha_state()


class CentralEntity(Entity):
    """One integration-wide control device, independent of employee subentries."""
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry, key, name):
        self.entry, self.key = entry, key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_central_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)},
            name="Desk Booking Zentrale", manufacturer="Desk Booking", model="Zentrale Steuerung",
            entry_type=DeviceEntryType.SERVICE)

    @property
    def fleet(self):
        return self.entry.runtime_data.fleet

    def save(self, value):
        self.hass.config_entries.async_update_entry(self.entry, options={**self.entry.options, self.key: value})
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(self.hass, update_signal(self.entry.entry_id), self.async_write_ha_state))

