#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned-display real GTK2 radio group press/release and sensitivity fixture."""
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
window = Gtk.Window(); window.set_default_size(300, 180); window.set_name('themeLabCanvasWindow')
window.set_title('I167 button fixture ' + str(os.getpid()))
fixed = Gtk.Fixed(); fixed.set_name('themeLabCanvas'); window.add(fixed)
peer = Gtk.RadioButton.new_with_label_from_widget(None, 'Outra')
peer.set_name('themeLabRadio'); peer.set_can_focus(False); peer.set_size_request(180,50)
fixed.put(peer,25,85)
button = Gtk.RadioButton.new_with_label_from_widget(peer,'Pressione'); button.set_name('themeLabRadio')
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

group_checks=[]
def group(expected):
    pair=[bool(button.get_active()),bool(peer.get_active())]
    assert pair == expected and sum(pair)==1, pair
    group_checks.append(pair)

group([False,True])
x('mousemove', ox+250, oy+160); capture('normal')
x('mousemove', ox+80, oy+45); capture('hover')
try:
    x('mousedown',1); drain(); group([False,True]); assert not clicks
    capture('pressed')
finally: x('mouseup',1)
drain(); group([True,False]); assert len(clicks)==1
capture('selected-hover')
x('mousemove',ox+250,oy+160);capture('selected')
button.set_sensitive(False);capture('disabled-selected')
x('mousemove',ox+80,oy+45,'click',1);drain();group([True,False]);assert len(clicks)==1
peer.set_active(True);group([False,True]);x('mousemove',ox+250,oy+160);capture('disabled')
button.set_sensitive(True);button.set_active(True);group([True,False])
before_repeat=len(clicks)
x('mousemove',ox+80,oy+45)
try:
    x('mousedown',1);capture('selected-pressed');group([True,False])
finally:x('mouseup',1)
drain();group([True,False]);assert len(clicks)==before_repeat+1
# Select the other member by real input: no programmatic deactivation.
x('mousemove',ox+80,oy+105,'click',1);drain();group([False,True])
x('mousemove',ox+250,oy+160);capture('released')
button.set_name('themeLabBackdropRadio');capture('backdrop')
button.set_active(True);group([True,False]);capture('backdrop-selected')
properties = {}
for key in ('indicator-size', 'indicator-spacing', 'interior-focus', 'focus-line-width', 'focus-padding'):
    spec = button.find_style_property(key); value = GObject.Value(); value.init(spec.value_type)
    button.style_get_property(key, value); item = value.get_value()
    properties[key] = item
result = {'native_widget': button.__gtype__.name, 'allocation': [allocation.x, allocation.y, allocation.width, allocation.height],
          'natural_request': [natural.width, natural.height], 'style_properties': properties,
          'captures': captures, 'click_count': len(clicks), 'native_release_clicks': 3, 'group_exclusive_checks': group_checks, 'second_click_retains_selection': True,
          'disabled_input_blocked': True, 'border_width': button.get_border_width()}
window.destroy()
print(json.dumps(result))
