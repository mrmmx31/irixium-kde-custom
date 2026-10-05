#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Integrate into a LOCAL checkout; never commit, push, or execute installers."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
BUNDLE = Path(__file__).resolve().parent
sys.path.insert(0, str(BUNDLE / 'tools'))
from layout import update_layout
from manage import Failure, atomic, no_links, verify_bundle, digest

FILES = ('aurorae/Irixium/Irixiumrc', 'update-irixium.sh')
HOOK = '''# IRIXIUM_MODERN_LAYOUT_BEGIN
# Keep the SVG theme and the scoped Aurorae layout patch installed together.
bash "$bundle_dir/moderno/geometria/instalar.sh"
# IRIXIUM_MODERN_LAYOUT_END
'''
GUARD = '''# IRIXIUM_MODERN_LAYOUT_USER_BEGIN
if [ "$(id -u)" -eq 0 ]; then
    printf '%s\\n' 'Execute como usuário normal, sem sudo; a autorização é solicitada quando necessária.' >&2
    exit 1
fi
# IRIXIUM_MODERN_LAYOUT_USER_END
'''


def patch_installer(data: bytes) -> bytes:
    text = data.decode('utf-8')
    if 'bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)' not in text:
        raise Failure('O instalador local não usa a variável bundle_dir esperada. Revise a integração manualmente.')
    if '# IRIXIUM_MODERN_LAYOUT_BEGIN' in text:
        if text.count(HOOK) != 1 or text.count(GUARD) != 1:
            raise Failure('O hook de geometria existente é diferente; não será sobrescrito.')
        return data
    if len(re.findall(r'^set -eu$', text, re.M)) != 1:
        raise Failure('Preâmbulo do instalador diferente da base analisada.')
    text = re.sub(r'^set -eu\n', lambda _: 'set -eu\n\n' + GUARD, text, count=1, flags=re.M)
    point = re.search(r'^printf[^\n]*Irixium customiza[^\n]*$', text, re.M)
    if point is None:
        raise Failure('Não foi encontrado o final esperado do instalador; adapte o hook manualmente.')
    text = text[:point.start()] + HOOK + '\n' + text[point.start():]
    return text.encode('utf-8')


def payload_files():
    manifest = json.loads((BUNDLE / 'MANIFEST.json').read_text())
    return sorted([*manifest['files'], 'MANIFEST.json'])


def plan(repo: Path):
    no_links(repo)
    for name in FILES:
        no_links(repo / name)
        if not (repo / name).is_file():
            raise Failure('Arquivo não encontrado: ' + name)
    old = {name: (repo / name).read_bytes() for name in FILES}
    new = {FILES[0]: update_layout(old[FILES[0]]), FILES[1]: patch_installer(old[FILES[1]])}
    target = repo / 'moderno/geometria'
    no_links(target)
    if target.exists():
        expected = set(payload_files())
        actual = {str(p.relative_to(target)) for p in target.rglob('*')
                  if p.is_file() and '__pycache__' not in p.relative_to(target).parts}
        if expected != actual:
            raise Failure('A pasta moderno/geometria existente tem outro conteúdo; preserve e revise antes de substituir.')
        for rel in expected:
            no_links(target / rel)
            if (target / rel).read_bytes() != (BUNDLE / rel).read_bytes():
                raise Failure('A pasta moderno/geometria existente foi modificada: ' + rel)
    return old, new, target


def git(repo: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                          text=True, check=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--verificar', action='store_true')
    args = parser.parse_args()
    verify_bundle(BUNDLE)
    repo = args.repo.expanduser().absolute()
    if Path(git(repo, 'rev-parse', '--show-toplevel')).resolve() != repo.resolve():
        raise Failure('Informe a raiz do checkout Git.')
    old, new, target = plan(repo)
    changes = [name for name in FILES if old[name] != new[name]]
    for name in changes:
        print('Atualizar no checkout:', name)
    print('Pacote local:', target, '(já presente)' if target.exists() else '(será adicionado)')
    print('Não serão alterados SVGs, MenuButton.qml, fontes, GTK ou IRIX Classic.')
    if args.verificar or (not changes and target.exists()):
        print('Nenhum arquivo alterado.')
        return
    storage = Path(git(repo, 'rev-parse', '--absolute-git-dir')) / 'irixium-geometria-backups'
    no_links(storage)
    storage.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-'), dir=storage))
    modes = {name: stat.S_IMODE((repo / name).stat().st_mode) for name in changes}
    for name in changes:
        file = backup / name
        file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        atomic(file, old[name])
    atomic(backup / 'receipt.json', json.dumps({'paths': changes,
           'before': {k: digest(old[k]) for k in changes}, 'new_directory': not target.exists()}, indent=2).encode())
    done = []
    added = False
    try:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.layout-stage-', dir=target.parent) as tmp:
                staged = Path(tmp) / 'payload'
                for rel in payload_files():
                    out = staged / rel
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(BUNDLE / rel, out)
                os.replace(staged, target)
                added = True
        for name in changes:
            if (repo / name).read_bytes() != old[name]:
                raise Failure('Arquivo alterado durante a preparação: ' + name)
            atomic(repo / name, new[name], modes[name])
            done.append(name)
    except Exception:
        for name in reversed(done):
            atomic(repo / name, old[name], modes[name])
        if added:
            shutil.rmtree(target)
        raise
    print('Integração local concluída. Backup privado:', backup)
    print('Revise com git diff e git status. Não foram feitos commit, push ou instalação.')


if __name__ == '__main__':
    try:
        main()
    except (Failure, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print('ERRO:', exc, file=sys.stderr)
        raise SystemExit(1)
