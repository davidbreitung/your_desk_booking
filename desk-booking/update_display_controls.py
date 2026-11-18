"""Upgrade occupancy firmware: global branding, desk label, four light pages."""
from pathlib import Path
import datetime
import re
import sys


def once(s, old, new):
    assert s.count(old) == 1, old[:80]
    return s.replace(old, new, 1)


def transform(s):
    assert 'company_from_ha' not in s
    s = once(s, 'globals:\n', '''globals:
  - id: booking_message
    type: bool
    restore_value: false
    initial_value: 'false'
''')
    # Explicit booking feedback leaves normal notification priorities intact.
    s = once(s, '      then:\n        - globals.set:\n            id: message_open',
             '      then:\n        - lambda: id(booking_message) = false;\n        - globals.set:\n            id: message_open')
    start = s.index('  - platform: template\n    id: send_message_button')
    end = s.index('  - platform: template\n    name: "Hoehe anzeigen"', start)
    button = s[start:end]
    button = once(button, '    on_press:\n', '    on_press:\n      - lambda: id(booking_message) = false;\n')
    booking_button = button.replace('send_message_button', 'send_booking_message_button').replace('"Nachricht senden"', '"Check-in Nachricht senden"').replace('id(booking_message) = false;', 'id(booking_message) = true;')
    s = s[:start] + button + booking_button + s[end:]
    s = s.replace('return id(message_priority).current_option() == "1" || id(message_priority).current_option() == "2";',
                  'return id(booking_message) || id(message_priority).current_option() == "1" || id(message_priority).current_option() == "2";')
    s = s.replace('return lv_color_hex(id(message_priority).current_option() == "1" ? 0xFF3030 : 0xFFD230);',
                  'return lv_color_hex(id(booking_message) ? 0x36FF7F : (id(message_priority).current_option() == "1" ? 0xFF3030 : 0xFFD230));')

    # Give the existing page's labels IDs before duplicating its light controls.
    brand = '''        - label:
            align: CENTER
            y: -140
            text: "your-admins"
            text_font: montserrat_28
            text_color: 0x00D2FF'''
    assert s.count(brand) == 3
    for label in ('company_booking', 'company_dimmer', 'company_height'):
        s = s.replace(brand, brand.replace('        - label:\n', f'        - label:\n            id: {label}\n').replace('text_font: montserrat_28', 'text_font: desk_name_font\n            width: 340\n            long_mode: DOT\n            text_align: CENTER'), 1)
    s = once(s, '            y: -94\n            text: "ARBEITSPLATZ 01"', '            y: -94\n            id: desk_display_name\n            width: 340\n            text_align: CENTER\n            long_mode: DOT\n            text_font: desk_name_font\n            text: "Arbeitsplatz 01"')
    s = once(s, '            text: "DIMMER"', '            id: light_name\n            width: 340\n            height: 58\n            long_mode: WRAP\n            text_align: CENTER\n            text_font: desk_name_font\n            text: "Kein Licht zugeordnet"')
    s = once(s, '    - id: dimmer_page\n', '    - id: dimmer_page\n      skip: true\n')
    start = s.index('    - id: dimmer_page\n')
    end = s.index('    - id: height_page\n', start)
    page = s[start:end]
    pages = page
    for slot in range(2, 5):
        copy = page
        # Only widget IDs/references belonging to the light page are duplicated.
        for name in ('dimmer_page', 'dimmer_arc', 'dimmer_label', 'company_dimmer', 'light_name',
                     'nav_dimmer_booking', 'nav_dimmer_dimmer', 'nav_dimmer_height'):
            copy = re.sub(r'\b' + name + r'\b', name + '_' + str(slot), copy)
        pages += copy
    s = s[:start] + pages + s[end:]

    start = s.index('  - platform: lvgl\n    id: dimmer_value')
    end = s.index('\nevent:\n', start)
    number = s[start:end]
    copies = number
    for slot in range(2, 5):
        copy = number
        for name in ('dimmer_value', 'dimmer_arc', 'dimmer_label'):
            copy = re.sub(r'\b' + name + r'\b', name + '_' + str(slot), copy)
        copies += copy.replace('"Dimmer Regelwert"', f'"Dimmer Regelwert {slot}"')
    s = s[:start] + copies + s[end:]
    event = '''  - platform: template
    id: dimmer_toggle_event
    name: "Dimmer Taster"
    device_class: button
    event_types: [toggle]
'''
    s = once(s, event, event + ''.join(event.replace('dimmer_toggle_event', f'dimmer_toggle_event_{i}').replace('"Dimmer Taster"', f'"Dimmer Taster {i}"') for i in range(2, 5)))
    # Preserve the original controls and add only slot-specific branches.
    for direction in (1, -1):
        anchor = f'''      - script.execute: display_wake
      - if:
          condition:
            lambda: return !id(message_open);
          then:
            - if:
                condition:
                  lvgl.page.is_showing: dimmer_page
                then:
                  - lvgl.arc.update:
                      id: dimmer_arc
                      value: !lambda return std::max(0, std::min(100, (int)lv_arc_get_value(id(dimmer_arc)) + ({direction} * 5)));'''
        extra = ''
        for slot in range(2, 5):
            extra += f'''
      - if:
          condition:
            lambda: return !id(message_open) && id(dimmer_page_{slot})->is_showing() && !id(dimmer_page_{slot})->skip;
          then:
            - lvgl.arc.update:
                id: dimmer_arc_{slot}
                value: !lambda return std::max(0, std::min(100, (int)lv_arc_get_value(id(dimmer_arc_{slot})) + ({direction} * 5)));
'''
        # Extra conditions precede existing logic and never touch height controls.
        s = once(s, anchor, extra.lstrip('\n') + anchor)
    # The ring's event dispatch is inside the no-notification branch.
    anchor = '''            - event.trigger:
                id: dimmer_toggle_event
                event_type: toggle'''
    assert anchor in s
    # Add page branches at the same level as the existing page check.
    marker = '\nscript:\n'
    start = s.index('binary_sensor:\n')
    end = s.index(marker, start)
    section = s[start:end]
    for slot in range(2, 5):
        section += f'''
      - if:
          condition:
            lambda: return !id(message_open) && id(dimmer_page_{slot})->is_showing() && !id(dimmer_page_{slot})->skip;
          then:
            - event.trigger:
                id: dimmer_toggle_event_{slot}
                event_type: toggle
'''
    s = s[:start] + section + s[end:]

    sensors = '''  - platform: homeassistant
    id: company_from_ha
    entity_id: sensor.schreibtisch_01_belegung
    attribute: company_name
    internal: true
    on_value:
      - lambda: |-
          if (x == "unknown" || x == "unavailable") return;
'''
    for label in ('company_booking', 'company_dimmer', 'company_dimmer_2', 'company_dimmer_3', 'company_dimmer_4', 'company_height'):
        sensors += f'          lv_label_set_text(id({label}), x.c_str());\n'
    sensors += '''  - platform: homeassistant
    id: desk_label_from_ha
    entity_id: sensor.schreibtisch_01_belegung
    attribute: display_name
    internal: true
    on_value:
      - lambda: |-
          if (x != "unknown" && x != "unavailable") lv_label_set_text(id(desk_display_name), x.c_str());
'''
    for slot in range(1, 5):
        suffix = '' if slot == 1 else f'_{slot}'
        sensors += f'''  - platform: homeassistant
    id: light_name_from_ha_{slot}
    entity_id: sensor.schreibtisch_01_belegung
    attribute: light_{slot}_name
    internal: true
    on_value:
      - lambda: |-
          const bool enabled = !x.empty() && x != "unknown" && x != "unavailable";
          id(dimmer_page{suffix})->skip = !enabled;
          lv_label_set_text(id(light_name{suffix}), enabled ? x.c_str() : "Kein Licht zugeordnet");
'''
    s = once(s, 'text_sensor:\n', 'text_sensor:\n' + sensors)
    return s


if __name__ == '__main__':
    path = Path(sys.argv[1])
    before = path.read_text(encoding='utf-8')
    after = transform(before)
    if '--apply' in sys.argv:
        backup = Path('/config/desk_display_backups') / ('before-controls-' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.yaml')
        backup.write_text(before, encoding='utf-8')
        path.write_text(after, encoding='utf-8')
        print('DISPLAY_CONTROLS_SAVED', backup)
    else:
        Path(sys.argv[2]).write_text(after, encoding='utf-8')
