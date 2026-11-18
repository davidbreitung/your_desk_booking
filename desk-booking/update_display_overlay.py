"""Do not render the obscured occupancy glow behind notification animation."""
from pathlib import Path
import sys

def transform(s):
    old = '          if (free) lv_obj_clear_flag(id(desk_free_ring), LV_OBJ_FLAG_HIDDEN);'
    assert s.count(old) == 1
    s = s.replace(old, '          if (free && !id(message_open)) lv_obj_clear_flag(id(desk_free_ring), LV_OBJ_FLAG_HIDDEN);')
    start = s.index('  - id: message_countdown\n')
    pos = s.index('    then:\n', start) + len('    then:\n')
    s = s[:pos] + '      - lvgl.widget.hide: desk_free_ring\n' + s[pos:]
    end_state = "      - globals.set:\n          id: message_open\n          value: 'false'"
    assert s.count(end_state) == 2
    s = s.replace(end_state, end_state + '\n      - script.execute: render_desk_status')
    s = s.replace('    - id: cover_page\n', '    - id: cover_page\n      text_font: desk_name_font\n')
    s = s.replace('            id: cover_position_label\n            align:', '            id: cover_position_label\n            text_font: desk_name_font\n            align:')
    s = s.replace('                  text: "Höhe"\n', '                  text: "Höhe"\n                  text_font: desk_name_font\n')
    return s

if __name__ == '__main__':
    source, dest = map(Path, sys.argv[1:])
    dest.write_text(transform(source.read_text(encoding='utf-8')), encoding='utf-8')
    print('OCCLUDED_GLOW_OPTIMIZED')
