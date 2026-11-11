#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private investigation: ACTIVE painting versus a real held GTK2 button.

Not a theme-fidelity test or permission to enable forced states in the product.
Uses no editable fields, user data or personal display.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if os.environ.get('T04_PRIVATE_PRESSED_PROBE') != '1':
    raise SystemExit('Run only in the explicitly private Xvfb fixture.')

import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk


def settle():
    deadline = time.monotonic() + .15
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(.005)


def snapshot(button):
    box = button.get_allocation()
    child = button.get_child().get_allocation()
    return {'state': int(button.get_state()),
            'allocation': [box.x, box.y, box.width, box.height],
            'child_allocation': [child.x, child.y, child.width, child.height]}


def main():
    output = Path(sys.argv[1])
    displacement = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    method = sys.argv[3] if len(sys.argv) > 3 else 'state'
    observe_hover = len(sys.argv) > 4 and sys.argv[4] == 'hover'
    assert 0 <= displacement <= 8
    assert method in ('state', 'native-signals', 'native-crossing',
                      'native-bridge', 'native-bridge-sticky', 'project-bridge')
    sticky_method = method in ('native-bridge-sticky', 'project-bridge')
    bridge_method = method in ('native-bridge', 'native-bridge-sticky', 'project-bridge')
    Gtk.init([])
    if displacement:
        # Geometry-only private override exercises GtkButton's internal
        # depressed layout; no static palette or personal RC is written.
        Gtk.rc_parse_string('style "pressed-probe-geometry" { '
            'GtkButton::child-displacement-x = %d '
            'GtkButton::child-displacement-y = %d } '
            'widget "*pressedProbeButton" style : highest "pressed-probe-geometry"'
            % (displacement, displacement))
    window = Gtk.Window()
    window.set_title('T04 private GTK2 pressed-state investigation')
    window.set_default_size(320, 160)
    button = Gtk.Button(label='Native press')
    button.set_name('pressedProbeButton')
    button.set_size_request(180, 60)
    fixed = Gtk.Fixed()
    fixed.put(button, 40, 40)
    window.add(fixed)
    clicks = []
    button.connect('clicked', lambda *_: clicks.append(True))
    window.show_all()
    settle()
    subprocess.run(['xdotool', 'mousemove', '700', '500'], check=True, timeout=5)
    settle()
    normal = snapshot(button)
    demonstration = None
    if bridge_method:
        import ctypes as C
        if method == 'project-bridge':
            from gtk2_press_bridge import Gtk2PressBridge
            project_bridge = Gtk2PressBridge(Path(__file__).resolve().parents[3])
            library = project_bridge.library
            setter = library.theme_lab_gtk2_press_set
        else:
            library = C.CDLL(os.environ['T04_GTK2_PRESS_BRIDGE_FILE'])
            setter = library.t04_gtk2_demo_depressed
        setter.argtypes, setter.restype = [C.c_void_p, C.c_int], C.c_int
        capsule = C.pythonapi.PyCapsule_GetPointer
        capsule.argtypes, capsule.restype = [C.py_object, C.c_char_p], C.c_void_p
        pointer = capsule(button.__gpointer__, None)
        input_flags = (library.theme_lab_gtk2_press_input_flags if method == 'project-bridge'
                       else library.t04_gtk2_demo_input_flags)
        input_flags.argtypes, input_flags.restype = [C.c_void_p], C.c_int
        flags_before = input_flags(pointer)
        if sticky_method:
            from gtk2_pressed_state import PressedButtonDemo
            if method == 'project-bridge':
                set_visual = project_bridge.bind(button)
            else:
                def set_visual(enabled):
                    if setter(pointer, int(enabled)) != 0:
                        raise ValueError('Private GTK2 bridge rejected visual state')
            demonstration = PressedButtonDemo(button, set_visual)
        else:
            assert setter(pointer, 1) == 0
    def crossing(kind):
        event = Gdk.Event.new(kind)
        event.crossing.window = button.get_event_window()
        event.crossing.detail = Gdk.NotifyType.NONLINEAR
        event.crossing.mode = Gdk.CrossingMode.NORMAL
        button.event(event)

    if bridge_method:
        pass  # The guarded C experiment already updated the visual flag.
    elif method == 'native-crossing':
        crossing(Gdk.EventType.ENTER_NOTIFY)
        button.pressed()
    elif method == 'native-signals':
        button.enter()
        button.pressed()
    else:
        button.set_state(Gtk.StateType.ACTIVE)
    button.queue_resize()
    settle()
    forced = snapshot(button)
    flags_forced = input_flags(pointer) if bridge_method else None
    forced_clicks = len(clicks)
    hover_observations = []
    if observe_hover:
        xid = subprocess.check_output(['xdotool', 'search', '--name',
            '^T04 private GTK2 pressed-state investigation$'], text=True,
            timeout=5).strip()
        assert xid.isdecimal()
        for name, args in (
            ('enter', ['mousemove', '--window', xid, '120', '65']),
            ('leave', ['mousemove', '700', '500']),
        ):
            subprocess.run(['xdotool', *args], check=True, timeout=5)
            settle()
            hover_observations.append({'event': name, 'native': snapshot(button),
                'activations': len(clicks), 'input_flags':
                input_flags(pointer) if bridge_method else None})
    if demonstration is not None:
        demonstration.close()
    if bridge_method:
        if demonstration is None:
            assert setter(pointer, 0) == 0
    elif method == 'native-crossing':
        crossing(Gdk.EventType.LEAVE_NOTIFY)
        button.released()
    elif method == 'native-signals':
        # Release outside the button so the display-only demonstration does
        # not activate it; the following physical click proves cleanup.
        button.leave()
        button.released()
    else:
        button.set_state(Gtk.StateType.NORMAL)
    settle()
    restored = snapshot(button)
    flags_restored = input_flags(pointer) if bridge_method else None
    cleaned_hover = []
    if sticky_method:
        for args in (['mousemove', '--window', xid, '120', '65'],
                     ['mousemove', '700', '500']):
            subprocess.run(['xdotool', *args], check=True, timeout=5)
            settle()
            cleaned_hover.append(snapshot(button))
    xid = subprocess.check_output(['xdotool', 'search', '--name',
        '^T04 private GTK2 pressed-state investigation$'], text=True, timeout=5).strip()
    assert xid.isdecimal(), 'Expected exactly one private preview window'
    allocation = button.get_allocation()
    subprocess.run(['xdotool', 'mousemove', '--window', xid,
                    str(allocation.x + 80), str(allocation.y + 25), 'mousedown', '1'],
                   check=True, timeout=5)
    try:
        settle()
        held = snapshot(button)
    finally:
        subprocess.run(['xdotool', 'mouseup', '1'], check=True, timeout=5)
    settle()
    released_clicks = len(clicks)
    destroyed_demo = None
    if sticky_method:
        destruction_calls = []
        if method == 'project-bridge':
            set_visual = project_bridge.bind(button)
        def destruction_setter(enabled):
            destruction_calls.append(enabled)
            set_visual(enabled)
        dying_demo = PressedButtonDemo(button, destruction_setter)
        button.destroy()
        settle()
        destroyed_demo = {'closed': dying_demo.closed,
                          'remaining_handlers': len(dying_demo.handlers),
                          'setter_calls': destruction_calls,
                          'activations_after_destroy': len(clicks)}
    result = {'status': 'observed', 'normal': normal, 'forced_active': forced,
              'private_child_displacement_px': displacement,
              'demonstration_method': method,
              'restored': restored, 'native_held': held,
              'forced_activations': forced_clicks, 'native_activations': released_clicks,
              'allocation_equal': forced['allocation'] == held['allocation'],
              'child_allocation_equal': forced['child_allocation'] == held['child_allocation'],
              'product_guard_changed': False, 'palette_changed': False,
              'historical_fidelity_claimed': False}
    if observe_hover:
        result['hover_observations'] = hover_observations
    if cleaned_hover:
        result['hover_after_disconnect'] = cleaned_hover
    if destroyed_demo is not None:
        result['native_destroy_cleanup'] = destroyed_demo
    if bridge_method:
        result['input_flags'] = [flags_before, flags_forced, flags_restored]
    output.write_text(json.dumps(result, indent=2) + '\n')
    window.destroy()
    # Retain measurements even when the investigated method is inadequate.
    assert forced_clicks == 0, 'Display-only state activated the button'
    assert forced['state'] == held['state'] == int(Gtk.StateType.ACTIVE)
    assert released_clicks == 1, 'Restored native press/release did not activate exactly once'
    if method == 'native-crossing' or bridge_method:
        assert result['allocation_equal'] and result['child_allocation_equal']
        assert restored == normal, 'Demonstration did not restore native geometry/state'
    if bridge_method:
        assert flags_before == flags_forced == flags_restored == 0
    assert all(x['activations'] == 0 for x in hover_observations)
    if sticky_method:
        assert len(hover_observations) == 2
        assert all(x['native'] == forced for x in hover_observations)
        assert [x['input_flags'] for x in hover_observations] == [1, 0]
        assert [x['state'] for x in cleaned_hover] == [
            int(Gtk.StateType.PRELIGHT), int(Gtk.StateType.NORMAL)]
        assert all(x['child_allocation'] == normal['child_allocation']
                   for x in cleaned_hover)
        assert destroyed_demo == {'closed': True, 'remaining_handlers': 0,
                                 'setter_calls': [True],
                                 'activations_after_destroy': 1}


if __name__ == '__main__':
    main()
