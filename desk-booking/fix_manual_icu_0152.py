from pathlib import Path
import json
root=Path(__file__).parent;base=root/'custom_components/desk_booking'
old=json.loads((root/'dist/desk-booking-0.15.1.sha256.json').read_text())
(root/'dist/desk-booking-0.15.1-baseline.sha256.json').write_text(json.dumps(old,indent=2)+'\n')
for path in [base/'strings.json',*sorted((base/'translations').glob('*.json'))]:
    data=json.loads(path.read_text(encoding='utf-8'))
    data['options']['step']['manuals']['description']='Die Handbücher gehören zur installierten Integrationsversion und öffnen separat im Browser.\n\n{links}\n\nBeide Handbücher bieten Inhaltsverzeichnis, Suche und Drucken / als PDF speichern.\n\nZurück mit OK. Es werden keine Einstellungen geändert.'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=base/'manifest.json';data=json.loads(p.read_text());data['version']='0.15.2';p.write_text(json.dumps(data,indent=2)+'\n')
installer=(root/'install_features_0151.py').read_text().replace('0.15.1','0.15.2').replace("== '0.15.0'","== '0.15.1'").replace('0.15.0-baseline','0.15.1-baseline').replace('0151','0152')
(root/'install_features_0152.py').write_text(installer)
