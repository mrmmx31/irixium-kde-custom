#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 IRIX Classic contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify functional SVG roles and render actual native Plasma components.

The historical prototype palette is an origin reference, not a functional
color expectation. The native test now checks Header/Window/View/Button and
Selection roles under current, dark, yellow and strongly differing schemes.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
STYLE = Path(__file__).resolve().parents[1]
ROOT = STYLE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/irix-domainos-style-verification'))
    args = parser.parse_args()
    optional_missing = []
    for module in ('PyQt6.QtQuick', 'PyQt6.QtWidgets', 'PyQt6.QtSvg', 'PyQt6.QtQml'):
        try:
            present = importlib.util.find_spec(module) is not None
        except ModuleNotFoundError:
            present = False
        if not present:
            optional_missing.append(module)
    if not shutil.which('dbus-run-session'):
        optional_missing.append('dbus-run-session')
    if optional_missing:
        parser.error('Optional native QA tools missing: '+', '.join(optional_missing)+
                     '. They are required only for this verifier, not for theme installation or use.')
    output = args.output.resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    resources = {str(path.relative_to(STYLE)):{'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                 for path in sorted(STYLE.rglob('*.svg'))}
    cases = {}
    with tempfile.TemporaryDirectory(prefix='.qa-style-verification-', dir=ROOT) as temporary:
        private = Path(temporary)
        env = dict(os.environ, DOMAINOS_NATIVE_STYLE_OUTPUT=str(private/'results'))
        try:
            result = subprocess.run([sys.executable, '-B', str(ROOT/'plasma/tests/test_domainos_native_style_palette.py')],
                                    env=env, capture_output=True, text=True, timeout=90)
            suite_pass = result.returncode == 0
            result_text = result.stdout+result.stderr
        except subprocess.TimeoutExpired:
            suite_pass = False
            result_text = 'Native style verification exceeded its external 90-second bound.'
        for path in sorted((private/'results').glob('*.json')):
            cases[path.stem] = json.loads(path.read_text())
        for path in sorted((private/'results').glob('*')):
            if path.suffix in {'.json', '.png'}:
                shutil.copyfile(path, output/path.name)
        missing_reference_report = private/'results/missing-reference/current_roles.json'
        fresh_comparison = json.loads(missing_reference_report.read_text()) if missing_reference_report.is_file() else {}
        if fresh_comparison:
            shutil.copyfile(missing_reference_report, output/'missing-reference.json')
    checks = {case+'/'+key:value for case, report in cases.items() for key, value in report['checks'].items()}
    checks['four_fresh_native_scheme_cases'] = set(cases) == {'current_roles', 'dark', 'yellow', 'strong_roles'}
    checks['structural_roles_ids_classic_and_native_suite_passed'] = suite_pass
    checks['missing_installed_reference_declared_skip'] = fresh_comparison.get('geometry_reference', {}).get('status') == 'skipped'
    report = {'pass':all(checks.values()), 'checks':checks, 'cases':cases, 'resources':resources,
              'scope':'Real installed KSvg, PlasmoidHeading and Plasma Controls in private offscreen XDG/D-Bus fixtures. FormFactor is a read-only private context; no applet configuration, audio, notifications, accounts or desktop actions are read or changed.',
              'limits':'Native stretch may interpolate checker cells. Existing installed artwork is an optional geometry comparison, explicitly skipped when unavailable; this render does not prove real notification delivery or existing-user cache invalidation.',
              'missing_reference_case':fresh_comparison,
              'desktop_modified':False, 'user_services_called':False,
              'suite_result':result_text}
    (output/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'pass':report['pass'], 'native_checks':len(checks), 'output':str(output)}, indent=2))
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
