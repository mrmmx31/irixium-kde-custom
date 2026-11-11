# SPDX-License-Identifier: GPL-3.0-or-later
"""Real controller checks for mixed GTK2 button/range native previews."""
import json
import hashlib
import time
import sys
import os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from preview_event_writer import EventWriter


def run(output, observation, click, wait, move_separate, separate_visible):
    def buttons(width, height, both=False):
        rows = [row for row in observation().get('native_controls', []) if row['control'] == 0]
        if len(rows) != (2 if both else 1): return None
        if any((row['width'], row['height']) != (width, height) or
               row['font_kind'] != 1 or not row['font'] for row in rows): return None
        return rows
    wait(lambda: observation().get('window'))
    initial = wait(lambda: buttons(180, 50))
    click('separatePreview')
    both = wait(lambda: buttons(180, 50, True))
    move_separate()
    (output / 'home/reveal-spin').write_text('set-width 280')
    wait(lambda: observation().get('width_text') == '280')
    (output / 'home/reveal-spin').write_text('set-height 60')
    wait(lambda: observation().get('height_text') == '60')
    click('apply')
    changed = wait(lambda: buttons(280, 60, True))
    assert 'GTK2 acoplado' in observation().get('metrics', '')
    assert 'GTK2 separado' in observation().get('metrics', '')
    project = json.loads((output / 'home/lab/working.json').read_text())
    assert project['recipes']['gtk2']['sizes'][0] == [280, 60]
    assert project['recipes']['gtk3']['sizes'][0] == [220, 80]
    generation = json.loads((output / 'home/lab/generated/latest.json').read_text())
    folder = output / 'home' / generation['generation_dir'].removeprefix('/home/domainos-test/')
    result = json.loads((folder / 'RESULTADO.json').read_text())
    assert result['status'] == 'partially_generated'
    assert result['families']['gtk2']['translated_controls'] == ['push','toggle','scroll_h','scroll_v']
    assert not result['families']['gtk2']['recipe_applied']
    instances = {}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit(): continue
        try:
            argv = (path/'cmdline').read_bytes().split(b'\0')
            env = (path/'environ').read_bytes().split(b'\0')
            if (path.stat().st_uid == os.getuid() and
                    b'/fixture/root/tools/theme-lab/preview_gtk2.py' in argv and
                    b'TL_SPIN_PROBE=/home/domainos-test/probe.json' in env and
                    b'--preview-instance' in argv):
                # Match this owned test home through the mounted scene inode.
                inner_scene=Path('/proc')/path.name/'root/home/domainos-test/lab/scene.json'
                inside=inner_scene.stat(); outside=(output/'home/lab/scene.json').stat()
                if (inside.st_dev,inside.st_ino)!=(outside.st_dev,outside.st_ino): continue
                origin='coupled' if b'--embed-window' in argv else 'separate'
                assert origin not in instances
                instances[origin]=argv[argv.index(b'--preview-instance')+1].decode()
        except (OSError, PermissionError): pass
    assert set(instances)=={'coupled','separate'}
    writers={origin:EventWriter(output/'home/lab/preview-events', Path(__file__).resolve().parents[3],
                               family='gtk2',instance_id=instance) for origin,instance in instances.items()}

    scene_hash = hashlib.sha256((output/'home/lab/scene.json').read_bytes()).hexdigest()
    def queued_measure(origin, width, height):
        writer=writers[origin]
        before = set(writer.directory.glob('event-*.json'))
        writer.emit('metrics',0,scene_hash,width=width,height=height,
                    minimum_width=74,minimum_height=34,natural_width=74,natural_height=34,
                    scale_factor=1,origin=origin,coordinate_space='gtk_logical_px',
                    font_kind=1,font_description='Sans 13px',sensitive=True)
        paths = set(writer.directory.glob('event-*.json')) - before
        # The controller may consume the atomic event before this glob. A
        # successful emit guarantees publication; positive sentinel acceptance
        # below proves that it actually reached the current controller.
        wait(lambda: not any(p.exists() for p in paths),5)
        consumed = time.time_ns()
        wait(lambda:(output/'home/probe.json').stat().st_mtime_ns > consumed,5)
    # Synthetic IPC sentinel: prove this family/hash/payload is accepted while
    # its origin is enabled before checking rejection after closing it.
    queued_measure('separate',333,77)
    wait(lambda:any(row['separate'] and (row['width'],row['height'])==(333,77)
                    for row in observation().get('native_controls',[])),5)
    move_separate()
    click('separatePreview')
    wait(lambda: not observation().get('separate_preview_checked', True), 5)
    wait(lambda: not separate_visible(), 5)
    wait(lambda: not any(row['separate'] for row in observation().get('native_controls',[])), 5)
    queued_measure('separate',444,88)
    assert not any(row['separate'] for row in observation().get('native_controls',[])), 'Closed origin accepted queued metrics'
    queued_measure('coupled',281,61)
    wait(lambda:any(not row['separate'] and (row['width'],row['height'])==(281,61)
                    for row in observation().get('native_controls',[])),5)
    queued_measure('coupled',280,60)
    wait(lambda: any(row['control']==0 and not row['separate'] and
                    (row['width'],row['height'])==(280,60)
                    for row in observation().get('native_controls',[])), 5)
    click('separatePreview')
    reopened = wait(lambda:buttons(280,60,True))
    move_separate()
    click('separatePreview')
    wait(lambda:not separate_visible(),5)
    wait(lambda:not any(row['separate'] for row in observation().get('native_controls',[])),5)
    return {'status':'passed', 'scope':'Real Motif controller -> private GTK2 button/range generation and both previews',
            'initial':initial, 'both':both, 'after_apply':changed,
            'gtk3_recipe_preserved':True, 'partial_scope_explicit':True,
            'toggle_unchecked':True, 'separate_window_no_longer_visible':True,
            'coupled_preview_retained':True, 'closed_origin_metrics_cleared':True,
            'valid_ipc_accepted_before_close':True,'late_detached_metrics_rejected':True,
            'coupled_ipc_still_accepted':True,
            'reopened_native_origins':reopened,
            'synthetic_IPC_sentinels_not_native_dimensions':[333,77,444,88,281,61],
            'process_exit_not_claimed':True}
