#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import json
import os
from pathlib import Path
import subprocess
from test_gtk2_paint_native import ROOT

parser = argparse.ArgumentParser(description='GTK2 replacement/rollback on a private display')
parser.add_argument('--scenes', type=Path, required=True)
parser.add_argument('--generation', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
results = []
for mode in ('coupled', 'separate'):
    target = args.output.resolve() / mode
    target.mkdir(exist_ok=True)
    folder = args.generation.resolve() / 'DomainOS'
    folder.chmod(0o700)  # Only this freshly generated private test fixture.
    command = ['xvfb-run', '-a', '/usr/bin/python3', '-B',
               str(ROOT / 'tools/theme-lab/tests/probe_gtk2_session.py'),
               '--project', str(args.scenes.resolve() / 'DomainOS' / ('state0-' + mode) / 'PROJECT.json'),
               '--rc', str(folder / 'gtk2-scrollbars/gtkrc'), '--output', str(target)]
    if mode == 'coupled': command.append('--embedded')
    child = subprocess.run(command, env=dict(os.environ, GTK_MODULES='', GTK2_RC_FILES='/dev/null',
                           I167_PRIVATE_PROBE='1'), text=True, capture_output=True, timeout=25)
    (target / 'native.json').write_text(child.stdout)
    (target / 'stderr.log').write_text(child.stderr)
    if child.returncode or child.stderr: raise RuntimeError(child.stderr or child.stdout)
    results.append(json.loads(child.stdout))
(args.output / 'results.json').write_text(json.dumps({'status': 'passed', 'rows': results,
    'scope': 'Native session core only; main controller launch/reload remains pending'}, indent=2))
print(json.dumps({'status': 'passed', 'native_origins': len(results), 'replacements': 20}))
