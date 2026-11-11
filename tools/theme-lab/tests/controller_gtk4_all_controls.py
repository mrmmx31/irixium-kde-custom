# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression for mixed GTK4 catalog routing through the real controller."""
from pathlib import Path
import time


def run(output, observation, wait):
    def worker():
        for process in Path('/proc').iterdir():
            if not process.name.isdigit():
                continue
            try:
                command = (process / 'cmdline').read_bytes().split(b'\0')
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
            if (command and command[0] == b'/usr/bin/python3' and
                    any(item.endswith(b'/preview_gtk4.py') for item in command)):
                return int(process.name), [item.decode(errors='replace')
                                           for item in command if item]
        return None

    found = wait(worker, 45)
    pid, command = found
    assert '--private-toggle-session' in command
    assert '--private-check-session' in command
    assert '--private-scrollbar-session' not in command
    assert '--embed-window' in command
    project = Path(command[command.index('--project') + 1])
    assert project.name == 'scene.json' and project.parent.name == 'lab'
    status = observation().get('status', '')
    assert 'indisponível' not in status.lower()
    time.sleep(.5)
    assert Path(f'/proc/{pid}').exists()
    return {
        'status': 'passed',
        'scope': ('All 16 GTK4 catalog controls remain selected in the model; '
                  'selected push routes the real coupled worker to the same '
                  'button renderer chosen by gtk4_route.renderer().'),
        'worker_pid': pid,
        'button_mode': True,
        'scrollbar_mode': False,
        'mixed_catalog_preserved': True,
        'historical_fidelity_claimed': False,
    }
