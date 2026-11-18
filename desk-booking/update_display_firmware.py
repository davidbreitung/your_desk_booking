"""Transform the known display configuration, preserving secrets and other pages."""
from pathlib import Path
import datetime
import hashlib
import re
import sys


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one configuration anchor: {old[:55]!r}")
    return source.replace(old, new, 1)


def transform(source):
    if "desk_status_from_ha" in source:
        raise ValueError("Occupancy firmware already present; do not apply twice")
    source = replace_once(source, "api:\n  actions:", '''api:
  on_client_disconnected:
    - lambda: |-
        if (client_info.rfind("Home Assistant", 0) == 0) {
          id(desk_data_valid) = false;
          id(desk_name_valid) = false;
          id(render_desk_status).execute();
        }
  actions:''')
    source = replace_once(source, "# UI preview only: no booking is created until a backend is connected.\nglobals:", '''# Desk Booking supplies the authoritative occupancy and employee name.
globals:
  - id: desk_data_valid
    type: bool
    restore_value: false
    initial_value: 'false'
  - id: desk_name_valid
    type: bool
    restore_value: false
    initial_value: 'false'
'''.rstrip())
    source = replace_once(source, '''  - id: booking_minutes
    type: int
    restore_value: false
    initial_value: '60'
''', "")
    for direction in ("1", "-1"):
        source = replace_once(source, f'''                      else:
                        - lambda: 'id(booking_minutes) = std::max(15, std::min(480, id(booking_minutes) + ({direction} * 15)));'
                        - script.execute: refresh_duration
''', "")
    start = source.index("  - id: refresh_duration\n")
    end = source.index("\nimage:", start)
    source = source[:start] + source[end:]
    source = replace_once(source, "\nsensor:\n", '''
font:
  - file: "gfonts://Roboto"
    id: desk_name_font
    size: 24
    glyphsets:
      - GF_Latin_Core

text_sensor:
  - platform: homeassistant
    id: desk_status_from_ha
    entity_id: sensor.schreibtisch_01_belegung
    internal: true
    on_value:
      - lambda: id(desk_data_valid) = true;
      - script.execute: render_desk_status
      - script.execute: display_wake
  - platform: homeassistant
    id: desk_employee_from_ha
    entity_id: sensor.schreibtisch_01_angemeldeter_mitarbeiter
    internal: true
    on_value:
      - lambda: id(desk_name_valid) = true;
      - script.execute: render_desk_status
      - script.execute: display_wake

sensor:
''')
    source = replace_once(source, "script:\n", '''script:
  - id: render_desk_status
    mode: restart
    then:
      - lambda: |-
          const auto &status = id(desk_status_from_ha).state;
          const bool valid = id(desk_data_valid);
          const bool free = valid && status == "free";
          const bool occupied = valid && status == "checked_in";
          // Static full-circle border and shadow: no animation or spinner.
          if (free) lv_obj_clear_flag(id(desk_free_ring), LV_OBJ_FLAG_HIDDEN);
          else lv_obj_add_flag(id(desk_free_ring), LV_OBJ_FLAG_HIDDEN);
          const char *headline = "STATUS OFFEN";
          const char *hint = "Verbindung zu Home Assistant";
          uint32_t color = 0xFFCB70;
          std::string name;
          if (free) {
            headline = "FREI";
            hint = "Check-in in Home Assistant";
            color = 0x36FF7F;
          } else if (occupied) {
            headline = "EINGECHECKT";
            hint = "Dein Arbeitsplatz";
            color = 0xFFFFFF;
            const auto &employee = id(desk_employee_from_ha).state;
            if (id(desk_name_valid) && !employee.empty() && employee != "unknown" && employee != "unavailable" && employee != "—") name = employee;
            else name = "Name wird geladen";
          } else if (valid && status == "applying") {
            headline = "BITTE WARTEN";
            hint = "Check-in wird aktualisiert";
          } else if (valid && status == "error") {
            headline = "BITTE PRUEFEN";
            hint = "Status in Home Assistant pruefen";
          }
          lv_label_set_text(id(desk_status_label), headline);
          lv_obj_set_style_text_color(id(desk_status_label), lv_color_hex(color), LV_PART_MAIN);
          lv_label_set_text(id(desk_employee_label), name.c_str());
          lv_label_set_text(id(desk_hint_label), hint);
          lv_label_set_text(id(desk_name_header), name.c_str());
          if (occupied) lv_obj_clear_flag(id(desk_name_header), LV_OBJ_FLAG_HIDDEN);
          else lv_obj_add_flag(id(desk_name_header), LV_OBJ_FLAG_HIDDEN);
''')
    # Replace the old duration preview, keeping its navigation buttons unchanged.
    start = source.index("        - arc:\n            id: duration_arc")
    end = source.index("        - button:\n            id: nav_booking_booking", start)
    source = source[:start] + '''        - label:
            align: CENTER
            y: -140
            text: "your-admins"
            text_font: montserrat_28
            text_color: 0x00D2FF
        - label:
            align: CENTER
            y: -94
            text: "ARBEITSPLATZ 01"
        - label:
            id: desk_status_label
            align: CENTER
            y: -35
            width: 370
            text_align: CENTER
            text: "STATUS OFFEN"
            text_color: 0xFFCB70
            text_font: montserrat_28
        - label:
            id: desk_employee_label
            align: CENTER
            y: 25
            width: 340
            height: 76
            long_mode: WRAP
            text_align: CENTER
            text: ""
            text_font: desk_name_font
        - label:
            id: desk_hint_label
            align: CENTER
            y: 92
            width: 350
            text_align: CENTER
            text: "Verbindung zu Home Assistant"
            text_color: 0xA9BBC9
            text_font: montserrat_16
        - obj:
            align: CENTER
            y: -10
            width: 360
            height: 240
            bg_opa: TRANSP
            border_width: 0
            pad_all: 0
            clickable: true
            scrollable: false
''' + source[end:]
    source = replace_once(source, "  top_layer:\n    widgets:\n", '''  top_layer:
    widgets:
      - obj:
          id: desk_free_ring
          hidden: true
          align: CENTER
          width: 464
          height: 464
          radius: 232
          bg_opa: TRANSP
          border_width: 10
          border_color: 0x36FF7F
          border_opa: COVER
          shadow_color: 0x36FF7F
          shadow_width: 16
          shadow_opa: 55%
          pad_all: 0
          clickable: false
          scrollable: false
      - label:
          id: desk_name_header
          hidden: true
          align: CENTER
          y: -178
          width: 290
          height: 28
          long_mode: DOT
          text_align: CENTER
          text: ""
          text_font: desk_name_font
          text_color: 0xFFFFFF
          clickable: false
''')
    assert not any(token in source for token in ("booking_minutes", "duration_arc", "duration_label", "refresh_duration"))
    return source


def main():
    path = Path(sys.argv[1])
    before = path.read_text(encoding="utf-8")
    after = transform(before)
    if "--apply" in sys.argv:
        backup_dir = Path('/config/desk_display_backups')
        backup_dir.mkdir(exist_ok=True)
        backup = backup_dir / (path.stem + '-before-occupancy-' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.yaml')
        backup.write_text(before, encoding="utf-8")
        path.write_text(after, encoding="utf-8")
        print('OCCUPANCY_FIRMWARE_SAVED; backup:', backup)
    else:
        target = Path(sys.argv[2])
        target.write_text(after, encoding="utf-8")
        print('OCCUPANCY_FIRMWARE_PREPARED', target.name)
    print('SHA256', hashlib.sha256(after.encode()).hexdigest())


if __name__ == '__main__':
    main()
