# SPDX-License-Identifier: GPL-3.0-or-later
"""Replay a real writer's obsolete identity after same-scene native restart."""
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys


def run(output, observation, click, wait, environment):
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / 'tools/theme-lab'))
    from preview_event_writer import EventWriter
    scene = output / 'home/lab/scene.json'; working = output / 'home/lab/working.json'
    events = output / 'home/lab/preview-events'
    wait(lambda: observation().get('native_push_allocation') == [220, 80], 90)

    def identity():
        matches = []
        for path in Path('/proc').iterdir():
            if not path.name.isdigit(): continue
            try:
                argv = (path / 'cmdline').read_bytes().split(b'\0')
                env = (path / 'environ').read_bytes().split(b'\0')
                if (path.stat().st_uid == os.getuid() and
                        b'/fixture/root/tools/theme-lab/preview_gtk.py' in argv and
                        b'--embed-window' in argv and
                        ('DISPLAY=' + environment['DISPLAY']).encode() in env and
                        b'TL_SPIN_PROBE=/home/domainos-test/probe.json' in env):
                    token = argv[argv.index(b'--preview-instance') + 1].decode() if b'--preview-instance' in argv else '0' * 32
                    matches.append((int(path.name), token))
            except (OSError, PermissionError): pass
        return matches[0] if len(matches) == 1 else None

    old = wait(identity, 10); applied = scene.read_bytes()
    click('apply')
    current = wait(lambda: (value if (value := identity()) and value[0] != old[0] else None), 30)
    wait(lambda: observation().get('native_push_allocation') == [220, 80], 30)
    assert scene.read_bytes() == applied, 'Unchanged Apply rewrote the scene'
    before = working.read_bytes()
    kwargs = {'instance_id': old[1]} if 'instance_id' in inspect.signature(EventWriter).parameters else {}
    writer = EventWriter(events, root, **kwargs)
    extra = {} if kwargs else {'preview_instance': old[1]}
    writer.emit('move', 0, hashlib.sha256(applied).hexdigest(), x=177, y=188,
                coordinate_space='gtk_logical_px', scale_factor=1, **extra)
    wait(lambda: not list(events.glob('event-*.json')), 10)
    assert scene.read_bytes() == applied and working.read_bytes() == before, \
        'Obsolete same-scene preview event changed current project/scene'
    assert old[1] != current[1], 'Restart reused the preview identity'
    return {'status': 'passed', 'scope': 'Native GTK3 same-scene regeneration; actual EventWriter replays obsolete instance move, file consumed without changing project/scene. No other action/origin/toolkit or historical fidelity claim.',
            'old_pid': old[0], 'new_pid': current[0], 'old_instance': old[1],
            'new_instance': current[1], 'scene_hash_unchanged': True}
