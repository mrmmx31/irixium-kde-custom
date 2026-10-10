#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Recoverable GTK2 palette resources for the two installed adaptive themes.

These entry points are called explicitly or by the opt-in native observer. They
do not select themes, write the user's gtkrc, contact a session, or poll files.
The renderer's immutable resource store is shared by XDG and ~/.themes copies.
Running GTK2 applications still require their native RC reload notification.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Callable

from gtk2_palette import exported_palette, include_palette, prepare
from theme_transaction import (Change, Failure, Transaction, decode, image,
                               no_links, replace_checked, sha, snapshot)

OWNED = {'IrixClassic-KDE': 'IrixClassic', 'IrixClassic-KDE-Reload': 'IrixClassic',
         'Irixium-KDE': 'Irixium', 'Irixium-KDE-Reload': 'Irixium',
         'DomainOS-SR10-4-KDE': 'DomainOS-SR10-4',
         'DomainOS-SR10-4-KDE-Reload': 'DomainOS-SR10-4'}
FORMAT = 1
MAX_CSS = 256 * 1024


@dataclass(frozen=True)
class Roots:
    data: Path
    config: Path
    state: Path
    home: Path

    def __post_init__(self):
        for name in ('data', 'config', 'state', 'home'):
            value = Path(getattr(self, name))
            no_links(value)
            if value == Path('/'):
                raise Failure('Raiz GTK2 não pode ser o sistema de arquivos inteiro.')
            object.__setattr__(self, name, value)

    @property
    def runtime(self):
        return self.state / 'irixium-gtk2-palette'

    @property
    def store(self):
        return self.data / 'irixium/gtk2-palette'

    @property
    def control(self):
        return self.runtime / 'active.json'

    def wrappers(self):
        return {base / name / 'gtk-2.0/gtkrc': name
                for base in (self.data / 'themes', self.home / '.themes')
                for name in OWNED}

    def identity(self):
        return {key: str(getattr(self, key)) for key in ('data', 'config', 'state', 'home')}


def _owned_file(path: Path, maximum=8 * 1024 * 1024):
    no_links(path)
    try:
        info = path.stat()
    except OSError as error:
        raise Failure('Arquivo GTK2 indisponível: ' + str(path)) from error
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > maximum:
        raise Failure('Arquivo GTK2 precisa ser regular, do próprio usuário e limitado: ' + str(path))
    return snapshot(path)


def native_colors(roots: Roots, path: Path | None = None):
    """Read only the native GTK Config export; never expand CSS expressions."""
    candidates = [roots.config / f'gtk-{version}/colors.css' for version in ('3.0', '4.0')]
    if path is not None:
        path = Path(path)
        if path not in candidates:
            raise Failure('A origem deve ser colors.css nativo deste XDG_CONFIG_HOME.')
        candidates = [path]
    selected = next((candidate for candidate in candidates if candidate.exists()), None)
    if selected is None:
        raise Failure('Exportação nativa de cores GTK ainda não está disponível.')
    before = _owned_file(selected, MAX_CSS)
    contents = decode(before)
    # KDE's writer emits one literal declaration per role. Reject an ambiguous
    # duplicate rather than letting its position silently choose the color.
    try:
        names = re.findall(r'^\s*@define-color\s+(\w+)\s+', contents.decode('utf-8'), re.M)
    except UnicodeError as error:
        raise Failure('Exportação nativa GTK não é UTF-8.') from error
    if len(names) != len(set(names)):
        raise Failure('Exportação nativa GTK contém papéis duplicados.')
    exported_palette(contents)
    if _owned_file(selected, MAX_CSS) != before:
        raise Failure('As cores nativas mudaram durante a leitura.')
    return selected, before, contents


def _resource_path(roots, path):
    try:
        parts = path.relative_to(roots.store).parts
    except ValueError:
        return False
    return (len(parts) == 2 and re.fullmatch(r'[0-9a-f]{64}', parts[0]) is not None
            and parts[1] in ('gtkrc', 'manifest.json')) or (
        len(parts) == 3 and re.fullmatch(r'[0-9a-f]{64}', parts[0]) is not None
        and parts[1] == 'assets' and re.fullmatch(r'[a-z0-9-]+\.png', parts[2]) is not None)


