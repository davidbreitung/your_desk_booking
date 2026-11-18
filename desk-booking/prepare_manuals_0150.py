from pathlib import Path
import json,hashlib
root=Path(__file__).parent
base=root/'custom_components/desk_booking'
for path in [base/'strings.json',*sorted((base/'translations').glob('*.json'))]:
    data=json.loads(path.read_text(encoding='utf-8'))
    data['options']['step']['init']['menu_options']['manuals']='Handbücher'
    data['options']['step']['manuals']={'title':'Desk Booking · Handbücher','description':'Die Handbücher gehören zur installierten Integrationsversion. Sie enthalten alle aktuellen Bedienabläufe und Einstellungen.\n\n- [Benutzerhandbuch öffnen](/desk_booking_static/docs/benutzer.html)\n- [Administratorhandbuch öffnen](/desk_booking_static/docs/administrator.html)\n\nBeide Handbücher bieten Inhaltsverzeichnis, Suche und Drucken / als PDF speichern.\n\nMarkdown-Quellen: [Benutzer](/desk_booking_static/docs/benutzer.md) · [Administrator](/desk_booking_static/docs/administrator.md)\n\nZurück mit Absenden. Es werden keine Einstellungen geändert.'}
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=base/'manifest.json';data=json.loads(p.read_text());data['version']='0.15.0';p.write_text(json.dumps(data,indent=2)+'\n')
backup=root/'backups/pre-0150'
manifest={p.relative_to(backup).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in backup.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='PROJECT_README.md'}
(root/'dist/desk-booking-0.14.2-baseline.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
installer=(root/'install_features_0142.py').read_text().replace('0.14.2','0.15.0').replace("== '0.14.1'","== '0.14.2'").replace('0.14.1-baseline','0.14.2-baseline').replace('0142','0150')
(root/'install_features_0150.py').write_text(installer)
print('Prepared manuals release 0.15.0')
