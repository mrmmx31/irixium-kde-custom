#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Recoverable, user-local Kvantum copies; canonical artwork stays unchanged."""
from __future__ import annotations
import json
import os
from pathlib import Path

from gtk2_palette import exported_palette
from select_companions import kvantum_theme, require_global
from user_bundle import Bundle
from theme_transaction import (Change, Failure, Transaction, atomic, decode,
                               edit_ini, image, no_links, sha, snapshot)

THEMES = ('IrixClassic', 'Irixium')


def accepts(current, theme):
    return theme in THEMES and current in (theme, theme+'-KDE', theme+'-KDE-Reload')


def generated_paths(config, theme):
    if theme not in THEMES: raise Failure('Família Kvantum desconhecida.')
    return [config/'Kvantum'/name/(name+suffix)
        for name in (theme+'-KDE', theme+'-KDE-Reload') for suffix in ('.svg', '.kvconfig')]


def owned_selection(config, state, theme):
    """Recognize only a journaled, unedited alias; preserve no arbitrary alias."""
    selector = config/'Kvantum/kvantum.kvconfig'
    current = kvantum_theme(selector)
    if not accepts(current, theme) or current == theme:
        return False
    control = state/'irixium-kvantum-palette'/theme/'control.json'
    value = snapshot(control)
    if not value['exists']:
        return False
    prior = json.loads(decode(value))
    targets = generated_paths(config, theme)
    identity = {'format': 1, 'uid': os.getuid(), 'theme': theme,
        'targets': [str(path) for path in targets], 'selector': str(selector)}
    return all(prior.get(key) == value for key, value in identity.items()) and \
        set(prior.get('after', {})) == {str(path) for path in targets} and \
        all(snapshot(path) == prior['after'][str(path)] for path in targets)


def render(theme, svg, settings, palette, *, native_qt_palette):
    if theme == 'IrixClassic':
        from kvantum_classic_palette import render as mapper
    elif theme == 'Irixium':
        from kvantum_modern_palette import render as mapper
    else: raise Failure('Família Kvantum desconhecida.')
    return mapper(svg, settings, palette, native_qt_palette=native_qt_palette)


def refresh(config, state, profile, *, notify_style, style_name, native, dry=False):
    theme = profile['kvantum']
    if theme not in THEMES: raise Failure('Família Kvantum desconhecida.')
    require_global(config, profile['global'])
    if style_name(config).lower() != 'kvantum':
        return {'status': 'preserved_independent_application_style'}
    if not accepts(kvantum_theme(config/'Kvantum/kvantum.kvconfig'), theme):
        return {'status': 'preserved_independent_kvantum_theme'}
    if dry: return _refresh(config, state, profile, notify_style=notify_style, style_name=style_name, native=native, dry=True)
    # Shared across both refresh and restore; guards are read again under it.
    with Bundle(state/'irixium-kvantum-palette'/theme/'operation-lock', ()).locked():
        return _refresh(config, state, profile, notify_style=notify_style, style_name=style_name, native=native)


