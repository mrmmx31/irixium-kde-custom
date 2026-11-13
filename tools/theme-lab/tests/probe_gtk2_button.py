#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned-display real GTK2 push-button press/release and sensitivity fixture."""
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
args = parser.parse_args()
import gi
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk, GObject
Gtk.init([]); Gtk.rc_parse(str(args.rc))
window = Gtk.Window(); window.set_default_size(300, 120)
window.set_title('I167 button fixture ' + str(os.getpid()))
fixed = Gtk.Fixed(); window.add(fixed)
button = Gtk.Button(label='Pressione'); button.set_name('themeLabPush')
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
    capture('pressed')
finally: x('mouseup', 1)
drain(); assert len(clicks) == 1
x('mousemove', ox + 250, oy + 90); button.set_can_focus(False); capture('released')
button.set_sensitive(False); capture('disabled')
x('mousemove', ox + 80, oy + 45, 'click', 1); drain(); assert len(clicks) == 1
# Recreate the widget instead of renaming it after realization. GTK2 keeps the
# original child-label RC style when only the parent name changes, which made
# the backdrop capture lie about the label foreground.
button.destroy()
button = Gtk.Button(label='Pressione')
button.set_name('themeLabBackdropPush')
button.set_can_focus(False)
button.set_size_request(180, 50)
fixed.put(button, 25, 25)
button.show_all(); drain()
x('mousemove', ox + 250, oy + 90); capture('backdrop')
properties = {}
for key in ('inner-border', 'focus-line-width', 'focus-padding'):
    spec = button.find_style_property(key); value = GObject.Value(); value.init(spec.value_type)
    button.style_get_property(key, value); item = value.get_value()
    properties[key] = [item.left, item.right, item.top, item.bottom] if key == 'inner-border' else item
result = {'native_widget': button.__gtype__.name, 'allocation': [allocation.x, allocation.y, allocation.width, allocation.height],
          'natural_request': [natural.width, natural.height], 'style_properties': properties,
          'captures': captures, 'click_count': len(clicks), 'disabled_input_blocked': True}
window.destroy()
print(json.dumps(result))
