# SPDX-License-Identifier: GPL-3.0-or-later
"""Private Theme Lab route to the real Plasma Components/KSvg renderer."""
from pathlib import Path
import os
import backend
from plasma_recipe import generate as generate_snapshot, verify as verify_snapshot
from scene_contract import scene


def records(model):
    return scene(model, 'plasma')


def generate(root, folder, model, source_digest, kdeglobals):
    snapshot = backend.private_output(Path(folder) / 'plasma-snapshot', root)
    project_file = snapshot / 'PROJECT.json'
    backend.write_json(project_file, model)
    saved, saved_digest = backend.project(project_file)
    receipt = generate_snapshot(root, snapshot, saved, saved_digest, kdeglobals)
    return dict(receipt, snapshot=str(snapshot), project_path=str(project_file),
                source_project_sha256=source_digest, preview_project_sha256=saved_digest,
                project=saved)


def verify(root, receipt, model):
    snapshot = backend.private_output(Path(receipt['snapshot']), root)
    saved, digest = backend.project(snapshot / 'PROJECT.json')
    if (saved != receipt.get('project') or saved != model or
            digest != receipt.get('preview_project_sha256')):
        raise ValueError('Plasma preview scene identity mismatch')
    return verify_snapshot(root, receipt, model)


def environment(root, receipt, model):
    verified = verify(root, receipt, model)
    return {
        'XDG_CONFIG_HOME': verified['preview_config'],
        'XDG_DATA_HOME': verified['preview_data'],
        'XDG_CONFIG_DIRS': '/etc/xdg',
        'XDG_DATA_DIRS': '/usr/local/share:/usr/share',
        'XDG_CURRENT_DESKTOP': 'KDE',
        'KDE_SESSION_VERSION': '6',
    }


def command(root, receipt, model, project_file, *, output=None,
            embed_window=None, host_pid=None, host_bridge=None,
            host_session_root=None):
    verify(root, receipt, model)
    snapshot = Path(receipt['snapshot'])
    output = backend.private_output(output or snapshot / 'native-preview', root)
    command = ['/usr/bin/python3', '-B', str(root / 'plasma/tests/galerias-nativas/plasma_style_demo.py'),
               '--snapshot', str(snapshot / 'PLASMA-RECIPE.json'),
               '--project', str(project_file), '--output', str(output)]
    test_close = os.environ.get('THEMELAB_PLASMA_TEST_CLOSE_MS')
    if test_close is not None:
        try:
            milliseconds = int(test_close)
        except ValueError as error:
            raise ValueError('Invalid private Plasma test close interval') from error
        if not 500 <= milliseconds <= 60000:
            raise ValueError('Private Plasma test close interval is out of range')
        command += ['--test-close-ms', str(milliseconds)]
    from direct_preview_route import append_host_arguments
    return append_host_arguments(command, embed_window=embed_window,
        host_pid=host_pid, host_bridge=host_bridge,
        host_session_root=host_session_root)
