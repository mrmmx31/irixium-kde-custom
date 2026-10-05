#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Recoverable file updates. No desktop action is performed by this module."""
from __future__ import annotations
import base64
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Callable

class Failure(RuntimeError):
    pass

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def no_links(path: Path) -> None:
    if not path.is_absolute() or '..' in path.parts:
        raise Failure('Caminho absoluto e sem .. necessário: ' + str(path))
    for part in (path, *path.parents):
        if part.is_symlink():
            raise Failure('Link simbólico recusado: ' + str(part))

def atomic(path: Path, data: bytes, mode: int = 0o600) -> None:
    no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.irix-write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
        # Persist the rename, not just the file content.
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def image(data: bytes | None, mode: int = 0o644) -> dict:
    if data is None:
        return {'exists': False}
    return {'exists': True, 'mode': mode, 'sha256': sha(data),
            'base64': base64.b64encode(data).decode('ascii')}

def decode(snap: dict) -> bytes | None:
    if snap.get('exists') is False:
        if set(snap) != {'exists'}:
            raise Failure('Registro de arquivo ausente inválido.')
        return None
    if snap.get('exists') is not True or set(snap) != {'exists', 'mode', 'sha256', 'base64'}:
        raise Failure('Registro de arquivo inválido.')
    data = base64.b64decode(snap['base64'], validate=True)
    if len(data) > 8 * 1024 * 1024 or sha(data) != snap['sha256']:
        raise Failure('Conteúdo do backup divergente.')
    if type(snap['mode']) is not int or not 0 <= snap['mode'] <= 0o777:
        raise Failure('Permissão inválida no backup.')
    return data

def snapshot(path: Path) -> dict:
    no_links(path)
    if not path.exists():
        return image(None)
    if not path.is_file():
        raise Failure('O destino não é um arquivo regular: ' + str(path))
    if path.stat().st_size > 8 * 1024 * 1024:
        raise Failure('Arquivo inesperadamente grande: ' + str(path))
    return image(path.read_bytes(), stat.S_IMODE(path.stat().st_mode))

def replace_checked(path: Path, expected: dict, desired: dict) -> None:
    data = decode(desired)
    decode(expected)
    if snapshot(path) != expected:
        raise Failure('Destino modificado durante a operação: ' + str(path))
    if data is None:
        path.unlink(missing_ok=True)
    else:
        atomic(path, data, desired['mode'])
    if snapshot(path) != desired:
        raise Failure('Falha na conferência da escrita: ' + str(path))

@dataclass(frozen=True)
class Change:
    path: Path
    data: bytes
    phase: int = 0  # 0 theme files, 1 privileged files, 2 selection/preferences
    mode: int = 0o644
    expected: dict | None = None

