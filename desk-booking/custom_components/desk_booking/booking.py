"""Calendar projection with explicit Entra identity and strict time boundaries."""
from datetime import datetime, timezone
from math import ceil
from .graph import GraphError


def graph_time(value):
    if not isinstance(value, dict) or not isinstance(value.get("dateTime"), str):
        raise GraphError("invalid_response")
    result = datetime.fromisoformat(value["dateTime"].replace("Z", "+00:00"))
    if result.tzinfo is None:
        # Graph calendarView defaults to UTC when no Prefer timezone is sent.
        if value.get("timeZone") not in ("UTC", "Etc/UTC", "GMT"):
            raise GraphError("invalid_response")
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def email_index(users):
    result = {}
    for oid, user in users.items():
        addresses = [user.get("mail"), user.get("userPrincipalName")]
        addresses += [p.split(":", 1)[1] for p in user.get("proxyAddresses", []) if isinstance(p, str) and p.lower().startswith("smtp:")]
        for value in addresses:
            if isinstance(value, str) and value.strip():
                result.setdefault(value.strip().casefold(), set()).add(oid)
    return result


def project_events(events, users):
    index, result = email_index(users), {}
    principals = {}
    for oid, user in users.items():
        upn = user.get("userPrincipalName")
        if isinstance(upn, str) and upn.strip():
            principals.setdefault(upn.strip().casefold(), set()).add(oid)
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("id"), str):
            raise GraphError("invalid_response")
        if event.get("isCancelled") is True or event.get("showAs") == "free" or (event.get("responseStatus") or {}).get("response") == "declined":
            continue
        start, end = graph_time(event.get("start")), graph_time(event.get("end"))
        if end <= start:
            raise GraphError("invalid_response")
        organizer = ((event.get("organizer") or {}).get("emailAddress") or {}).get("address", "")
        address = organizer.strip().casefold()
        # Entra UPN is a unique account identifier; mail/proxyAddresses are not.
        # Match the exact principal first, never a display name or fuzzy address.
        candidates = principals.get(address) or index.get(address, set())
        oid = next(iter(candidates)) if len(candidates) == 1 else None
        result[event["id"]] = {"id": event["id"], "start": start.isoformat(), "end": end.isoformat(),
                               "organizer_name": ((event.get("organizer") or {}).get("emailAddress") or {}).get("name") or organizer,
                               "booker_object_id": oid, "identity_status": "resolved" if oid else "ambiguous" if candidates else "unresolved"}
    return sorted(result.values(), key=lambda e: (e["start"], e["id"]))


def next_event(events, now):
    # An ongoing reservation is not a future reservation. It must not keep the
    # yellow warning active or hide the following booking.
    return next((e for e in events if datetime.fromisoformat(e["start"]) > now), None)


def active_event(events, now):
    return next((e for e in events if datetime.fromisoformat(e["start"]) <= now < datetime.fromisoformat(e["end"])), None)


def booking_presentation(event, now, tz):
    if event is None:
        return {"label": "Keine weitere Buchung (365 Tage)", "minutes": None, "warning": False}
    start = datetime.fromisoformat(event["start"])
    seconds = (start - now).total_seconds()
    if seconds <= 0:
        return {"label": "Buchung gestartet", "minutes": 0, "warning": False}
    minutes = ceil(seconds / 60)
    return {"label": f"In {minutes} Minuten" if seconds < 7200 else start.astimezone(tz).strftime("%d.%m.%Y %H:%M"),
            "minutes": minutes, "warning": seconds < 3600}
