from pathlib import Path
import json, hashlib, ast
root=Path(__file__).parent
component=root/'custom_components/desk_booking'
p=component/'frontend/desk-booking-floorplan.js'
s=p.read_text(encoding='utf-8').replace('if(!this._hass||this.editing)return;', 'if(!this._hass||this.editing||this.passwordPrompt)return;')
s=s.replace("if(e.key==='Escape'&&!this.editing){this.selected=null;this.render();}", "if(e.key==='Escape'&&!this.editing){this.selected=null;this.passwordPrompt=false;this.render();}")
p.write_text(s,encoding='utf-8')
baseline=root/'backups/pre-0140-20261116-135547/desk_booking'
manifest={p.relative_to(baseline).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in baseline.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
(root/'dist/desk-booking-0.13.2-baseline.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
installer=(root/'install_features_0132.py').read_text().replace('0.13.2','0.14.0').replace("== '0.13.1'","== '0.13.2'").replace('0.13.1-baseline','0.13.2-baseline').replace('0132','0140')
(root/'install_features_0140.py').write_text(installer)
for path in component.rglob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
print('Prepared 0.14.0; baseline files',len(manifest))
