#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Install a geometry-only update to the existing Irixium Aurorae decoration."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
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
from typing import Callable
from layout import update_layout

BUNDLE = Path(__file__).resolve().parent.parent
VERSION = '1.0.0-rc1'


class Failure(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized(data: bytes) -> bytes:
    return b'\n'.join(x.rstrip() for x in data.splitlines() if x.strip())


def no_links(path: Path) -> None:
    if not path.is_absolute():
        raise Failure('Use caminho absoluto: ' + str(path))
    for p in (path, *path.parents):
        if p.is_symlink():
            raise Failure('Link simbólico não aceito: ' + str(p))


def atomic(path: Path, data: bytes, mode: int = 0o600) -> None:
    no_links(path)
    fd, name = tempfile.mkstemp(prefix='.irixium-layout-', dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        temp.chmod(mode)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


# The elevated operation is a single validated, atomic file replacement. It
# compares the destination hash again AFTER authorization to avoid stale writes.
SYSTEM_COPY = r'''
import hashlib, os, pathlib, sys, tempfile
source, target, expected = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
if target.name != 'AuroraeButtonGroup.qml' or not target.is_absolute():
    raise SystemExit('Destino QML inválido.')
for p in (target, *target.parents):
    if p.is_symlink(): raise SystemExit('Link simbólico recusado.')
if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
    raise SystemExit('O QML mudou antes da cópia administrativa.')
data = source.read_bytes()
fd, tmp = tempfile.mkstemp(prefix='.irixium-layout-', dir=target.parent)
try:
    with os.fdopen(fd, 'wb') as out:
        out.write(data); out.flush(); os.fsync(out.fileno())
    os.chmod(tmp, 0o644)
    os.replace(tmp, target)
finally:
    if os.path.exists(tmp): os.unlink(tmp)
'''


def privileged_copy(data: bytes, target: Path, expected: bytes) -> None:
    launcher = shutil.which('pkexec') or shutil.which('sudo')
    python = shutil.which('python3')
    if not launcher or not python:
        raise Failure('São necessários Python 3 e pkexec ou sudo para copiar o QML do sistema.')
    # This directory is private, not part of the package or a Git checkout.
    with tempfile.TemporaryDirectory(prefix='irixium-layout-copy-') as tmp:
        source = Path(tmp) / 'AuroraeButtonGroup.qml'
        source.write_bytes(data)
        result = subprocess.run([launcher, python, '-c', SYSTEM_COPY,
                                 str(source), str(target), digest(expected)], check=False)
    if result.returncode != 0:
        raise Failure('Cópia administrativa cancelada ou falhou; código ' + str(result.returncode))


def verify_bundle(bundle: Path) -> None:
    manifest = json.loads((bundle / 'MANIFEST.json').read_text('utf-8'))
    if manifest.get('version') != VERSION:
        raise Failure('Manifesto de outra revisão.')
    files = manifest.get('files', {})
    if not files or 'AuroraeButtonGroup.qml' not in files:
        raise Failure('Manifesto incompleto.')
    for rel, checksum in files.items():
        path = bundle / rel
        if Path(rel).is_absolute() or '..' in Path(rel).parts:
            raise Failure('Caminho inválido no manifesto.')
        no_links(path)
        if not path.is_file() or digest(path.read_bytes()) != checksum:
            raise Failure('Integridade divergente: ' + rel)


def discover_qml(explicit: str | None) -> Path:
    if explicit:
        target = Path(explicit).expanduser().absolute() / 'AuroraeButtonGroup.qml'
        no_links(target)
        if not target.is_file():
            raise Failure('Componente não encontrado: ' + str(target))
        if '/qt6/' not in str(target):
            raise Failure('O destino deve ser o módulo do Qt 6, não Qt 5.')
        return target
    matches = []
    for pattern in ('/usr/lib/*/qt6/qml/org/kde/kwin/decoration/AuroraeButtonGroup.qml',
                    '/usr/lib/qt6/qml/org/kde/kwin/decoration/AuroraeButtonGroup.qml',
                    '/usr/lib64/qt6/qml/org/kde/kwin/decoration/AuroraeButtonGroup.qml'):
        matches += [Path(x) for x in glob.glob(pattern)]
    matches = list(dict.fromkeys(matches))
    if len(matches) != 1:
        raise Failure('Não foi encontrado um único módulo Aurorae/Qt 6. '
                      'Informe --qml-dir com o diretório correto.')
    no_links(matches[0])
    return matches[0]


class Installer:
    def __init__(self, qml: Path, rc: Path, state: Path, bundle: Path = BUNDLE,
                 copy_system: Callable[[bytes, Path, bytes], None] = privileged_copy):
        self.qml, self.rc, self.state = qml, rc, state
        self.bundle, self.copy_system = bundle, copy_system

    def current(self):
        for p in (self.qml, self.rc, self.state):
            no_links(p)
        if not self.qml.is_file() or not self.rc.is_file():
            raise Failure('O Irixium moderno e o módulo Aurorae precisam estar instalados. '
                          'Este pacote é uma atualização de geometria, não o tema completo.')
        return {'qml': self.qml.read_bytes(), 'rc': self.rc.read_bytes()}

    def plan(self):
        old = self.current()
        known = {normalized(p.read_bytes()): p.stem for p in
                 (self.bundle / 'compatibilidade').glob('*.qml')}
        new_qml = (self.bundle / 'AuroraeButtonGroup.qml').read_bytes()
        known[normalized(new_qml)] = 'geometria moderna ' + VERSION
        if normalized(old['qml']) not in known:
            raise Failure('O AuroraeButtonGroup.qml instalado tem código não analisado. '
                          'Preserve-o para adaptar o patch; não force a substituição.')
        new = {'qml': new_qml, 'rc': update_layout(old['rc'])}
        print('Base reconhecida:', known[normalized(old['qml'])])
        print('QML:', self.qml)
        print('Configuração:', self.rc)
        print('Escopo: somente geometria do Irixium; seleção e IRIX Classic não são alteradas.')
        return old, new

    @contextmanager
    def locked(self):
        no_links(self.state)
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock = self.state / 'lock'
        no_links(lock)
        with lock.open('a+b') as stream:
            os.chmod(lock, 0o600)
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise Failure('Outra instalação/restauração está em execução.') from exc
            yield

    def latest(self):
        file = self.state / 'latest'
        no_links(file)
        if not file.is_file():
            return None
        token = file.read_text().strip()
        if not re.fullmatch(r'[0-9A-Za-z._-]+', token):
            raise Failure('Ponteiro de backup inválido.')
        path = self.state / 'backups' / token
        no_links(path / 'receipt.json')
        if not path.is_dir():
            raise Failure('Backup registrado não foi encontrado.')
        return path

    def save_receipt(self, backup: Path, receipt: dict):
        atomic(backup / 'receipt.json', (json.dumps(receipt, indent=2) + '\n').encode())

    def install(self, dry_run: bool = False):
        old, new = self.plan()
        prior = self.latest()
        if prior:
            status = json.loads((prior / 'receipt.json').read_text()).get('status')
            if status in ('prepared', 'recovery_needed'):
                raise Failure('Operação anterior incompleta. Execute restaurar.sh --recuperar.')
        changes = [key for key in old if old[key] != new[key]]
        print('Atualizar:', ', '.join(changes) if changes else 'nenhum arquivo; já aplicado')
        if dry_run or not changes:
            print('Nenhum arquivo alterado.')
            return None
        backups = self.state / 'backups'
        no_links(backups)
        backups.mkdir(exist_ok=True, mode=0o700, parents=True)
        backup = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-'), dir=backups))
        modes = {'rc': stat.S_IMODE(self.rc.stat().st_mode)}
        receipt = {'format': 1, 'version': VERSION, 'status': 'prepared', 'changes': changes,
                   'qml_path': str(self.qml), 'rc_path': str(self.rc), 'modes': modes,
                   'before': {k: digest(v) for k, v in old.items()},
                   'after': {k: digest(v) for k, v in new.items()},
                   'previous': prior.name if prior else None}
        for key in old:
            atomic(backup / (key + '.before'), old[key])
            atomic(backup / (key + '.after'), new[key])
        self.save_receipt(backup, receipt)
        atomic(self.state / 'latest', (backup.name + '\n').encode())
        try:
            if self.current() != old:
                raise Failure('Arquivos alterados durante a preparação.')
            if 'qml' in changes:
                self.copy_system(new['qml'], self.qml, old['qml'])
                if self.qml.read_bytes() != new['qml']:
                    raise Failure('A conferência do QML instalado falhou.')
            if 'rc' in changes:
                if self.rc.read_bytes() != old['rc']:
                    raise Failure('O Irixiumrc mudou antes da escrita.')
                atomic(self.rc, new['rc'], modes['rc'])
            receipt['status'] = 'installed'
            self.save_receipt(backup, receipt)
        except Exception as exc:
            try:
                self._restore(backup, receipt, recovery=True)
            except Exception as rollback:
                receipt['status'] = 'recovery_needed'
                self.save_receipt(backup, receipt)
                raise Failure(f'Instalação incompleta: {exc}. Recuperação pendente: {rollback}. Backup: {backup}') from exc
            raise Failure('Instalação interrompida e estado anterior recuperado: ' + str(exc)) from exc
        print('Atualização instalada. Backup:', backup)
        print('Salve o trabalho, encerre a sessão KDE e entre novamente. Nenhuma sessão foi reiniciada.')
        return backup

    def _restore(self, backup: Path, receipt: dict, recovery: bool, dry_run: bool = False):
        if receipt.get('format') != 1 or receipt.get('version') != VERSION:
            raise Failure('Recibo incompatível.')
        allowed = ('prepared', 'recovery_needed', 'installed') if recovery else ('installed',)
        if receipt.get('status') not in allowed:
            raise Failure('Status de backup não restaurável por esta operação.')
        if receipt.get('qml_path') != str(self.qml) or receipt.get('rc_path') != str(self.rc):
            raise Failure('Destinos diferentes dos registrados no backup.')
        old, new = {}, {}
        for key in ('qml', 'rc'):
            for suffix, output, field in (('before', old, 'before'), ('after', new, 'after')):
                file = backup / (key + '.' + suffix)
                no_links(file)
                data = file.read_bytes()
                if digest(data) != receipt[field][key]:
                    raise Failure('Backup corrompido: ' + file.name)
                output[key] = data
        current = self.current()
        for key in ('qml', 'rc'):
            if current[key] != new[key] and not (recovery and current[key] == old[key]):
                raise Failure('O arquivo ' + key + ' mudou após a instalação. '
                              'Restauração recusada para preservar a edição ou a atualização do KDE.')
        print('Restaurar cópia anterior:', backup)
        if dry_run:
            print('Nenhum arquivo alterado.')
            return
        # Keep the receipt recoverable until both copies have been restored.
        receipt['status'] = 'recovery_needed'
        self.save_receipt(backup, receipt)
        if current['qml'] != old['qml']:
            self.copy_system(old['qml'], self.qml, current['qml'])
            if self.qml.read_bytes() != old['qml']:
                raise Failure('O QML restaurado não passou na conferência.')
        if current['rc'] != old['rc']:
            if self.rc.read_bytes() != current['rc']:
                raise Failure('Configuração mudou durante a restauração.')
            atomic(self.rc, old['rc'], receipt['modes']['rc'])
        receipt['status'] = 'restored'
        self.save_receipt(backup, receipt)
        previous = receipt.get('previous')
        if previous:
            if not re.fullmatch(r'[0-9A-Za-z._-]+', previous):
                raise Failure('Ponteiro anterior inválido.')
            atomic(self.state / 'latest', (previous + '\n').encode())
        else:
            (self.state / 'latest').unlink(missing_ok=True)
        print('Cópia anterior restaurada. Encerre a sessão KDE e entre novamente.')

    def restore(self, recovery: bool = False, dry_run: bool = False):
        backup = self.latest()
        if backup is None:
            raise Failure('Nenhum backup registrado por este pacote.')
        receipt = json.loads((backup / 'receipt.json').read_text())
        self._restore(backup, receipt, recovery, dry_run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'restore'))
    parser.add_argument('--verificar', action='store_true')
    parser.add_argument('--recuperar', action='store_true', help='recuperar uma operação interrompida')
    parser.add_argument('--qml-dir', help='diretório do módulo Aurorae do Qt 6')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise Failure('Execute como usuário normal, sem sudo. Só a cópia QML solicita autorização.')
    if args.recuperar and args.action != 'restore':
        raise Failure('--recuperar só se aplica à restauração.')
    verify_bundle(BUNDLE)
    data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))).expanduser()
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))).expanduser()
    no_links(data)
    no_links(state)
    installer = Installer(discover_qml(args.qml_dir), data / 'aurorae/themes/Irixium/Irixiumrc',
                          state / 'irixium-moderno-geometria')
    def run():
        if args.action == 'install':
            installer.install(args.verificar)
        else:
            installer.restore(args.recuperar, args.verificar)
    if args.verificar:
        run()
    else:
        with installer.locked():
            run()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Failure, OSError, ValueError, KeyError, TypeError) as exc:
        print('ERRO:', exc, file=sys.stderr)
        raise SystemExit(1)
