import test from 'node:test';
import assert from 'node:assert/strict';
const registry=new Map();
globalThis.HTMLElement=class {attachShadow(){this.shadowRoot={innerHTML:'',querySelector:()=>null,querySelectorAll:()=>[],getElementById:()=>null};}};
globalThis.customElements={get:k=>registry.get(k),define:(k,v)=>registry.set(k,v)};
globalThis.window={};
await import('../custom_components/desk_booking/frontend/desk-booking-floorplan.js');
const Card=registry.get('desk-booking-floorplan');
function card(config={}){const c=new Card();c.setConfig(config);c.day='2026-11-16';c.data={today:c.day,date:c.day,timezone:'Europe/Berlin',can_edit:true,plans:[],resources:[],booking_url:'https://places.cloud.microsoft/test'};c.plan={name:'Büro',aspect:1.6,items:[]};c.render();return c;}
test('headings, full image, legend, date/time, search and management remain in order',()=>{
 const c=card();const html=c.shadowRoot.innerHTML;
 const map=html.indexOf('<div class="mapframe">'),head=html.indexOf('<div class="head">');
 assert.ok(head<map);assert.ok(map<html.indexOf('<div class="legend">'));
 assert.ok(html.indexOf('<div class="legend">')<html.indexOf('<div class="toolbar">'));
 assert.ok(html.indexOf('<div class="timeline">')<html.indexOf('<div class="controls">'));
 assert.ok(html.indexOf('<div class="controls">')<html.indexOf('<div class="plan-actions">'));
 assert.ok(html.includes('width:100%;aspect-ratio:'));assert.ok(!html.includes('max-height:70vh'));assert.ok(!html.includes('id="plus"'));
 assert.ok(!html.includes('Räume zeigen Reservierungen'));assert.ok(!html.includes('Planungsansicht: Reservierungen'));
 assert.ok(html.indexOf('<div class="summary">')>map);
});
test('headings editable, escaped and independently hidden',()=>{
 assert.ok(card({title:'<Titel>',eyebrow:'Firma'}).shadowRoot.innerHTML.includes('&lt;Titel&gt;'));
 const html=card({show_title:false,show_eyebrow:false}).shadowRoot.innerHTML;
 assert.ok(!html.includes('<h2>'));assert.ok(!html.includes('<div class="eyebrow">'));
});
test('reservation link is shown only for a free resource and opens separately',()=>{
 const c=card();const r={id:'desk',name:'Desk',kind:'desk',active:true,fresh:true,events:[]};
 c.data.resources=[r];c.plan.items=[{resource_id:'desk',x:50,y:50,size:64,rotation:0}];c.render();
 assert.ok(!c.shadowRoot.innerHTML.includes('class="reserve"'));
 c.selected='desk';c.render();let html=c.shadowRoot.innerHTML;
 assert.ok(html.includes('<span class="caption"><strong>Desk</strong>Frei<small></small><a class="reserve"'));
 assert.ok(html.includes('target="_blank" rel="noopener noreferrer"'));
 r.checked_in=true;r.occupant={name:'Anna'};c.render();assert.ok(!c.shadowRoot.innerHTML.includes('class="reserve"'));
 r.checked_in=false;r.fresh=false;c.render();assert.ok(!c.shadowRoot.innerHTML.includes('class="reserve"'));
});
test('protected editing waits for authorization, unprotected editing opens directly',async()=>{
 const c=card();c.data.edit_password_required=true;await c.requestEdit(true);assert.equal(c.editing,undefined);assert.equal(c.passwordPrompt,true);assert.equal(c.editFresh,true);
 c.data.edit_password_required=false;await c.requestEdit(true);assert.equal(c.editing,true);
});
