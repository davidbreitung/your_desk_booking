import test from 'node:test';
import assert from 'node:assert/strict';
import {attendance} from '../custom_components/desk_booking/frontend/attendance-model.js';
const person={id:'p',name:'Person'};
const data={date:'2026-11-16',today:'2026-11-16',day_start:'2026-11-15T23:00:00Z',day_end:'2026-11-16T23:00:00Z',resources:[]};
const event=(start,end)=>({person,start,end});
test('earliest to latest across resources, no duplicate people, clipped midnight',()=>{
 const d={...data,resources:[{id:'d',active:true,fresh:true,kind:'desk',events:[event('2026-11-15T22:00:00Z','2026-11-16T09:00:00Z')]},{id:'r',active:true,fresh:true,kind:'room',events:[event('2026-11-16T12:00:00Z','2026-11-17T01:00:00Z')]}]};
 const rows=attendance(d);assert.equal(rows.length,1);assert.equal(rows[0].start,Date.parse(data.day_start));assert.equal(rows[0].end,Date.parse(data.day_end));assert.equal(attendance(d,new Set(['d']))[0].end,Date.parse('2026-11-16T09:00:00Z'));
});
test('walk-ins have no invented end and future dates do not include current checkin',()=>{
 const d={...data,resources:[{id:'d',active:true,fresh:true,kind:'desk',events:[],checked_in:true,occupant:person,checkin_at:'2026-11-16T09:00:00Z'}]};
 assert.equal(attendance(d)[0].end,null);assert.equal(attendance(d)[0].checked,true);assert.equal(attendance({...d,date:'2026-11-17'}).length,0);
});
test('inactive and unknown organizer excluded',()=>{assert.equal(attendance({...data,resources:[{id:'r',active:false,events:[event(data.day_start,data.day_end)]}]}).length,0);});
