# SPDX-License-Identifier: GPL-3.0-or-later
"""Verified route from a saved Theme Lab recipe to a real Kvantum preview."""
from pathlib import Path

import backend
from kvantum_recipe import generate as generate_snapshot, verify as verify_snapshot


def generate(root, folder, model, source_digest, kdeglobals):
    snapshot = backend.private_output(Path(folder) / 'kvantum-snapshot', root)
    project_file = snapshot / 'PROJECT.json'
    backend.write_json(project_file, model)
    saved, saved_digest = backend.project(project_file)
    receipt = generate_snapshot(root, snapshot, model, saved_digest, kdeglobals)
    routed = dict(receipt, snapshot=str(snapshot), project_path=str(project_file),
                  source_project_sha256=source_digest, preview_project_sha256=saved_digest,
                  project=saved)
    # The native gallery opens KVANTUM-RECIPE.json directly; make it the same
    # complete, verifiable receipt used by the backend and the preview route.
    backend.write_json(snapshot / 'KVANTUM-RECIPE.json', routed)
    return routed


def verify(root, receipt, model):
    snapshot = backend.private_output(Path(receipt['snapshot']), root)
    saved, digest = backend.project(snapshot / 'PROJECT.json')
    if saved != receipt.get('project') or saved != model or digest != receipt.get('preview_project_sha256'):
        raise ValueError('Kvantum preview scene identity mismatch')
    return verify_snapshot(root, receipt, model)


def environment(root, receipt, model):
    verified = verify(root, receipt, model)
    return {
        'XDG_CONFIG_HOME': verified['preview_config'],
        'XDG_DATA_HOME': verified['preview_data'],
        'XDG_CONFIG_DIRS': '/etc/xdg',
        'XDG_DATA_DIRS': '/usr/local/share:/usr/share',
        'QT_STYLE_OVERRIDE': 'kvantum',
        'QT_QPA_PLATFORMTHEME': 'kde',
        'XDG_CURRENT_DESKTOP': 'KDE',
        'KDE_SESSION_VERSION': '6',
    }


def command(root, receipt, model, project_file, *, output=None,
            embed_window=None, host_pid=None, host_bridge=None,
            host_session_root=None, test_close_ms=None):
    verify(root, receipt, model)
    snapshot = Path(receipt['snapshot'])
    command = ['/usr/bin/python3', '-B', str(root / 'plasma/tests/galerias-nativas/qt6_demo.py'),
            '--qt-major', '6', '--theme-lab-kvantum-root', str(root),
            '--theme-lab-kvantum-snapshot',
            str(snapshot / 'KVANTUM-RECIPE.json'), '--theme-lab-project', str(project_file),
            '--output', str(output or snapshot / 'qtwidgets-proof')]
    if test_close_ms is not None:
        if type(test_close_ms) is not int or not 1500 <= test_close_ms <= 120000:
            raise ValueError('Private Kvantum test close must be between 1500 and 120000 ms.')
        command += ['--theme-lab-test-close-ms', str(test_close_ms)]
    from direct_preview_route import append_host_arguments
    return append_host_arguments(command, embed_window=embed_window,
        host_pid=host_pid, host_bridge=host_bridge,
        host_session_root=host_session_root)
