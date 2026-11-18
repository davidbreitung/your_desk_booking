"""Stage and install an already reviewed component bundle on HAOS."""
from pathlib import Path
import datetime
import json
import py_compile
import shutil
import sys

root = Path('/config')
stage = root / 'desk_booking_stage_050' / 'custom_components' / 'desk_booking'
bundle = json.loads((root / 'www/desk-booking-update-050.json').read_text())
stage.mkdir(parents=True, exist_ok=True)
for name, source in bundle.items():
    relative = Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding='utf-8')
    if target.suffix == '.py':
        py_compile.compile(str(target), doraise=True)
print('DESK_BOOKING_STAGE_OK', len(bundle))
if '--install' in sys.argv:
    current = root / 'custom_components/desk_booking'
    backup = root / ('desk_booking_backup_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    shutil.copytree(current, backup)
    for name in bundle:
        target = current / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage / name, target)
    print('DESK_BOOKING_050_INSTALLED; BACKUP', backup)