def _transaction(roots, writer):
    wrapper_paths = roots.wrappers()

    def allowed(path, phase):
        return ((phase == 0 and _resource_path(roots, path))
                or (phase == 2 and (path in wrapper_paths or path == roots.control)))

    def guarded_writer(path, before, after):
        old_time = path.stat().st_mtime_ns if path in wrapper_paths and path.exists() else None
        writer(path, before, after)
        if old_time is not None and after['exists']:
            # _GTK_READ_RCFILES reparses only when st_mtime *seconds* changed.
            # Do not sleep or toggle ThemeName. Only our changed RC metadata is
            # advanced if two commits occurred within the same native second.
            info = path.stat()
            if info.st_mtime_ns // 10**9 == old_time // 10**9:
                os.utime(path, ns=(info.st_atime_ns, old_time + 10**9))

    def no_system_writer(_entries):
        raise Failure('Esta operação GTK2 não possui fase privilegiada.')

    return Transaction(roots.runtime, no_system_writer, allowed, guarded_writer)


def _active(roots):
    if not roots.control.exists():
        return None
    original = _owned_file(roots.control, 1024 * 1024)
    try:
        record = json.loads(decode(original))
    except (UnicodeError, ValueError) as error:
        raise Failure('Registro GTK2 ativo inválido.') from error
    if (not isinstance(record, dict) or record.get('format') != FORMAT or record.get('roots') != roots.identity()
            or record.get('status') not in ('active', 'restored')
            or not isinstance(record.get('themes'), list)
            or not isinstance(record.get('resources'), list)):
        raise Failure('Registro GTK2 não corresponde às raízes explícitas.')
    seen = set()
    for entry in record['themes']:
        if not isinstance(entry, dict) or set(entry) != {'path', 'name', 'baseline', 'after'}:
            raise Failure('Registro de tema GTK2 inválido.')
        path = Path(entry['path'])
        if path in seen or roots.wrappers().get(path) != entry['name']:
            raise Failure('Tema do registro GTK2 fora do escopo próprio.')
        seen.add(path)
        decode(entry['baseline']); decode(entry['after'])
    for entry in record['resources']:
        if not isinstance(entry, dict) or set(entry) != {'path', 'sha256', 'mode'}:
            raise Failure('Registro de recurso GTK2 inválido.')
        path = Path(entry['path'])
        if (path in seen or not _resource_path(roots, path)
                or not isinstance(entry['sha256'], str)
                or not re.fullmatch(r'[0-9a-f]{64}', entry['sha256'])
                or type(entry['mode']) is not int or not 0 <= entry['mode'] <= 0o777):
            raise Failure('Recurso do registro GTK2 fora do escopo próprio.')
        seen.add(path)
    return original, record


def _validate_active(roots, record):
    for entry in record['themes']:
        if _owned_file(Path(entry['path'])) != entry['after']:
            raise Failure('Edição posterior no tema GTK2; preserve-a antes de continuar: ' + entry['path'])
    for entry in record['resources']:
        current = _owned_file(Path(entry['path']))
        if (current['sha256'], current['mode']) != (entry['sha256'], entry['mode']):
            raise Failure('Recurso GTK2 gerado foi modificado: ' + entry['path'])


def _renderer(name, renderers):
    name = name.removesuffix('-Reload')
    if name in renderers:
        return renderers[name]
    if name == 'IrixClassic-KDE':
        return prepare
    try:
        if name == 'DomainOS-SR10-4-KDE':
            return importlib.import_module('gtk2_domainos_palette').prepare_domainos
        return importlib.import_module('gtk2_modern_palette').prepare_modern
    except (ImportError, AttributeError) as error:
        raise Failure('O renderer GTK2 instalado é necessário para ' + name + '.') from error