def _refresh(config, state, profile, *, notify_style, style_name, native, dry=False):
    """Commit resources before the selection, then send native style and palette events."""
    from theme_companion_bridge import native_palette_signature
    if native_palette_signature(config) != native['source_signature']:
        raise Failure('As cores do KDE mudaram antes da atualização Qt.')
    theme = profile['kvantum']
    selector = config/'Kvantum/kvantum.kvconfig'
    require_global(config, profile['global'])
    if style_name(config).lower() != 'kvantum':
        return {'status': 'preserved_independent_application_style'}
    current = kvantum_theme(selector)
    if not accepts(current, theme): return {'status': 'preserved_independent_kvantum_theme'}
    css = config/'gtk-3.0/colors.css'
    no_links(css)
    if not css.is_file(): return {'status': 'waiting_native_palette'}
    if css.stat().st_uid != os.getuid(): raise Failure('Paleta pertence a outro usuário.')
    css_before = snapshot(css)
    palette = exported_palette(decode(css_before))
    source_paths = [config/'Kvantum'/theme/(theme+suffix) for suffix in ('.svg', '.kvconfig')]
    source = {path: snapshot(path) for path in source_paths}
    if not all(value['exists'] for value in source.values()): raise Failure('Fonte Kvantum instalada ausente.')
    svg, settings, coverage = render(theme, *(decode(source[p]) for p in source_paths), palette, native_qt_palette=native['palette'])
    targets = generated_paths(config, theme)
    files = {path: svg if path.suffix == '.svg' else settings for path in targets}
    base = state/'irixium-kvantum-palette'/theme
    control = base/'control.json'
    notification = base/'native-notification.json'
    notification_before = snapshot(notification)
    before_control = snapshot(control)
    prior = json.loads(decode(before_control)) if before_control['exists'] else None
    if not prior and current != theme:
        raise Failure('Seleção de variante Kvantum sem recibo; adoção recusada.')
    identity = {'format': 1, 'uid': os.getuid(), 'theme': theme,
                'targets': [str(path) for path in targets], 'selector': str(selector)}
    if prior and any(prior.get(key) != value for key, value in identity.items()):
        raise Failure('Recibo Kvantum não pertence a estes caminhos/usuário.')
    signature = sha(json.dumps({'roles': palette, 'native_qt': native['palette'], 'sources': {str(p): value['sha256']
        for p, value in source.items()}, 'generated': {str(p): sha(value) for p, value in files.items()}},
        sort_keys=True).encode())
    originals = prior['originals'] if prior else {str(path): snapshot(path) for path in targets}
    if not prior and any(value['exists'] for value in originals.values()):
        raise Failure('Variante Kvantum existente sem recibo; substituição recusada.')
    allowed = set(targets)|{selector, control, notification}
    tx = Transaction(base/'transactions', lambda _: (_ for _ in ()).throw(Failure('Sem operações administrativas.')),
        lambda path, phase: path in allowed and phase in (0, 2))
    tx.assert_ready()
    if prior:
        if prior.get('source') != {str(path): value['sha256'] for path, value in source.items()}:
            raise Failure('Fonte Kvantum mudou após a instalação; restaure a variante antes de atualizar.')
        if set(prior.get('after', {})) != {str(path) for path in targets}:
            raise Failure('Recibo de recursos Kvantum incompleto.')
        for path in targets:
            if snapshot(path) != prior['after'][str(path)]:
                raise Failure('Variante Kvantum editada após instalação: '+str(path))
        previous_notification = json.loads(decode(notification_before)) if notification_before['exists'] else None
        if not previous_notification or previous_notification.get('uid') != os.getuid() or previous_notification.get('status') != 'native_events_sent':
            raise Failure('Notificação Qt interrompida ou sem recibo; restaure explicitamente antes de continuar.')
        if prior.get('signature') == signature and previous_notification.get('signature') == signature and snapshot(selector) == prior['selector_after']:
            return {'status': 'unchanged', 'theme': current}
    selector_before = snapshot(selector)
    next_theme = theme+'-KDE-Reload' if current == theme+'-KDE' else theme+'-KDE'
    selector_after = edit_ini(decode(selector_before) or b'', 'General', {'theme': next_theme})
    record = dict(identity, signature=signature, coverage=coverage, originals=originals,
        after={str(path): image(contents, 0o644) for path, contents in files.items()},
        source={str(path): value['sha256'] for path, value in source.items()},
        selector_before=prior['selector_before'] if prior else selector_before,
        selector_after=image(selector_after, selector_before.get('mode', 0o600)))
    allowed = set(targets)|{selector, control, notification}
    tx = Transaction(base/'transactions', lambda _: (_ for _ in ()).throw(Failure('Sem operações administrativas.')),
        lambda path, phase: path in allowed and phase in (0, 2))
    changes = [Change(path, contents, 0, 0o644, snapshot(path)) for path, contents in files.items()]
    changes.append(Change(notification, (json.dumps({'uid': os.getuid(), 'status': 'prepared',
        'signature': signature, 'theme': next_theme})+'\n').encode(), 0, 0o600, notification_before))
    changes += [Change(selector, selector_after, 2, selector_before.get('mode', 0o600), selector_before),
                Change(control, (json.dumps(record, sort_keys=True)+'\n').encode(), 2, 0o600, before_control)]
    if dry:
        tx.install(changes, dry=True)
        return {'status': 'ready', 'theme': next_theme, 'coverage': coverage}
    with tx.locked():
        require_global(config, profile['global'])
        if style_name(config).lower() != 'kvantum' or kvantum_theme(selector) != current:
            raise Failure('Escolha Qt mudou antes da atualização.')
        if native_palette_signature(config) != native['source_signature'] or snapshot(css) != css_before or any(snapshot(p) != value for p, value in source.items()):
            raise Failure('Paleta/fonte mudou antes da atualização Qt.')
        receipt = tx.install(changes)
        try:
            require_global(config, profile['global'])
            if style_name(config).lower() != 'kvantum' or snapshot(selector) != record['selector_after']:
                raise Failure('Escolha Qt mudou antes da notificação nativa.')
            if native_palette_signature(config) != native['source_signature'] or snapshot(css) != css_before or any(snapshot(p) != value for p, value in source.items()):
                raise Failure('Paleta/fonte mudou durante a atualização Qt.')
            if notify_style(config, profile) != 'native_style_and_palette_sent':
                raise Failure('O Qt mudou de estilo antes da notificação; atualização recusada.')
            atomic(notification, (json.dumps({'uid': os.getuid(), 'status': 'native_events_sent',
                'signature': signature, 'theme': next_theme, 'receipt': str(receipt) if receipt else None})+'\n').encode())
        except BaseException as error:
            errors = []
            if receipt:
                try: tx.restore()
                except BaseException as restore_error: errors.append(str(restore_error))
            atomic(base/'last-error.json', (json.dumps({'error': str(error), 'recovery_errors': errors})+'\n').encode())
            if errors: raise Failure('Atualização Qt falhou; recuperação incompleta: '+'; '.join(errors)) from error
            raise
    return {'status': 'reloaded', 'theme': next_theme, 'coverage': coverage,
            'receipt': str(receipt) if receipt else None}