class Transaction:
    """A private journal; crashes require explicit recovery, never blind retry.

    Not an atomic transaction with the compositor. Unknown subsequent edits
    block rollback rather than being overwritten. Empty created dirs may remain.
    """
    def __init__(self, state: Path, system_writer: Callable[[list[dict]], None],
                 allowed: Callable[[Path, int], bool],
                 writer: Callable = replace_checked):
        self.state, self.system_writer, self.allowed = state, system_writer, allowed
        self.writer = writer

    @contextmanager
    def locked(self):
        no_links(self.state)
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        lock = self.state / 'lock'
        no_links(lock)
        with lock.open('a+b') as stream:
            os.chmod(lock, 0o600)
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise Failure('Outra operação está em andamento.') from exc
            yield

    def latest(self) -> tuple[Path, dict] | None:
        pointer = self.state / 'latest'
        no_links(pointer)
        if not pointer.exists():
            return None
        token = pointer.read_text('ascii').strip()
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', token):
            raise Failure('Referência de backup inválida.')
        file = self.state / 'backups' / token / 'receipt.json'
        no_links(file)
        rec = json.loads(file.read_text('utf-8'))
        if rec.get('format') != 1 or not isinstance(rec.get('entries'), list):
            raise Failure('Recibo de backup inválido.')
        seen = set()
        for item in rec['entries']:
            path = Path(item['path']); phase = item['phase']
            if phase not in (0, 1, 2) or not self.allowed(path, phase) or path in seen:
                raise Failure('Destino do recibo não pertence a esta instalação.')
            seen.add(path)
            no_links(path)
            decode(item['before']); decode(item['after'])
        return file, rec

    def save(self, file: Path, rec: dict) -> None:
        atomic(file, (json.dumps(rec, ensure_ascii=False, indent=2) + '\n').encode())

    def assert_ready(self):
        prior = self.latest()
        if prior and prior[1]['status'] in ('prepared', 'restoring', 'recovery_needed'):
            raise Failure('Há atualização interrompida. Execute a restauração com --recuperar.')

    def plan(self, changes: list[Change]) -> list[dict]:
        self.assert_ready()
        result, seen = [], set()
        for change in sorted(changes, key=lambda c: (c.phase, str(c.path))):
            if change.path in seen or not self.allowed(change.path, change.phase):
                raise Failure('Destino duplicado ou fora do escopo: ' + str(change.path))
            seen.add(change.path)
            old = snapshot(change.path)
            if change.expected is not None and change.expected != old:
                raise Failure('Arquivo mudou desde a preparação: ' + str(change.path))
            new = image(change.data, change.mode)
            if old != new:
                result.append({'path': str(change.path), 'phase': change.phase,
                               'before': old, 'after': new})
        return result

    def install(self, changes: list[Change], dry: bool = False) -> Path | None:
        entries = self.plan(changes)
        print('Arquivos a atualizar:', len(entries))
        for item in entries:
            print('  ' + item['path'])
        if dry or not entries:
            print('Nenhum arquivo alterado.')
            return None
        base = self.state / 'backups'
        no_links(base)
        base.mkdir(mode=0o700, parents=True, exist_ok=True)
        token = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + os.urandom(6).hex()
        directory = base / token
        directory.mkdir(mode=0o700)
        file = directory / 'receipt.json'
        rec = {'format': 1, 'status': 'prepared', 'entries': entries}
        self.save(file, rec)
        # Both data copies and hashes exist BEFORE writing a target file.
        atomic(self.state / 'latest', (token + '\n').encode())
        try:
            for phase in (0, 1, 2):
                group = [e for e in entries if e['phase'] == phase]
                if phase == 1 and group:
                    self.system_writer(group)
                else:
                    for entry in group:
                        self.writer(Path(entry['path']), entry['before'], entry['after'])
                for entry in group:
                    if snapshot(Path(entry['path'])) != entry['after']:
                        raise Failure('Verificação final de fase falhou.')
            rec['status'] = 'installed'
            self.save(file, rec)
        except BaseException as exc:
            try:
                self._restore(file, rec, recovery=True)
            except BaseException as rollback:
                rec['status'] = 'recovery_needed'
                self.save(file, rec)
                raise Failure('Atualização incompleta; recuperação necessária. '
                              f'Erro: {exc}; restauração: {rollback}. Backup: {directory}') from exc
            raise Failure('Atualização cancelada/falhou; arquivos anteriores restaurados: ' + str(exc)) from exc
        print('Atualização concluída. Backup privado:', directory)
        return file

    def _restore(self, file: Path, rec: dict, recovery: bool, dry: bool = False):
        if rec['status'] not in ('installed', 'prepared', 'restoring', 'recovery_needed'):
            raise Failure('Este backup já foi restaurado.')
        if rec['status'] != 'installed' and not recovery:
            raise Failure('Use --recuperar para concluir a operação interrompida.')
        undo = []
        # Check ALL destinations before restoring ANY. No unrecognized overwrite.
        for entry in rec['entries']:
            path = Path(entry['path'])
            current = snapshot(path)
            if current != entry['after'] and current != entry['before']:
                raise Failure('Edição posterior detectada; preserve-a antes de restaurar: ' + str(path))
            if current != entry['before']:
                undo.append({'path': str(path), 'phase': entry['phase'],
                             'before': current, 'after': entry['before']})
        print('Arquivos a restaurar:', len(undo))
        if dry:
            print('Nenhum arquivo alterado.'); return
        rec['status'] = 'restoring'
        self.save(file, rec)
        try:
            for phase in (2, 1, 0):
                group = [e for e in undo if e['phase'] == phase]
                if phase == 1 and group:
                    self.system_writer(group)
                else:
                    for entry in reversed(group):
                        self.writer(Path(entry['path']), entry['before'], entry['after'])
                for entry in group:
                    if snapshot(Path(entry['path'])) != entry['after']:
                        raise Failure('Verificação da restauração falhou.')
            rec['status'] = 'restored'
            self.save(file, rec)
        except BaseException:
            rec['status'] = 'recovery_needed'
            self.save(file, rec)
            raise
        print('Cópias anteriores restauradas. Backups mantidos em:', file.parent)

    def restore(self, recovery: bool = False, dry: bool = False):
        previous = self.latest()
        if not previous:
            raise Failure('Nenhum backup registrado por este instalador.')
        self._restore(*previous, recovery, dry)


def edit_ini(data: bytes, group: str, values: dict[str, str]) -> bytes:
    """Preserve unrelated lines. Reject duplicate/immutable target groups/keys."""
    text = data.decode('utf-8')
    eol = '\r\n' if '\r\n' in text else '\n'
    lines = text.splitlines(keepends=True)
    starts = []
    for index, line in enumerate(lines):
        header = line.strip()
        if header == '[' + group + ']':
            starts.append(index)
        elif header.startswith('[' + group + ']'):
            raise Failure('Grupo KConfig com opções especiais; alteração recusada: ' + group)
    if len(starts) > 1:
        raise Failure('Grupo duplicado: ' + group)
    if not starts:
        if lines and not lines[-1].endswith(('\n', '\r')):
            lines[-1] += eol
        lines.extend([eol, '[' + group + ']' + eol])
        starts = [len(lines) - 1]
    start = starts[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].lstrip().startswith('[')), len(lines))
    seen = set()
    for index in range(start, end):
        line = lines[index].strip()
        if not line or line.startswith(('#', ';')) or '=' not in line:
            continue
        key = line.split('=', 1)[0].strip()
        base = key.split('[', 1)[0]
        if base not in values:
            continue
        if base in seen or key != base:
            raise Failure('Chave duplicada ou protegida: ' + key)
        seen.add(base)
        lines[index] = base + '=' + values[base] + eol
    if end and not lines[end - 1].endswith(('\n', '\r')):
        lines[end - 1] += eol
    lines[end:end] = [key + '=' + value + eol for key, value in values.items() if key not in seen]
    return ''.join(lines).encode('utf-8')
