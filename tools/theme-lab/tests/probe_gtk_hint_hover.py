#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Real pointer/tooltip checks, restricted to a caller-owned X display."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

assert os.environ.get('T07_PRIVATE_PROBE') == '1'
os.environ['GDK_BACKEND'] = 'x11'
os.environ.pop('WAYLAND_DISPLAY', None)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--family', choices=('gtk2', 'gtk3'), required=True)
parser.add_argument('--control', default='push',
                    choices=('arrow', 'check', 'combo', 'entry', 'frame', 'list',
                             'progress', 'push', 'radio', 'scale_h', 'scale_v',
                             'scroll_h', 'scroll_v', 'spin', 'text', 'toggle'),
                    help='Native control under the pointer; GTK2 and GTK3 support the full catalog.')
parser.add_argument('--rc', type=Path)
parser.add_argument('--button-y', type=int, default=240)
parser.add_argument('--button-x', type=int, default=440,
                    help='Native control X position inside the fixture window.')
parser.add_argument('--window-x', type=int, default=100,
                    help='Fixture window X position in the caller-owned display.')
parser.add_argument('--window-y', type=int, default=80,
                    help='Fixture window Y position in the caller-owned display.')
parser.add_argument('--output', type=Path,
                    help='Private artifact directory below ~/tempia for generated GTK2 control styles.')
parser.add_argument('--embedded', action='store_true')
parser.add_argument('--capture', type=Path)
args = parser.parse_args()
if args.family == 'gtk2' and args.control != 'push' and args.output is None:
    parser.error('A generated GTK2 composite control requires --output below ~/tempia.')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gi
gi.require_version('Gtk', '2.0' if args.family == 'gtk2' else '3.0')
gi.require_version('Gdk', '2.0' if args.family == 'gtk2' else '3.0')
from gi.repository import Gtk, Gdk
assert Gdk.Display.get_default().get_name() == os.environ['DISPLAY']
other_tip = None
if args.family == 'gtk2':
    other_tip = Gtk.Window(type=Gtk.WindowType.POPUP)
    other_tip.set_type_hint(Gdk.WindowTypeHint.TOOLTIP)
    other_tip.set_name('T07OtherTip')
if args.rc:
    assert args.family == 'gtk2'
    Gtk.rc_parse(str(args.rc))
host = None
embed_id = None
if args.embedded:
    assert args.family == 'gtk2'
    host = Gtk.Window()
    host.set_default_size(640, 600)
    host.move(100, 80)
    socket = Gtk.Socket()
    host.add(socket)
    host.show_all()
    while Gtk.events_pending(): Gtk.main_iteration()
    embed_id = socket.get_id()

if args.family == 'gtk3':
    gi.require_version('GdkX11', '3.0')
    from gi.repository import GdkX11  # noqa: F401 — registers the X11 GdkWindow API
    from preview_gtk import NativeScene
    owner = SimpleNamespace(Gtk=Gtk, changed=lambda *_a, **_k: None,
                            queue_window_measurements=lambda *_a: None,
                            bind_text_editor=lambda *_a: None)
    widget = NativeScene.factory(owner, args.control, 0)
    window = Gtk.Window()
    fixed = Gtk.Fixed()
    window.add(fixed)
    fixed.put(widget, args.button_x, args.button_y)