def restore(config, state, theme, *, dry=False):
    if theme not in THEMES: raise Failure('Família Kvantum desconhecida.')
    if dry: return _restore(config, state, theme, dry=True)
    with Bundle(state/'irixium-kvantum-palette'/theme/'operation-lock', ()).locked():
        return _restore(config, state, theme)


def _restore(config, state, theme, *, dry=False):
    targets = generated_paths(config, theme)
    control = state/'irixium-kvantum-palette'/theme/'control.json'
    prior = json.loads(decode(snapshot(control)))
    selector = config/'Kvantum/kvantum.kvconfig'
    identity = {'format': 1, 'uid': os.getuid(), 'theme': theme,
        'targets': [str(path) for path in targets], 'selector': str(selector)}
    if any(prior.get(k) != v for k, v in identity.items()): raise Failure('Recibo Qt divergente.')
    if set(prior['originals']) != {str(path) for path in targets} or set(prior['after']) != set(prior['originals']):
        raise Failure('Recibo Qt incompleto.')
    changes = []
    for path in targets:
        if snapshot(path) != prior['after'][str(path)]: raise Failure('Edição posterior na variante Qt.')
        before = prior['originals'][str(path)]
        changes.append(Change(path, decode(before), 0, before.get('mode', 0o644), snapshot(path)))
    # A later unrelated choice wins. Restore only the precise owned selection.
    if snapshot(selector) == prior['selector_after']:
        before = prior['selector_before']
        changes.append(Change(selector, decode(before), 2, before.get('mode', 0o600), snapshot(selector)))
    changes.append(Change(control, None, 2, 0o600, snapshot(control)))
    notification = control.parent/'native-notification.json'
    changes.append(Change(notification, None, 2, 0o600, snapshot(notification)))
    allowed = {change.path for change in changes}
    tx = Transaction(control.parent/'restoration', lambda _: (_ for _ in ()).throw(Failure('Sem operações administrativas.')),
        lambda path, phase: path in allowed and phase in (0, 2))
    if dry: tx.install(changes, dry=True)
    else:
        with tx.locked(): tx.install(changes)
    return {'status': 'restore_ready' if dry else 'restored'}
