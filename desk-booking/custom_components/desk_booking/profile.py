"""Pure validation logic. No Microsoft calls or hardware control."""

from math import isfinite
from uuid import UUID

from .const import DEFAULT_SITTING, DEFAULT_STANDING, MAX_HEIGHT, MIN_HEIGHT


class ProfileError(ValueError):
    """A field validation error safe to expose in the UI."""

    def __init__(self, field: str, code: str) -> None:
        self.field = field
        self.code = code
        super().__init__(code)


def validate_heights(sitting: float, standing: float) -> None:
    for field, value in (("sitting_height", sitting), ("standing_height", standing)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ProfileError(field, "invalid_height")
        if not isfinite(value) or not MIN_HEIGHT <= value <= MAX_HEIGHT:
            raise ProfileError(field, "invalid_height")
    if sitting >= standing:
        raise ProfileError("base", "height_order")


def normalize_profile(data: dict) -> dict:
    result = dict(data)
    name = str(result.get("name", "")).strip()
    if not name or len(name) > 100:
        raise ProfileError("name", "invalid_name")
    result["name"] = name
    result["test_profile"] = bool(result.get("test_profile", False))
    if result["test_profile"]:
        identifier = str(result.get("object_id", "")).strip()
        if not identifier or len(identifier) > 100:
            raise ProfileError("object_id", "invalid_test_id")
        result["object_id"] = identifier
        result["tenant_id"] = ""
    else:
        for field in ("tenant_id", "object_id"):
            try:
                value = UUID(str(result.get(field, "")).strip())
                if value.int == 0:
                    raise ValueError
                result[field] = str(value)
            except (ValueError, AttributeError) as err:
                raise ProfileError(field, "invalid_uuid") from err
    # Tag strings are opaque and case-sensitive, matching HA tag_scanned IDs.
    tag = str(result.get("nfc_tag_id", "")).strip()
    if len(tag) > 255 or any(ord(c) < 32 for c in tag):
        raise ProfileError("nfc_tag_id", "invalid_tag")
    result["nfc_tag_id"] = tag
    result["active"] = bool(result.get("active", True))
    result.setdefault("sitting_height", DEFAULT_SITTING)
    result.setdefault("standing_height", DEFAULT_STANDING)
    validate_heights(result["sitting_height"], result["standing_height"])
    return result


def identity(data: dict) -> str:
    if data["test_profile"]:
        return f"test:{data['object_id']}"
    return f"entra:{data['tenant_id']}:{data['object_id']}"


def profile_title(data: dict) -> str:
    return f"[TEST] {data['name']}" if data["test_profile"] else data["name"]


def validate_unique(data: dict, profiles, exclude_id: str | None = None) -> None:
    for subentry in profiles:
        if subentry.subentry_id == exclude_id:
            continue
        if identity(data) == identity(subentry.data):
            raise ProfileError("object_id", "duplicate_identity")
        if data["nfc_tag_id"] and data["nfc_tag_id"] == subentry.data.get("nfc_tag_id"):
            raise ProfileError("nfc_tag_id", "duplicate_tag")