else:
    if args.control == 'push':
        from native_scene_gtk2 import ScrollbarScene
        model = {'recipes': {'gtk2': {'visible_controls': 1,
            'positions': [[args.button_x,args.button_y]] + [[16,16] for _ in range(15)]}}}
        scene = ScrollbarScene(Gtk, model, embed_window=embed_id, show=False)
        widget, window = scene.widgets[0], scene.window
    else:
        import hashlib
        from test_backend import backend, model as sample_model
        from gtk2_generation import generate_scrollbar_snapshot
        from gtk2_session import NativeSession
        from scene_contract import CONTROLS
        root = Path(__file__).resolve().parents[3]
        output = args.output.expanduser().resolve()
        if not output.is_relative_to((Path.home() / 'tempia').resolve()):
            parser.error('--output must be inside ~/tempia')
        output.mkdir(parents=True, exist_ok=True, mode=0o700)
        output.chmod(0o700)
        folder = output / 'DomainOS'
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        model = sample_model()
        model['selected_family'] = 'gtk2'
        recipe = model['recipes']['gtk2']
        target_index = CONTROLS.index(args.control)
        recipe.update(visible_categories=31, visible_controls=1 << target_index,
                      selected_control=target_index, edit_state=0)
        recipe['positions'] = [[args.button_x, args.button_y] if index == target_index else [16, 16]
                               for index in range(len(CONTROLS))]
        recipe['sizes'] = [[0, 0] for _ in CONTROLS]
        snapshot = generate_scrollbar_snapshot(
            backend, root, folder, model, root / 'colors/DomainOS-SR10.4.colors')
        project = folder / 'PROJECT.json'
        backend.write_json(project, model)
        digest = hashlib.sha256(project.read_bytes()).hexdigest()
        session = NativeSession(backend, Gtk, Gdk, root, snapshot['rc'],
                               model, digest, None, embed_window=embed_id)
        scene = session.scene
        widget, window = scene.widgets[target_index], scene.window
window.set_default_size(640, 600)
window.set_title('T07 hover fixture ' + str(os.getpid()))
if not args.embedded: window.move(args.window_x, args.window_y)
widget.set_size_request(120, 36)
actions = []
if args.control == 'push' and hasattr(widget, 'connect'):
    try:
        widget.connect('clicked', lambda *_: actions.append(True))
    except TypeError:
        pass


def drain(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration()
        time.sleep(.002)


def move(x, y):
    subprocess.run(['xdotool', 'mousemove', str(x), str(y)],
                   check=True, capture_output=True, timeout=3)
    deadline = time.monotonic() + 1
    location = ''
    while time.monotonic() < deadline:
        location = subprocess.run(['xdotool', 'getmouselocation', '--shell'],
                                  check=True, capture_output=True, text=True,
                                  timeout=3).stdout
        point = dict(line.split('=', 1) for line in location.splitlines() if '=' in line)
        if (int(point['X']), int(point['Y'])) == (x, y):
            return
        time.sleep(.01)
    raise RuntimeError(f'Pointer did not reach requested probe point {(x, y)}: {location}')


def tips():
    return [w for w in Gtk.Window.list_toplevels()
            if w.get_visible() and w.get_mapped() and w.get_type_hint() == Gdk.WindowTypeHint.TOOLTIP]


window.show_all()
drain(.2)
move(0, 0)
settings = Gtk.Settings.get_default()
delay = settings.get_property('gtk-tooltip-timeout') / 1000
assert .1 <= delay <= 5, delay
# This process has not shown a tooltip yet; settle only the initial pointer
# leave, without waiting out GTK2's long browse-mode timeout from the desktop.
drain(max(1.0, delay + .2))
assert not tips()
offset = widget.translate_coordinates(window, 0, 0)
def x(*args):
    return subprocess.run(['xdotool', *map(str,args)],check=True,
                          capture_output=True,text=True,timeout=3).stdout
if args.family == 'gtk3':
    # Under a reparenting WM, xdotool resolves the toplevel to the decoration
    # frame. GTK child coordinates are relative to the client XID, so query
    # that exact GDK window and use its absolute root coordinates instead.
    xid = window.get_window().get_xid()
    geometry_text = subprocess.check_output(
        ['xwininfo', '-id', str(xid)], text=True, timeout=3)
    geometry = {}
    for line in geometry_text.splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        if key.strip() in ('Absolute upper-left X', 'Absolute upper-left Y'):
            geometry[key.strip()] = int(value.strip())
    if len(geometry) != 2:
        raise RuntimeError('xwininfo did not report GTK client origin: ' + geometry_text)
    origin = (geometry['Absolute upper-left X'], geometry['Absolute upper-left Y'])
else:
    # GTK2 widgets without their own GdkWindow (notably GtkProgressBar) inherit
    # the fixed container's window. xdotool getwindowgeometry can report the
    # reparented frame origin rather than the client origin, shifting the probe
    # outside such a widget. Use the same GDK root-coordinate path as the
    # production tooltip placer. Keep the window lookup only as a diagnostic
    # that the intended fixture is still mapped on this display.
    wid=str(window.get_id()) if args.embedded else x('search','--onlyvisible','--name',window.get_title()).split()[0]
    if not wid:
        raise RuntimeError('GTK2 fixture window was not found by the X11 window manager')
allocation = widget.get_allocation()
if args.family == 'gtk2':
    parent_window = widget.get_parent_window()
    if parent_window is None:
        raise RuntimeError('GTK2 control has no realized parent GDK window')
    root_x, root_y = parent_window.get_root_coords(offset[0], offset[1])
    rect = (root_x, root_y, allocation.width, allocation.height)
else:
    rect = (origin[0] + offset[0], origin[1] + offset[1], allocation.width, allocation.height)
move(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)
drain(delay * .4)
assert not tips(), 'Tooltip appeared before native delay'
drain(delay * .6 + .4)
visible = tips()
if not visible:
    print('DIAGNOSTIC',rect,x('getmouselocation','--shell'),
          [(w.get_name(),str(w.get_type_hint()),w.get_visible(),w.get_mapped(),w.get_position(),w.get_size())
           for w in Gtk.Window.list_toplevels()],file=sys.stderr)
assert len(visible) == 1, len(visible)
tip = visible[0]
position, size = tip.get_position(), tip.get_size()
tip_rect = (*position, *size)
style_colors = None
if args.capture:
    args.capture.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['import','-display',os.environ['DISPLAY'],'-window','root',str(args.capture)],
                   check=True,capture_output=True,timeout=5)