def _update(roots, *, setup, theme_name=None, colors_path=None, dry=False,
            renderers=None, writer=replace_checked):
    if theme_name is not None and theme_name not in OWNED:
        return {'status': 'ignored', 'reason': 'theme_not_owned'}
    publication, published_targets = {}, {}

    def current_colors():
        if publication and _owned_file(publication['path'], MAX_CSS) != publication['before']:
            raise Failure('As cores nativas mudaram durante a atualização GTK2.')

    def publish_checked(path, before, after):
        # Resources may be prepared before an asynchronous KDE export completes.
        # Recheck immediately before publishing any new include/control record.
        # Rollback's desired image is different and must never depend on the
        # exporter still containing an obsolete palette.
        if published_targets.get(path) == after:
            current_colors()
        writer(path, before, after)

    transaction = _transaction(roots, publish_checked)

    def prepare_update():
        transaction.assert_ready()
        active = _active(roots)
        if not setup and (active is None or active[1]['status'] != 'active'):
            return {'status': 'ignored', 'reason': 'not_set_up'}, []
        if active is not None:
            _validate_active(roots, active[1])
        old_record = active[1] if active and active[1]['status'] == 'active' else None
        installed = {path: name for path, name in roots.wrappers().items() if path.exists()}
        if not installed:
            return {'status': 'ignored', 'reason': 'no_owned_installed_themes'}, []
        if theme_name is not None and theme_name not in installed.values():
            return {'status': 'ignored', 'reason': 'selected_owned_theme_not_installed'}, []
        colors_file, colors_before, contents = native_colors(roots, colors_path)
        previous = {Path(value['path']): value for value in old_record['themes']} if old_record else {}
        themes, resources, changes, bundles, rendered = [], {}, [], {}, {}
        for name in sorted(set(installed.values())):
            source = next((base / OWNED[name] for base in (roots.data / 'themes', roots.home / '.themes')
                           if (base / OWNED[name] / 'gtk-2.0/gtkrc').exists()), None)
            if source is None:
                raise Failure('Tema GTK2 original instalado ausente: ' + OWNED[name])
            _owned_file(source / 'gtk-2.0/gtkrc', MAX_CSS)
            family = name.removesuffix('-Reload')
            if family not in rendered:
                rendered[family] = _renderer(name, renderers or {})(source, contents, roots.store)
            bundle = rendered[family]
            if not _resource_path(roots, bundle.gtkrc) or bundle.gtkrc not in bundle.files:
                raise Failure('Renderer GTK2 devolveu include fora do store próprio.')
            bundles[name] = str(bundle.directory)
            for path, data in bundle.files.items():
                if not _resource_path(roots, path) or not isinstance(data, bytes):
                    raise Failure('Renderer GTK2 devolveu recurso fora do escopo.')
                before = snapshot(path)
                wanted = image(data, 0o644)
                if before['exists'] and (_owned_file(path) != wanted):
                    raise Failure('Colisão ou edição no recurso GTK2 imutável: ' + str(path))
                entry = {'path': str(path), 'sha256': sha(data), 'mode': 0o644}
                if str(path) in resources:
                    if resources[str(path)] != entry:
                        raise Failure('Renderers GTK2 produziram conteúdo divergente no mesmo destino.')
                else:
                    resources[str(path)] = entry
                    changes.append(Change(path, data, expected=before))
            for path in sorted(path for path, installed_name in installed.items() if installed_name == name):
                before = _owned_file(path, MAX_CSS)
                baseline = previous[path]['baseline'] if path in previous else before
                # Rebuild exactly our include, preserving every other directive.
                after = image(include_palette(decode(before), bundle.gtkrc), before['mode'])
                themes.append({'path': str(path), 'name': name, 'baseline': baseline, 'after': after})
                changes.append(Change(path, decode(after), phase=2, mode=after['mode'], expected=before))
        record = {'format': FORMAT, 'status': 'active', 'roots': roots.identity(),
                  'themes': themes, 'resources': list(resources.values()),
                  'colors_source': str(colors_file), 'colors_sha256': colors_before['sha256']}
        control_before = active[0] if active else image(None)
        payload = (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode()
        changes.append(Change(roots.control, payload, phase=2, mode=0o600, expected=control_before))
        if _owned_file(colors_file, MAX_CSS) != colors_before:
            raise Failure('As cores nativas mudaram durante a preparação; nenhuma escrita realizada.')
        publication.update(path=colors_file, before=colors_before)
        published_targets.update({change.path: image(change.data, change.mode)
                                  for change in changes if change.phase == 2})
        return {'status': 'ready' if dry else 'updated', 'themes': sorted(bundles), 'bundles': bundles,
                'colors_sha256': record['colors_sha256'],
                'native_reload_required': True}, changes

    def commit():
        result, changes = prepare_update()
        if not changes:
            return result
        planned = transaction.plan(changes)
        if not planned:
            result.update(status='unchanged', native_reload_required=False)
            return result
        result['native_reload_required'] = any(Path(entry['path']) in roots.wrappers() for entry in planned)
        receipt = transaction.install(changes, dry=dry)
        if receipt is not None:
            result['receipt'] = str(receipt)
            try:
                current_colors()
            except Failure as error:
                # No theme selection/reload has happened. Undo this transaction
                # only, protecting both the previous setup and concurrent edits.
                try:
                    transaction.restore(recovery=True)
                except BaseException as rollback:
                    raise Failure(str(error) + '; restauração recusada/incompleta: '
                                  + str(rollback) + '. Backup: ' + str(receipt)) from error
                raise Failure(str(error) + '; arquivos anteriores restaurados.') from error
        return result

    if dry or theme_name is not None and theme_name not in OWNED:
        return commit()
    with transaction.locked():
        return commit()


def setup(data: Path, config: Path, state: Path, home: Path, theme=None, **options):
    """Start a journaled palette binding for installed owned adaptive variants."""
    return _update(Roots(data, config, state, home), setup=True, theme_name=theme, **options)


def refresh(data: Path, config: Path, state: Path, home: Path, theme=None, **options):
    """Refresh on a native event; ignored for other themes and before setup."""
    return _update(Roots(data, config, state, home), setup=False, theme_name=theme, **options)


def restore(data: Path, config: Path, state: Path, home: Path, *, dry=False,
            recovery=False, writer=replace_checked):
    """Restore setup's exact RC bytes/modes, or recover the last interrupted commit.

    Immutable cache resources are deliberately retained: a still running GTK2
    process can hold old RC references until it receives its native reload.
    """
    roots = Roots(data, config, state, home)
    transaction = _transaction(roots, writer)

    def commit():
        if recovery:
            transaction.restore(recovery=True, dry=dry)
            return {'status': 'recovery_ready' if dry else 'recovered', 'native_reload_required': not dry}
        transaction.assert_ready()
        active = _active(roots)
        if active is None or active[1]['status'] != 'active':
            raise Failure('Nenhuma adaptação GTK2 ativa para restaurar.')
        _validate_active(roots, active[1])
        record = active[1]
        changes = [Change(Path(value['path']), decode(value['baseline']), phase=2,
                          mode=value['baseline'].get('mode', 0o644), expected=value['after'])
                   for value in record['themes']]
        restored = dict(record, status='restored', resources=[],
                        themes=[dict(value, after=value['baseline']) for value in record['themes']])
        changes.append(Change(roots.control, (json.dumps(restored, ensure_ascii=False, indent=2)+'\n').encode(),
                              phase=2, mode=0o600, expected=active[0]))
        receipt = transaction.install(changes, dry=dry)
        result = {'status': 'restore_ready' if dry else 'restored', 'receipt': str(receipt) if receipt else None,
                  'native_reload_required': not dry, 'immutable_resources_retained': True}
        if dry:
            # The suite's whole-tree check can view these exact validated file
            # restores without temporarily writing/removing any resources.
            result['overlays'] = [{'path': value['path'], 'before': value['after'],
                                   'after': value['baseline']} for value in record['themes']]
        return result

    if dry:
        return commit()
    with transaction.locked():
        return commit()
