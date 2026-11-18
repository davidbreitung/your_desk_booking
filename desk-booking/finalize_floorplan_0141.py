from pathlib import Path
p=Path(__file__).parent/'custom_components/desk_booking/frontend/desk-booking-floorplan.js'
s=p.read_text(encoding='utf-8')
s=s.replace('.marker.selected .caption{pointer-events:auto}', '.marker.selected .caption{pointer-events:auto;min-width:145px;font-size:12px;transform:scale(calc(1 / var(--object-factor,1)));transform-origin:top left}')
s=s.replace('<div class="marker ${', '<div tabindex="-1" class="marker ${')
p.write_text(s,encoding='utf-8')
