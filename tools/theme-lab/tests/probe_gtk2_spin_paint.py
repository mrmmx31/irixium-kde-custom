# SPDX-License-Identifier: GPL-3.0-or-later
"""GtkSpinButton foundation only, on an explicitly isolated X display."""
import os
assert os.environ.get('T04_PRIVATE_SPIN') == '1'
import configparser
import json
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageChops
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_spins import paint_spin
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk, GLib
from preview_text_editing import bind
from sample_contract import SAMPLES
Gtk.init([])
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
builder = backend.load_builder(ROOT)
recipe = model()['recipes']['gtk2']
schemes = {'DomainOS': ROOT/'colors/DomainOS-SR10.4.colors',
           'BreezeLight': Path('/usr/share/color-schemes/BreezeLight.colors'),
           'BreezeDark': Path('/usr/share/color-schemes/BreezeDark.colors')}
yellow = configparser.ConfigParser(interpolation=None)
yellow.optionxform = str
yellow.read(schemes['DomainOS'])
yellow['General']['Name'] = 'Artificial yellow test'
for section in ('Colors:Window', 'Colors:Button', 'Colors:View'):
    yellow[section]['BackgroundNormal'] = '236,216,112'
    yellow[section]['ForegroundNormal'] = '32,28,12'
yellow['Colors:Selection']['BackgroundNormal'] = '88,72,24'
yellow['Colors:Selection']['ForegroundNormal'] = '255,248,216'
schemes['TestYellow'] = output/'TestYellow.colors'
with schemes['TestYellow'].open('w') as stream:
    yellow.write(stream)

def drain():
    deadline = time.monotonic() + .15
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration()
        time.sleep(.001)

editing_only = '--editing-only' in sys.argv
if editing_only:
    schemes = {'DomainOS': schemes['DomainOS']}
