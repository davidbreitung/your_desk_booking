from pathlib import Path
import json, hashlib
root=Path(__file__).parent
base=root/'custom_components/desk_booking'
p=base/'frontend/desk-booking-floorplan.js'
s=p.read_text(encoding='utf-8')
# Keep headings above the image; editing and plan selection below search.
start=s.index('      <div class="head">');end=s.index('\n',start)
head=s[start:end];s=s[:start]+s[end:]
split=head.index('${admin?')
heading=head[:split]+'</div>'
actions='<div class="plan-actions">'+head[split:head.rindex('</div>')]+'</div>'
anchor='      ${this.error?'
s=s.replace(anchor,heading+'\n'+anchor,1)
legend_start=s.index('      <div class="legend">');legend_end=s.index('\n',legend_start)
legend=s[legend_start:legend_end];s=s[:legend_start]+s[legend_end:]
map_end=s.index('\n      <div class="toolbar">')
s=s[:map_end]+'\n'+legend+s[map_end:]
notice_start=s.index('      <div class="notice">${this.live?')
notice_end=s.index('</div>',notice_start)+6
s=s[:notice_start]+"      ${this.photoNotice?`<div class=\"notice\">${esc(this.photoNotice)}</div>`:''}"+s[notice_end:]
# Plan selector belongs to management row, not the date row.
select_start=s.index('<select id="plan"');select_end=s.index('</select>',select_start)+9
select=s[select_start:select_end];s=s[:select_start]+s[select_end:]
actions=actions.replace('<div class="plan-actions">','<div class="plan-actions">'+select+'<span class="grow"></span>')
zoom_start=s.index('<span class="grow"></span><button id="minus"');zoom_end=s.index('</div>',zoom_start)
s=s[:zoom_start]+s[zoom_end:]
s=s.replace("      ${chosen&&!this.editing?this.details(chosen,instant):''}", '      '+actions)
s=s.replace('overflow:auto;max-height:70vh;', 'overflow:visible;')
s=s.replace('.viewport{max-height:60vh}', '')
s=s.replace('width:${this.zoom*100}%;aspect-ratio:', 'width:100%;aspect-ratio:')
s=s.replace('(p.object_scale??100)/100*this.zoom', '(p.object_scale??100)/100')
# A native symbol button and a sibling popover link avoid nested interactive buttons.
s=s.replace('return `<button class="marker ', 'return `<div class="marker ')
s=s.replace('aria-label="${esc(r.name+', '><button class="marker-hit" aria-label="${esc(r.name+')
s=s.replace('</ha-icon>`}</span>${`<span class="caption">', '</ha-icon>`}</span></button>${`<span class="caption">')
s=s.replace('<small>${esc(note)}</small></span>`}</button>`;', '<small>${esc(note)}</small>${!this.editing&&this.selected===r.id&&s.state===\'free\'&&d.booking_url?`<a class="reserve" href="${esc(d.booking_url)}" target="_blank" rel="noopener noreferrer">Reservieren</a>`:\'\'}</span>`}</div>`;')
# Remove duplicate reservation action from former lower detail panel.
old="${s.state==='free'&&this.data.booking_url?`<a class=\"reserve\" href=\"${esc(this.data.booking_url)}\" target=\"_blank\" rel=\"noopener noreferrer\">Reservieren</a>`:''}"
s=s.replace(old,'')
s=s.replace("el.onclick=()=>{if(this.suppressClick)", "el.onclick=e=>{if(e.target.closest('a')){e.stopPropagation();return;}e.stopPropagation();if(this.suppressClick)")
s=s.replace(".marker,.details,.password-dialog", ".marker,.details,.password-dialog")
s=s.replace("const STYLE=`", '''const STYLE=`
.marker-hit{display:block;width:64px;height:64px;min-height:0;padding:0;border:0;background:transparent;border-radius:50%}.marker:focus-within{z-index:12}.marker:focus-within .caption{display:block}.marker.selected{z-index:12}.marker.selected .caption{pointer-events:auto}.caption .reserve{display:block;margin:8px 0 0;text-align:center;padding:7px 10px;font-size:12px;color:#fff}.caption{min-width:145px}.plan-actions{display:flex;align-items:center;flex-wrap:wrap;gap:8px;padding:12px 22px;border-top:1px solid var(--divider-color,#e1e9eb)}
''')
# Keep the visible popover inside the image on edge-positioned desks.
anchor='    this.bind();this.shadowRoot.onkeydown='
s=s.replace(anchor,'''    const mapRect=this.shadowRoot.querySelector('.mapframe')?.getBoundingClientRect();
    if(mapRect)for(const caption of this.shadowRoot.querySelectorAll('.marker.selected .caption')){
      const rect=caption.getBoundingClientRect();const factor=caption.parentElement.getBoundingClientRect().width/64;
      if(rect.right>mapRect.right)caption.style.left=-(rect.right-mapRect.right)/factor+'px';
      if(rect.bottom>mapRect.bottom) {caption.style.top='auto';caption.style.bottom='72px';}
    }
    this.bind();this.shadowRoot.onkeydown=''')
p.write_text(s,encoding='utf-8')
p=base/'manifest.json';data=json.loads(p.read_text());data['version']='0.14.1';p.write_text(json.dumps(data,indent=2)+'\n')
baseline=root/'backups/pre-0141'
manifest={p.relative_to(baseline).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in baseline.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
(root/'dist/desk-booking-0.14.0-baseline.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
installer=(root/'install_features_0140.py').read_text().replace('0.14.0','0.14.1').replace("== '0.13.2'","== '0.14.0'").replace('0.13.2-baseline','0.14.0-baseline').replace('0140','0141')
(root/'install_features_0141.py').write_text(installer)
