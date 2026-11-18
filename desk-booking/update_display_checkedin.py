"""Give confirmed check-in precedence over calendar hints on the display."""
from pathlib import Path
import sys


def transform(source):
    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old[:100]
        source = source.replace(old, new, 1)
    replace('if ((free || booking_warn || reservation_active) && !id(message_open))',
            'if (!occupied && (free || booking_warn || reservation_active) && !id(message_open))')
    replace('if (reservation_active || (free && booking_warn)) {',
            'if (!occupied && (reservation_active || (free && booking_warn))) {')
    replace('hint = "Dein Arbeitsplatz";\n            color = 0xFFFFFF;',
            'hint = "Dein Arbeitsplatz";\n            color = 0x3399FF;')
    replace('lv_label_set_text(id(next_booking_who_label), booking_fresh ? id(next_booking_who).c_str() : "");',
            'lv_label_set_text(id(next_booking_who_label), !occupied && booking_fresh ? id(next_booking_who).c_str() : "");')
    replace('if (occupied) lv_obj_clear_flag(id(desk_name_header), LV_OBJ_FLAG_HIDDEN);',
            'if (occupied && id(menu_index) != 0) lv_obj_clear_flag(id(desk_name_header), LV_OBJ_FLAG_HIDDEN);')
    # Navigation redraws on each page load, ensuring the header follows the page.
    replace('          if (!enabled[id(menu_index)]) id(menu_index) = 0;',
            '          if (!enabled[id(menu_index)]) id(menu_index) = 0;\n          id(render_desk_status).execute();')
    return source


if __name__ == '__main__':
    src,dst=map(Path,sys.argv[1:3])
    assert src.resolve()!=dst.resolve()
    dst.write_text(transform(src.read_text(encoding='utf-8')),encoding='utf-8')
    print('CHECKEDIN_FIRMWARE_STAGED')