if args.family == 'gtk2':
    if args.capture:
        from PIL import Image
        pixels=list(Image.open(args.capture).convert('RGB').crop(
            (position[0],position[1],position[0]+size[0],position[1]+size[1])).getdata())
        style_colors={}
        for key, prop in (('face','T07_HINT_FACE'),('text','T07_HINT_TEXT')):
            value=os.environ[prop].lstrip('#')
            expected=tuple(int(value[n:n+2],16) for n in (0,2,4))
            count=pixels.count(expected)
            assert count>5,(key,expected,count)
            style_colors[key]={'rgb8':expected,'matching_pixels':count}
screen = Gdk.Screen.get_default()
assert 0 <= position[0] and 0 <= position[1]
assert position[0] + size[0] <= screen.get_width()
assert position[1] + size[1] <= screen.get_height()
bx, by, bw, bh = rect
tx, ty, tw, th = tip_rect
overlap_width = max(0, min(bx + bw, tx + tw) - max(bx, tx))
overlap_height = max(0, min(by + bh, ty + th) - max(by, ty))
overlap_pixels = overlap_width * overlap_height
drain(.4)
stable_tips = tips()
assert (stable_tips == [tip] and tip.get_position() == position and tip.get_size() == size), (
    'Tooltip oscillated', {'initial': (position, size),
                           'current': [(item.get_position(), item.get_size()) for item in stable_tips]})
move(0, 0)
drain(.3)
assert not tips(), 'Tooltip remained after leaving'
if args.family == 'gtk2': assert tip._theme_lab_hint_owner is None
if other_tip: assert not hasattr(other_tip,'_theme_lab_hint_position_bound')
if args.control == 'push':
    move(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)
    subprocess.run(['xdotool','click','1'],check=True,capture_output=True,timeout=3)
    drain(.1)
    assert actions == [True], actions
else:
    # The placement probe does not open the combo popup. Keep popup lifecycle
    # separate so this result measures only delayed hover and tooltip geometry.
    drain(.1)
    assert window.get_visible() and widget.get_mapped()
    assert not tips()
if args.family == 'gtk2' and args.control != 'push':
    scene.gestures.close()
window.destroy()
if host: host.destroy()
if other_tip: other_tip.destroy()
drain(.1)
result = {'status': 'passed' if overlap_pixels == 0 else 'failed',
    'family': args.family, 'control': args.control,
    'native_delay_ms': round(delay * 1000), 'control_rect': rect,
    'tooltip_rect': tip_rect, 'overlap_pixels': overlap_pixels,
    'stability_ms': 400, 'closed_after_pointer_leave': True,
    'style_colors':style_colors, 'embedded':args.embedded,
    'scope': 'one production control, cold native delay, bounds/nonoverlap, 400ms stability, leave; one screen/layout'}
print(json.dumps(result))
if overlap_pixels:
    raise SystemExit(1)
