"""Validated floorplan persistence and timezone-aware day windows."""
import base64
import math
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

MAX_IMAGE_BYTES = 4 * 1024 * 1024


def image_data(value):
    if value == "":
        return value
    if not isinstance(value, str) or len(value) > MAX_IMAGE_BYTES * 4 // 3 + 100:
        raise ValueError("Bild zu groß (maximal 4 MB).")
    head, sep, encoded = value.partition(",")
    allowed = {"data:image/png;base64": b"\x89PNG\r\n\x1a\n",
               "data:image/jpeg;base64": b"\xff\xd8\xff",
               "data:image/webp;base64": b"RIFF"}
    if not sep or head not in allowed:
        raise ValueError("Bitte PNG, JPEG oder WebP auswählen.")
    try:
        data = base64.b64decode(encoded, validate=True)
    except ValueError as err:
        raise ValueError("Ungültiges Bild.") from err
    if len(data) > MAX_IMAGE_BYTES or not data.startswith(allowed[head]):
        raise ValueError("Ungültiges Bild.")
    if head == "data:image/webp;base64" and data[8:12] != b"WEBP":
        raise ValueError("Ungültiges Bild.")
    return value


def finite(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("Ungültige Position oder Größe.")
    return value


def validate_plan(value, resources):
    if not isinstance(value, dict):
        raise ValueError("Ungültiger Plan.")
    plan_id = str(UUID(value["id"]))
    name = value.get("name", "").strip()
    if not name or len(name) > 80 or any(ord(c) < 32 for c in name):
        raise ValueError("Bitte einen Plannamen mit maximal 80 Zeichen eingeben.")
    items, seen = [], set()
    if not isinstance(value.get("items"), list) or len(value["items"]) > 200:
        raise ValueError("Maximal 200 Objekte pro Plan.")
    for item in value["items"]:
        rid = item["resource_id"]
        if rid not in resources or rid in seen:
            raise ValueError("Objekt fehlt oder ist mehrfach im Plan enthalten.")
        seen.add(rid)
        items.append({"resource_id": rid, "x": finite(item["x"], 0, 100),
                      "y": finite(item["y"], 0, 100), "size": finite(item.get("size", 64), 16, 140),
                      "rotation": finite(item.get("rotation", 0), 0, 359),
                      "anchor": "top_left" if item.get("anchor") == "top_left" else "center",
                      "label": bool(item.get("label", True))})
    return {"id": plan_id, "name": name, "image": image_data(value.get("image", "")),
            "aspect": finite(value.get("aspect", 1.6), 0.2, 5), "items": items,
            "object_scale": finite(value.get("object_scale", 100), 25, 150),
            "object_opacity": finite(value.get("object_opacity", 100), 20, 100),
            "white_background": bool(value.get("white_background", True))}


def day_window(selected, now, zone):
    tz = ZoneInfo(zone)
    today = now.astimezone(tz).date()
    day = date.fromisoformat(selected) if selected else today
    if not today <= day <= today + timedelta(days=30):
        raise ValueError("Bitte einen Tag zwischen heute und in 30 Tagen wählen.")
    start = datetime.combine(day, time(), tz)
    end = datetime.combine(day + timedelta(days=1), time(), tz)
    return day, start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def day_events(events, start, end):
    return [e for e in events if datetime.fromisoformat(e["start"]) < end and datetime.fromisoformat(e["end"]) > start]
