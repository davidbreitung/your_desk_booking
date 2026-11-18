"""Employee selection for the local test check-in."""
from .records import records_of_type, category_id

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import ServiceValidationError
from .const import DESK, GROUP
from .entity import EmployeeEntity, CentralEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([CentralPriority(entry, "message_priority", "Nachricht Priorität")])
    for desk in records_of_type(entry, DESK):
        async_add_entities([DeskEmployee(entry, desk, "selected_employee")], config_subentry_id=category_id(entry, desk))
    for kind in (DESK, GROUP):
        for record in records_of_type(entry, kind):
            async_add_entities([TargetPriority(entry, record, "message_priority")], config_subentry_id=category_id(entry, record))


class TargetPriority(EmployeeEntity, SelectEntity):
    _attr_name = "Nachricht Priorität"
    _attr_entity_category = None
    _attr_options = ["1", "2", "3"]

    @property
    def current_option(self):
        return str(self.profile.get(self.key, "3"))

    async def async_select_option(self, option):
        self.update_profile(**{self.key: option})


class DeskEmployee(EmployeeEntity, SelectEntity):
    _attr_entity_category = None

    @property
    def options(self):
        return list(self.entry.runtime_data.choices())

    @property
    def current_option(self):
        selected = self.profile.get("selected_profile", "")
        return next((label for label, pid in self.entry.runtime_data.choices().items() if pid == selected), "—")

    async def async_select_option(self, option):
        if self.profile.get("status", "free") != "free":
            raise ServiceValidationError("Zuerst auschecken, bevor ein anderer Mitarbeiter gewählt wird.")
        self.update_profile(selected_profile=self.entry.runtime_data.choices()[option])


class CentralPriority(CentralEntity, SelectEntity):
    _attr_options = ["1", "2", "3"]

    @property
    def current_option(self):
        return self.entry.options.get(self.key, "3")

    async def async_select_option(self, option):
        self.save(option)
