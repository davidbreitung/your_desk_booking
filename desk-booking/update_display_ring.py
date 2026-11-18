"""Keep a static message ring and animate only four small highlight objects."""
from pathlib import Path
import re
import sys

def transform(s):
    assert '  buffer_size: 12%' in s
    assert s.count('            - spinner:\n') == 1
    s = s.replace('  buffer_size: 12%', '  buffer_size: 50%', 1)
    s = s.replace('globals:\n', "globals:\n  - id: message_ring_phase\n    type: int\n    initial_value: '0'\n", 1)
    start=s.index('            - lvgl.spinner.update:')
    end=s.index('            - lvgl.widget.show: message_priority_ring',start)
    s=s[:start]+'''            - lambda: |-
                uint32_t rgb = id(booking_message) ? 0x36FF7F : (id(message_priority).current_option() == "1" ? 0xFF3030 : 0xFFD230);
                lv_color_t color = lv_color_hex(rgb);
                lv_obj_set_style_border_color(id(message_priority_ring), lv_color_mix(color, lv_color_hex(0x101820), 64), LV_PART_MAIN);
                lv_obj_t *dots[] = {id(message_ring_dot_0), id(message_ring_dot_1), id(message_ring_dot_2), id(message_ring_dot_3)};
                for (int i = 0; i < 4; ++i)
                  lv_obj_set_style_bg_color(dots[i], lv_color_mix(color, lv_color_hex(0x101820), 255 - i * 48), LV_PART_MAIN);
'''+s[end:]
    start=s.index('            - spinner:\n')
    end=s.index('            - label:\n',start)
    ring='''            - obj:
                id: message_priority_ring
                hidden: true
                align: CENTER
                width: 470
                height: 470
                radius: 235
                border_width: 24
                border_color: 0x4C1E24
                border_opa: COVER
                bg_opa: TRANSP
                pad_all: 0
                clickable: false
                scrollable: false
                widgets:
'''
    for i in range(4):
        ring+=f'''                  - obj:
                      id: message_ring_dot_{i}
                      align: CENTER
                      width: 24
                      height: 24
                      radius: 12
                      x: 0
                      y: -223
                      border_width: 0
                      pad_all: 0
                      bg_color: 0xFF3030
                      bg_opa: COVER
                      shadow_width: 0
                      clickable: false
                      scrollable: false
'''
    s=s[:start]+ring+s[end:]
    s=s.replace('interval:\n','''interval:
  - interval: 70ms
    then:
      - lambda: |-
          if (!id(message_open) || !id(display_enabled).state || lv_obj_has_flag(id(message_priority_ring), LV_OBJ_FLAG_HIDDEN)) return;
          id(message_ring_phase) = (id(message_ring_phase) + 12) % 360;
          lv_obj_t *dots[] = {id(message_ring_dot_0), id(message_ring_dot_1), id(message_ring_dot_2), id(message_ring_dot_3)};
          // Moving children invalidates only the old/new highlight rectangles.
          // The large ring itself stays unchanged throughout the animation.
          for (int i = 0; i < 4; ++i) {
            const float angle = (id(message_ring_phase) - i * 6 - 90) * 0.01745329252f;
            lv_obj_set_pos(dots[i], (int)std::lround(223 * std::cos(angle)), (int)std::lround(223 * std::sin(angle)));
          }
''',1)
    return s

if __name__=='__main__':
    source,destination=map(Path,sys.argv[1:])
    destination.write_text(transform(source.read_text(encoding='utf-8')),encoding='utf-8')
    print('SMALL_AREA_RING_ANIMATION_PREPARED')
