"""Patch the current firmware without touching credentials or hardware setup."""
from pathlib import Path
import sys
import shutil


def transform(source):
    if 'id: next_booking_input' in source:
        raise ValueError('Booking firmware is already present')
    def replace(old, new):
        nonlocal source
        if source.count(old) != 1:
            raise ValueError('Unexpected source: '+old[:60])
        source = source.replace(old, new, 1)
    replace('globals:\n', '''json:

globals:
  - id: next_booking_time
    type: std::string
    initial_value: '"Buchungen werden geladen"'
  - id: next_booking_who
    type: std::string
    initial_value: '""'
  - id: next_booking_warning
    type: bool
    initial_value: 'false'
  - id: next_booking_received
    type: uint32_t
    initial_value: '0'
''')
    replace('text:\n', '''text:
  - platform: template
    id: next_booking_input
    name: "Naechste Buchung"
    entity_category: config
    mode: text
    min_length: 0
    max_length: 255
    optimistic: true
    restore_value: false
    initial_value: ""
    set_action:
      - lambda: |-
          const bool parsed = json::parse_json(x, [](JsonObject root) -> bool {
            if (!root["time"].is<const char *>() || !root["who"].is<const char *>() || !root["warn"].is<bool>()) return false;
            id(next_booking_time) = root["time"].as<std::string>();
            id(next_booking_who) = root["who"].as<std::string>();
            id(next_booking_warning) = root["warn"].as<bool>();
            id(next_booking_received) = millis();
            return true;
          });
          if (parsed) id(render_desk_status).execute();
''')
    replace('          if (free && !id(message_open)) lv_obj_clear_flag(id(desk_free_ring), LV_OBJ_FLAG_HIDDEN);', '''          const bool booking_fresh = id(next_booking_received) != 0 && (uint32_t)(millis() - id(next_booking_received)) < 90000;
          const bool booking_warn = booking_fresh && id(next_booking_warning);
          const uint32_t ring_color = booking_warn ? 0xFFD43B : 0x36FF7F;
          lv_obj_set_style_border_color(id(desk_free_ring), lv_color_hex(ring_color), LV_PART_MAIN);
          lv_obj_set_style_shadow_color(id(desk_free_ring), lv_color_hex(ring_color), LV_PART_MAIN);
          lv_label_set_text(id(next_booking_time_label), booking_fresh ? id(next_booking_time).c_str() : "Buchungen nicht aktuell");
          lv_label_set_text(id(next_booking_who_label), booking_fresh ? id(next_booking_who).c_str() : "");
          if ((free || booking_warn) && !id(message_open)) lv_obj_clear_flag(id(desk_free_ring), LV_OBJ_FLAG_HIDDEN);''')
    replace('            id: desk_employee_label\n            align: CENTER\n            y: 25\n            width: 340\n            height: 76', '            id: desk_employee_label\n            align: CENTER\n            y: 8\n            width: 340\n            height: 42')
    replace('            id: desk_hint_label\n            align: CENTER\n            y: 92', '            id: desk_hint_label\n            align: CENTER\n            y: 42')
    anchor='''            text: "Verbindung zu Home Assistant"
            text_color: 0xA9BBC9
            text_font: montserrat_16
'''
    replace(anchor, anchor+'''        - label:
            id: next_booking_time_label
            align: CENTER
            y: 77
            width: 350
            long_mode: DOT
            text_align: CENTER
            text: "Buchungen werden geladen"
            text_font: montserrat_20
            text_color: 0xFFD43B
        - label:
            id: next_booking_who_label
            align: CENTER
            y: 105
            width: 340
            long_mode: DOT
            text_align: CENTER
            text: ""
            text_font: montserrat_20
''')
    replace('interval:\n', '''interval:
  - interval: 5s
    then:
      - lambda: |-
          if (id(next_booking_received) != 0 && (uint32_t)(millis() - id(next_booking_received)) >= 90000) {
            id(next_booking_received) = 0;
            id(next_booking_warning) = false;
            id(render_desk_status).execute();
          }
''')
    return source


if __name__ == '__main__':
    src, dst = map(Path, sys.argv[1:3])
    updated = transform(src.read_text(encoding='utf-8'))
    if src.resolve() == dst.resolve():
        raise ValueError('Use a separate staged file')
    dst.write_text(updated, encoding='utf-8')
    print('BOOKING_FIRMWARE_STAGED', dst.name)
