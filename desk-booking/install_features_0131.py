"""Install reviewed package with an adjacent source backup; leave HA data intact."""
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
import hashlib
import json
import shutil
import ast

root = Path('/config')
package = root / 'desk-booking-0.13.1.zip'
expected = json.loads((root / 'desk-booking-0.13.1.sha256.json').read_text())
component = root / 'custom_components/desk_booking'
assert json.loads((component / 'manifest.json').read_text())['version'] == '0.13.0'
baseline = json.loads((root / 'desk-booking-0.13.0-baseline.sha256.json').read_text())
assert all(hashlib.sha256((component / name).read_bytes()).hexdigest() == digest for name, digest in baseline.items()), 'Live sources differ from reviewed baseline'
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
backup = root / ('desk_booking_backup_0131_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
shutil.copytree(component, backup)
for name, data in files.items():
    target = component / name
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = target.with_suffix(target.suffix + '.staged0131')
    staged.write_bytes(data)
    staged.replace(target)
assert all(hashlib.sha256((component / name).read_bytes()).hexdigest() == digest for name, digest in expected.items())
print('INSTALLED_0131', len(files), 'FILES; BACKUP', backup)

