/* Pure time/status helpers shared by the card and regression tests. */
export const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
export function localParts(date, zone) {
  return Object.fromEntries(new Intl.DateTimeFormat('en-GB', {timeZone:zone, year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(date).filter(p=>p.type!=='literal').map(p=>[p.type,p.value]));
}
export function localDate(date, zone) { const p=localParts(date,zone); return `${p.year}-${p.month}-${p.day}`; }
export function localMinute(date, zone) { const p=localParts(date,zone); return +p.hour*60 + +p.minute; }
export function addDays(day, delta) { return new Date(Date.parse(day+'T12:00:00Z')+delta*86400000).toISOString().slice(0,10); }
export function atMinute(day, minute, zone) {
  const target=Date.parse(day+'T00:00:00Z')+minute*60000;
  let guess=target;
  for(let i=0;i<3;i++) { const p=localParts(new Date(guess),zone); const wall=Date.parse(`${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}:${p.second}Z`); guess+=target-wall; }
  return guess;
}
export function timeLabel(iso, zone) { return new Intl.DateTimeFormat('de-DE',{timeZone:zone,hour:'2-digit',minute:'2-digit'}).format(new Date(iso)); }
export function initials(name) { return (name||'?').trim().split(/\s+/).slice(0,2).map(x=>Array.from(x)[0]||'').join('').toUpperCase(); }
export function statusAt(resource, instant, live) {
  const current=resource.events.filter(e=>Date.parse(e.start)<=instant && Date.parse(e.end)>instant);
  const next=resource.events.find(e=>Date.parse(e.start)>instant) || resource.following;
  const booked=current[0] || next || null;
  let state='free', label='Frei', person=null;
  if(!resource.active) { state='inactive'; label='Nicht verfügbar'; }
  else if(!resource.fresh) { state='stale'; label='Daten nicht aktuell'; }
  else if(live && resource.kind==='desk' && resource.checked_in) { state='occupied'; label='In Benutzung'; person=resource.occupant; }
  else if(current.length) { state='reserved'; label=current.length>1?'Buchungskonflikt':'Reserviert'; person=current[0].person; }
  else if(next && Date.parse(next.start)-instant<3600000) { state='soon'; label='Bald reserviert'; person=next.person; }
  return {state,label,person,current,next,booked};
}
export function matches(resource, query) {
  const text=[resource.name,resource.occupant?.name,...resource.events.map(e=>e.name)].join(' ').toLocaleLowerCase('de');
  return text.includes(query.trim().toLocaleLowerCase('de'));
}
