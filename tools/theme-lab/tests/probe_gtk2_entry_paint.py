# SPDX-License-Identifier: GPL-3.0-or-later
"""GtkEntry foundation only, on an explicitly isolated X display."""
import os
assert os.environ.get('T04_PRIVATE_ENTRY') == '1'
import configparser
import json
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_backend import ROOT, backend, model
from gtk2_entries import paint_entry
import gi
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk, Gdk, GLib
from preview_text_editing import bind
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

rows = []
keyboard_proof = None
focus_proof = []
for name, source in schemes.items():
    palette, origin = backend.native_roles(ROOT, source, builder.art, backend.sha(source.read_bytes()))
    folder = output/name
    with backend.recipe_rules(builder, recipe['palette']):
        generated = paint_entry(builder, recipe, palette, folder)
    Gtk.rc_parse(generated['rc'])
    for coupled in (False, True):
        for variant, index, prefix in (('normal', 0, 'themeLabEntry'),
                                      ('backdrop', 1, 'themeLabBackdropEntry'),
                                      ('disabled', 2, 'themeLabInsensitiveEntry')):
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
            entry = Gtk.Entry()
            entry.set_name(prefix + '_' + generated['style_id'])
            entry.set_text('Ação — seleção')
            entry.set_sensitive(index != 2)
            entry.set_size_request(260, 44)
            fixed.put(entry, 16, 16)
            window.show_all()
            drain()
            allocation = entry.get_allocation()
            assert [allocation.width, allocation.height] == [260, 44]
            assert entry.get_text() == 'Ação — seleção'
            assert entry.get_sensitive() == (index != 2)
            if variant == 'normal':
                window.set_focus(None)
                drain()
                assert not entry.is_focus(), 'GtkEntry did not relinquish keyboard focus'
                unfocused_png = folder/('coupled-' if coupled else 'separate-')
                unfocused_png = unfocused_png.with_name(unfocused_png.name + 'entry-unfocused.png')
                subprocess.run(['import', '-window', 'root', str(unfocused_png)], check=True, timeout=10)
                window.set_focus(entry)
                entry.grab_focus()
                drain()
                assert entry.is_focus(), 'GtkEntry did not receive keyboard focus'
                # Gtk.Window.set_focus() changes GTK's internal focus child,
                # but does not prove that the mapped X toplevel received
                # FocusIn. Direct X focus also exercises state-hint on a real
                # GDK toplevel, including the embedded GtkPlug case.
                title = 'I167 mapped focus %s %s' % (name, coupled)
                host.set_title(title)
                drain()
                window_id = subprocess.check_output(
                    ['xdotool', 'search', '--name', '^' + title + '$'],
                    text=True, timeout=5).split()[0]
                subprocess.run(['xdotool', 'windowmap', window_id,
                                'windowraise', window_id,
                                'windowfocus', '--sync', window_id],
                               check=True, timeout=5)
                drain()
                actual_xid = subprocess.check_output(
                    ['xdotool', 'getwindowfocus'], text=True, timeout=5).strip()
                assert actual_xid == window_id, (window_id, actual_xid)
                assert host.get_property('has-toplevel-focus'), \
                    'X focus did not reach GTK toplevel'
                focused_png = folder/('coupled-' if coupled else 'separate-')
                focused_png = focused_png.with_name(focused_png.name + 'entry-focused.png')
                subprocess.run(['import', '-window', 'root', str(focused_png)], check=True, timeout=10)
                before = Image.open(unfocused_png).convert('RGB')
                after = Image.open(focused_png).convert('RGB')
                x, y = host.get_position()
                region = (max(0, x + 8), max(0, y + 8),
                          min(after.width, x + 300), min(after.height, y + 80))
                before_roi, after_roi = before.crop(region), after.crop(region)
                focus_rgb = builder.art._rgb(palette[builder.art.ROLES['focus'][0]])
                before_count = sum(pixel == focus_rgb for pixel in before_roi.getdata())
                after_count = sum(pixel == focus_rgb for pixel in after_roi.getdata())
                changed = sum(a != b for a, b in zip(before_roi.getdata(), after_roi.getdata()))
                assert after_count > before_count, (name, coupled, focus_rgb, before_count, after_count)
                assert changed > 0, (name, coupled, 'focus transfer did not change rendered pixels')
                focus_proof.append(dict(scheme=name, coupled=coupled, focus_rgb=focus_rgb,
                                        unfocused_role_pixels=before_count,
                                        focused_role_pixels=after_count,
                                        changed_pixels=changed, roi=list(region)))
            png = folder/('coupled-' if coupled else 'separate-')
            png = png.with_name(png.name + variant + '.png')
            subprocess.run(['import', '-window', 'root', str(png)], check=True, timeout=10)
            screen = Image.open(png).convert('RGB')
            x, y = host.get_position()
            pixel = screen.getpixel((x + 245, y + 35))
            expected = builder.art._rgb(palette[builder.art.ROLES['view'][index]])
            assert pixel == expected, (name, coupled, variant, pixel, expected)
            rows.append(dict(scheme=name, variant=variant, coupled=coupled,
                             background=pixel, size=[allocation.width, allocation.height],
                             font=entry.get_pango_context().get_font_description().to_string(),
                             style_id=generated['style_id'], origin=origin))
            if name == 'DomainOS' and not coupled and variant == 'normal':
                bind(entry, Gtk, Gdk, GLib)
                host.set_title('I200 private GTK2 entry keyboard')
                expected = 'Ação — ç'
                entry.set_text(expected); drain()
                window_id = subprocess.check_output(
                    ['xdotool', 'search', '--name', '^I200 private GTK2 entry keyboard$'],
                    text=True, timeout=5).split()[0]
                subprocess.run(['xdotool', 'windowfocus', window_id,
                                'mousemove', '--window', window_id, '40', '34', 'click', '1'],
                               check=True, timeout=5); drain()
                def key(sequence):
                    subprocess.run(['xdotool', 'key', '--clearmodifiers', sequence],
                                   check=True, timeout=5); drain()
                key('ctrl+a')
                selection = entry.get_selection_bounds()
                if len(selection) == 3: selection = selection[1:] if selection[0] else ()
                assert selection == (0, len(expected)), selection
                key('ctrl+c')
                subprocess.run(['xdotool', 'type', '--clearmodifiers', 'Replacement'],
                               check=True, timeout=5); drain()
                assert entry.get_text() == 'Replacement', entry.get_text()
                key('ctrl+a'); key('ctrl+v')
                assert entry.get_text() == expected, entry.get_text()
                key('ctrl+a'); key('ctrl+x')
                assert entry.get_text() == ''
                key('ctrl+z'); assert entry.get_text() == expected, entry.get_text()
                key('ctrl+y'); assert entry.get_text() == ''
                key('ctrl+v'); assert entry.get_text() == expected
                key('ctrl+z'); assert entry.get_text() == ''
                key('ctrl+shift+z'); assert entry.get_text() == expected
                entry.select_region(0, 4); drain()
                subprocess.run(['xdotool', 'type', '--clearmodifiers', 'Test'],
                               check=True, timeout=5); drain()
                assert entry.get_text() == 'Test — ç', entry.get_text()
                undo_steps = 0
                while entry.get_text() != expected and undo_steps < 5:
                    key('ctrl+z'); undo_steps += 1
                assert entry.get_text() == expected, entry.get_text()
                popup_labels = []
                def inspect_popup(_widget, menu):
                    popup_labels.extend(child.get_label() for child in menu.get_children()
                                        if hasattr(child, 'get_label'))
                entry.connect_after('populate-popup', inspect_popup)
                subprocess.run(['xdotool', 'mousemove', '--window', window_id,
                                '40', '34', 'click', '3'], check=True, timeout=5); drain()
                subprocess.run(['xdotool', 'key', 'Escape'], check=True, timeout=5); drain()
                normalized = {label.strip().lower() for label in popup_labels}
                required = {'undo', 'redo', 'gtk-cut', 'gtk-copy', 'gtk-paste', 'gtk-select-all'}
                assert required <= normalized, sorted(normalized)
                keyboard_proof = {'utf8_text': True, 'select_all': True, 'selection_replacement': True,
                                  'copy_paste_cut': True, 'undo_ctrl_z': True,
                                  'redo_ctrl_y': True, 'redo_ctrl_shift_z': True,
                                  'replacement_undo_steps': undo_steps,
                                  'edit_menu_actions': sorted(required),
                                  'native_popup_actions': sorted(normalized)}
            window.destroy()
            if coupled:
                host.destroy()
            drain()
result = dict(status='passed', rows=rows,
              focus_outline=focus_proof,
              keyboard_editing=keyboard_proof,
              scope='GtkEntry native foundation in 24 palette/state/origin scenes plus real X11 keyboard/clipboard test in the DomainOS scene. Focus role was tested by explicit keyboard-focus transfer in four palettes and both origins. Not controller integration, persisted text-history, full selected-text pixel proof or historical approval.')
(output/'RESULTADO.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(dict(status='passed', native_scenes=len(rows))))
