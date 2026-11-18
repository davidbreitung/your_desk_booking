"""Pure directory projection; Graph never owns local preferences or history."""
from .profile import identity, normalize_profile
from .graph import GraphError
from .places import resource_users


def profile_updates(profiles, snapshot, excluded=()):
    tenant = snapshot["tenant_id"]
    users = snapshot["users"]
    existing = {identity(p.data): p for p in profiles}
    updates = []
    resources = set(resource_users(snapshot)) | set(excluded)
    for oid, user in users.items():
        if not isinstance(user.get("accountEnabled"), bool) or user.get("userType") not in ("Member", "Guest"):
            raise GraphError("invalid_response")
        uid = f"entra:{tenant}:{oid}"
        current = existing.get(uid)
        active = user.get("accountEnabled") is True and user.get("userType") == "Member" and oid not in resources
        if not current and not active:
            continue
        data = dict(current.data) if current else {}
        data["resource_account"] = oid in resources
        data.update({"source": "m365", "test_profile": False, "tenant_id": tenant, "object_id": oid,
                     "name": user.get("displayName") or user.get("userPrincipalName") or oid,
                     "active": active, "mail": user.get("mail"), "user_principal_name": user.get("userPrincipalName"),
                     "department": user.get("department"), "job_title": user.get("jobTitle"),
                     "group_ids": sorted(gid for gid, group in snapshot["groups"].items() if oid in group.get("members", []))})
        updates.append((current, normalize_profile(data)))
    for current in profiles:
        data = current.data
        if (data.get("test_profile") or data.get("tenant_id") != tenant or data.get("object_id") not in users) and data.get("active"):
            updates.append((current, {**data, "active": False}))
    return updates
