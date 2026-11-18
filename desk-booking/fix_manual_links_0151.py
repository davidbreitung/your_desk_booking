from pathlib import Path
import json,shutil,hashlib
root=Path(__file__).parent;base=root/'custom_components/desk_booking'
backup=root/'backups/pre-0151'
# Baseline uses the exact package installed on HA, before this manual edit.
old=json.loads((root/'dist/desk-booking-0.15.0.sha256.json').read_text())
(root/'dist/desk-booking-0.15.0-baseline.sha256.json').write_text(json.dumps(old,indent=2)+'\n')
shutil.copytree(base,backup)
for path in [base/'strings.json',*sorted((base/'translations').glob('*.json'))]:
    data=json.loads(path.read_text(encoding='utf-8'))
    data['options']['step']['manuals']['description']='Die Handbücher gehören zur installierten Integrationsversion und öffnen separat im Browser.\n\n<p><a href="/desk_booking_static/docs/benutzer.html" target="_blank">Benutzerhandbuch öffnen</a></p>\n<p><a href="/desk_booking_static/docs/administrator.html" target="_blank">Administratorhandbuch öffnen</a></p>\n\nBeide Handbücher bieten Inhaltsverzeichnis, Suche und Drucken / als PDF speichern.\n\n<p>Markdown-Quellen: <a href="/desk_booking_static/docs/benutzer.md" target="_blank">Benutzer</a> · <a href="/desk_booking_static/docs/administrator.md" target="_blank">Administrator</a></p>\n\nZurück mit Absenden. Es werden keine Einstellungen geändert.'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=base/'manifest.json';data=json.loads(p.read_text());data['version']='0.15.1';p.write_text(json.dumps(data,indent=2)+'\n')
installer=(root/'install_features_0150.py').read_text().replace('0.15.0','0.15.1').replace("== '0.14.2'","== '0.15.0'").replace('0.14.2-baseline','0.15.0-baseline').replace('0150','0151')
(root/'install_features_0151.py').write_text(installer)
