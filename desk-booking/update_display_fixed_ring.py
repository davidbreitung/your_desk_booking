"""Animate fixed ring segments without moving LVGL objects/layouts."""
from pathlib import Path
import math
import sys

def transform(s):
    start = s.index('                lv_obj_set_style_border_color(id(message_priority_ring)')
    end = s.index('            - lvgl.widget.show: message_priority_ring', start)
    ids = ', '.join(f'id(message_ring_segment_{i})' for i in range(60))
    s = s[:start] + f'''                lv_obj_t *segments[] = {{{ids}}};
                for (auto *segment : segments)
                  lv_obj_set_style_bg_color(segment, lv_color_mix(color, lv_color_hex(0x101820), 64), LV_PART_MAIN);
''' + s[end:]
    start = s.index('                  - obj:\n                      id: message_ring_dot_0')
    end = s.index('            - label:\n', start)
    widgets = ''
    for i in range(60):
        a = (i * 6 - 90) * math.pi / 180
        widgets += f'''                  - obj:
                      id: message_ring_segment_{i}
                      align: CENTER
                      x: {round(223 * math.cos(a))}
                      y: {round(223 * math.sin(a))}
                      width: 24
                      height: 24
                      radius: 12
                      border_width: 0
                      pad_all: 0
                      bg_color: 0x4C1E24
                      bg_opa: COVER
                      shadow_width: 0
                      clickable: false
                      scrollable: false
'''
    s = s[:start] + widgets + s[end:]
    start = s.index('  - interval: 70ms\n')
    end = s.index('  - interval: 1s\n', start)
    s = s[:start] + f'''  - interval: 70ms
    then:
      - lambda: |-
          if (!id(message_open) || !id(display_enabled).state || lv_obj_has_flag(id(message_priority_ring), LV_OBJ_FLAG_HIDDEN)) return;
          id(message_ring_phase) = (id(message_ring_phase) + 1) % 60;
          const uint32_t rgb = id(booking_message) ? 0x36FF7F : (id(message_priority).current_option() == "1" ? 0xFF3030 : 0xFFD230);
          lv_obj_t *segments[] = {{{ids}}};
          for (int i = 0; i < 5; ++i) {{
            const int index = (id(message_ring_phase) - i + 60) % 60;
            lv_obj_set_style_bg_color(segments[index], lv_color_mix(lv_color_hex(rgb), lv_color_hex(0x101820), i == 4 ? 64 : 255 - i * 48), LV_PART_MAIN);
          }}
''' + s[end:]
    s = s.replace('            id: cover_position_label\n            align:', '            id: cover_position_label\n            text_font: desk_name_font\n            align:')
    s = s.replace('                  text: "Höhe"\n', '                  text: "Höhe"\n                  text_font: desk_name_font\n')
    return s

if __name__ == '__main__':
    source, dest = map(Path, sys.argv[1:])
    dest.write_text(transform(source.read_text(encoding='utf-8')), encoding='utf-8')
    print('FIXED_SEGMENTS_PREPARED')
