#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private generated GTK2 pressure session, replacements and rollback."""
import copy
import io
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch
from PIL import Image

if os.environ.get('T04_PRIVATE_PRESSED_PROBE') != '1':
    raise SystemExit('Use the private GTK2 Xvfb fixture.')
ROOT = Path(next((a for a in sys.argv[3:] if not a.startswith('--')), str(Path(__file__).resolve().parents[3]))).resolve()
control = 12 if '--arrow' in sys.argv else 0
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
from test_backend import model as initial_model
# The fixture model loads its own source backend and changes sys.path. Restore
# the requested frozen runtime precedence before importing production modules.
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))
import backend
assert Path(backend.__file__).resolve().is_relative_to(ROOT), 'Probe must use requested runtime root'
from gtk2_generation import generate_scrollbar_snapshot
from gtk2_session import NativeSession
from preview_event_writer import EventWriter

output = Path(sys.argv[1]).resolve()
output.mkdir(mode=0o700, parents=True, exist_ok=True)
data = initial_model()
data['selected_family'] = 'gtk2'
recipe = data['recipes']['gtk2']
recipe.update(visible_controls=1 << control, selected_control=control, edit_state=1,
              positions=[[16, 16] for _ in range(16)],
              sizes=[[220, 80] if i == control else [0, 0] for i in range(16)])
palette_source = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / 'colors/DomainOS-SR10.4.colors'
receipt = generate_scrollbar_snapshot(backend, ROOT, output, data, palette_source)
colors = json.loads((output / 'GTK2-NATIVE-COLORS.json').read_text())['colors']
builder = backend.load_builder(ROOT)
pixel_rows = []
rc = Path(receipt['rc'])
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk
Gtk.init([])


def settle():
    deadline = time.monotonic() + .2
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(.005)


def digest(proposal):
    return hashlib.sha256(json.dumps(proposal, sort_keys=True).encode()).hexdigest()


def verify_paint(session, embedded, state, iteration, host):
    widget = session.scene.widgets[control]
    a = widget.get_allocation()
    path = output / ('paint-%s-%s-%s.png' % ('coupled' if embedded else 'separate', state, iteration))
    subprocess.run(['import', '-window', 'root', str(path)],
                   check=True, timeout=5)
    ox, oy = (host if host is not None else session.scene.window).get_position()
    actual = Image.open(path).convert('RGB').crop((ox+a.x, oy+a.y, ox+a.x+a.width, oy+a.y+a.height))
    shadow = recipe['geometry']['shadow_px']
    with backend.recipe_rules(builder, recipe['palette']):
        pixels = builder.art.bevel(builder.art.blank(a.width, a.height, 'face'),
                                   thickness=shadow, down=bool(state))
        expected = Image.open(io.BytesIO(builder.png(pixels, 'button', colors))).convert('RGB')
    edges = [(x, y) for y in range(a.height) for x in range(a.width)
             if x < shadow or y < shadow or x >= a.width-shadow or y >= a.height-shadow]
    differences = sum(actual.getpixel(p) != expected.getpixel(p) for p in edges)
    face = [(x, y) for x in range(shadow+2, shadow+8) for y in range(shadow+2, shadow+8)]
    face_differences = sum(actual.getpixel(p) != expected.getpixel(p) for p in face)
    row = {'origin': 'coupled' if embedded else 'separate', 'state': state,
           'capture': str(path), 'edge_pixels': len(edges), 'edge_differences': differences,
           'face_pixels': len(face), 'face_differences': face_differences}
    if control == 12:
        row['glyph_state'] = int(widget.get_child().get_state())
        assert row['glyph_state'] == int(Gtk.StateType.ACTIVE if state else Gtk.StateType.NORMAL), row
    pixel_rows.append(row)
    (output / 'PIXELS.json').write_text(json.dumps(pixel_rows, indent=2)+'\n')
    assert differences == 0 and face_differences == 0, row


