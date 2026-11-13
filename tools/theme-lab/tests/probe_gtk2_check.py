#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned-display real GTK2 checkbox press/release and sensitivity fixture."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
assert os.environ.get('I167_PRIVATE_PROBE') == '1'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rc', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--toggle', action='store_true')
args = parser.parse_args()
import gi
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk, GObject
Gtk.init([]); Gtk.rc_parse(str(args.rc))
window = Gtk.Window(); window.set_default_size(300, 120); window.set_name('themeLabCanvasWindow')
window.set_title('I167 button fixture ' + str(os.getpid()))
fixed = Gtk.Fixed(); fixed.set_name('themeLabCanvas'); window.add(fixed)
button = (Gtk.CheckButton if args.toggle else Gtk.Button)(label='Pressione'); button.set_name('themeLabCheck' if args.toggle else 'themeLabPush')
fixed.put(button, 25, 25)
button.set_can_focus(False)  # This fixture isolates relief; focus is a separate gate.
button.ensure_style(); natural = Gtk.Requisition(); button.size_request(natural)
button.set_size_request(180, 50)
clicks = []
button.connect('clicked', lambda widget: clicks.append(True))
window.show_all()

def drain():
    end = time.monotonic() + .07
    while time.monotonic() < end:
        while Gtk.events_pending(): Gtk.main_iteration()
        time.sleep(.001)

def x(*args):
    child = subprocess.run(['xdotool', *map(str, args)], text=True,
                           capture_output=True, timeout=5)
    if child.returncode: raise RuntimeError(child.stderr or child.stdout)
    return child.stdout.strip()

drain()
wid = x('search', '--onlyvisible', '--pid', os.getpid())
origin = dict(line.split('=', 1) for line in x('getwindowgeometry', '--shell', wid).splitlines() if '=' in line)
ox, oy = int(origin['X']), int(origin['Y'])
allocation = button.get_allocation()
captures = {}
def capture(name):
    drain(); p = args.output / (name + '.png')
    subprocess.run(['import', '-window', wid, str(p)], check=True, timeout=5)
    captures[name] = str(p)

x('mousemove', ox + 250, oy + 90); capture('normal')
x('mousemove', ox + 80, oy + 45); capture('hover')
try:
    x('mousedown', 1); drain()
    assert not clicks
    if args.toggle: assert not button.get_active()
    capture('pressed')
finally: x('mouseup', 1)
drain(); assert len(clicks) == 1
if args.toggle:
    assert button.get_active(); capture('selected-hover')
x('mousemove', ox + 250, oy + 90); capture('selected' if args.toggle else 'released')
button.set_sensitive(False); capture('disabled-selected' if args.toggle else 'disabled')
x('mousemove', ox + 80, oy + 45, 'click', 1); drain(); assert len(clicks) == 1
if args.toggle:
    assert button.get_active()
    button.set_active(False); capture('disabled')
button.set_sensitive(True)
if args.toggle:
    button.set_active(True); x('mousemove', ox + 80, oy + 45)
    # set_active itself emits clicked in GTK2; count the native input delta
    # separately from the explicit state preparation above.
    before_second_click = len(clicks)
    try:
        x('mousedown',1); capture('selected-pressed'); assert button.get_active()
    finally: x('mouseup',1)
    drain(); assert not button.get_active() and len(clicks)==before_second_click+1
    x('mousemove', ox + 250, oy + 90); capture('released')
button.set_name('themeLabBackdropCheck' if args.toggle else 'themeLabBackdropPush')
x('mousemove', ox + 250, oy + 90); capture('backdrop')
if args.toggle:
    button.set_active(True); capture('backdrop-selected')
properties = {}
for key in ('indicator-size', 'indicator-spacing', 'interior-focus', 'focus-line-width', 'focus-padding'):
    spec = button.find_style_property(key); value = GObject.Value(); value.init(spec.value_type)
    button.style_get_property(key, value); item = value.get_value()
    properties[key] = item
result = {'native_widget': button.__gtype__.name, 'allocation': [allocation.x, allocation.y, allocation.width, allocation.height],
          'natural_request': [natural.width, natural.height], 'style_properties': properties,
          'captures': captures, 'click_count': len(clicks), 'native_release_clicks': 2,
          'disabled_input_blocked': True, 'border_width': button.get_border_width()}
window.destroy()
print(json.dumps(result))
