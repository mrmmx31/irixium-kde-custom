#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Irixium menu/minimize update. Does not write the v2 separator component."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

BUNDLE = Path(__file__).resolve().parent
BASE_COMMIT = '790fcbcb44c3ba05dbcc4114b473b9b875e30820'
EXPECTED_CLOSE_BLOB = 'a887833d039a897dd37c9bfebd8601c09ce9d565'
GROUP = 'org.kde.kdecoration2'
DESIRED = {'ButtonsOnLeft': 'M', 'ButtonsOnRight': 'IA'}

class Failure(RuntimeError):
    pass

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def normalized(data: bytes) -> bytes:
    return b'\n'.join(x.rstrip() for x in data.splitlines() if x.strip())

def atomic(path: Path, data: bytes, mode: int = 0o600) -> None:
    fd, name = tempfile.mkstemp(prefix='.irixium-v3-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)

def config(data: bytes, changes: dict[str, str | None] | None = None):
    """Read/edit only the chosen group; preserve all other bytes/lines."""
    text = data.decode('utf-8')
    lines = text.splitlines(keepends=True)
    eol = '\r\n' if '\r\n' in text else '\n'
    heads = [i for i, line in enumerate(lines) if line.strip().startswith('[' + GROUP + ']')]
    if len(heads) != 1 or lines[heads[0]].strip() != '[' + GROUP + ']':
        raise Failure('A configuração deve ter uma única seção [' + GROUP + '] sem flags de bloqueio.')
    start = heads[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].lstrip().startswith('[')), len(lines))
    values, positions = {}, {}
    for i in range(start, end):
        match = re.match(r'^\s*([^#;=]+?)\s*=\s*(.*?)\s*$', lines[i])
        if not match:
            continue
        key, value = match.groups()
        if key.split('[')[0] not in (*DESIRED, 'theme'):
            continue
        if '[' in key or key in values:
            raise Failure('Entrada duplicada, localizada ou bloqueada: ' + key)
        values[key], positions[key] = value, i
    if changes is None:
        return values
    missing = []
    for key, value in changes.items():
        if key in positions:
            lines[positions[key]] = '' if value is None else key + '=' + value + eol
        elif value is not None:
            missing.append(key + '=' + value + eol)
    if missing:
        if end > 0 and not lines[end - 1].endswith(('\n', '\r')):
            lines[end - 1] += eol
        lines[end:end] = missing
    return ''.join(lines).encode('utf-8')

def admin_copy(source: Path, target: Path) -> None:
    install = shutil.which('install')
    elev = shutil.which('pkexec') or shutil.which('sudo')
    if not elev or not install:
        raise Failure('É necessário install (coreutils) e pkexec ou sudo para copiar o QML.')
    result = subprocess.run([elev, install, '-m', '0644', '--', str(source), str(target)], check=False)
    if result.returncode:
        raise Failure(f'Cópia administrativa cancelada/falhou: código {result.returncode}.')

def qml_path(directory: str | None) -> Path:
    if directory:
        return Path(directory).expanduser().absolute() / 'MenuButton.qml'
    candidates = set()
    for pattern in ('/usr/lib/*/qt6/qml/org/kde/kwin/decoration/MenuButton.qml',
                    '/usr/lib/qt6/qml/org/kde/kwin/decoration/MenuButton.qml',
                    '/usr/lib64/qt6/qml/org/kde/kwin/decoration/MenuButton.qml'):
        candidates.update(Path(p) for p in glob.glob(pattern))
    if len(candidates) != 1:
        raise Failure('MenuButton.qml do Qt 6 não identificado. Use --qml-dir CAMINHO.')
    return next(iter(candidates))