rows = []
for embedded in (False, True):
    # The preceding origin intentionally clicked the button. Move away before
    # testing a NORMAL baseline in the next origin, otherwise native PRELIGHT
    # is legitimate and must not be mistaken for a renderer regression.
    subprocess.run(['xdotool', 'mousemove', '900', '700'], check=True, timeout=4)
    host = None
    if embedded:
        host = Gtk.Window()
        socket = Gtk.Socket()
        host.add(socket)
        host.show_all()
        settle()
        xid = socket.get_id()
    else:
        xid = None
    events = output / ('coupled' if embedded else 'separate')
    events.mkdir(mode=0o700)
    writer = EventWriter(events, ROOT, family='gtk2')
    session = NativeSession(backend, Gtk, Gdk, ROOT, rc, data, digest(data), writer, xid)
    window = session.scene.window
    try:
        settle()
        assert session.scene.widgets[control].get_state() == Gtk.StateType.ACTIVE
        for iteration, state in enumerate((0, 1, 0, 1)):
            proposal = copy.deepcopy(data)
            proposal['recipes']['gtk2']['edit_state'] = state
            previous = session.scene
            session.replace(proposal, digest(proposal))
            settle()
            assert session.scene.window is window
            assert not previous.gestures.handlers
            assert all(demo.closed for demo in previous.press_demos.values())
            assert session.scene.widgets[control].get_state() == (
                Gtk.StateType.ACTIVE if state else Gtk.StateType.NORMAL)
            verify_paint(session, embedded, state, iteration, host)
        current = session.scene
        original_factory = __import__('gtk2_session').LayoutGestures
        attempts = []
        def fail_after_transfer(scene, gdk):
            attempts.append(scene)
            if len(attempts) == 1:
                raise RuntimeError('Injected failure after container transfer')
            return original_factory(scene, gdk)
        with patch('gtk2_session.LayoutGestures', side_effect=fail_after_transfer):
            try:
                session.replace(data, digest(data))
            except RuntimeError as error:
                assert 'Injected failure' in str(error)
            else:
                raise AssertionError('Fault injection did not reach rollback')
        settle()
        assert session.scene is current and window.get_child() is current.fixed
        assert not current.press_demos[control].closed
        assert current.widgets[control].get_state() == Gtk.StateType.ACTIVE
        assert all(demo.closed for demo in attempts[0].press_demos.values())
        assert not attempts[0].gestures.handlers
        # No click may be manufactured by construction or replacements.
        assert not any(json.loads(p.read_text()).get('state', {}).get('clicked')
                       for p in events.glob('*.json'))
        allocation = current.widgets[control].get_allocation()
        ox, oy = (host if host is not None else window).get_position()
        subprocess.run(['xdotool', 'mousemove',
                        str(ox + allocation.x + allocation.width // 2),
                        str(oy + allocation.y + allocation.height // 2),
                        'click', '1'], check=True, timeout=4)
        settle()
        clicked = sum(bool(json.loads(p.read_text()).get('state', {}).get('clicked'))
                      for p in events.glob('*.json'))
        observation = {'origin': 'coupled' if embedded else 'separate',
                       'physical_click_events': clicked,
                       'state_after_physical_release': int(current.widgets[control].get_state())}
        (output / ('CLICK-' + observation['origin'] + '.json')).write_text(
            json.dumps(observation, indent=2)+'\n')
        assert clicked == 1
        if control == 12:
            assert current.widgets[control].get_child().get_state() == Gtk.StateType.ACTIVE
        assert current.widgets[control].get_state() == Gtk.StateType.ACTIVE
        rows.append({'origin': 'coupled' if embedded else 'separate',
                     'normal_pressed_replacements': 4,
                     'rollback_after_transfer': True,
                     'old_scene_preserved': True,
                     'failed_candidate_closed': True,
                     'zero_artificial_clicks': True})
    finally:
        session.close()
        if host is not None:
            host.destroy()
        settle()
    assert all(demo.closed for demo in current.press_demos.values())
(output / 'RESULTADO.json').write_text(json.dumps({'status': 'passed', 'rows': rows,
    'generated_palette': receipt['selected_scheme'], 'pixel_rows': pixel_rows, 'runtime_root': str(ROOT),
    'control': 'arrow' if control == 12 else 'push', 'personal_runtime_updated': False, 'historical_fidelity_claimed': False}, indent=2)+'\n')
