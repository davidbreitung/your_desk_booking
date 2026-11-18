"""Persistent preferred sitting and standing heights in centimetres."""
from .records import records_of_type, category_id


from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfLength
from homeassistant.exceptions import ServiceValidationError

from .const import MAX_HEIGHT, MIN_HEIGHT, PROFILE, DESK, GROUP
from .entity import EmployeeEntity, CentralEntity
from .profile import ProfileError, validate_heights
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import update_signal

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([CentralNumber(entry, "display_brightness", "Alle Displays Helligkeit", 1, 100, 50, "%"),
                        CentralNumber(entry, "message_duration", "Nachricht Anzeigedauer", 1, 300, 15, "s")])
    known = set()
    @callback
    def add_profiles():
        for profile in records_of_type(entry, PROFILE):
            if profile.subentry_id in known:
                continue
            known.add(profile.subentry_id)
            async_add_entities(
                [EmployeeHeight(entry, profile, key) for key in ("sitting_height", "standing_height")],
                config_subentry_id=category_id(entry, profile))
    entry.async_on_unload(async_dispatcher_connect(hass, update_signal(entry.entry_id), add_profiles))
    add_profiles()
    for kind in (DESK, GROUP):
        for record in records_of_type(entry, kind):
            async_add_entities([TargetDuration(entry, record, "message_duration")], config_subentry_id=category_id(entry, record))


class TargetDuration(EmployeeEntity, NumberEntity):
    _attr_name = "Nachricht Anzeigedauer"
    _attr_entity_category = None
    _attr_native_min_value = 1
    _attr_native_max_value = 300
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "s"
    _attr_mode = NumberMode.BOX

    @property
    def native_value(self):
        return self.profile.get(self.key, 15)

    async def async_set_native_value(self, value):
        self.update_profile(**{self.key: value})


class EmployeeHeight(EmployeeEntity, NumberEntity):
    _attr_native_min_value = MIN_HEIGHT
    _attr_native_max_value = MAX_HEIGHT
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_mode = NumberMode.BOX

    @property
    def native_value(self):
        return self.profile[self.key]

    async def async_set_native_value(self, value):
        updated = {**self.profile, self.key: value}
        try:
            validate_heights(updated["sitting_height"], updated["standing_height"])
        except ProfileError as err:
            raise ServiceValidationError(
                translation_domain="desk_booking", translation_key=err.code
            ) from err
        self.update_profile(**{self.key: value})


class CentralNumber(CentralEntity, NumberEntity):
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, entry, key, name, minimum, maximum, default, unit):
        super().__init__(entry, key, name)
        self._attr_native_min_value, self._attr_native_max_value = minimum, maximum
        self.default, self._attr_native_unit_of_measurement = default, unit

    @property
    def native_value(self):
        return self.entry.options.get(self.key, self.default)

    async def async_set_native_value(self, value):
        if self.key == "display_brightness":
            await self.fleet.brightness(value, self._context)
        else:
            self.save(value)
