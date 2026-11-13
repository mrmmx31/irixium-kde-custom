#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Repeatable real GTK2 catalog mount test in an owned Xvfb display."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PROBE = ROOT / 'tools/theme-lab/tests/probe_gtk2_all_controls_native.py'

def main():
    supplied = os.environ.get('I167_ALL_CONTROLS_OUTPUT')
    temp_root = Path.home() / 'tempia' / 'domainos-theme-work'
    temp_root.mkdir(parents=True, exist_ok=True)
    xvfb_tmp = temp_root / 'xvfb-runtime'
    xvfb_tmp.mkdir(parents=True, exist_ok=True)
    temporary = None
    if supplied:
        output = Path(supplied).expanduser().resolve()
        if output == temp_root.resolve() or not output.is_relative_to(temp_root.resolve()):
            raise SystemExit('A saída de teste precisa ficar sob ~/tempia/domainos-theme-work/.')
        if output.exists() and any(output.iterdir()):
            raise SystemExit('A saída já contém arquivos; use um diretório exclusivo.')
        output.mkdir(parents=True, exist_ok=True)
        output.chmod(0o700)
    else:
        temporary = tempfile.TemporaryDirectory(prefix='qa-I167-all-controls-', dir=temp_root)
        output = Path(temporary.name)
    try:
        command = ['xvfb-run', '-a', 'env', 'I167_PRIVATE_ALL_CONTROLS=1',
                   'GTK_MODULES=', 'GTK2_RC_FILES=/dev/null', 'GDK_BACKEND=x11',
                   '/usr/bin/python3', '-B', str(PROBE), str(output)]
        child_env = dict(os.environ, TMPDIR=str(xvfb_tmp))
        subprocess.run(command, cwd=ROOT, check=True, timeout=120, env=child_env)
        result = json.loads((output / 'ALL-CONTROLS-RESULTADO.json').read_text(encoding='utf-8'))
        assert result['status'] == 'passed'
        assert result['control_count'] == 16 and len(result['controls']) == 16
        assert len(result['native_scenes']) == 8
        assert {row['scheme'] for row in result['native_scenes']} == {
            'DomainOS', 'BreezeLight', 'BreezeDark', 'TestYellow'}
        assert {row['origin'] for row in result['native_scenes']} == {'separate', 'coupled'}
        assert all(len(row['controls']) == 16 and row['all_mapped'] and row['within_viewport']
                   for row in result['native_scenes'])
        print(json.dumps({'status': 'passed', 'control_types': 16,
                          'schemes': 4, 'origins': 2, 'native_scenes': 8}))
    finally:
        if temporary is not None:
            temporary.cleanup()

if __name__ == '__main__':
    main()
