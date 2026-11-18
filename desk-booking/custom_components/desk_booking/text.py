"""Message composer for all mapped displays."""
from .records import records_of_type, category_id

from homeassistant.components.text import TextEntity
from .entity import CentralEntity, EmployeeEntity
from .const import DESK, GROUP

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([CentralMessage(entry, "message_text", "Nachricht Text")])
    for kind in (DESK, GROUP):
        for record in records_of_type(entry, kind):
            async_add_entities([TargetMessage(entry, record, "message_text")], config_subentry_id=category_id(entry, record))


class TargetMessage(EmployeeEntity, TextEntity):
    _attr_name = "Nachricht Text"
    _attr_native_max = 255
    _attr_entity_category = None

    @property
    def native_value(self):
        return self.profile.get(self.key, "")

    async def async_set_value(self, value):
        self.update_profile(**{self.key: value})

class CentralMessage(CentralEntity, TextEntity):
    _attr_native_max = 255

    @property
    def native_value(self):
        return self.entry.options.get(self.key, "")

    async def async_set_value(self, value):
        self.save(value)
