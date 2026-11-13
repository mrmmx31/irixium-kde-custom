"""Native Qt label font evidence. No theme installation or editable fields."""
import configparser
import hashlib
import json
import os
from pathlib import Path
import sys

major, target = sys.argv[1:]
if major not in ('5', '6'):
    raise SystemExit('Expected Qt major 5 or 6 and output directory')
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
if major == '5':
    from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGridLayout
    from PyQt5.QtGui import QFont, QFontInfo, QPalette, QColor, QRawFont, QTextLayout
    from PyQt5.QtCore import QT_VERSION_STR, QPoint
    window_role, text_role = QPalette.Window, QPalette.WindowText
else:
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QGridLayout
    from PyQt6.QtGui import QFont, QFontInfo, QPalette, QColor, QRawFont, QTextLayout
    from PyQt6.QtCore import QT_VERSION_STR, QPoint
    window_role, text_role = QPalette.ColorRole.Window, QPalette.ColorRole.WindowText

out = Path(target)
out.mkdir(parents=True, exist_ok=True)
config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'kdeglobals'
parser = configparser.ConfigParser(interpolation=None, strict=False)
parser.optionxform = str
parser.read(config)
app = QApplication(['font-probe'])
widget = QWidget()
widget.setWindowTitle('I120 — Qt'+major+' native labels')
palette = widget.palette()
for role, name in ((window_role, 'BackgroundNormal'), (text_role, 'ForegroundNormal')):
    rgb = [int(x) for x in parser['Colors:Window'][name].split(',')]
    if len(rgb) != 3 or any(x < 0 or x > 255 for x in rgb):
        raise ValueError('Invalid KDE role')
    palette.setColor(role, QColor(*rgb))
widget.setPalette(palette)
widget.setAutoFillBackground(True)
grid = QGridLayout(widget)
rows = []
samples = ['OK', 'Cancel', 'Help', 'Terminal', 'Árvore — ação']
for row, (family, bold, px) in enumerate((('Nimbus Sans', True, 12), ('Liberation Sans', True, 12), ('Nimbus Mono PS', False, 13), ('Liberation Mono', False, 13))):
    heading = QLabel(family+' '+str(px)+'px')
    grid.addWidget(heading, row, 0)
    for column, value in enumerate(samples, 1):
        font = QFont(family)
        font.setBold(bold)
        font.setPixelSize(px)
        label = QLabel(value)
        label.setFont(font)
        grid.addWidget(label, row, column)
        info, raw = QFontInfo(font), QRawFont.fromFont(font)
        layout = QTextLayout(value, font)
        layout.beginLayout()
        line = layout.createLine()
        line.setLineWidth(1000)
        layout.endLayout()
        runs = layout.glyphRuns()
        rows.append({'requested': family, 'absolute_px': px, 'text': value,
                     'stored_text_identical': label.text() == value,
                     'resolved_family': info.family(), 'exact_match': info.exactMatch(),
                     'primary_missing_codepoints': [hex(ord(c)) for c in value if not raw.supportsCharacter(ord(c))],
                     'glyph_run_families': [r.rawFont().familyName() for r in runs],
                     'zero_glyph_count': sum(list(r.glyphIndexes()).count(0) for r in runs),
                     '_label': label})
widget.adjustSize()
widget.show()
app.processEvents()
image = widget.grab()
if not image.save(str(out/('qt'+major+'.png'))):
    raise RuntimeError('Cannot save native capture')
for row in rows:
    label = row.pop('_label')
    pos = label.mapTo(widget, QPoint(0, 0))
    row['allocation'] = [pos.x(), pos.y(), label.width(), label.height()]
assert all(r['stored_text_identical'] and r['zero_glyph_count'] == 0 for r in rows)
result = {'qt_version': QT_VERSION_STR, 'platform': app.platformName(),
          'scope': 'Native QLabel rendering offscreen, no Kvantum/Plasma or personal-window proof',
          'palette_source_sha256': hashlib.sha256(config.read_bytes()).hexdigest(),
          'effective_window_roles': {'face': palette.color(window_role).name(), 'text': palette.color(text_role).name()},
          'device_pixel_ratio': image.devicePixelRatio(), 'rows': rows}
(out/('qt'+major+'.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
widget.close()
print('Qt'+major+' native labels passed: '+str(len(rows)))
