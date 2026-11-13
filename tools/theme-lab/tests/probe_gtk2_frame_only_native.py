#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Render a frame-only GTK2 scene in the caller's private Xvfb."""
import argparse
import json
import os
from pathlib import Path
import sys

if os.environ.get('I167_PRIVATE_PROBE') != '1':
    raise SystemExit('Use somente em Xvfb privado do teste I167.')

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project', type=Path, required=True)
parser.add_argument('--rc', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/theme-lab'))

import backend
from gtk2_session import NativeSession
from preview_event_writer import EventWriter

import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, Gdk

model, digest = backend.project(args.project)
if [row['id'] for row in __import__('native_scene_gtk2').scene_records(model)] != ['frame']:
    raise ValueError('A cena privada deveria conter apenas a moldura.')
Gtk.init([])
args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
writer = EventWriter(args.output / 'events', ROOT, family='gtk2', backend_api=backend)
session = NativeSession(backend, Gtk, Gdk, ROOT, args.rc, model, digest, writer,
                        sample_directory=None, capture_mode=True)
try:
    window = session.scene.window
    window.show_all()
    for _ in range(12):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        window.queue_draw()
    metrics = session.scene.metrics()
    pixbuf = window.get_pixbuf()
    if len(metrics) != 1 or metrics[0]['id'] != 'frame':
        raise ValueError('GTK2 não montou exclusivamente a moldura solicitada.')
    if pixbuf is None or pixbuf.get_width() < 1 or pixbuf.get_height() < 1:
        raise ValueError('GtkOffscreenWindow não produziu pixels da moldura.')
    image = args.output / 'gtk2-frame-only.png'
    if image.exists():
        raise ValueError('Captura já existe; não sobrescrever evidência.')
    pixbuf.savev(str(image), 'png', [], [])
    print(json.dumps({'status': 'passed', 'family': 'gtk2', 'controls': ['frame'],
                      'allocation': metrics[0]['allocation'],
                      'widget_source': 'native_gtk2', 'private_display': os.environ.get('DISPLAY'),
                      'capture': str(image)}, ensure_ascii=False))
finally:
    session.close()
