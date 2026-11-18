"""Replace ring toggle with touch controls and add native device diagnostics."""
from pathlib import Path
import datetime
import sys

ICONS = ['lightbulb-outline', 'spotlight-beam', 'led-strip-variant', 'ceiling-light', 'floor-lamp', 'desk-lamp']


def once(s, old, new):
    assert s.count(old) == 1, old[:80]
    return s.replace(old, new, 1)


def transform(s):
    assert 'render_light_navigation' not in s
    # Ring press only wakes the display. It never emits a light command.
    start = s.index('    on_press:\n', s.index('binary_sensor:\n'))
    end = s.index('\nscript:\n', start)
    s = s[:start] + '    on_press:\n      - script.execute: display_wake\n' + s[end:]
    s = s.replace('event_types: [toggle]', 'event_types: [turn_on, turn_off]')
    s = once(s, 'esphome:\n', 'esphome:\n  includes:\n    - display_resources.h\n')
    s = once(s, '    sdkconfig_options:\n', '''    sdkconfig_options:
      CONFIG_FREERTOS_USE_TRACE_FACILITY: y
      CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS: y
      CONFIG_FREERTOS_RUN_TIME_STATS_USING_ESP_TIMER: y
''')
    s = once(s, 'logger:\n', 'debug:\n  update_interval: 30s\n\nlogger:\n')
    diagnostic = '''  - platform: debug
    free:
      name: "Heap frei"
      entity_category: diagnostic
    block:
      name: "Heap groesster Block"
      entity_category: diagnostic
    fragmentation:
      name: "Heap Fragmentierung"
      entity_category: diagnostic
    loop_time:
      name: "Schleifenzeit Maximum"
      entity_category: diagnostic
    psram:
      name: "PSRAM frei"
      entity_category: diagnostic
'''
    for name, expression, interval in (
        ('CPU Auslastung', 'desk_resources::cpu_busy()', '30s'),
        ('RAM Belegung', 'desk_resources::used_percent(MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT)', '30s'),
        ('PSRAM Belegung', 'desk_resources::used_percent(MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT)', '30s'),
        ('Firmware Flash Belegung', 'desk_resources::firmware_percent()', '300s')):
        diagnostic += f'''  - platform: template
    name: "{name}"
    entity_category: diagnostic
    unit_of_measurement: "%"
    accuracy_decimals: 1
    state_class: measurement
    update_interval: {interval}
    lambda: return {expression};
'''
    s = once(s, '\nsensor:\n', '\nsensor:\n' + diagnostic)
    images = ''
    for i, icon in enumerate(ICONS):
        images += f'''  - platform: file
    file: mdi:{icon}
    id: light_icon_{i}
    resize: 28x28
    type: RGB565
    transparency: alpha_channel
'''
    s = once(s, '\nimage:\n', '\nimage:\n' + images)
    # Monochrome icons use alpha masks; their displayed color is supplied by
    # LVGL. Preserve smooth edges while avoiding redundant RGB pixel data.
    s = s.replace('    type: RGB565\n    transparency: alpha_channel',
                  '    type: GRAYSCALE\n    transparency: alpha_channel')

    # Replace hint labels and their gesture catchment together so it cannot
    # obscure the touch buttons. Main bottom navigation stays unchanged.
    old_start = '''        - label:
            align: CENTER
            y: 55
            text: "Drehen oder Ring beruehren"'''
    for page in range(1, 5):
        suffix = '' if page == 1 else f'_{page}'
        start = s.index(old_start)
        end = s.index('        - button:\n            id: nav_dimmer_booking' + suffix + '\n', start)
        controls = '''        - obj:
            align: CENTER
            y: -52
            width: 300
            height: 126
            bg_opa: TRANSP
            border_width: 0
            clickable: true
            scrollable: false
'''
        for action, x, color in [('turn_on', -62, '0x165C3A'), ('turn_off', 62, '0x343E48')]:
            controls += f'''        - button:
            id: light_{action}_{page}
            align: CENTER
            x: {x}
            y: 40
            width: 112
            height: 44
            radius: 12
            bg_color: {color}
            border_width: 0
            shadow_width: 0
            on_click:
              - event.trigger:
                  id: dimmer_toggle_event{suffix}
                  event_type: {action}
              - script.execute: display_wake
            widgets:
              - label:
                  align: CENTER
                  text: "{'Ein' if action == 'turn_on' else 'Aus'}"
                  clickable: false
'''
        controls += f'''        - obj:
            id: light_nav_{page}
            align: CENTER
            y: 100
            width: 256
            height: 52
            hidden: true
            bg_opa: TRANSP
            border_width: 0
            pad_all: 0
            scrollable: false
            widgets:
'''
        for target in range(1, 5):
            target_suffix = '' if target == 1 else f'_{target}'
            controls += f'''              - button:
                  id: light_nav_{page}_{target}
                  align: CENTER
                  x: {(target - 1) * 56 - 84}
                  width: 48
                  height: 46
                  radius: 12
                  pad_all: 0
                  bg_color: {'0x143746' if page == target else '0x101820'}
                  border_width: {3 if page == target else 0}
                  border_color: 0x00D2FF
                  shadow_width: 0
                  on_click:
                    - lvgl.page.show: dimmer_page{target_suffix}
                    - script.execute: display_wake
                  widgets:
                    - image:
                        id: light_nav_image_{page}_{target}
                        align: CENTER
                        src: light_icon_0
                        image_recolor: {'0x00D2FF' if page == target else '0xFFFFFF'}
                        image_recolor_opa: COVER
                        clickable: false
'''
        s = s[:start] + controls + s[end:]

    sensors = ''
    for slot in range(1, 5):
        suffix = '' if slot == 1 else f'_{slot}'
        anchor = f'          lv_label_set_text(id(light_name{suffix}), enabled ? x.c_str() : "Kein Licht zugeordnet");\n'
        s = once(s, anchor, anchor + '      - script.execute: render_light_navigation\n')
        sensors += f'''  - platform: homeassistant
    id: light_icon_from_ha_{slot}
    entity_id: sensor.schreibtisch_01_belegung
    attribute: light_{slot}_icon
    internal: true
    on_value:
'''
        ids = ', '.join(f'light_nav_image_{p}_{slot}' for p in range(1, 5))
        for i, icon in enumerate(ICONS):
            sensors += f'''      - if:
          condition:
            lambda: return x == "mdi:{icon}";
          then:
            - lvgl.image.update:
                id: [{ids}]
                src: light_icon_{i}
'''
    s = once(s, '\ntext_sensor:\n', '\ntext_sensor:\n' + sensors)
    render = '''  - id: render_light_navigation
    then:
      - lambda: |-
          const bool enabled[] = { !id(dimmer_page)->skip, !id(dimmer_page_2)->skip, !id(dimmer_page_3)->skip, !id(dimmer_page_4)->skip };
          int count = 0;
          for (bool value : enabled) if (value) ++count;
'''
    for page in range(1, 5):
        render += f'          if (count > 1) lv_obj_clear_flag(id(light_nav_{page}), LV_OBJ_FLAG_HIDDEN); else lv_obj_add_flag(id(light_nav_{page}), LV_OBJ_FLAG_HIDDEN);\n'
        render += '          { int index = 0;\n'
        for target in range(1, 5):
            render += f'''            if (enabled[{target-1}]) {{
              lv_obj_clear_flag(id(light_nav_{page}_{target}), LV_OBJ_FLAG_HIDDEN);
              lv_obj_set_x(id(light_nav_{page}_{target}), (index++ * 56) - ((count - 1) * 28));
            }} else lv_obj_add_flag(id(light_nav_{page}_{target}), LV_OBJ_FLAG_HIDDEN);
'''
        render += '          }\n'
    s = once(s, '\nscript:\n', '\nscript:\n' + render)
    return s


if __name__ == '__main__':
    p = Path(sys.argv[1])
    before = p.read_text(encoding='utf-8')
    after = transform(before)
    if '--apply' in sys.argv:
        backup = Path('/config/desk_display_backups') / ('before-touch-' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.yaml')
        backup.write_text(before, encoding='utf-8')
        p.write_text(after, encoding='utf-8')
        print('DISPLAY_TOUCH_SAVED', backup)
    else:
        Path(sys.argv[2]).write_text(after, encoding='utf-8')
