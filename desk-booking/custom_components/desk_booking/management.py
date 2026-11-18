"""Administrative visibility and inactive-only local deletion."""
from copy import deepcopy
from homeassistant.helpers import entity_registry as er, device_registry as dr
from .records import records, update_record
from .floorplan import KEY


def set_hidden(hass, entry, rid, hidden):
    record = records(entry)[rid]
    update_record(hass, entry, record, data={**record.data, 'hidden': bool(hidden)})


async def delete_inactive(hass, entry, rid):
    runtime = entry.runtime_data
    # Serialize with imports, calendar reads, check-in and reminder delivery.
    async with runtime.directory.lock, runtime.bookings.lock, runtime.mail.lock, runtime.lock:
        record = records(entry).get(rid)
        if not record or record.data.get('active', True):
            raise ValueError('Nur inaktive Objekte können dauerhaft gelöscht werden.')
        if record.data.get('status', 'free') != 'free' or any(r.data.get('occupant') == rid for r in records(entry).values()):
            raise ValueError('Das Objekt ist noch eingecheckt oder einem Check-in zugeordnet. Zuerst auschecken.')
        manager = hass.data[KEY]
        async with manager.lock, manager.photo_lock:
            plans = deepcopy(manager.plans)
            for plan in plans.values():
                items = [i for i in plan['items'] if i['resource_id'] != rid]
                if items != plan['items']:
                    plan['items'] = items
                    plan['revision'] += 1
            await manager.store.async_save({'plans':plans})
            manager.plans = plans
            photo_key = f"{record.data.get('tenant_id')}:{record.data.get('object_id')}"
            photos = {k:v for k,v in manager.photos.items() if k != photo_key}
            await manager.photo_store.async_save({'photos':photos})
            manager.photos = photos
        runtime.bookings.cache.pop(rid, None)
        runtime.bookings.errors.pop(rid, None)
        if not await runtime.bookings._save():
            raise ValueError('Buchungscache konnte nicht gespeichert werden.')
        runtime.mail.history = {k:v for k,v in runtime.mail.history.items() if rid not in (v.get('resource_id'),v.get('employee_id'))}
        await runtime.mail.save()
        registry = er.async_get(hass)
        entities = [e for e in er.async_entries_for_config_entry(registry, entry.entry_id) if e.unique_id.startswith(rid+'_')]
        if entities and hass.services.has_service('recorder','purge_entities'):
            await hass.services.async_call('recorder','purge_entities', {'entity_id':[e.entity_id for e in entities], 'keep_days':0}, blocking=True)
        for entity in entities:
            registry.async_remove(entity.entity_id)
        devices = dr.async_get(hass)
        device = devices.async_get_device_by_identifier(('desk_booking',rid),entry.entry_id)
        if device:
            devices.async_remove_device(device.id)
        stored = dict(entry.data['records'])
        stored.pop(rid)
        hass.config_entries.async_update_entry(entry, data={**entry.data,'records':stored})
        # Reload required also for employees, which normally use dynamic entities.
        hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