class Installer:
    def __init__(self, qml: Path, theme: Path, kwin: Path, state: Path,
                 copy_system=admin_copy, bundle: Path = BUNDLE,
                 asset: Path = Path('/usr/share/kwin/aurorae/Irixium/applications.png')):
        self.qml, self.theme, self.kwin, self.state = qml, theme, kwin, state
        self.copy_system, self.bundle, self.asset = copy_system, bundle, asset

    def check(self):
        targets = {'menu': self.qml, 'minimize': self.theme / 'minimize.svg', 'kwinrc': self.kwin}
        for p in (*targets.values(), self.theme / 'close.svg'):
            if p.is_symlink() or not p.is_file():
                raise Failure(f'Arquivo ausente ou link simbólico (não alterado): {p}')
        if not self.asset.is_file():
            raise Failure(f'Imagem do menu ausente: {self.asset}. Instale primeiro o tema personalizado.')
        old = {name: p.read_bytes() for name, p in targets.items()}
        patched = (self.bundle / 'MenuButton.qml').read_bytes()
        known = [patched] + [p.read_bytes() for p in (self.bundle / 'upstream').glob('MenuButton*.qml')]
        if normalized(old['menu']) not in {normalized(x) for x in known}:
            raise Failure('MenuButton.qml difere das bases analisadas. Não será sobrescrito. '
                          'Envie esse arquivo para adaptação; não force a instalação.')
        artwork = (self.theme / 'close.svg').read_bytes()
        if git_blob(artwork) != EXPECTED_CLOSE_BLOB:
            raise Failure('O close.svg local difere do pequeno quadrado analisado. Nenhuma alteração. '
                          'É preciso conferir esse desenho antes de reutilizá-lo como minimizar.')
        ids = {e.get('id') for e in ET.fromstring(artwork).iter()}
        if not {'active-center', 'inactive-center', 'hover-center', 'pressed-center'} <= ids:
            raise Failure('SVG sem os estados esperados.')
        values = config(old['kwinrc'])
        if values.get('theme') != '__aurorae__svg__Irixium':
            raise Failure('Selecione a decoração Irixium no KDE antes de instalar este complemento.')
        for p in (self.theme, self.kwin.parent):
            if not os.access(p, os.W_OK):
                raise Failure(f'Diretório sem permissão de escrita: {p}')
        new = {'menu': patched, 'minimize': artwork, 'kwinrc': config(old['kwinrc'], DESIRED)}
        print('MenuButton.qml: base conhecida; símbolo pequeno: confirmado.')
        print('Disposição: M à esquerda; IA à direita. Divisórias e Irixiumrc: não serão escritos.')
        return targets, old, new, values

    def install(self, dry=False):
        paths, old, new, old_values = self.check()
        changed = [key for key in paths if old[key] != new[key]]
        for key in changed:
            print('Atualizar:', paths[key])
        if dry:
            print('Verificação concluída; nenhum arquivo ou backup criado.')
            return None
        if not changed:
            print('V3 já aplicada; nenhum novo backup criado.')
            return None
        backups = self.state / 'backups'
        backups.mkdir(parents=True, exist_ok=True, mode=0o700)
        folder = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-'), dir=backups))
        modes = {k: stat.S_IMODE(p.stat().st_mode) for k, p in paths.items()}
        manifest = {'format': 3, 'status': 'prepared', 'base_commit': BASE_COMMIT,
                    'paths': {k: str(p.absolute()) for k, p in paths.items()}, 'changed': changed,
                    'before': {k: sha(v) for k, v in old.items()},
                    'after': {k: sha(v) for k, v in new.items()}, 'modes': modes,
                    'old_keys': {k: old_values.get(k) for k in DESIRED}}
        def save():
            atomic(folder / 'manifest.json', (json.dumps(manifest, indent=2) + '\n').encode())
        for key in paths:
            atomic(folder / (key + '.before'), old[key])
            atomic(folder / (key + '.after'), new[key])
        save()
        attempted = []
        try:
            if any(p.read_bytes() != old[k] for k, p in paths.items()):
                raise Failure('Um destino mudou durante a preparação. Execute novamente.')
            for key in changed:
                if paths[key].read_bytes() != old[key]:
                    raise Failure('Destino mudou: ' + str(paths[key]))
                attempted.append(key)
                if key == 'menu':
                    self.copy_system(folder / (key + '.after'), paths[key])
                else:
                    atomic(paths[key], new[key], modes[key])
                if paths[key].read_bytes() != new[key]:
                    raise Failure('Conferência da gravação falhou: ' + key)
            manifest['status'] = 'installed'
            save()
            atomic(self.state / 'latest', (str(folder) + '\n').encode())
        except Exception as exc:
            errors = []
            for key in reversed(attempted):
                try:
                    if paths[key].is_file() and paths[key].read_bytes() == old[key]:
                        continue
                    if key == 'menu':
                        self.copy_system(folder / (key + '.before'), paths[key])
                    else:
                        atomic(paths[key], old[key], modes[key])
                    if paths[key].read_bytes() != old[key]:
                        raise Failure('Backup não restaurado')
                except Exception as error:
                    errors.append(key + ': ' + str(error))
            manifest['status'] = 'recovery_needed' if errors else 'failed_rolled_back'
            manifest['error'] = str(exc)
            manifest['recovery_errors'] = errors
            save()
            raise Failure(f'Instalação interrompida: {exc}. Backup: {folder}. '
                          + ('RESTAURAÇÃO MANUAL: ' + '; '.join(errors) if errors else 'Alterações revertidas.')) from exc
        print('Backup:', folder)
        return folder

    def restore(self, backup=None, dry=False):
        if backup is None:
            pointer = self.state / 'latest'
            if not pointer.is_file():
                raise Failure('Nenhum backup da v3 registrado. Use --backup CAMINHO.')
            backup = Path(pointer.read_text().strip())
        folder = Path(backup).absolute()
        if not folder.resolve().is_relative_to((self.state / 'backups').resolve()):
            raise Failure('O backup deve estar dentro da pasta de backups desta instalação.')
        manifest = json.loads((folder / 'manifest.json').read_text())
        if manifest.get('format') != 3 or manifest.get('status') != 'installed':
            raise Failure('Backup não é uma instalação v3 concluída e ainda ativa.')
        paths = {'menu': self.qml, 'minimize': self.theme / 'minimize.svg', 'kwinrc': self.kwin}
        if manifest['paths'] != {k: str(p.absolute()) for k, p in paths.items()}:
            raise Failure('Os destinos atuais diferem dos registrados no backup.')
        old, current, restore_data = {}, {}, {}
        for key, p in paths.items():
            if p.is_symlink() or not p.is_file():
                raise Failure('Destino ausente ou link simbólico: ' + str(p))
            current[key] = p.read_bytes()
            old[key] = (folder / (key + '.before')).read_bytes()
            if sha(old[key]) != manifest['before'][key]:
                raise Failure('Backup alterado/corrompido: ' + key)
            if key not in manifest['changed']:
                continue
            if key == 'kwinrc':
                values = config(current[key])
                if any(values.get(k) != v for k, v in DESIRED.items()):
                    raise Failure('A disposição dos botões mudou depois da v3; revise antes de restaurar.')
                restore_data[key] = config(current[key], manifest['old_keys'])
            else:
                if sha(current[key]) != manifest['after'][key]:
                    raise Failure('Arquivo mudou depois da v3; não será sobrescrito: ' + str(p))
                restore_data[key] = old[key]
        if dry:
            print('Restauração verificada; nenhum arquivo alterado.')
            return
        # Save exact pre-restore data, including unrelated current KWin settings.
        for key, data in current.items():
            atomic(folder / (key + '.pre-restore'), data)
        attempted = []
        try:
            for key, data in restore_data.items():
                if paths[key].read_bytes() != current[key]:
                    raise Failure('Destino mudou durante a restauração: ' + key)
                attempted.append(key)
                if key == 'menu':
                    self.copy_system(folder / (key + '.before'), paths[key])
                else:
                    atomic(paths[key], data, manifest['modes'][key])
                if paths[key].read_bytes() != data:
                    raise Failure('Conferência da restauração falhou: ' + key)
        except Exception as exc:
            errors = []
            for key in reversed(attempted):
                try:
                    if paths[key].read_bytes() == current[key]:
                        continue
                    if key == 'menu':
                        self.copy_system(folder / (key + '.pre-restore'), paths[key])
                    else:
                        atomic(paths[key], current[key], manifest['modes'][key])
                    if paths[key].read_bytes() != current[key]:
                        raise Failure('Conferência falhou')
                except Exception as error:
                    errors.append(key + ': ' + str(error))
            if errors:
                manifest['status'] = 'recovery_needed'
                manifest['recovery_errors'] = errors
                atomic(folder / 'manifest.json', (json.dumps(manifest, indent=2) + '\n').encode())
            raise Failure(f'Restauração interrompida: {exc}. Backup: {folder}. ' + '; '.join(errors)) from exc
        manifest['status'] = 'restored'
        atomic(folder / 'manifest.json', (json.dumps(manifest, indent=2) + '\n').encode())
        print('Estado anterior à v3 restaurado. Configurações não relacionadas foram preservadas.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'restore'])
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--qml-dir')
    parser.add_argument('--theme-dir')
    parser.add_argument('--backup', type=Path)
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise Failure('Execute como usuário da sessão, sem sudo na frente do script.')
    home = Path.home()
    theme = Path(args.theme_dir).expanduser() if args.theme_dir else Path(os.environ.get('XDG_DATA_HOME', home / '.local/share')) / 'aurorae/themes/Irixium'
    kwin = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config')) / 'kwinrc'
    state = Path(os.environ.get('XDG_STATE_HOME', home / '.local/state')) / 'irixium-controles-v3'
    inst = Installer(qml_path(args.qml_dir), theme.absolute(), kwin.absolute(), state.absolute())
    if args.action == 'install':
        result = inst.install(dry=args.verificar)
        applied = result is not None
    else:
        inst.restore(backup=args.backup, dry=args.verificar)
        applied = not args.verificar
    if applied:
        # Request settings reload only. This neither replaces KWin nor closes windows.
        qdbus = shutil.which('qdbus6')
        if qdbus:
            try:
                subprocess.run([qdbus, 'org.kde.KWin', '/KWin', 'reconfigure'], timeout=10,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except (OSError, subprocess.TimeoutExpired):
                pass
        print('Salve o trabalho, encerre a sessão do KDE e entre novamente para carregar o QML.')

if __name__ == '__main__':
    try:
        main()
    except (Failure, OSError, ValueError, ET.ParseError) as exc:
        print('ERRO:', exc, file=sys.stderr)
        sys.exit(1)
