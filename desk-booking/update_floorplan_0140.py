"""Apply reviewed frontend and translation changes for 0.14.0."""
from pathlib import Path
import json

base = Path(__file__).parent / 'custom_components/desk_booking'
path = base / 'frontend/desk-booking-floorplan.js'
s = path.read_text(encoding='utf-8')
s = s.replace("title:'Raumplan',default_time:", "title:'Raumplan',eyebrow:'DESK BOOKING',show_title:true,show_eyebrow:true,default_time:")
s = s.replace('  startEdit(fresh=false){', '''  async requestEdit(fresh=false){
    if(!this.data?.can_edit)return;
    if(this.data.edit_password_required){this.passwordPrompt=true;this.editFresh=fresh;this.authError='';this.render();this.shadowRoot.getElementById('edit_password')?.focus();return;}
    this.editToken='';this.startEdit(fresh);
  }
  async unlock(){
    const password=this.shadowRoot.getElementById('edit_password')?.value||'';
    this.shadowRoot.getElementById('edit_password').value='';
    try{const result=await this.ws('authorize',{password});this.editToken=result.token;this.passwordPrompt=false;this.startEdit(this.editFresh);}
    catch{this.authError='Kennwort nicht bestätigt. Nach mehreren Versuchen bitte eine Minute warten.';this.render();}
  }
  startEdit(fresh=false){''')
s=s.replace("this.ws('save',this.draft)","this.ws('save',{...this.draft,edit_token:this.editToken||''})")
s=s.replace("()=>this.startEdit()", "()=>this.requestEdit()")
s=s.replace("()=>this.startEdit(true)", "()=>this.requestEdit(true)")

# Move header, navigation, time selection and editing controls below the map.
head_start=s.index('      <div class="head">')
head_end=s.index('\n      ${this.error?',head_start)
head=s[head_start:head_end]
head=head.replace('<div class="eyebrow">DESK BOOKING</div><h2>${esc(this.config.title||p?.name||\'Raumplan\')}</h2>', '${this.config.show_eyebrow!==false?`<div class="eyebrow">${esc(this.config.eyebrow??\'DESK BOOKING\')}</div>`:\'\'}${this.config.show_title!==false?`<h2>${esc(this.config.title??\'Raumplan\')}</h2>`:\'\'}')
live='${d?`<span class="live ${this.live?\'\':\'off\'}">${this.live?\'● LIVE\':\'PLANUNG\'}</span>`:\'\'}'
assert live in head
head=head.replace(live,'')
s=s[:head_start]+s[head_end:]
toolbar_start=s.index('      <div class="toolbar">')
map_start=s.index('      ${p?`<div class="viewport">',toolbar_start)
controls=s[toolbar_start:map_start]
summary_start=controls.index(':`<div class="summary">')+1
summary=controls.rstrip()[summary_start:-1]
controls=controls[:summary_start-1]+":''}"+'\n'
# Overlay is outside the scrollable canvas, so it stays in its corner while zooming.
s=s[:toolbar_start]+s[map_start:]
map_end=s.index('\n      ${unavailable.length?',toolbar_start)
map_html=s[toolbar_start:map_end]
map_html=map_html.replace('${p?`<div class="viewport">','${p?`<div class="mapframe"><div class="overlays">${!this.editing?'+summary+":''}"+'<span class="live ${this.live?\'\':\'off\'}">${this.live?\'● LIVE\':\'PLANUNG\'}</span></div><div class="viewport">')
map_html=map_html.replace('${markers}</div></div>`','${markers}</div></div></div>`')
s=s[:toolbar_start]+map_html+'\n'+head+'\n'+controls+s[map_end:]
s=s.replace('    </ha-card>`;', '''      ${this.passwordPrompt?`<div class="password-backdrop"><form id="unlock_form" class="password-dialog" role="dialog" aria-modal="true" aria-labelledby="password_title"><h3 id="password_title">Raumplan bearbeiten</h3><label>Kennwort<input id="edit_password" type="password" maxlength="256" autocomplete="off" required></label>${this.authError?`<p role="alert">${esc(this.authError)}</p>`:''}<button type="button" id="unlock_cancel">Abbrechen</button><button type="submit" class="primary">Entsperren</button></form></div>`:''}
    </ha-card>`;''')
