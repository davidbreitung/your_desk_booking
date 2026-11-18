"""Upgrade the known 0.4 display source, retaining its secrets and partition layout."""
from pathlib import Path
import re
import sys


def transform(s):
    if 'id: menu_selection' in s:
        raise ValueError('Already upgraded')
    # Replace the duplicated per-page navigation with one shared overlay.
    s, count = re.subn(r'^        - button:\n            id: nav_[\s\S]*?(?=^        - \w|^    - id:|^  top_layer:)', '', s, flags=re.M)
    assert count == 18, count
    s = s.replace('globals:\n', '''globals:
  - id: menu_selection
    type: bool
    initial_value: 'true'
  - id: menu_index
    type: int
    initial_value: '0'
  - id: cover_tilt_focus
    type: bool
    initial_value: 'false'
''', 1)
    enabled = '{true, !id(dimmer_page)->skip, true, !id(cover_page)->skip, !id(switch_page)->skip}'
    scripts = f'''  - id: render_main_navigation
    then:
      - lambda: |-
          if (id(menu_booking) == nullptr || id(menu_switch) == nullptr) return;
          const bool enabled[] = {enabled};
          lv_obj_t *buttons[] = {{id(menu_booking), id(menu_dimmer), id(menu_height), id(menu_cover), id(menu_switch)}};
          if (!enabled[id(menu_index)]) id(menu_index) = 0;
          int count = 0, position = 0;
          for (bool e : enabled) if (e) ++count;
          for (int i = 0; i < 5; ++i) {{
            if (!enabled[i]) {{ lv_obj_add_flag(buttons[i], LV_OBJ_FLAG_HIDDEN); continue; }}
            lv_obj_clear_flag(buttons[i], LV_OBJ_FLAG_HIDDEN);
            lv_obj_set_x(buttons[i], position++ * 60 - (count - 1) * 30);
            bool selected = i == id(menu_index);
            lv_obj_set_style_border_width(buttons[i], selected ? 3 : 0, LV_PART_MAIN);
            lv_obj_set_style_border_color(buttons[i], lv_color_hex(id(menu_selection) ? 0x999999 : 0x00D2FF), LV_PART_MAIN);
          }}
  - id: show_menu_page
    then:
'''
    categories = ['booking', 'dimmer', 'height', 'cover', 'switch']
    for index, page in enumerate(categories):
        scripts += f'''      - if:
          condition:
            lambda: return id(menu_index) == {index};
          then:
            - lvgl.page.show: {page}_page
'''
    scripts += '''      - script.execute: render_main_navigation
  - id: standby_home_page
    then:
      - lambda: |-
          id(menu_index) = 0;
          id(menu_selection) = true;
      - script.execute: show_menu_page
  - id: rotate_dashboard
    parameters:
      direction: int
    then:
      - script.execute: display_wake
      - if:
          condition:
            lambda: return !id(message_open) && id(display_enabled).state;
          then:
            - if:
                condition:
                  lambda: return id(menu_selection);
                then:
                  - lambda: |-
'''
    scripts += f'''                      const bool enabled[] = {enabled};
                      do {{ id(menu_index) = (id(menu_index) + direction + 5) % 5; }} while (!enabled[id(menu_index)]);
                  - script.execute: render_main_navigation
                else:
'''
    for page, widget, low, high, step in [('dimmer', 'dimmer_arc', 0,100,5), *[(f'dimmer_page_{i}',f'dimmer_arc_{i}',0,100,5) for i in range(2,5)], ('height','height_arc',62,128,1)]:
        page_id = page if 'page_' in page else page+'_page'
        scripts += f'''                  - if:
                      condition:
                        lvgl.page.is_showing: {page_id}
                      then:
                        - lvgl.arc.update:
                            id: {widget}
                            value: !lambda return std::max({low}, std::min({high}, (int)lv_arc_get_value(id({widget})) + direction * {step}));
'''
    scripts += '''                  - if:
                      condition:
                        lambda: return id(cover_page)->is_showing() && id(cover_available).state;
                      then:
                        - if:
                            condition:
                              lambda: return id(cover_tilt_focus) && id(cover_has_tilt).state;
                            then:
                              - lvgl.slider.update:
                                  id: cover_tilt_slider
                                  value: !lambda return std::max(0, std::min(100, (int)lv_slider_get_value(id(cover_tilt_slider)) + direction * 5));
                            else:
                              - lvgl.slider.update:
                                  id: cover_position_slider
                                  value: !lambda return std::max(0, std::min(100, (int)lv_slider_get_value(id(cover_position_slider)) + direction * 5));
                  - if:
                      condition:
                        lvgl.page.is_showing: switch_page
                      then:
                        - event.trigger:
                            id: switch_command
                            event_type: !lambda return direction > 0 ? "turn_on" : "turn_off";
'''
    s = s.replace('script:\n', 'script:\n'+scripts, 1)
    s = s.replace('      - script.execute: display_wake\n', '      - script.execute: display_wake\n      - script.execute: render_main_navigation\n', 1)
    s = re.sub(r'    on_clockwise:[\s\S]*?(?=\nnumber:)', '''    on_clockwise:
      - script.execute:
          id: rotate_dashboard
          direction: 1
    on_anticlockwise:
      - script.execute:
          id: rotate_dashboard
          direction: -1
''', s, count=1)
    marker = '    on_press:\n      - script.execute: display_wake\n\nscript:'
    assert marker in s
    s = s.replace(marker, '''    on_press:
      - script.execute: display_wake
      - if:
          condition:
            lambda: return !id(message_open) && id(display_enabled).state;
          then:
            - if:
                condition:
                  lambda: return id(menu_selection);
                then:
                  - lambda: id(menu_selection) = false;
                  - script.execute: show_menu_page
                else:
                  - lambda: id(menu_selection) = true;
            - script.execute: render_main_navigation

script:''', 1)
    # All existing touchscreen light navigation remains. Touch opens control mode.
    s = re.sub(r'(\s*)- lvgl.page.show: (\w+)', lambda m: m[1]+'- lambda: id(menu_selection) = false;'+m[1]+'- lvgl.page.show: '+m[2] if len(m[1].split('\n')[-1]) >= 18 else m[0], s)
    s = s.replace('      - lambda: id(swipe_direction) = 0;', '      - lambda: id(swipe_direction) = 0; id(menu_selection) = false;\n      - script.execute: render_main_navigation')
    # No swiping across a cover slider: the upper header remains a swipe target.
    s = s.replace('            int dx =', '            if (id(cover_page)->is_showing() && t.y_org > 170) continue;\n            int dx =', 1)
    s = s.replace('  - id: render_light_navigation\n    then:\n', '  - id: render_light_navigation\n    then:\n      - script.execute: render_main_navigation\n', 1)
    # Power-off is persistent through activity and settings updates; explicit power-on wakes.
    start = s.index('  - id: display_wake\n')
    end = s.index('  - id: change_page\n', start)
    s = s[:start]+'''  - id: display_wake
    mode: restart
    then:
      - lambda: |-
          if (!id(display_enabled).state) return;
          id(display_last_activity) = millis();
          id(display_is_standby) = false;
          float value = id(display_brightness).state;
          auto call = id(display_backlight).turn_on();
          call.set_brightness((std::isnan(value) ? 50.0f : std::max(1.0f, std::min(100.0f, value))) / 100.0f);
          call.set_transition_length(0);
          call.perform();
'''+s[end:]
    s += '''
switch:
  - platform: template
    id: display_enabled
    name: "Display Aktiv"
    optimistic: true
    restore_mode: RESTORE_DEFAULT_ON
    turn_on_action:
      - delay: 1ms
      - script.execute: display_wake
    turn_off_action:
      - light.turn_off: display_backlight
'''
    s = s.replace('          // Keep notifications bright;', '          if (!id(display_enabled).state) return;\n          // Keep notifications bright;', 1)
    s = s.replace('          id(display_is_standby) = true;', '          id(display_is_standby) = true;\n          if (id(standby_return_home).state) id(standby_home_page).execute();',1)
    s = s.replace('binary_sensor:\n', '''binary_sensor:
  - platform: homeassistant
    id: standby_return_home
    entity_id: sensor.schreibtisch_01_belegung
    attribute: standby_home
    internal: true
  - platform: homeassistant
    id: cover_available
    entity_id: sensor.schreibtisch_01_belegung
    attribute: cover_available
    internal: true
  - platform: homeassistant
    id: cover_has_tilt
    entity_id: sensor.schreibtisch_01_belegung
    attribute: cover_tilt
    internal: true
    trigger_on_initial_state: true
    on_state:
      - lambda: |-
          if (x) {
            lv_obj_clear_flag(id(cover_tilt_slider), LV_OBJ_FLAG_HIDDEN);
            lv_obj_clear_flag(id(cover_tilt_label), LV_OBJ_FLAG_HIDDEN);
            lv_obj_clear_flag(id(cover_tilt_select), LV_OBJ_FLAG_HIDDEN);
          } else {
            lv_obj_add_flag(id(cover_tilt_slider), LV_OBJ_FLAG_HIDDEN);
            lv_obj_add_flag(id(cover_tilt_label), LV_OBJ_FLAG_HIDDEN);
            lv_obj_add_flag(id(cover_tilt_select), LV_OBJ_FLAG_HIDDEN);
            id(cover_tilt_focus) = false;
          }
''',1)
    extra_text = ''
    for kind in ['cover','switch']:
        extra_text += f'''  - platform: homeassistant
    id: {kind}_name_from_ha
    entity_id: sensor.schreibtisch_01_belegung
    attribute: {kind}_name
    internal: true
    on_value:
      - lambda: |-
          const bool valid = !x.empty() && x != "unknown" && x != "unavailable";
          id({kind}_page)->skip = !valid;
          lv_label_set_text(id({kind}_name_label), valid ? x.c_str() : "Nicht zugeordnet");
      - script.execute: render_main_navigation
'''
    extra_text += '''  - platform: homeassistant
    id: switch_state_from_ha
    entity_id: sensor.schreibtisch_01_belegung
    attribute: switch_state
    internal: true
    on_value:
      - lambda: lv_label_set_text(id(switch_state_label), x == "on" ? "Ein" : x == "off" ? "Aus" : "Nicht erreichbar");
'''
    icons = ['power', 'power-socket-eu','fan','monitor','radiator','toggle-switch']
    extra_text += '''  - platform: homeassistant
    id: switch_icon_from_ha
    entity_id: sensor.schreibtisch_01_belegung
    attribute: switch_icon
    internal: true
    on_value:
'''
    for i, icon in enumerate(icons):
        extra_text += f'''      - if:
          condition:
            lambda: return x == "mdi:{icon}";
          then:
            - lvgl.image.update:
                id: [menu_switch_image, switch_dashboard_image]
                src: switch_icon_{i}
'''
    s = s.replace('text_sensor:\n', 'text_sensor:\n'+extra_text,1)
    for key, name in [('position','Rollo Position Sollwert'),('tilt','Lamellen Position Sollwert')]:
        event_name = 'Rollo Position Befehl' if key == 'position' else 'Lamellen Position Befehl'
        s = s.replace('event:\n', f'''event:
  - platform: template
    id: cover_{key}_event
    name: "{event_name}"
    event_types: [apply]
''', 1)
        s = s.replace('number:\n',f'''number:
  - platform: lvgl
    id: cover_{key}_command
    name: "{name}"
    widget: cover_{key}_slider
    trigger: on_value
    restore_value: false
    on_value:
      - if:
          condition:
            lambda: return id(cover_page)->is_showing() && id(cover_available).state;
          then:
            - delay: 20ms
            - event.trigger:
                id: cover_{key}_event
                event_type: apply
''',1)
        attr = 'cover_position' if key == 'position' else 'cover_tilt_position'
        label = 'Höhe' if key == 'position' else 'Lamellen'
        s = s.replace('\nsensor:\n',f'''
sensor:
  - platform: homeassistant
    id: cover_{key}_feedback
    entity_id: sensor.schreibtisch_01_belegung
    attribute: {attr}
    internal: true
    on_value:
      - lambda: |-
          // Native LVGL feedback deliberately does not emit a command event.
          if (std::isfinite(x) && x >= 0 && x <= 100) {{
            lv_slider_set_value(id(cover_{key}_slider), (int)x, LV_ANIM_OFF);
            lv_label_set_text(id(cover_{key}_label), str_sprintf("{label}: %.0f %%", x).c_str());
          }} else lv_label_set_text(id(cover_{key}_label), "{label}: --");
''',1) if '\nsensor:\n' in s else s
    s = s.replace('event:\n', '''event:
  - platform: template
    id: switch_command
    name: "Schaltkanal Taster"
    device_class: button
    event_types: [turn_on, turn_off]
''',1)
    images = ''
    for name, icon in [('nav_icon_cover','blinds-horizontal'), *[(f'switch_icon_{i}', icon) for i,icon in enumerate(icons)]]:
        images += f'''  - platform: file
    file: mdi:{icon}
    id: {name}
    resize: 32x32
    type: GRAYSCALE
    transparency: alpha_channel
'''
    s = s.replace('\nimage:\n','\nimage:\n'+images,1)
    pages = ''
    for kind in ['cover','switch']:
        pages += f'''    - id: {kind}_page
      skip: true
      bg_color: 0x101820
      scrollable: false
      widgets:
        - image:
            src: your_admins_background
            align: CENTER
            clickable: false
        - label:
            id: {kind}_name_label
            align: CENTER
            y: -128
            width: 300
            long_mode: DOT
            text_align: CENTER
            text: "Nicht zugeordnet"
            text_font: desk_name_font
'''
        if kind == 'cover':
            for key, label, ypos in [('position','Höhe',-15),('tilt','Lamellen',80)]:
                hidden = 'true' if key == 'tilt' else 'false'
                pages += f'''        - label:
            id: cover_{key}_label
            align: CENTER
            y: {ypos-35}
            hidden: {hidden}
            text: "{label}: --"
        - slider:
            id: cover_{key}_slider
            align: CENTER
            y: {ypos}
            width: 250
            height: 16
            min_value: 0
            max_value: 100
            value: 0
            hidden: {hidden}
            on_press:
              - lambda: id(menu_selection) = false; id(cover_tilt_focus) = {hidden};
              - script.execute: render_main_navigation
            on_value:
              - script.execute: display_wake
              - lvgl.label.update:
                  id: cover_{key}_label
                  text: !lambda return str_sprintf("{label}: %.0f %%", x);
'''
            for key,label,xpos,focus in [('position','Höhe',-65,'false'),('tilt','Lamellen',65,'true')]:
                pages += f'''        - button:
            id: cover_{key}_select
            align: CENTER
            x: {xpos}
            y: -85
            width: 120
            height: 32
            hidden: {focus}
            on_click:
              - lambda: id(cover_tilt_focus) = {focus}; id(menu_selection) = false;
              - script.execute: render_main_navigation
            widgets:
              - label:
                  text: "{label}"
                  align: CENTER
'''
        else:
            pages += '''        - image:
            id: switch_dashboard_image
            src: switch_icon_0
            align: CENTER
            y: -70
        - label:
            id: switch_state_label
            align: CENTER
            y: -20
            text: "Nicht erreichbar"
'''
            for name,label,xpos in [('on','Ein',-65),('off','Aus',65)]:
                pages += f'''        - button:
            align: CENTER
            x: {xpos}
            y: 50
            width: 115
            height: 55
            on_click:
              - script.execute: display_wake
              - event.trigger:
                  id: switch_command
                  event_type: turn_{name}
            widgets:
              - label:
                  text: "{label}"
                  align: CENTER
'''
    s = s.replace('  top_layer:\n',pages+'  top_layer:\n',1)
    nav = ''
    for index,kind in enumerate(categories):
        icon = 'switch_icon_0' if kind == 'switch' else 'nav_icon_'+kind
        nav += f'''      - button:
          id: menu_{kind}
          align: CENTER
          x: {(index-2)*60}
          y: 155
          width: 54
          height: 52
          radius: 14
          bg_color: 0x101820
          border_width: 0
          pad_all: 3
          shadow_width: 0
          scrollable: false
          on_click:
            - script.execute: display_wake
            - lambda: id(menu_index) = {index}; id(menu_selection) = false;
            - script.execute: show_menu_page
          widgets:
            - image:
                id: menu_{kind}_image
                src: {icon}
                align: CENTER
                image_recolor: 0xFFFFFF
                image_recolor_opa: COVER
                clickable: false
'''
    s = s.replace('  top_layer:\n    widgets:\n','  top_layer:\n    widgets:\n'+nav,1)
    # on_load also keeps swipe / light-strip navigation synchronized with the menu.
    for index,kind in enumerate(categories):
        page_ids = ['dimmer_page','dimmer_page_2','dimmer_page_3','dimmer_page_4'] if kind=='dimmer' else [kind+'_page']
        for page in page_ids:
            s = s.replace(f'    - id: {page}\n',f'''    - id: {page}
      on_load:
        - lambda: id(menu_index) = {index};
        - script.execute: render_main_navigation
''',1)
    # C++ ternaries and label colons require YAML block scalars.
    s = re.sub(r'^(\s*)([^\n]+?: !lambda) (?!\|-)([^\n]+)$',
               lambda m: m[1]+m[2]+' |-\n'+m[1]+'  '+m[3], s, flags=re.M)
    s = re.sub(r'^( *)(- )?lambda: (?!\|-)([^\n]+)$',
               lambda m: m[1]+(m[2] or '')+'lambda: |-\n'+m[1]+('  ' if m[2] else '')+'  '+m[3], s, flags=re.M)
    return s


if __name__ == '__main__':
    source, destination = map(Path, sys.argv[1:])
    destination.write_text(transform(source.read_text(encoding='utf-8')), encoding='utf-8')
    print('Central display firmware prepared:', destination.name)
