"""Use internal LVGL draw RAM and a German-capable font on the cover page."""
from pathlib import Path
import sys

def transform(source):
    assert source.count('  buffer_size: 50%') == 1
    assert source.count('    - id: cover_page\n') == 1
    assert 'id: desk_name_font' in source and 'GF_Latin_Core' in source
    source = source.replace('  buffer_size: 50%', '  buffer_size: 12%', 1)
    source = source.replace('    - id: cover_page\n',
        '    - id: cover_page\n      text_font: desk_name_font\n', 1)
    return source

if __name__ == '__main__':
    source, destination = map(Path, sys.argv[1:])
    destination.write_text(transform(source.read_text(encoding='utf-8')), encoding='utf-8')
    print('PERFORMANCE_AND_GERMAN_FONT_PATCH_PREPARED')
