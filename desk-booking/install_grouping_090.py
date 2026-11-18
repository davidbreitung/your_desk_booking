"""Install reviewed package with an adjacent source backup; leave HA data intact."""
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
import hashlib
import json
import shutil
import ast

root = Path('/config')
package = root / 'desk-booking-0.9.0.zip'
expected = json.loads((root / 'desk-booking-0.9.0.sha256.json').read_text())
component = root / 'custom_components/desk_booking'
assert json.loads((component / 'manifest.json').read_text())['version'] == '0.8.1'
with ZipFile(package) as archive:
    files = {name.removeprefix('custom_components/desk_booking/'): archive.read(name) for name in archive.namelist()}
assert set(files) == set(expected)
for name, data in files.items():
    path = (component / name).resolve()
    assert path.is_relative_to(component.resolve())
    assert hashlib.sha256(data).hexdigest() == expected[name]
    if name.endswith('.py'):
        ast.parse(data)
    if name.endswith('.json'):
        json.loads(data)
backup = root / ('desk_booking_backup_090_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
shutil.copytree(component, backup)
# Retain a private local baseline for post-migration identity/data comparison.
entry_id = '01M7FSZBDNKBGJSMM0YE4B6WNG'
config = json.loads((root / '.storage/core.config_entries').read_text())
entry = next(e for e in config['data']['entries'] if e['entry_id'] == entry_id)
entities = json.loads((root / '.storage/core.entity_registry').read_text())['data']['entities']
devices = json.loads((root / '.storage/core.device_registry').read_text())['data']['devices']
baseline = {'subentries': entry['subentries'], 'options':entry['options'],
    'entities':[e for e in entities if e.get('config_entry_id') == entry_id],
    'devices':[d for d in devices if d.get('config_entry_id') == entry_id or entry_id in d.get('config_entries', [])]}
(root / 'desk-booking-090-baseline.json').write_text(json.dumps(baseline))
print('BASELINE',len(baseline['subentries']),'RECORDS',len(baseline['devices']),'DEVICES',len(baseline['entities']),'ENTITIES')
for name, data in files.items():
    target = component / name
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = target.with_suffix(target.suffix + '.staged090')
    staged.write_bytes(data)
    staged.replace(target)
assert all(hashlib.sha256((component / name).read_bytes()).hexdigest() == digest for name, digest in expected.items())
print('INSTALLED_090', len(files), 'FILES; BACKUP', backup)

