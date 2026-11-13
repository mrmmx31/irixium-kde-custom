#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Entry-point lifecycle fixture on its own Xvfb; namespace guard tested separately."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

assert os.environ.get('I167_PRIVATE_PROBE') == '1'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fixture', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--embedded', action='store_true')
args = parser.parse_args()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import preview_gtk2 as entry
from gtk2_generation import generate_scrollbar_snapshot
api = entry.backend
recipe = json.loads(args.fixture.read_text())['recipes']['gtk2']
recipe['geometry'].update(view_bar_gap_px=4, view_inset_px=2, control_padding_px=4, font_px=13)
model = {'schema_version': 2, 'kind': 'theme_lab_project', 'selected_family': 'gtk2',
         'color_scheme': '', 'recipes': {family: copy.deepcopy(recipe) for family in api.FAMILIES}}
target = api.private_output(args.output, api.ROOT)
project = target / 'PROJECT.json'
project.write_text(json.dumps(model))
model, _digest = api.project(project)
snapshot = api.private_output(target / 'snapshot', api.ROOT)
receipt = generate_scrollbar_snapshot(api, api.ROOT, snapshot, model,
                                     api.ROOT / 'colors/DomainOS-SR10.4.colors')
import gi
gi.require_version('Gtk', '2.0')
gi.require_version('Gdk', '2.0')
from gi.repository import Gtk, GLib
Gtk.init([])
host = None
arguments = ['--project', str(project), '--rc', receipt['rc'], '--events-dir', str(target / 'events')]
if args.embedded:
    host = Gtk.Window(); socket = Gtk.Socket(); host.add(socket); host.show_all()
    arguments += ['--embed-window', str(socket.get_id())]
captured = []
factory = entry.NativeSession
def capture(*values):
    session = factory(*values); captured.append(session); return session
failures, stages = [], []
window = []
def step(number):
    try:
        session = captured[0]
        if number == 0:
            window.append(session.scene.window)
            session.scene.widgets[10].get_adjustment().set_value(47)
            model['recipes']['gtk2']['positions'][10] = [72, 61]
            model['recipes']['gtk2']['sizes'][10] = [280, 15]
            project.write_text(json.dumps(model))
        elif number == 1:
            assert session.scene.window is window[0]
            assert session.scene.metrics()[0]['allocation'] == [72, 61, 280, 15]
            assert session.scene.widgets[10].get_adjustment().get_value() == 47
            stages.append('valid_change_applied')
            project.write_text('{ invalid json')
        elif number == 2:
            assert session.scene.metrics()[0]['allocation'] == [72, 61, 280, 15]
            assert 'preservada' in session.scene.window.get_title()
            stages.append('invalid_change_preserves_scene')
            model['recipes']['gtk2']['positions'][10] = [81, 65]
            project.write_text(json.dumps(model))
        else:
            assert session.scene.metrics()[0]['allocation'] == [81, 65, 280, 15]
            assert session.scene.window is window[0]
            assert session.scene.widgets[10].get_adjustment().get_value() == 47
            stages.append('subsequent_valid_change_recovers')
            session.scene.window.destroy()
    except Exception as error:
        failures.append(repr(error)); Gtk.main_quit()
    return False
for number in range(4): GLib.timeout_add(100 + number * 650, step, number)
# This patch is strictly fixture isolation, not evidence of bwrap compliance.
with patch.object(api, 'private_namespace', return_value={'fixture_only': True}), \
     patch.object(entry, 'NativeSession', side_effect=capture):
    result = entry.main(arguments)
if host: host.destroy()
assert result == 0 and not failures, failures
assert len(stages) == 3, stages
events = [json.loads(path.read_text()) for path in (target / 'events').glob('*.json')]
assert events and all(row['family'] == 'gtk2' for row in events)
print(json.dumps({'status': 'passed', 'stages': stages, 'embedded': args.embedded,
                  'event_count': len(events), 'namespace_guard_mocked_for_fixture': True}))
