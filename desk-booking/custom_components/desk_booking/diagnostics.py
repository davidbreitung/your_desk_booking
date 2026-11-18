"""Only non-personal sync health; no credentials, cursors or directory records."""
from .records import records_of_type
from .const import DESK, ROOM


async def async_get_config_entry_diagnostics(hass, entry):
    directory = entry.runtime_data.directory
    bookings = entry.runtime_data.bookings
    return {"configured": bool(directory.config), "state": directory.state, **directory.status,
            "bookings_state": bookings.state, "booking_interval": bookings.interval,
            "booking_errors": list(set(bookings.errors.values())),
            "booking_cached_desks": sum(d.subentry_id in bookings.cache for d in records_of_type(entry, DESK)),
            "booking_cached_rooms": sum(r.subentry_id in bookings.cache for r in records_of_type(entry, ROOM)),
            'daily_checkout_time':entry.runtime_data.checkout_schedule.time,
            'daily_checkout_state':entry.runtime_data.checkout_schedule.state,
            'daily_checkout_pending':len(entry.runtime_data.checkout_schedule.data.get('pending', {}))}
