# SPDX-License-Identifier: GPL-3.0-or-later
"""Render GTK2 Entry active frame offscreen; do not map a host window."""
import configparser, json, os, sys, tempfile, time
from pathlib import Path
assert os.environ.get('T04_PRIVATE_ENTRY') == '1'
TEMP_ROOT = Path.home() / 'tempia'
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_backend import ROOT, backend, model
from gtk2_entries import paint_entry
import gi
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk
if not Gtk.init_check([])[0]:
    raise SystemExit('GTK2 focus test needs an existing X display.')

builder = backend.load_builder(ROOT)
recipe = model()['recipes']['gtk2']
output = Path(os.environ.get('I167_FOCUS_OUTPUT', TEMP_ROOT / 'i167-entry-focus-offscreen'))
output.mkdir(parents=True, exist_ok=True)
sources = {'DomainOS': ROOT/'colors/DomainOS-SR10.4.colors',
           'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
           'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors')}
yellow = configparser.ConfigParser(interpolation=None)
yellow.optionxform = str
yellow.read(sources['DomainOS'])
yellow['General']['Name'] = 'Artificial yellow focus test'
for section, bg, fg in (('Colors:Window','236,216,112','32,28,12'),
                        ('Colors:Button','216,196,92','32,28,12'),
                        ('Colors:View','196,176,72','32,28,12')):
    yellow[section]['BackgroundNormal'] = bg
    yellow[section]['ForegroundNormal'] = fg
yellow['Colors:Selection']['BackgroundNormal'] = '88,72,24'
yellow['Colors:Selection']['ForegroundNormal'] = '255,248,216'
yellow['Colors:Button']['DecorationFocus'] = '64,96,32'
yellow_path = output/'TestYellow.colors'
with yellow_path.open('w', encoding='utf-8') as stream: yellow.write(stream)
sources['TestYellow'] = yellow_path

def drain():
    deadline = time.monotonic() + .15
    while time.monotonic() < deadline:
        while Gtk.events_pending(): Gtk.main_iteration()
        time.sleep(.001)

rows = []
with tempfile.TemporaryDirectory(dir=TEMP_ROOT, prefix='i167-focus-offscreen-') as temp:
    for name, source in sources.items():
        palette, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
        folder = Path(temp)/name
        with backend.recipe_rules(builder, recipe['palette']): generated = paint_entry(builder, recipe, palette, folder)
        Gtk.rc_parse(generated['rc'])
        window = Gtk.OffscreenWindow(); window.set_default_size(300,80)
        entry = Gtk.Entry(); entry.set_name('themeLabEntry_'+generated['style_id'])
        entry.set_text('Foco GTK2 DomainOS'); entry.set_size_request(260,44); window.add(entry)
        window.show_all(); drain(); window.set_focus(None); drain()
        assert not entry.has_focus()
        unfocused = window.get_pixbuf()
        unfocused.savev(str(output/(name+'-unfocused.png')), 'png', [], [])
        # OffscreenWindow has no GDK toplevel-focus event; set GTK's active
        # paint state that GtkEntry::state-hint uses for focused-frame drawing.
        entry.set_state(Gtk.StateType.ACTIVE); entry.queue_draw(); drain()
        assert entry.get_state() == Gtk.StateType.ACTIVE
        focused = window.get_pixbuf()
        focused.savev(str(output/(name+'-active.png')), 'png', [], [])
        focus_rgb = builder.art._rgb(palette[builder.art.ROLES['focus'][0]])
        before, after = unfocused.get_pixels(), focused.get_pixels()
        stride, channels = focused.get_rowstride(), focused.get_n_channels()
        width, height = focused.get_width(), focused.get_height()
        def count(data):
            return sum(tuple(data[y*stride+x*channels:y*stride+x*channels+3]) == focus_rgb
                       for y in range(height) for x in range(width))
        before_count, after_count = count(before), count(after)
        changed = sum(before[i:i+3] != after[i:i+3]
                      for i in range(0, min(len(before),len(after)), channels))
        assert after_count > before_count, (name, focus_rgb, before_count, after_count)
        assert changed > 0, (name, 'active frame did not change pixels')
        rows.append({'scheme':name,'focus_rgb':focus_rgb,'unfocused_focus_pixels':before_count,
                     'active_focus_pixels':after_count,'changed_pixels':changed,
                     'gtk_has_focus':entry.has_focus(),'gtk_state_hint':True,
                     'allocation':[260,44],'origin':origin})
        window.destroy(); drain()

result = {'status':'passed','rows':rows,
          'scope':'GTK2 GtkEntry rendered offscreen in four KDE role palettes. Active-state frame is verified without mapping a host window. OffscreenWindow does not emit a GDK toplevel-focus event; real keyboard-focus delivery remains open.'}
(output/'RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'passed','schemes':len(rows),'rows':rows},ensure_ascii=False))
