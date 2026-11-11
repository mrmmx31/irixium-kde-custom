#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Parse events emitted by real GTK2 scenes with the C controller protocol."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from test_gtk2_paint_native import ROOT


def run(fixtures, output, gestures=False):
    output.mkdir(parents=True, exist_ok=True)
    parser = ROOT / 'tools/theme-lab/build/preview-event-file-test'
    results = []
    for mode in ('coupled', 'separate'):
        target = output / mode
        target.mkdir(exist_ok=True)
        project = fixtures / 'DomainOS' / ('state0-' + mode) / 'PROJECT.json'
        command = ['xvfb-run', '-a', '/usr/bin/python3', '-B',
                   str(ROOT / 'tools/theme-lab/tests/probe_gtk2_scene.py'),
                   '--project', str(project), '--rc', str(fixtures / 'DomainOS/gtk2-scrollbars/gtkrc'),
                   '--output', str(target), '--gestures' if gestures else '--ipc']
        if mode == 'coupled': command.append('--embedded')
        child = subprocess.run(command, env=dict(os.environ, GTK_MODULES='', GTK2_RC_FILES='/dev/null',
                               I167_PRIVATE_PROBE='1'), text=True, capture_output=True, timeout=25)
        (target / 'native.json').write_text(child.stdout)
        (target / 'stderr.log').write_text(child.stderr)
        if child.returncode or child.stderr: raise RuntimeError(child.stderr or child.stdout)
        native = json.loads(child.stdout)
        hash_value = native['project_sha256']
        actions = set()
        events = []
        for file in sorted((target / 'events').glob('event-*.json')):
            payload = json.loads(file.read_text())
            actions.add(payload['action'])
            assert payload['family'] == 'gtk2' and payload['project_sha256'] == hash_value
            assert file.stat().st_mode & 0o777 == 0o600
            parsed = subprocess.run([str(parser), 'gtk2', hash_value, str(file)], capture_output=True, text=True)
            assert parsed.returncode == 0, (file, parsed.stdout, parsed.stderr)
            for family, hash_test in [('gtk3', hash_value), ('gtk2', 'f' * 64)]:
                rejected = subprocess.run([str(parser), family, hash_test, str(file)], capture_output=True)
                assert rejected.returncode == 1, (family, file)
            events.append({'payload': payload, 'parsed': json.loads(parsed.stdout)})
        assert actions == ({'select', 'move', 'native'} if gestures else {'select', 'move', 'native', 'metrics'}), actions
        move = next(row['payload'] for row in events if row['payload']['action'] == 'move')
        assert (move['x'], move['y']) == ((77, 81) if gestures else (83, 91))
        results.append({'mode': mode, 'gesture_results': native.get('gesture_results'), 'events': events, 'cross_family_and_stale_rejected': True})
    (output / 'results.json').write_text(json.dumps({'status': 'passed', 'rows': results,
        'scope': 'Native GTK2 input to C parser' if gestures else 'Native scene APIs to C parser; main application launch remains pending'}, indent=2))
    print(json.dumps({'status': 'passed', 'origins': len(results),
                      'native_events_parsed': sum(len(row['events']) for row in results)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--gestures', action='store_true')
    args = parser.parse_args()
    run(args.fixtures.resolve(), args.output.resolve(), args.gestures)