s=s.replace("!e.target.closest('.marker,.details')", "!e.target.closest('.marker,.details,.password-dialog')")
s=s.replace("const q=id=>this.shadowRoot.getElementById(id);", "const q=id=>this.shadowRoot.getElementById(id);")
s=s.replace("    on('edit','click'", "    on('unlock_form','submit',e=>{e.preventDefault();this.unlock();});on('unlock_cancel','click',()=>{this.passwordPrompt=false;this.render();});\n    on('edit','click'")
s=s.replace("this.editing=false;this.draft=null;this.selected=null;", "this.editing=false;this.editToken='';this.draft=null;this.selected=null;")
s=s.replace("</p>${!r.fresh?", '''</p>${s.state==='free'&&this.data.booking_url?`<a class="reserve" href="${esc(this.data.booking_url)}" target="_blank" rel="noopener noreferrer">Reservieren</a>`:''}${!r.fresh?''')
s=s.replace("const STYLE=`", """const STYLE=`
.mapframe{position:relative}.overlays{position:absolute;inset:12px 12px auto;z-index:10;display:flex;align-items:flex-start;gap:12px;pointer-events:none}.overlays .summary{padding:9px 12px;border-radius:12px;background:var(--ha-card-background,#fff);box-shadow:0 2px 8px #0002;max-width:calc(100% - 100px);flex:1 1 auto;width:max-content;margin-right:auto;flex-grow:0}.overlays .live{margin-left:auto;flex-shrink:0}.reserve{display:inline-block;text-decoration:none;background:#236c70;color:white;padding:10px 16px;border-radius:9px;margin-bottom:12px}.password-backdrop{position:absolute;inset:0;z-index:30;background:#0007;display:flex;align-items:center;justify-content:center;padding:20px}.password-dialog{max-width:400px;width:100%;padding:24px;border-radius:14px;background:var(--ha-card-background,#fff)}.password-dialog label{display:block;margin-bottom:20px}.password-dialog input{display:block;width:100%;margin-top:8px}.password-dialog p{color:var(--error-color,#c44949)}ha-card{position:relative}
""")
# Editor retains backward-compatible defaults, with independent heading visibility.
s=s.replace('<label>Kartentitel<input id="title" value="${esc(this.config.title||\'Raumplan\')}"></label>', '''<label>Obere Überschrift<input id="eyebrow" value="${esc(this.config.eyebrow??'DESK BOOKING')}"></label><label><input id="show_eyebrow" type="checkbox" ${this.config.show_eyebrow!==false?'checked':''}> Obere Überschrift anzeigen</label><label>Kartentitel<input id="title" value="${esc(this.config.title??'Raumplan')}"></label><label><input id="show_title" type="checkbox" ${this.config.show_title!==false?'checked':''}> Kartentitel anzeigen</label>''')
s=s.replace('[e.target.id]:e.target.value','[e.target.id]:e.target.type===\'checkbox\'?e.target.checked:e.target.value')
s=s.replace("input,select{display:block;margin-top:6px", "input[type=checkbox]{width:auto;display:inline-block}input,select{display:block;margin-top:6px")
path.write_text(s,encoding='utf-8')

for path in [base/'strings.json', *sorted((base/'translations').glob('*.json'))]:
    data=json.loads(path.read_text(encoding='utf-8'))
    options=data['options']
    options['step']['init']['menu_options']['floorplan']='Raumplan · Reservierungslink und Kennwort'
    options['step']['floorplan']={'title':'Raumplan · zentrale Einstellungen','description':'Der Reservierungslink öffnet sich in einem neuen Fenster. Kennwortschutz: {password_status}. Ein leeres Kennwortfeld behält das bisherige Kennwort. Ohne hinterlegtes Kennwort entfällt die Abfrage. Bearbeiten bleibt auf Administratoren beschränkt.','data':{'booking_url':'Reservierungs-URL (HTTPS)','password':'Neues Kennwort für Plan bearbeiten und + Plan','clear_password':'Kennwort entfernen'}}
    options.setdefault('error',{})['invalid_floorplan_settings']='Bitte eine gültige HTTPS-Adresse und ein Kennwort mit höchstens 256 Zeichen eingeben.'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
path=base/'manifest.json';data=json.loads(path.read_text());data['version']='0.14.0';path.write_text(json.dumps(data,indent=2)+'\n')
