# SPDX-License-Identifier: GPL-3.0-or-later
"""Isolated native GTK2 Entry painting and editing contract."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PROBE = ROOT / 'tools/theme-lab/tests/probe_gtk2_entry_paint.py'


def main():
    with tempfile.TemporaryDirectory(prefix='qa-I200-gtk2-entry-') as temporary:
        output = Path(temporary)
        command = [
            'xvfb-run', '-a', 'env', 'T04_PRIVATE_ENTRY=1', 'GTK_MODULES=',
            'GDK_BACKEND=x11', '/usr/bin/python3', '-B', str(PROBE), str(output),
        ]
        subprocess.run(command, cwd=ROOT, check=True, timeout=90)
        result = json.loads((output / 'RESULTADO.json').read_text(encoding='utf-8'))
        assert result['status'] == 'passed'
        assert len(result['rows']) == 24
        assert {row['scheme'] for row in result['rows']} == {
            'DomainOS', 'BreezeLight', 'BreezeDark', 'TestYellow'}
        keyboard = result['keyboard_editing']
        assert all(keyboard[name] for name in (
            'utf8_text', 'select_all', 'selection_replacement', 'copy_paste_cut',
            'undo_ctrl_z', 'redo_ctrl_y', 'redo_ctrl_shift_z'))
        assert {'undo', 'redo', 'gtk-cut', 'gtk-copy', 'gtk-paste', 'gtk-select-all'} <= \
            set(keyboard['native_popup_actions'])
        assert keyboard['replacement_undo_steps'] >= 1
        print(json.dumps({'status': 'passed', 'native_scenes': len(result['rows']),
                          'schemes': 4, 'keyboard_clipboard': True,
                          'popup_edit_actions': 6}, ensure_ascii=False))


if __name__ == '__main__':
    main()
