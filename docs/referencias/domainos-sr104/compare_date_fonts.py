"""Read archived SR10.4 date metrics and measure explicit Pango candidates."""
import json
from pathlib import Path
import gi
from compare_font_metrics import GLYPH, text_metrics

gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo
root = Path(__file__).resolve().parent
raw = (root/'i120-x11-metrics/system17-glyphs.txt').read_text(encoding='latin1')
glyphs = {int(m[1], 16): tuple(map(int, m.groups()[1:])) for line in raw.splitlines() if (m := GLYPH.match(line))}
texts = ['Oct 11', 'Fri']
reference = {value: text_metrics(glyphs, value) for value in texts}
context = PangoCairo.FontMap.get_default().create_context()
rows = []
for family in ('Nimbus Sans Bold', 'Liberation Sans Bold'):
    for px in (12, 13, 14):
        font = Pango.FontDescription(family)
        font.set_absolute_size(px*Pango.SCALE)
        samples = {}
        for value in texts:
            layout = Pango.Layout.new(context)
            layout.set_font_description(font)
            layout.set_text(value, -1)
            ink, logical = layout.get_pixel_extents()
            samples[value] = {'ink': [ink.x, ink.y, ink.width, ink.height], 'logical': [logical.x, logical.y, logical.width, logical.height], 'advance_delta_px': logical.width-reference[value]['advance'], 'ink_height_delta_px': ink.height-reference[value]['ink'][3]}
        rows.append({'requested': family, 'absolute_px': px, 'samples': samples})
print(json.dumps({'scope': 'Archived system17 ASCII date vs Pango, no panel typography change or glyph equality', 'reference': reference, 'rows': rows}, ensure_ascii=False, indent=2))
