#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Update four files in a LOCAL checkout. Never commit, push, or run an installer."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from controles import BUNDLE, EXPECTED_CLOSE_BLOB, DESIRED, Failure, atomic, config, git_blob, normalized

FILES = ('MenuButton.qml', 'aurorae/Irixium/minimize.svg', 'kwin-decoration.conf', 'update-irixium.sh')

def plan(repo: Path):
    for name in (*FILES, 'aurorae/Irixium/close.svg'):
        p = repo / name
        if not p.is_file() or p.is_symlink():
            raise Failure('Arquivo ausente ou link simbólico: ' + str(p))
    old = {name: (repo / name).read_bytes() for name in FILES}
    known = [p.read_bytes() for p in (BUNDLE / 'upstream').glob('MenuButton*.qml')]
    known.append((BUNDLE / 'MenuButton.qml').read_bytes())
    if normalized(old['MenuButton.qml']) not in {normalized(x) for x in known}:
        raise Failure('MenuButton.qml do checkout tem mudanças não analisadas.')
    close = (repo / 'aurorae/Irixium/close.svg').read_bytes()
    if git_blob(close) != EXPECTED_CLOSE_BLOB:
        raise Failure('close.svg do checkout não é o pequeno quadrado analisado.')
    script = old['update-irixium.sh'].decode()
    pattern = r'(--key\s+ButtonsOnRight\s+)HXA(?=\s|$)'
    script, count = re.subn(pattern, r'\g<1>IA', script)
    if count != 1 and not (count == 0 and re.search(r'--key\s+ButtonsOnRight\s+IA(?=\s|$)', script)):
        raise Failure('Não foi localizada uma única definição HXA/IA no instalador do repositório.')
    new = {'MenuButton.qml': (BUNDLE / 'MenuButton.qml').read_bytes(),
           'aurorae/Irixium/minimize.svg': close,
           'kwin-decoration.conf': config(old['kwin-decoration.conf'], DESIRED),
           'update-irixium.sh': script.encode()}
    return old, new

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--verificar', action='store_true')
    args = parser.parse_args()
    repo = args.repo.expanduser().resolve()
    result = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True, check=True)
    if Path(result.stdout.strip()).resolve() != repo:
        raise Failure('Informe a raiz do checkout Git.')
    result = subprocess.run(['git', '-C', str(repo), 'diff', 'HEAD', '--name-only', '--', *FILES],
                            capture_output=True, text=True, check=True)
    if result.stdout.strip():
        raise Failure('Há mudanças locais nesses arquivos. Revise e registre-as antes de integrar:\n' + result.stdout)
    old, new = plan(repo)
    changes = [name for name in FILES if new[name] != old[name]]
    for name in changes:
        print('Atualizar no checkout:', name)
    if args.verificar or not changes:
        print('Nenhum arquivo alterado.')
        return
    gitdir = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--absolute-git-dir'],
                            capture_output=True, text=True, check=True).stdout.strip()
    storage = Path(gitdir) / 'irixium-controles-v3-backups'
    storage.mkdir(exist_ok=True, mode=0o700)
    backup = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-'), dir=storage))
    modes = {name: stat.S_IMODE((repo / name).stat().st_mode) for name in changes}
    for name in changes:
        target = backup / name
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        atomic(target, old[name], modes[name])
    done = []
    try:
        for name in changes:
            if (repo / name).read_bytes() != old[name]:
                raise Failure('Arquivo mudou durante a preparação: ' + name)
            atomic(repo / name, new[name], modes[name])
            done.append(name)
    except Exception:
        for name in reversed(done):
            atomic(repo / name, old[name], modes[name])
        raise
    print('Backup local:', backup)
    print('Integração concluída. Revise com git diff. Não foram feitos commit, push ou instalação.')
    print('O script update-irixium.sh conserva suas outras ações, inclusive fontes e cópia do tema completo.')

if __name__ == '__main__':
    try:
        main()
    except (Failure, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print('ERRO:', exc, file=sys.stderr)
        sys.exit(1)