rows = []
for name, source in schemes.items():
    palette, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
    folder = output/name
    with backend.recipe_rules(builder, recipe['palette']):
        generated = paint_spin(builder, recipe, palette, folder)
    Gtk.rc_parse(generated['rc'])
    for coupled in (False, True):
        variants = (('normal',0,'themeLabSpin'),) if editing_only else (('normal',0,'themeLabSpin'),('backdrop',1,'themeLabBackdropSpin'),('disabled',2,'themeLabInsensitiveSpin'))
        for variant, index, prefix in variants:
            host = Gtk.Window()
            if coupled:
                socket = Gtk.Socket()
                host.add(socket)
                host.show_all()
                drain()
                window = Gtk.Plug.new(socket.get_id())
            else:
                window = host
            fixed = Gtk.Fixed()
            window.add(fixed)
            entry = Gtk.SpinButton.new_with_range(0, 100, 1)
            entry.set_name(prefix + '_' + generated['style_id'])
            entry.set_value(SAMPLES['spin'])
            editor = bind(entry, Gtk, Gdk, GLib)
            entry.set_sensitive(index != 2)
            entry.set_size_request(260, 44)
            fixed.put(entry, 16, 16)
            window.show_all()
            drain()
            allocation = entry.get_allocation()
            assert [allocation.width, allocation.height] == [260, 44]
            assert entry.get_text() == str(SAMPLES['spin']) and entry.get_value()==SAMPLES['spin']
            assert entry.get_sensitive() == (index != 2)
            png = folder/('coupled-' if coupled else 'separate-')
            png = png.with_name(png.name + variant + '.png')
            subprocess.run(['import', '-window', 'root', str(png)], check=True, timeout=10)
            screen = Image.open(png).convert('RGB')
            x, y = host.get_position()
            pixel = screen.getpixel((x + 150, y + 35))
            expected = builder.art._rgb(palette[builder.art.ROLES['view'][index]])
            assert pixel == expected, (name, coupled, variant, pixel, expected)
            panel_pixel = screen.getpixel((x + 268, y + 17))
            assert panel_pixel == expected, (name, coupled, variant, panel_pixel, expected)
            native_input = None
            native_relief = []
            if name == 'DomainOS' and index == 0:
                host.set_title('T04 private numeric spin');drain()
                subprocess.run(['xdotool','search','--name','^T04 private numeric spin$','windowfocus'],check=True,timeout=5)
                entry.grab_focus();drain()
                if not coupled:
                    # Compare each real GtkSpinButton child in normal, held,
                    # and released states. The crop excludes the text field;
                    # the glyph PNG is composited over the effective View
                    # role so transparent pixels remain palette-driven.
                    view = builder.art._rgb(palette[builder.art.ROLES['view'][0]])
                    for direction, dy in (('up', 24), ('down', 38)):
                        px, py = x + 268, y + dy
                        subprocess.run(['xdotool','mousemove',str(px),str(py),'mousedown','1'],check=True,timeout=5)
                        try:
                            drain()
                            held = folder/(direction+'-held.png')
                            subprocess.run(['import','-window','root',str(held)],check=True,timeout=10)
                        finally:
                            subprocess.run(['xdotool','mouseup','1'],check=True,timeout=5)
                        drain()
                        released = folder/(direction+'-released.png')
                        subprocess.run(['import','-window','root',str(released)],check=True,timeout=10)
                        box = (x + 261, y + (18 if direction == 'up' else 31),
                               x + 274, y + (31 if direction == 'up' else 44))
                        baseline = screen.crop(box)
                        held_screen = Image.open(held).convert('RGB')
                        released_screen = Image.open(released).convert('RGB')
                        held_pixels = held_screen.crop(box)
                        released_pixels = released_screen.crop(box)
                        self_change = ImageChops.difference(baseline, held_pixels).getbbox()
                        assert self_change, (direction, 'held glyph did not change')
                        assert ImageChops.difference(baseline, released_pixels).getbbox() is None, direction
                        expected_name = next(folder.glob('spin-'+direction+'-pressed-*.png'))
                        expected_image = Image.open(expected_name).convert('RGBA')
                        background = Image.new('RGBA', expected_image.size, view+(255,))
                        expected_image = Image.alpha_composite(background, expected_image).convert('RGB')
                        assert ImageChops.difference(held_pixels, expected_image).getbbox() is None, (
                            direction, 'held mask differs from generated Motif recipe', (x, y), box, view,
                            ImageChops.difference(held_pixels, expected_image).getbbox())
                        native_relief.append(direction)
                # The panel is allocated by GTK2, not by the renderer.
                subprocess.run(['xdotool','mousemove',str(x+268),str(y+24),'click','1'],check=True,timeout=5);drain()
                assert entry.get_value()==SAMPLES['spin']+1,entry.get_value()
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+z'],check=True,timeout=5);drain()
                assert entry.get_value()==SAMPLES['spin'] and entry.get_text()==str(SAMPLES['spin'])
                for keys, expected in (('Up',26),('Down',25)):
                    subprocess.run(['xdotool','key','--clearmodifiers',keys],check=True,timeout=5);drain()
                    assert entry.get_value()==expected
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','type','73'],check=True,timeout=5);drain()
                subprocess.run(['xdotool','key','Return'],check=True,timeout=5);drain()
                assert entry.get_value()==73 and entry.get_text()=='73'
                # Native typing can record a separate edit per character.
                # Walk the actual history, rather than require one batch edit.
                for keys, expected in (('ctrl+z',25),('ctrl+y',73)):
                    for _ in range(6):
                        subprocess.run(['xdotool','key','--clearmodifiers',keys],check=True,timeout=5);drain()
                        if entry.get_value()==expected and entry.get_text()==str(expected):
                            break
                    else:
                        raise AssertionError((keys,expected,entry.get_value(),entry.get_text(),editor.history.states))
                for keys, expected in (('ctrl+a ctrl+c ctrl+x',''),('ctrl+v','73'),('ctrl+z',''),('ctrl+shift+z','73')):
                    subprocess.run(['xdotool','key','--clearmodifiers',*keys.split()],check=True,timeout=5);drain()
                    assert entry.get_text()==expected,(keys,entry.get_text())
                native_input = {'mouse_step':True,'keyboard_step':True,'typed_numeric_commit':True,
                                'undo_redo_numeric':True,'clipboard_shortcuts':True,
                                'stepper_press_release':native_relief}
            rows.append(dict(native_input=native_input,scheme=name, variant=variant, coupled=coupled,
                             background=pixel, size=[allocation.width, allocation.height],
                             font=entry.get_pango_context().get_font_description().to_string(),
                             style_id=generated['style_id'], origin=origin))
            window.destroy()
            if coupled:
                host.destroy()
            drain()
result = dict(status='passed', rows=rows, editing_only=editing_only,
              scope='GtkSpinButton native foundation, 24 scenes in one process: field and flat stepper View roles, sample value, size, sensitivity and font. DomainOS normal both origins: real arrow click, Up/Down, typed numeric commit, Undo/Redo and clipboard shortcuts. Separate preview: both directions held/released against generated masks. Not product pipeline/controller integration, project text-history persistence, whole-control historical VM proof or approval.')
(output/'RESULTADO.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(dict(status='passed', native_scenes=len(rows))))
