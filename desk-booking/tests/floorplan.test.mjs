import test from 'node:test';
import assert from 'node:assert/strict';
import {statusAt,atMinute,localDate,addDays,esc,matches} from '../custom_components/desk_booking/frontend/model.js';
const now=Date.parse('2026-11-15T12:00:00Z');
const event=(s,e=120)=>({start:new Date(now+s*60000).toISOString(),end:new Date(now+e*60000).toISOString(),person:{id:'p',name:'Anna'},name:'Anna'});
const resource=extra=>({kind:'desk',active:true,fresh:true,events:[],name:'Desk',...extra});
test('exact booking boundaries and warning under 60 minutes',()=>{
  assert.equal(statusAt(resource({events:[event(60)]}),now,false).state,'free');
  assert.equal(statusAt(resource({events:[event(59)]}),now,false).state,'soon');
  assert.equal(statusAt(resource({events:[event(0)]}),now,false).state,'reserved');
  assert.equal(statusAt(resource({events:[event(-60,0)]}),now,false).state,'free');
});
test('actual occupancy only in live desk mode, not room or future planning',()=>{
  const r=resource({checked_in:true,occupant:{id:'p',name:'Anna'}});
  assert.equal(statusAt(r,now,true).state,'occupied');
  assert.equal(statusAt(r,now,false).state,'free');
  assert.equal(statusAt({...r,kind:'room'},now,true).state,'free');
  assert.equal(statusAt({...r,fresh:false},now,true).state,'stale');
});
test('conflicts are explicit and inactive resources never free',()=>{
  assert.equal(statusAt(resource({events:[event(0),event(-10)]}),now,false).label,'Buchungskonflikt');
  assert.equal(statusAt(resource({active:false}),now,true).state,'inactive');
});
test('time selection uses HA zone, including DST changes',()=>{
  assert.equal(atMinute('2026-11-15',540,'Europe/Berlin'),Date.parse('2026-11-15T08:00:00Z'));
  assert.equal(atMinute('2026-03-29',540,'Europe/Berlin'),Date.parse('2026-03-29T07:00:00Z'));
  assert.equal(atMinute('2026-10-25',540,'Europe/Berlin'),Date.parse('2026-10-25T08:00:00Z'));
  assert.equal(localDate(new Date('2026-11-15T23:30Z'),'Europe/Berlin'),'2026-11-16');
  assert.equal(addDays('2026-12-31',1),'2027-01-01');
});
test('user names are escaped and search includes all bookers',()=>{
  assert.equal(esc('<img onerror="x">'), '&lt;img onerror=&quot;x&quot;&gt;');
  assert.equal(matches(resource({events:[event(20)]}),'ANNA'),true);
});
test('next-day reservation still warns shortly before midnight',()=>{
  const midnight=Date.parse('2026-11-15T23:00:00Z');
  const r=resource({following:{start:new Date(midnight+10*60000).toISOString(),end:new Date(midnight+70*60000).toISOString(),name:'Anna',person:{id:'p',name:'Anna'}}});
  assert.equal(statusAt(r,midnight-20*60000,true).state,'soon');
});
