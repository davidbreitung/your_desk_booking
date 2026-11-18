"""Pure Places projection. Cloud metadata never owns local desk controls."""
from .graph import GraphError


def resource_users(snapshot):
    """Match mailbox identity, never names or the employee assigned to a desk."""
    users = snapshot["users"]
    by_email = {}
    for oid, user in users.items():
        for field in ("mail", "userPrincipalName"):
            email = user.get(field)
            if email:
                by_email.setdefault(email.casefold(), set()).add(oid)
    matched = {}
    for place_id, place in snapshot.get("places", {}).items():
        mailbox = place.get("mailboxDetails") or {}
        if not isinstance(mailbox, dict):
            raise GraphError("invalid_response")
        oid = mailbox.get("externalDirectoryObjectId")
        email = mailbox.get("emailAddress") or place.get("emailAddress")
        candidates = {key for key in users if oid and key.casefold() == oid.casefold()}
        if email:
            candidates |= by_email.get(email.casefold(), set())
        if len(candidates) > 1:
            raise GraphError("ambiguous_place_identity")
        for key in candidates:
            if key in matched and matched[key] != place_id:
                raise GraphError("ambiguous_place_identity")
            matched[key] = place_id
    return matched


def desk_identity(tenant, place_id):
    return f"places:{tenant}:{place_id}"


def room_updates(rooms, snapshot):
    """Project room metadata only; rooms never receive desk controls or state."""
    if "places" not in snapshot:
        return []
    tenant = snapshot["tenant_id"]
    resources = resource_users(snapshot)
    existing = {r.data.get("place_id"): r for r in rooms
                if r.data.get("tenant_id") == tenant and r.data.get("source") == "places"}
    changes, present = [], set()
    for place_id, place in snapshot["places"].items():
        if place.get("kind") != "room":
            continue
        present.add(place_id)
        current = existing.get(place_id)
        name = place.get("displayName") or place_id
        if not isinstance(name, str) or any(ord(c) < 32 for c in name):
            raise GraphError("invalid_response")
        mailbox = place.get("mailboxDetails") or {}
        oid = next((key for key, value in resources.items() if value == place_id), None)
        email = mailbox.get("emailAddress") or place.get("emailAddress")
        data = dict(current.data) if current else {}
        data.update(source="places", tenant_id=tenant, place_id=place_id,
                    name=name[:60], places_name=name, places_kind="room",
                    places_parent_id=place.get("parentId"), places_email=email,
                    object_id=oid, calendar_mailbox=mailbox.get("externalDirectoryObjectId") or oid or email,
                    active=True)
        changes.append((current, data))
    for place_id, current in existing.items():
        if place_id not in present:
            retired_name = (current.data.get("places_name") or current.data["name"])[:60] + " (inaktiv)"
            if current.data.get("active", True) or current.data["name"] != retired_name:
                changes.append((current, {**current.data, "active": False, "name": retired_name}))
    return changes


def desk_updates(desks, profiles, snapshot):
    """Return managed desk changes, including lossless employee reclassification."""
    if "places" not in snapshot:
        return []  # A 0.6 cache cannot prove a resource's type.
    tenant = snapshot["tenant_id"]
    resources = resource_users(snapshot)
    existing = {d.data.get("place_id"): d for d in desks if d.data.get("tenant_id") == tenant and d.data.get("source") == "places"}
    employees = {p.data.get("object_id"): p for p in profiles if p.data.get("tenant_id") == tenant}
    changes, present = [], set()
    for place_id, place in snapshot["places"].items():
        if place.get("kind") != "desk":
            continue
        present.add(place_id)
        oid = next((key for key, value in resources.items() if value == place_id), None)
        current = existing.get(place_id) or employees.get(oid)
        data = dict(current.data) if current else {}
        name = place.get("displayName") or place_id
        if not isinstance(name, str) or any(ord(c) < 32 for c in name):
            raise GraphError("invalid_response")
        mode = place.get("mode") or {}
        if not isinstance(mode, dict):
            raise GraphError("invalid_response")
        source_mode = mode.get("@odata.type", "").rsplit(".", 1)[-1]
        data.update(source="places", tenant_id=tenant, place_id=place_id,
                    calendar_mailbox=(place.get("mailboxDetails") or {}).get("externalDirectoryObjectId") or (place.get("mailboxDetails") or {}).get("emailAddress"),
                    places_name=name, places_kind=place["kind"], places_parent_id=place.get("parentId"),
                    places_mode=source_mode, places_email=(place.get("mailboxDetails") or {}).get("emailAddress") or place.get("emailAddress"),
                    active=source_mode != "unavailablePlaceMode")
        if oid:
            data["object_id"] = oid
        # A local alias and every existing display/accessory/booking preference survive.
        if not current or current.subentry_type != "desk":
            data["name"] = name[:60]
        data.setdefault("display_device", None)
        data.setdefault("display_name", data["name"])
        data.setdefault("light_entities", [])
        data.setdefault("light_details", {})
        data.setdefault("status", "free")
        changes.append((current, data))
    for place_id, current in existing.items():
        if place_id not in present and current.data.get("active", True):
            changes.append((current, {**current.data, "active": False}))
    return changes
