// One person per calendar day. Reservation bounds are clipped to that day.
export function attendance(data, resourceIds=null) {
  const rows=new Map(), start=Date.parse(data.day_start), end=Date.parse(data.day_end);
  const get=p=>{if(!rows.has(p.id))rows.set(p.id,{person:p,start:null,end:null,checked:false,checkin_at:null,fresh:true});return rows.get(p.id);};
  for(const r of data.resources){
    if(!r.active || (resourceIds && !resourceIds.has(r.id)))continue;
    for(const event of r.events){
      if(!event.person)continue;
      const a=Math.max(start,Date.parse(event.start)), b=Math.min(end,Date.parse(event.end));
      if(a>=b)continue;
      const row=get(event.person);
      row.start=row.start===null?a:Math.min(row.start,a);row.end=row.end===null?b:Math.max(row.end,b);row.fresh&&=r.fresh;
    }
    if(data.date===data.today&&r.kind==='desk'&&r.checked_in&&r.occupant){const row=get(r.occupant);row.checked=true;if(r.checkin_at){const stamp=Date.parse(r.checkin_at);if(Number.isFinite(stamp))row.checkin_at=row.checkin_at===null?stamp:Math.min(row.checkin_at,stamp);}}
  }
  return [...rows.values()].sort((a,b)=>a.person.name.localeCompare(b.person.name,'de'));
}
