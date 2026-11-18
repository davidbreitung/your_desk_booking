import {esc,addDays,initials,timeLabel} from './model.js?v=0.13.0';
import {attendance} from './attendance-model.js?v=0.13.0';

class AttendanceCard extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this.photos=new Map();this.seq=0;this.day='';}
  static getConfigElement(){return document.createElement('desk-booking-attendance-editor');}
  static getStubConfig(){return {title:'Anwesenheit'};}
  setConfig(c){this.config={title:'Anwesenheit',...c};if(this._hass)this.load();else this.render();}
  set hass(h){this._hass=h;if(!this.started&&this.isConnected){this.started=true;this.load();}}
  getCardSize(){return 5;}
  getGridOptions(){return {columns:'full',rows:'auto'};}
  connectedCallback(){this.timer=setInterval(()=>this.load(),30000);if(this._hass){this.started=true;this.load();}}
  disconnectedCallback(){clearInterval(this.timer);this.started=false;this.seq++;}
  ws(action,payload={}){return this._hass.callWS({type:'desk_booking/floorplan',action,payload});}
  async load(){const seq=++this.seq;try{
    const data=await this.ws('snapshot',this.day?{date:this.day}:{});let ids=null;
    if(this.config.plan_id){const plan=await this.ws('get',{id:this.config.plan_id});ids=new Set(plan.items.map(i=>i.resource_id));}
    if(seq!==this.seq||!this.isConnected)return;
    this.data=data;this.rows=attendance(data,ids);this.error='';this.render();
    for(const row of this.rows){const id=row.person.id,old=this.photos.get(id);if(old&&Date.now()-old.at<300000)continue;try{const p=await this.ws('photo',{id});this.photos.set(id,{src:p.image,at:Date.now()});}catch{this.photos.set(id,{src:null,at:Date.now()});}}
    if(seq===this.seq&&this.isConnected)this.render();
  }catch(e){if(seq!==this.seq)return;this.error=e.message||'Daten konnten nicht geladen werden.';this.render();}}
  render(){if(!this.config)return;const d=this.data;this.shadowRoot.innerHTML=`<style>
    :host{display:block}*{box-sizing:border-box}ha-card{display:block;padding:20px;border-radius:18px}h2{font-size:23px;margin:0 0 16px}nav{display:flex;gap:8px;align-items:center;flex-wrap:wrap}button,input{font:inherit;padding:9px;border:1px solid var(--divider-color,#ddd);border-radius:9px;color:var(--primary-text-color);background:var(--card-background-color)}button{cursor:pointer}button:disabled{opacity:.4}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(145px,1fr));gap:22px 14px;margin:25px 0}.person{text-align:center}.photo{margin:auto;width:85px;height:85px;border:4px solid #bd8700;border-radius:50%;background:var(--secondary-background-color);display:grid;place-items:center;font-size:25px;overflow:hidden}.photo.checked{border-color:#247bb5}.photo img{width:100%;height:100%;object-fit:cover}.name{font-weight:600;margin:10px 0 5px}small{display:block;color:var(--secondary-text-color);line-height:1.6}.error{color:#b64040;margin:16px 0}.empty{padding:30px 0;color:var(--secondary-text-color)}
    </style><ha-card><h2>${esc(this.config.title)}</h2>${d?`<nav><button id="prev" ${d.date<=d.today?'disabled':''} aria-label="Vorheriger Tag">←</button><input id="date" type="date" value="${d.date}" min="${d.today}" max="${addDays(d.today,30)}" aria-label="Datum"><button id="next" ${d.date>=addDays(d.today,30)?'disabled':''} aria-label="Nächster Tag">→</button><button id="today">Heute</button></nav>`:''}${this.error?`<div class="error">${esc(this.error)}</div>`:''}${d?`<div class="grid">${(this.rows||[]).map(r=>{const image=this.photos.get(r.person.id)?.src;const period=r.start!==null?timeLabel(r.start,d.timezone)+' – '+(r.end===Date.parse(d.day_end)?'24:00':timeLabel(r.end,d.timezone)):r.checkin_at!==null?'Seit '+timeLabel(r.checkin_at,d.timezone)+' eingecheckt':'Eingecheckt';return `<article class="person"><div class="photo ${r.checked?'checked':''}">${image?`<img src="${esc(image)}" alt="${esc(r.person.name)}">`:esc(initials(r.person.name))}</div><div class="name">${esc(r.person.name)}</div><small>${esc(period)}</small><small>${r.checked?'Eingecheckt':'Reserviert'}${!r.fresh||this.error?' · Daten nicht aktuell':''}</small></article>`;}).join('')}</div>${!this.rows?.length?'<div class="empty">Keine Reservierungen oder Check-ins an diesem Tag.</div>':''}<small>Reservierungen zeigen geplante Anwesenheit. Räume berücksichtigen nur die Buchenden. Zeitspanne: frühester Beginn bis spätestes Ende, einschließlich möglicher Pausen. Zeitzone: ${esc(d.timezone)}.</small>`:'<div class="empty">Lädt …</div>'}</ha-card>`;
    const q=id=>this.shadowRoot.getElementById(id);if(d){q('prev').onclick=()=>{this.day=addDays(d.date,-1);this.load();};q('next').onclick=()=>{this.day=addDays(d.date,1);this.load();};q('today').onclick=()=>{this.day='';this.load();};q('date').onchange=e=>{if(e.target.value){this.day=e.target.value;this.load();}};}}
}

class AttendanceEditor extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});}
  setConfig(c){this.config={...c};this.render();}
  set hass(h){if(!this.loaded){this.loaded=true;h.callWS({type:'desk_booking/floorplan',action:'snapshot'}).then(d=>{this.plans=d.plans;this.render();}).catch(()=>{});}}
  render(){if(!this.config)return;this.shadowRoot.innerHTML=`<style>label{display:block;margin:16px 0}input,select{display:block;padding:10px;margin-top:6px;width:100%;box-sizing:border-box}</style><label>Titel<input id="title" value="${esc(this.config.title||'Anwesenheit')}"></label><label>Raumplan-Filter<select id="plan_id"><option value="">Alle sichtbaren Ressourcen</option>${(this.plans||[]).map(p=>`<option value="${esc(p.id)}" ${p.id===this.config.plan_id?'selected':''}>${esc(p.name)}</option>`).join('')}</select></label>`;for(const el of this.shadowRoot.querySelectorAll('input,select'))el.onchange=e=>{this.config={...this.config,[e.target.id]:e.target.value};this.dispatchEvent(new CustomEvent('config-changed',{detail:{config:this.config},bubbles:true,composed:true}));};}
}
if(!customElements.get('desk-booking-attendance'))customElements.define('desk-booking-attendance',AttendanceCard);
if(!customElements.get('desk-booking-attendance-editor'))customElements.define('desk-booking-attendance-editor',AttendanceEditor);
window.customCards=window.customCards||[];
if(!window.customCards.some(c=>c.type==='desk-booking-attendance'))window.customCards.push({type:'desk-booking-attendance',name:'Desk Booking Anwesenheit',description:'M365-Profilbilder und Reservierungszeitspannen pro Kalendertag',preview:true});
