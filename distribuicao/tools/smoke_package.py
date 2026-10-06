#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the distributed user installer with a temporary HOME. No real setup.

Only run archives produced and verified from this checkout; never run code from
an arbitrary uploaded ZIP. The temporary installation is NOT desktop acceptance.
"""
from __future__ import annotations
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
import build_kvantum as B


def run(repo: Path) -> dict:
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        return {'status': 'unavailable', 'reason': 'Run as an ordinary user; no elevation is performed.', 'checks': []}
    outputs, _ = B.build_plan(repo)
    name = f'IrixClassic-{B.SUPPORTED_VERSION}-codigo.zip'
    archive = outputs[name]
    B.verify_archive(archive)
    checks = []
    def check(name, value):
        checks.append({'test': name, 'passed': bool(value)})
        if not value:
            raise B.Failure('Ensaio de instalação falhou: ' + name)
    with tempfile.TemporaryDirectory(prefix='irix-package-smoke-') as tmp:
        folder = Path(tmp)
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            # Content was generated above from explicit allowlisted repository files.
            z.extractall(folder / 'source')
        source = folder / 'source' / f'IrixClassic-{B.SUPPORTED_VERSION}-codigo'
        home = folder / 'home'; home.mkdir()
        config = home / '.config'; state = home / '.local/state'
        chooser = config / 'Kvantum/kvantum.kvconfig'; chooser.parent.mkdir(parents=True)
        original = b'[General]\ntheme=ExampleTheme\n[Applications]\nExample=demo\n'
        chooser.write_bytes(original); chooser.chmod(0o640)
        target = config / 'Kvantum/IrixClassic'
        wanted = B.document((source / 'kvantum/IrixClassic/MANIFEST.json').read_bytes())['files']
        # No DBus/desktop connection is required by the installer; HOME and all
        # XDG writable roots belong to this temporary directory.
        env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config),
                   XDG_STATE_HOME=str(state), XDG_DATA_HOME=str(home/'.local/share'),
                   XDG_CACHE_HOME=str(home/'.cache'), PYTHONDONTWRITEBYTECODE='1')
        def invoke(*args):
            p = subprocess.run([sys.executable, '-B', str(source/'tools/install_kvantum_classic.py'), *args],
                               cwd=source, env=env, capture_output=True, text=True, timeout=30)
            if p.returncode:
                raise B.Failure('Instalador isolado retornou ' + str(p.returncode) + ': ' + p.stderr[-1000:].replace(tmp, '<temporario>'))
        invoke('--verificar')
        check('dry-run leaves theme absent and selection intact', not target.exists() and chooser.read_bytes() == original)
        invoke()
        check('installed files match distributed manifest', all(B.digest((target/n).read_bytes()) == h for n,h in wanted.items()))
        check('default install preserves selection and exceptions', chooser.read_bytes() == original)
        invoke('--restaurar')
        check('restore removes only introduced files', all(not (target/n).exists() for n in wanted))
        check('restore preserves chooser contents and permissions', chooser.read_bytes() == original and chooser.stat().st_mode & 0o777 == 0o640)
        invoke('--ativar')
        check('opt-in activation sets IrixClassic and keeps exceptions', b'theme=IrixClassic' in chooser.read_bytes() and b'Example=demo' in chooser.read_bytes())
        invoke('--restaurar')
        check('activation restore recovers exact chooser', chooser.read_bytes() == original and chooser.stat().st_mode & 0o777 == 0o640)
        # Recreate a user-owned local file, then require exact restoration.
        target.mkdir(parents=True, exist_ok=True)
        existing = target/'README.md'; previous = b'Local test document\n'
        existing.write_bytes(previous); existing.chmod(0o600)
        invoke(); invoke('--restaurar')
        check('existing local file and mode restored', existing.read_bytes() == previous and existing.stat().st_mode & 0o777 == 0o600)
    return {'status': 'passed', 'checks': checks, 'archive_sha256': B.digest(archive),
            'scope': 'Real user-level file installation in temporary HOME; no Qt application was loaded.'}


if __name__ == '__main__':
    try:
        result = run(B.REPO)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result['status'] == 'passed' else 77)
    except (B.Failure, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status':'failed', 'error':str(exc)}, ensure_ascii=False)); sys.exit(1)
