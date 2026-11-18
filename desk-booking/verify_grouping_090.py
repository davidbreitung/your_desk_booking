"""Read-only post-deployment comparison; print counts and changed keys only."""
from pathlib import Path
import hashlib
import json

root = Path('/config')
eid = '01M7FSZBDNKBGJSMM0YE4B6WNG'
before = json.loads((root / 'desk-booking-090-baseline.json').read_text())
entry = next(e for e in json.loads((root / '.storage/core.config_entries').read_text())['data']['entries'] if e['entry_id'] == eid)
entities = [e for e in json.loads((root / '.storage/core.entity_registry').read_text())['data']['entities'] if e.get('config_entry_id') == eid]
devices = [d for d in json.loads((root / '.storage/core.device_registry').read_text())['data']['devices'] if d.get('config_entry_id') == eid or eid in d.get('config_entries', [])]
# Live registry snapshot via HA WebSocket API: disk saves may be deferred.
live = json.loads((root / 'grouping-live-registry.json').read_text())
entities, devices = live['entities'], live['devices']
assert entry['version'] == 2
assert len(entry['subentries']) == 3
assert set(s['title'] for s in entry['subentries']) == {'Mitarbeiter','Group','Schreibtisch'}
categories = {s['unique_id'].removeprefix('category:'):s['subentry_id'] for s in entry['subentries']}
records = entry['data']['records']
assert set(records) == {s['subentry_id'] for s in before['subentries']}
assert entry['options'] == before['options']
data_diffs=[]
for old in before['subentries']:
    current=records[old['subentry_id']]
    assert current['unique_id'] == old['unique_id']
    assert current['subentry_type'] == old['subentry_type']
    assert current['title'] == old['title']
    for key in set(old['data']) | set(current['data']):
        if old['data'].get(key) != current['data'].get(key): data_diffs.append(key)
assert set(data_diffs) <= {'occupant','status','selected_profile','applied','previous','display_name'}, sorted(set(data_diffs))
print('RUNTIME_CHANGES:',sorted(set(data_diffs)))
for table, key, preserved in [(entities,'entity_id',('id','unique_id','device_id','name','disabled_by','hidden_by','labels','area_id')),
                               (devices,'id',('identifiers','name','name_by_user','disabled_by','labels','area_id'))]:
    old_table=before['entities' if key=='entity_id' else 'devices']
    assert {x[key] for x in table} == {x[key] for x in old_table}
    for old in old_table:
        current=next(x for x in table if x[key]==old[key])
        assert all(current.get(k)==old.get(k) for k in preserved), 'Registry identity/preferences changed'
        rid=old.get('config_subentry_id')
        target=categories[records[rid]['subentry_type']] if rid in records else rid
        assert current.get('config_subentry_id') == target, (key, {k:v for k,v in old.items() if k.startswith('config_')}, {k:v for k,v in current.items() if k.startswith('config_')}, target)
manifest=json.loads((root/'desk-booking-0.9.0.sha256.json').read_text())
assert all(hashlib.sha256((root/'custom_components/desk_booking'/name).read_bytes()).hexdigest()==digest for name,digest in manifest.items())
print('VERIFIED_090:',len(records),'records;',len(devices),'unchanged device IDs;',len(entities),'unchanged entity IDs; local settings and options preserved;',len(manifest),'source hashes match')
print('CATEGORIES:', {kind:sum(r['subentry_type']==kind for r in records.values()) for kind in categories})
