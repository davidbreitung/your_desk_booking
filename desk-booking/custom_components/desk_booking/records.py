"""Stable cloud records, independent of the UI category subentries."""
from dataclasses import dataclass
from types import MappingProxyType

KINDS = {"employee": "Mitarbeiter", "group": "Group", "desk": "Schreibtisch", "room": "Raum"}


@dataclass(frozen=True)
class Record:
    subentry_id: str
    subentry_type: str
    title: str
    unique_id: str | None
    data: dict


def records(entry):
    stored = getattr(entry, "data", {}).get("records")
    if stored is None:
        return entry.subentries
    return {key: Record(key, **value) for key, value in stored.items()}


def records_of_type(entry, kind):
    if "records" not in getattr(entry, "data", {}):
        return list(entry.get_subentries_of_type(kind))
    return [item for item in records(entry).values() if item.subentry_type == kind]


def category_id(entry, record):
    if "records" not in getattr(entry, "data", {}):
        return record.subentry_id
    return next(item.subentry_id for item in entry.subentries.values()
                if item.unique_id == f"category:{record.subentry_type}")


def serialize(record):
    return {"subentry_type": record.subentry_type, "title": record.title,
            "unique_id": record.unique_id, "data": dict(record.data)}


def add_record(hass, entry, record):
    # Do not recreate a locally removed retired object from an older cache.
    if record.subentry_id not in records(entry) and not record.data.get('active', True):
        return False
    if "records" not in getattr(entry, "data", {}):
        return hass.config_entries.async_add_subentry(entry, record)
    stored = dict(entry.data["records"])
    if any(key != record.subentry_id and value["unique_id"] == record.unique_id
           for key, value in stored.items() if record.unique_id is not None):
        raise ValueError("Duplicate cloud record identity")
    stored[record.subentry_id] = serialize(record)
    return hass.config_entries.async_update_entry(entry, data={**entry.data, "records": stored})


def update_record(hass, entry, current, **updates):
    if "records" not in getattr(entry, "data", {}):
        return hass.config_entries.async_update_subentry(entry, current, **updates)
    latest = records(entry)[current.subentry_id]
    value = serialize(latest)
    value.update(updates)
    return add_record(hass, entry, Record(current.subentry_id, **value))


def ensure_categories(hass, entry):
    """Copy data before moving registries; repeat safely after interrupted startup.

    Only association fields change. Entity IDs, unique IDs, device IDs, user
    overrides, disabled entities, recorder references and record data survive.
    Call before platforms/listeners start. Never modify HA storage files.
    """
    from homeassistant.config_entries import ConfigSubentry
    from homeassistant.helpers import device_registry as dr, entity_registry as er

    legacy = [s for s in entry.subentries.values() if s.subentry_type in KINDS]
    stored = dict(entry.data.get("records", {}))
    for item in legacy:
        stored.setdefault(item.subentry_id, serialize(item))
    hass.config_entries.async_update_entry(entry, data={**entry.data, "records": stored})
    for kind, title in KINDS.items():
        if not any(s.unique_id == f"category:{kind}" for s in entry.subentries.values()):
            hass.config_entries.async_add_subentry(entry, ConfigSubentry(
                data=MappingProxyType({"record_type": kind}), subentry_type="category",
                title=title, unique_id=f"category:{kind}"))
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    targets = {key: category_id(entry, record) for key, record in records(entry).items()}
    for device in list(dr.async_entries_for_config_entry(device_registry, entry.entry_id)):
        record_id = next((identifier for domain, identifier in device.identifiers
                          if domain == "desk_booking" and identifier in targets), None)
        if record_id and device.config_subentry_id != targets[record_id]:
            device_registry.async_update_device(device.id, new_config_subentry_id=targets[record_id])
    for entity in list(er.async_entries_for_config_entry(entity_registry, entry.entry_id)):
        record_id = entity.unique_id.split("_", 1)[0]
        if record_id in targets and entity.config_subentry_id != targets[record_id]:
            entity_registry.async_update_entity(entity.entity_id, config_subentry_id=targets[record_id])
    # No active registry entries may still refer to a legacy subentry.
    legacy_ids = {s.subentry_id for s in legacy}
    assert not any(d.config_subentry_id in legacy_ids for d in
                   dr.async_entries_for_config_entry(device_registry, entry.entry_id))
    assert not any(e.config_subentry_id in legacy_ids for e in
                   er.async_entries_for_config_entry(entity_registry, entry.entry_id))
    for item in legacy:
        hass.config_entries.async_remove_subentry(entry, item.subentry_id)
