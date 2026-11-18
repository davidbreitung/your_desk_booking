"""Constants for Desk Booking."""

DOMAIN = "desk_booking"
PLATFORMS = ["number", "switch", "sensor", "select", "button", "text"]
PROFILE = "employee"
DESK = "desk"
GROUP = "group"
ROOM = "room"
MIN_HEIGHT = 50.0
MAX_HEIGHT = 140.0
DEFAULT_SITTING = 72.0
DEFAULT_STANDING = 110.0

DISPLAY_DEFAULTS = {"display_brightness": 50, "standby_brightness": 10,
                    "standby_timeout": 120, "standby_home": False}
SWITCH_ICONS = {"mdi:power": "Ein/Aus", "mdi:power-socket-eu": "Steckdose",
                "mdi:fan": "Ventilator", "mdi:monitor": "Monitor",
                "mdi:radiator": "Heizung", "mdi:toggle-switch": "Schalter"}


def update_signal(entry_id: str) -> str:
    return f"{DOMAIN}_{entry_id}_updated"
