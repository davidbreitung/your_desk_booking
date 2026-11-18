"""All directory groups and ID-based membership, including nested groups."""
from .records import records, records_of_type



def group_updates(current_groups, snapshot):
    tenant = snapshot["tenant_id"]
    groups = snapshot["groups"]
    current = {g.data.get("object_id"): g for g in current_groups if g.data.get("tenant_id") == tenant}
    result = []
    for oid, group in groups.items():
        if (not isinstance(oid, str) or not isinstance(group, dict)
                or not isinstance(group.get("members", []), list)
                or any(not isinstance(m, str) for m in group.get("members", []))):
            raise ValueError("Invalid group")
        old = current.get(oid)
        active = True
        data = dict(old.data) if old else {}
        data.update(source="m365", tenant_id=tenant, object_id=oid,
                    name=group.get("displayName") or oid, active=active,
                    security_enabled=group.get("securityEnabled") is True,
                    mail=group.get("mail"), description=group.get("description"), member_ids=list(group.get("members", [])))
        result.append((old, data))
    for oid, old in current.items():
        if oid not in groups and old.data.get("active"):
            result.append((old, {**old.data, "active": False, "member_ids": []}))
    return result


def member_ids(group_id, groups):
    result, visited, pending = set(), set(), [group_id]
    while pending:
        oid = pending.pop()
        if oid in visited:
            continue
        visited.add(oid)
        for member in groups.get(oid, {}).get("members", []):
            if member in groups:
                pending.append(member)
            else:
                result.add(member)
    return result


def recipient_devices(entry, group_id, snapshot):
    group = records(entry).get(group_id)
    if not group or not group.data.get("active") or group.data.get("tenant_id") != snapshot.get("tenant_id"):
        return []
    members = member_ids(group.data["object_id"], snapshot.get("groups", {}))
    devices = set()
    for desk in records_of_type(entry, "desk"):
        if not desk.data.get("active", True) or desk.data.get("status") != "checked_in" or not desk.data.get("display_device"):
            continue
        employee = records(entry).get(desk.data.get("occupant"))
        if (employee and employee.subentry_type == "employee" and employee.data.get("active")
                and employee.data.get("tenant_id") == group.data["tenant_id"]
                and employee.data.get("object_id") in members):
            devices.add(desk.data["display_device"])
    return sorted(devices)
