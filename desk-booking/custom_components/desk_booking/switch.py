"""Administrative profile enable/disable switch."""
from .records import records_of_type, category_id


from homeassistant.components.switch import SwitchEntity

from .const import PROFILE
from .entity import EmployeeEntity, CentralEntity
from .fleet import endpoint
from homeassistant.exceptions import ServiceValidationError

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AllDisplays(entry, "display_power", "Alle Displays")])
    for profile in records_of_type(entry, PROFILE):
        async_add_entities([EmployeeActive(entry, profile, "active")],
                           config_subentry_id=category_id(entry, profile))


class EmployeeActive(EmployeeEntity, SwitchEntity):
    @property
    def is_on(self):
        return self.profile["active"]

    async def async_turn_on(self, **kwargs):
        raise ServiceValidationError("Der Mitarbeiterstatus wird ausschließlich von Microsoft 365 verwaltet.")

    async def async_turn_off(self, **kwargs):
        raise ServiceValidationError("Der Mitarbeiterstatus wird ausschließlich von Microsoft 365 verwaltet.")


class AllDisplays(CentralEntity, SwitchEntity):
    @property
    def available(self):
        for device in self.fleet.devices():
            try:
                state = self.hass.states.get(endpoint(self.hass, device, "switch", "Display Aktiv"))
                if state and state.state in ("on", "off"):
                    return True
            except ServiceValidationError:
                continue
        return False

    @property
    def is_on(self):
        for device in self.fleet.devices():
            try:
                state = self.hass.states.get(endpoint(self.hass, device, "switch", "Display Aktiv"))
                if state and state.state == "on":
                    return True
            except ServiceValidationError:
                continue
        return False

    async def async_turn_on(self, **kwargs):
        await self.fleet.power(True, self._context)

    async def async_turn_off(self, **kwargs):
        await self.fleet.power(False, self._context)
