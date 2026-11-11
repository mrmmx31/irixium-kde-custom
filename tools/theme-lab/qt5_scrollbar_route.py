# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded routing for the partial Qt5 Widgets recipe."""
from pathlib import Path

import backend
from scene_contract import scene
from qt5_scrollbar_recipe import generate as generate_snapshot, verify as verify_snapshot


def records(model):
    rows = scene(model, 'qt5')
    invalid = [row['id'] for row in rows if row['id'] not in ('push', 'toggle', 'check', 'radio', 'entry', 'text', 'combo', 'spin', 'scale_h', 'scale_v', 'arrow', 'progress', 'list', 'frame', 'scroll_h', 'scroll_v')]
    if invalid or not rows:
        raise ValueError('Qt5 partial adapter accepts visible push/toggle/check/radio/entry/text/combo/spin/scale_h/scale_v/arrow/progress/list/frame/scroll_h/scroll_v controls')
    return rows


def generate(root, folder, model, source_digest, kdeglobals):
    records(model)
    snapshot = backend.private_output(folder / 'qt5-scrollbar-snapshot', root)
    backend.write_json(snapshot / 'PROJECT.json', model)
    saved_digest = backend.sha(backend.read_file(snapshot / 'PROJECT.json'))
    receipt = generate_snapshot(root, snapshot, model, saved_digest, kdeglobals)
    return dict(receipt, snapshot=str(snapshot), source_project_sha256=source_digest,
                preview_project_sha256=saved_digest)


def verify(root, receipt, model):
    records(model)
    snapshot = Path(receipt['snapshot'])
    saved, digest = backend.project(snapshot / 'PROJECT.json')
    if saved != model or digest != receipt.get('preview_project_sha256'):
        raise ValueError('Qt5 preview scene identity mismatch')
    return verify_snapshot(root, receipt, model)


def command(root, receipt, model, test_close_ms=None, *, embed_window=None,
            host_pid=None, host_bridge=None, host_session_root=None):
    verify(root, receipt, model)
    snapshot = Path(receipt['snapshot'])
    command = ['/usr/bin/python3', '-B', str(root / 'plasma/tests/galerias-nativas/qt5_demo.py'),
               '--theme-lab-qt5-scrollbar-snapshot', str(snapshot),
               '--theme-lab-project', str(snapshot / 'PROJECT.json')]
    if test_close_ms is not None:
        if type(test_close_ms) is not int or not 1500 <= test_close_ms <= 120000:
            raise ValueError('Private Qt5 test close must be between 1500 and 120000 ms.')
        command += ['--theme-lab-test-close-ms', str(test_close_ms)]
    from direct_preview_route import append_host_arguments
    return append_host_arguments(command, embed_window=embed_window,
        host_pid=host_pid, host_bridge=host_bridge,
        host_session_root=host_session_root)
