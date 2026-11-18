"""Add yellow/red reservation status to the installed booking firmware."""
from pathlib import Path
import sys

def transform(source):
    def replace(old, new):
        nonlocal source
        assert source.count(old) == 1, old[:70]
        source = source.replace(old,new,1)
    replace('  - id: next_booking_warning\n', '''  - id: booking_active
    type: bool
    initial_value: 'false'
  - id: next_booking_warning
''')
    replace('            id(next_booking_warning) = root["warn"].as<bool>();', '''            id(next_booking_warning) = root["warn"].as<bool>();
            id(booking_active) = root["active"].is<bool>() && root["active"].as<bool>();''')
    replace('          const uint32_t ring_color = booking_warn ? 0xFFD43B : 0x36FF7F;', '''          const bool reservation_active = booking_fresh && id(booking_active);
          const uint32_t ring_color = reservation_active ? 0xFF3B30 : booking_warn ? 0xFFD43B : 0x36FF7F;''')
    replace('          if ((free || booking_warn) && !id(message_open))', '          if ((free || booking_warn || reservation_active) && !id(message_open))')
    replace('          lv_label_set_text(id(desk_status_label), headline);', '''          if (reservation_active || (free && booking_warn)) {
            headline = "RESERVIERT";
            color = reservation_active ? 0xFF3B30 : 0xFFD43B;
            hint = reservation_active ? "Reservierung laeuft" : "Reservierung beginnt bald";
          }
          lv_label_set_text(id(desk_status_label), headline);''')
    return source

if __name__ == '__main__':
    src,dst=map(Path,sys.argv[1:3])
    assert src.resolve()!=dst.resolve()
    dst.write_text(transform(src.read_text(encoding='utf-8')),encoding='utf-8')
    print('RESERVED_FIRMWARE_STAGED')
