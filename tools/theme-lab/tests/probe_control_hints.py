#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native hint coverage on an owned X display; never start on a personal display."""
import argparse
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

assert os.environ.get('T07_PRIVATE_PROBE') == '1'
os.environ['GDK_BACKEND'] = 'x11'
os.environ.pop('WAYLAND_DISPLAY', None)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--family', choices=('gtk2', 'gtk3'), required=True)
parser.add_argument('--all-controls', action='store_true',
                    help='Mount all 16 real GTK2 controls from a generated private recipe.')
parser.add_argument('--output', type=Path,
                    help='Private artifact directory below ~/tempia; required with --all-controls.')
args = parser.parse_args()
if args.all_controls and (args.family != 'gtk2' or args.output is None):
    parser.error('--all-controls requires --family gtk2 and --output below ~/tempia')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gi
gi.require_version('Gtk', '2.0' if args.family == 'gtk2' else '3.0')
from gi.repository import Gtk
gi.require_version('Gdk', '2.0' if args.family == 'gtk2' else '3.0')
from gi.repository import Gdk
assert Gdk.Display.get_default().get_name() == os.environ['DISPLAY']
from control_hints import CONTROL_HINTS, control_hint

if args.family == 'gtk3':
    from preview_gtk import NativeScene, CONTROLS
    # Exercise the production factory, with an observation-only event sink.
    owner = SimpleNamespace(Gtk=Gtk, changed=lambda *_a, **_k: None,
                            queue_window_measurements=lambda *_a: None,
                            bind_text_editor=lambda *_a: None)
    window = Gtk.Window()
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    window.add(box)
    widgets = {identifier: NativeScene.factory(owner, identifier, index)
               for index, identifier in enumerate(CONTROLS)}
    for widget in widgets.values():
        box.pack_start(widget, False, False, 0)
else:
    if args.all_controls:
        import hashlib
        from test_backend import backend, model as sample_model
        from gtk2_generation import generate_scrollbar_snapshot
        from gtk2_session import NativeSession
        from scene_contract import CONTROLS
        root = Path(__file__).resolve().parents[3]
        output = args.output.expanduser().resolve()
        task_tmp = (Path.home() / 'tempia').resolve()
        if not output.is_relative_to(task_tmp):
            parser.error('--output must be inside ~/tempia')
        output.mkdir(parents=True, exist_ok=True, mode=0o700)
        output.chmod(0o700)
        folder = output / 'DomainOS'
        folder.mkdir(mode=0o700, exist_ok=True)
        base = sample_model()
        base['selected_family'] = 'gtk2'
        recipe = base['recipes']['gtk2']
        recipe.update(visible_categories=31,
                      visible_controls=(1 << len(CONTROLS)) - 1,
                      selected_control=0, edit_state=0)
        recipe['positions'] = [[16 + (index % 2) * 540,
                                16 + (index // 2) * 110]
                               for index in range(len(CONTROLS))]
        recipe['sizes'] = [[0, 0] for _ in CONTROLS]
        snapshot = generate_scrollbar_snapshot(
            backend, root, folder, base, root / 'colors/DomainOS-SR10.4.colors')
        if set(snapshot['translated_controls']) != set(CONTROLS):
            raise AssertionError('Generated GTK2 recipe does not cover the catalog.')
        project = folder / 'PROJECT.json'
        backend.write_json(project, base)
        project_hash = hashlib.sha256(project.read_bytes()).hexdigest()
        session = NativeSession(backend, Gtk, Gdk, root, snapshot['rc'],
                               base, project_hash, None)
        native = session.scene
        native.fixed.set_size_request(1100, 1000)
        native.window.set_default_size(1100, 1000)
        window = native.window
        widgets = {native.records[index]['id']: widget
                   for index, widget in native.widgets.items()}
    else:
        from native_scene_gtk2 import ScrollbarScene
        model = {'recipes': {'gtk2': {'visible_controls': sum(1 << n for n in (0, 1, 2, 3, 10, 11))}}}
        native = ScrollbarScene(Gtk, model, show=False)
        window = native.window
        widgets = {native.records[index]['id']: widget for index, widget in native.widgets.items()}
window.show_all()
while Gtk.events_pending():
    Gtk.main_iteration()
count = 0


def verify(widget, expected):
    global count
    assert widget.get_tooltip_text() == expected, (type(widget).__name__, widget.get_tooltip_text())
    count += 1
    if hasattr(widget, 'get_children'):
        for child in widget.get_children():
            verify(child, expected)


for identifier, widget in widgets.items():
    expected = control_hint(identifier, args.family)
    assert 'Ctrl+clique' in expected and 'Ctrl+arraste' in expected and 'px' in expected
    verify(widget, expected)
expected_types = 16 if args.family == 'gtk3' or args.all_controls else 6
assert len(widgets) == expected_types
assert len(CONTROL_HINTS) == 16
if args.all_controls:
    (output / 'hint-coverage.json').write_text(json.dumps({
        'status': 'passed', 'family': 'gtk2', 'native_types': len(widgets),
        'widgets_with_hint': count, 'controls': sorted(widgets),
        'scope': 'real generated GTK2 recipe; native controls and compound descendants; assignment only, no timed hover claim'
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
window.destroy()
while Gtk.events_pending():
    Gtk.main_iteration()
print(json.dumps({'status': 'passed', 'family': args.family, 'native_types': len(widgets),
                  'widgets_with_hint': count,
                  'scope': 'production native factories and compound descendants; no timing/pixel fidelity claim'}))
