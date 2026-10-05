#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Privileged helper: only three kinds of existing theme resources are writable."""
from __future__ import annotations
import fcntl
import json
import os
from pathlib import Path
import re
import sys
from theme_transaction import Failure, no_links, snapshot, decode, replace_checked


def allowed(path: Path, phase: int = 1) -> bool:
    if phase != 1 or not path.is_absolute() or '..' in path.parts:
        return False
    text = str(path)
    if text == '/usr/share/kwin/aurorae/Irixium/applications.png':
        return True
    if text == '/usr/share/kwin/aurorae/AuroraeButtonGroup.qml':
        return True
    return re.fullmatch(r'/usr/(?:lib(?:64)?(?:/[A-Za-z0-9_-]+)?)/qt6/qml/org/kde/kwin/decoration/(?:MenuButton|AuroraeButtonGroup)\.qml', text) is not None


def apply(entries: list[dict], writer=replace_checked, validator=allowed):
    if not isinstance(entries, list) or len(entries) > 3:
        raise Failure('Lote administrativo inválido.')
    seen = set()
    for entry in entries:
        path = Path(entry['path'])
        if not validator(path) or path in seen or entry.get('phase') != 1:
            raise Failure('Destino administrativo não permitido.')
        seen.add(path)
        no_links(path)
        decode(entry['before']); decode(entry['after'])
        if entry['after'].get('exists') and entry['after']['mode'] not in (0o600, 0o644):
            raise Failure('Permissão administrativa não permitida.')
        if snapshot(path) != entry['before']:
            raise Failure('Destino mudou antes da autorização: ' + str(path))
    try:
        for entry in entries:
            writer(Path(entry['path']), entry['before'], entry['after'])
    except BaseException as exc:
        failures = []
        for entry in reversed(entries):
            path = Path(entry['path']); current = snapshot(path)
            try:
                if current == entry['after']:
                    writer(path, current, entry['before'])
                elif current != entry['before']:
                    raise Failure('Edição concorrente; recuperação manual necessária.')
            except BaseException as rollback:
                failures.append(str(rollback))
        raise Failure('Lote administrativo interrompido: ' + str(exc)
                      + ('; recuperação pendente: ' + '; '.join(failures) if failures else '; lote revertido.')) from exc


def main():
    if os.geteuid() != 0 or len(sys.argv) != 2:
        raise Failure('Este auxiliar é invocado somente pelo instalador autorizado.')
    job = Path(sys.argv[1]).absolute()
    no_links(job)
    if job.stat().st_size > 16 * 1024 * 1024:
        raise Failure('Lote excessivo.')
    # Freeze the entire input before inspecting or changing a system file.
    entries = json.loads(job.read_bytes())
    lock = Path('/run/lock/irixium-system-theme.lock')
    no_links(lock)
    with lock.open('a+b') as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        apply(entries)
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Failure, OSError, ValueError, KeyError, TypeError) as exc:
        print('ERRO:', exc, file=sys.stderr)
        sys.exit(1)
