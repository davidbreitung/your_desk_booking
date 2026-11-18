"""Pure check-in decisions; all identities are Entra object IDs within a tenant."""
from datetime import datetime, timedelta


def protected_events(events, now):
    return [e for e in events if datetime.fromisoformat(e['end']) > now
            and datetime.fromisoformat(e['start']) <= now + timedelta(minutes=60)]


def decide(desk, employee, events, now, fresh):
    if desk.get('status', 'free') == 'checked_in' and desk.get('occupant') == employee.subentry_id:
        return 'already_checked_in', None
    if not fresh:
        return 'calendar_unavailable', None
    protected = protected_events(events, now)
    # Simultaneous/adjacent protected bookings for different people are
    # ambiguous: never choose by display name or silently pick the first.
    if any(not e.get('booker_object_id') or e['booker_object_id'] != employee.data.get('object_id') for e in protected):
        return 'reserved', None
    status = desk.get('status', 'free')
    if status in ('applying','error'):
        return 'occupied', None
    reservation = desk.get('checkin_reservation')
    if status != 'free':
        if not reservation:
            return 'occupied', None
        current = next((e for e in events if e['id'] == reservation['id']), None)
        # Cancellation/absence from a fresh query does not prove the old end
        # was reached. Keep its known end; observed extensions update it.
        end = (current or reservation)['end']
        if datetime.fromisoformat(end) > now:
            return 'occupied', None
    return ('replace' if status != 'free' else 'allow'), (protected[0] if protected else None)


def no_show(event, now, occupied, attended):
    return (not occupied and event['id'] not in attended
            and datetime.fromisoformat(event['start']) + timedelta(minutes=30) < now
            < datetime.fromisoformat(event['end']))


def warning_key(event, now):
    remaining = (datetime.fromisoformat(event['end']) - now).total_seconds()
    return f"{event['id']}:{event['end']}" if 0 < remaining <= 1800 else None
