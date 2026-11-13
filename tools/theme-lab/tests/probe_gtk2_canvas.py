#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Measure a real GTK2 Window/Plug canvas on an owned Xvfb display."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image

assert os.environ.get('I167_PRIVATE_PROBE') == '1'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project', type=Path, required=True)
parser.add_argument('--rc', type=Path, required=True)
parser.add_argument('--expected', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--embedded', action='store_true')
args = parser.parse_args()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk
from native_scene_gtk2 import ScrollbarScene

def drain():
    deadline = time.monotonic() + .12
    while time.monotonic() < deadline:
        while Gtk.events_pending(): Gtk.main_iteration()
        time.sleep(.002)

Gtk.init([])
Gtk.rc_parse(str(args.rc))
host = None
if args.embedded:
    host = Gtk.Window(); socket = Gtk.Socket(); host.add(socket); host.show_all(); drain()
    xid = socket.get_id()
else: xid = None
native = ScrollbarScene(Gtk, json.loads(args.project.read_text()), xid)
drain()
assert not args.embedded or native.window.get_embedded()
expected = json.loads(args.expected.read_text())
rows = []
for label, sensitive in (('normal', True), ('insensitive', False), ('restored', True)):
    native.window.set_sensitive(sensitive)
    native.window.queue_draw()
    drain()
    image = args.output / (label + '.png')
    subprocess.run(['import', '-window', 'root', str(image)], check=True, timeout=10)
    screen = Image.open(image).convert('RGB')
    color = tuple(expected['normal' if sensitive else 'insensitive'])
    pixels = list(screen.crop((2, 2, 10, 10)).getdata())
    assert pixels == [color] * 64, (label, color, sorted(set(pixels)))
    # GTK2 GIR cannot safely expose GtkStyle.bg[] in this runtime. The native
    # drawable pixels are the authoritative check, not that broken array binding.
    rows.append({'state': label, 'expected_rgb': list(color), 'matched_pixels': 64})
metrics = native.metrics()
native.window.destroy()
if host: host.destroy()
print(json.dumps({'status': 'passed', 'embedded': args.embedded, 'canvas': rows, 'metrics': metrics,
                  'scope': 'Canvas normal/insensitive/restore only; no historical fidelity claim'}))
