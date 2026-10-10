#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Retire the one canonical DomainOS color filename with its own journal.

The installer prepares this plan before deploying its four components, then
applies the same guarded snapshot afterward. This helper never selects a color
scheme, writes KDE preferences or removes edited files. The coordinator invokes
Bundle's public install/restore methods; its separate migration transaction must
be checked before restoring either installation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import stat
import uuid

from theme_transaction import Change, Failure, Transaction, decode, image, no_links, snapshot

LEGACY_FILENAME = 'DomainOS-SR10.4.colors'
LEGACY_SHA256 = '56cdc9ee06c8c4e69733be6e5dee967c1ecf4976ec5b6b8be10de3623eb17ebf'
JOURNAL_DIRECTORY = 'irixium-domainos-color-migration'
MIGRATION_ID = 'domainos-scheme-id-v1'


def _own_directory_if_present(path: Path) -> None:
    no_links(path)
    if path.exists() and (not path.is_dir() or path.stat().st_uid != os.getuid()):
        raise Failure('Pasta do próprio usuário necessária: ' + str(path))


def _own_file_if_present(path: Path) -> None:
    no_links(path)
    if path.exists() and (not path.is_file() or path.stat().st_uid != os.getuid()):
        raise Failure('Arquivo regular do próprio usuário necessário: ' + str(path))


def _paths(data: Path, state: Path) -> tuple[Path, Path]:
    if os.geteuid() == 0:
        raise Failure('Migração somente do próprio usuário, sem sudo.')
    data, state = Path(data), Path(state)
    _own_directory_if_present(data)
    _own_directory_if_present(state)
    target = data / 'color-schemes' / LEGACY_FILENAME
    journal = state / JOURNAL_DIRECTORY
    _own_directory_if_present(journal)
    if journal.exists() and stat.S_IMODE(journal.stat().st_mode) != 0o700:
        raise Failure('Pasta privada 0700 necessária para a migração: ' + str(journal))
    _own_file_if_present(target)
    return target, journal


class _MigrationTransaction(Transaction):
    """Validate this journal's identity in addition to Transaction's file guard."""

    def __init__(self, target: Path, journal: Path, operation_token: str | None = None):
        self.target = target
        self.operation_token = operation_token

        def no_system_write(entries):
            raise Failure('A migração de cores não pode escrever arquivos de sistema.')

        super().__init__(journal, no_system_write,
                         lambda path, phase: path == target and phase == 0)

    def latest(self):
        _own_file_if_present(self.state / 'latest')
        try:
            previous = super().latest()
        except (KeyError, TypeError, ValueError, UnicodeError) as error:
            raise Failure('Recibo da migração de cores inválido.') from error
        if previous is None:
            return None
        file, record = previous
        _own_file_if_present(file)
        if (type(record.get('format')) is not int or record.get('format') != 1
                or record.get('migration') != MIGRATION_ID or record.get('uid') != os.getuid()
                or record.get('legacySha256') != LEGACY_SHA256
                or record.get('status') not in ('prepared', 'installed', 'restoring',
                                               'recovery_needed', 'restored')
                or len(record['entries']) != 1):
            raise Failure('Recibo não pertence à migração canônica de cores deste usuário.')
        token = record.get('operationToken')
        if token is not None and (not isinstance(token, str)
                                  or not re.fullmatch(r'[0-9a-f]{32}', token)):
            raise Failure('Identidade da operação de migração inválida.')
        entry = record['entries'][0]
        before = entry['before']
        if (type(entry['phase']) is not int or entry['phase'] != 0
                or before.get('exists') is not True or before.get('sha256') != LEGACY_SHA256
                or entry['after'] != image(None)):
            raise Failure('Recibo não contém apenas a retirada do esquema legado canônico.')
        return file, record

    def save(self, file, record):
        record.update(migration=MIGRATION_ID, uid=os.getuid(), legacySha256=LEGACY_SHA256)
        if self.operation_token is not None:
            record['operationToken'] = self.operation_token
        super().save(file, record)


@dataclass(frozen=True)
class MigrationPlan:
    data: Path
    state: Path
    legacy_path: Path
    observed: dict
    change: Change | None
    status: str
    reason: str
    operation_token: str = field(default_factory=lambda: uuid.uuid4().hex)


def prepare_migration(data: Path, state: Path) -> MigrationPlan:
    """Read-only preflight. Edited legacy content is kept and reported explicitly."""
    data, state = Path(data), Path(state)
    target, journal = _paths(data, state)
    transaction = _MigrationTransaction(target, journal)
    transaction.assert_ready()
    observed = snapshot(target)
    if not observed['exists']:
        return MigrationPlan(data, state, target, observed, None, 'absent',
                             'O nome legado não existe; nenhum arquivo será retirado.')
    if observed['sha256'] != LEGACY_SHA256:
        return MigrationPlan(data, state, target, observed, None, 'preserved_modified',
                             'Esquema legado modificado preservado; a retirada automática foi ignorada.')
    # Change accepts an absent image through Transaction.image(None); no new
    # color path or preference is part of this separate transaction.
    change = Change(target, None, phase=0, expected=observed)
    return MigrationPlan(data, state, target, observed, change, 'canonical_legacy',
                         'Esquema legado canônico reconhecido para retirada com backup privado.')


