"""Example Home Assistant integration scaffold."""

from homeassistant.core import HomeAssistant

DOMAIN = "example_integration"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the example integration."""
    return True
