from pathlib import Path
import json, hashlib, shutil
root=Path(__file__).parent
base=root/'custom_components/desk_booking'
backup=root/'backups/pre-0142'
shutil.copytree(base,backup)
p=base/'frontend/desk-booking-floorplan.js'
s=p.read_text(encoding='utf-8')
needle='${markers}</div></div></div>`'
assert s.count(needle)==1
s=s.replace(needle,'${markers}</div></div>${d.booking_url?`<a class="reserve map-reserve" href="${esc(d.booking_url)}" target="_blank" rel="noopener noreferrer">Reservieren</a>`:\'\'}</div>`')
s=s.replace('.mapframe{position:relative}', '.mapframe{position:relative}.map-reserve{position:absolute;left:12px;bottom:12px;z-index:10;margin:0;box-shadow:0 2px 8px #0002}.map-reserve:focus-visible{outline:3px solid #48a7b0;outline-offset:2px}')
p.write_text(s,encoding='utf-8')
p=base/'manifest.json';data=json.loads(p.read_text());data['version']='0.14.2';p.write_text(json.dumps(data,indent=2)+'\n')
manifest={p.relative_to(backup).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in backup.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
(root/'dist/desk-booking-0.14.1-baseline.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
installer=(root/'install_features_0141.py').read_text().replace('0.14.1','0.14.2').replace("== '0.14.0'","== '0.14.1'").replace('0.14.0-baseline','0.14.1-baseline').replace('0141','0142')
(root/'install_features_0142.py').write_text(installer)