def _checked_transaction(plan: MigrationPlan) -> _MigrationTransaction:
    target, journal = _paths(plan.data, plan.state)
    if target != plan.legacy_path:
        raise Failure('Plano de migração não pertence ao destino legado esperado.')
    if (not isinstance(plan.operation_token, str)
            or not re.fullmatch(r'[0-9a-f]{32}', plan.operation_token)):
        raise Failure('Identidade do plano de migração inválida.')
    decode(plan.observed)
    if snapshot(target) != plan.observed:
        raise Failure('Esquema legado mudou após a preparação; nenhuma retirada feita: ' + str(target))
    if plan.change is not None:
        change = plan.change
        if (plan.status != 'canonical_legacy' or change.path != target
                or change.phase != 0 or change.data is not None
                or change.expected != plan.observed
                or plan.observed.get('sha256') != LEGACY_SHA256):
            raise Failure('Plano de retirada do esquema legado inválido.')
    elif plan.status not in ('absent', 'preserved_modified'):
        raise Failure('Plano de migração sem retirada inválido.')
    return _MigrationTransaction(target, journal, plan.operation_token)


def install_with_migration(bundle, pairs, plan: MigrationPlan, dry: bool = False) -> dict:
    """Deploy a Bundle, then retire its prepared canonical legacy color file.

    These are two guarded journals, not one atomic filesystem transaction. Only
    receipts created by this call are eligible for rollback; a previous migration
    is never rewound because a later no-op install fails. All rollback guards are
    checked before either journal writes, and the legacy scheme is restored first.
    Interrupted recovery remains explicit through restore_migration(recovery=True).
    """
    transaction = _checked_transaction(plan)
    transaction.assert_ready()
    migration_before = transaction.latest()
    if dry:
        bundle.install(pairs, dry=True)
        return {'migration': apply_migration(plan, dry=True), 'bundle_receipt': None}
    with bundle.locked():
        bundle_before = bundle.latest()
        try:
            bundle.install(pairs)
            migration = apply_migration(plan)
            current = bundle.latest()
            return {'migration': migration,
                    'bundle_receipt': str(current[0]) if current else None}
        except BaseException as original:
            try:
                current = bundle.latest()
                previous_path = bundle_before[0] if bundle_before else None
                undo_bundle = (current is not None and current[0] != previous_path
                               and current[1]['status'] in ('prepared', 'installed'))
                migrated = transaction.latest()
                migration_path = migration_before[0] if migration_before else None
                undo_migration = (migrated is not None and migrated[0] != migration_path
                                  and migrated[1].get('operationToken') == plan.operation_token
                                  and migrated[1]['status'] != 'restored')
                if undo_migration:
                    # Do not race another install's shared migration journal.
                    # Its latest pointer and token must still identify our receipt
                    # after obtaining the journal lock, before either rollback.
                    with transaction.locked():
                        locked = transaction.latest()
                        if (locked is None or locked[0] != migrated[0]
                                or locked[1].get('operationToken') != plan.operation_token):
                            raise Failure('O recibo da migração mudou antes da restauração.')
                        transaction.restore(recovery=True, dry=True)
                        if undo_bundle:
                            bundle.restore(dry=True)
                        transaction.restore(recovery=True)
                        if undo_bundle:
                            bundle.restore()
                elif undo_bundle:
                    bundle.restore(dry=True)
                    bundle.restore()
            except BaseException as rollback:
                raise Failure('Instalação incompleta; preserve os dois journals para recuperação '
                              'com --restaurar --recuperar. '
                              f'Componentes: {bundle.state}; migração: {transaction.state}. '
                              f'Erro: {original}; restauração: {rollback}') from original
            raise


def apply_migration(plan: MigrationPlan, dry: bool = False) -> dict:
    """Apply the preflight snapshot after component deployment, never a new plan."""
    transaction = _checked_transaction(plan)
    transaction.assert_ready()
    receipt = None
    if plan.change is not None:
        if dry:
            transaction.install([plan.change], dry=True)
        else:
            with transaction.locked():
                receipt = transaction.install([plan.change])
    print(plan.reason)
    return {'status': 'verified' if dry and plan.change else 'removed' if receipt else plan.status,
            'dry': dry, 'legacy_path': str(plan.legacy_path), 'reason': plan.reason,
            'receipt': str(receipt) if receipt else None}


def restore_migration(data: Path, state: Path, dry: bool = False,
                      recovery: bool = False) -> dict:
    """Preflight all migration guards before touching an independent Bundle.

    The caller checks this with dry=True and checks the main Bundle separately
    before restoring either. This journal restores only the old scheme bytes and
    mode; it never removes the new scheme or modifies application preferences.
    """
    target, journal = _paths(Path(data), Path(state))
    transaction = _MigrationTransaction(target, journal)
    previous = transaction.latest()
    if previous is None:
        return {'status': 'not_recorded', 'dry': dry, 'legacy_path': str(target), 'receipt': None}
    file, record = previous
    if record['status'] == 'restored':
        return {'status': 'already_restored', 'dry': dry, 'legacy_path': str(target), 'receipt': str(file)}
    if dry:
        transaction.restore(recovery=recovery, dry=True)
    else:
        with transaction.locked():
            transaction.restore(recovery=recovery)
    return {'status': 'verified_restore' if dry else 'restored', 'dry': dry,
            'legacy_path': str(target), 'receipt': str(file)}
