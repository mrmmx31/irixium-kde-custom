#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reload owned GTK4 palettes through two stable native GTK theme identities.

GTK4 caches user CSS once per process. Mirroring the owned theme CSS with its
own role namespace avoids stale user definitions; changing gtk-theme-name
then reloads that theme's provider using GTK's normal settings mechanism.
GTK3 continues to use the native GTKConfig export directly. No application
is closed, injected with a provider, or restarted by this helper.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess

from gtk2_palette import exported_palette
from select_gtk import gtk_paths, notify, gsettings, restore_previous, wait_for_theme_files
from theme_transaction import (Change, Failure, Transaction, atomic, decode, image,
                               no_links, replace_checked, sha, snapshot)

THEMES = ('IrixClassic-KDE', 'Irixium-KDE', 'DomainOS-SR10-4-KDE')
IMPORT = re.compile(r'@import\s+url\(\s*["\']([^"\']+\.css)["\']\s*\)\s*;')
ROLE = re.compile(r'(?<![\w-])([A-Za-z_][A-Za-z0-9_]*_breeze)\b')
MARKER = b'/* IRIX owned GTK4 palette entry point */\n'


def accepts(theme, canonical):
    return canonical in THEMES and theme in (canonical, canonical+'-Reload')


def roots_for(data, home, theme):
    if theme not in THEMES: raise Failure('Tema GTK4 próprio desconhecido.')
    result = [base/name for base in (data/'themes', home/'.themes')
        for name in (theme, theme+'-Reload')]
    for path in result:
        no_links(path)
        if not (path/'gtk-4.0/gtk.css').is_file():
            raise Failure('Variante de recarga GTK4 não instalada: ' + str(path))
    return result


def owned_target(path, roots):
    return any(path.is_relative_to(root) and (path == root/'gtk-4.0/gtk.css'
        or path.name.endswith('.kde-live.css')) for root in roots)


def mirror_css(root, entry, original, palette):
    """Same-directory mirrors preserve all relative SVG/image coordinates."""
    files, sources, visiting = {}, {}, set()
    manifest_path = root/'MANIFEST.json'
    no_links(manifest_path)
    manifest = json.loads(manifest_path.read_text())['files']
    def mirror(path, contents=None):
        path = path.resolve()
        if not path.is_relative_to(root): raise Failure('Import CSS fora do tema próprio.')
        no_links(path)
        if path in visiting: raise Failure('Import CSS circular no tema próprio.')
        output = path.with_name(path.stem+'.kde-live.css')
        if output in files: return output
        visiting.add(path)
        source = contents if contents is not None else path.read_bytes()
        relative = path.relative_to(root).as_posix()
        if sha(source) != manifest.get(relative):
            raise Failure('CSS do tema editado ou manifesto divergente: ' + str(path))
        sources[relative] = sha(source)
        text = source.decode('utf-8')
        def imported(match):
            raw = path.parent/match[1]
            if raw.is_symlink(): raise Failure('Import CSS simbólico recusado.')
            target = mirror(raw)
            relative_import = os.path.relpath(target, output.parent)
            return '@import url('+json.dumps(relative_import)+');'
        text = IMPORT.sub(imported, text)
        if re.search(r'@import\b', IMPORT.sub('', source.decode('utf-8'))):
            raise Failure('Formato de import CSS não reconhecido: ' + str(path))
        text = ROLE.sub(lambda match: 'irix_kde_'+match[1], text)
        # Definitions in this CSS scope use a private namespace, independent
        # of the process's once-loaded user colors.css *_breeze definitions.
        text += '\n' + ''.join('@define-color irix_kde_'+name+' '+value+';\n'
                              for name, value in sorted(palette.items()))
        files[output] = text.encode()
        visiting.remove(path)
        return output
    mirrored_entry = mirror(entry, original)
    files[entry] = MARKER + ('@import url('+json.dumps(mirrored_entry.name)+');\n').encode()
    return files, sources


def refresh(data, config, state, home, theme, *, dry=False, force_reload=False, notify_call=None, settings_call=None):
    if theme not in THEMES:
        return {'status': 'ignored_other_gtk_theme'}
    notify_call = notify if notify_call is None else notify_call
    settings_call = gsettings if settings_call is None else settings_call
    current = notify_call()
    if not accepts(current, theme): return {'status': 'preserved_independent_gtk_theme'}
    css = config/'gtk-3.0/colors.css'
    no_links(css)
    if not css.is_file(): return {'status': 'waiting_native_palette'}
    if css.stat().st_uid != os.getuid(): raise Failure('Exportação GTK pertence a outro usuário.')
    contents = css.read_bytes()
    palette = exported_palette(contents)
    roots = roots_for(data, home, theme)
    base = state/'irixium-gtk4-palette'/theme
    control = base/'control.json'
    selection_journal = base/'native-selection.json'
    no_links(control)
    control_before = snapshot(control)
    previous = json.loads(decode(control_before)) if control_before['exists'] else None
    identity = {'format': 1, 'uid': os.getuid(), 'roots': [str(root) for root in roots]}
    originals, expected = {}, {}
    if previous:
        if any(previous.get(key) != value for key, value in identity.items()):
            raise Failure('Registro GTK4 não pertence a estes temas/usuário.')
        originals = {Path(path): value for path, value in previous['originals'].items()}
        expected = {Path(path): value for path, value in previous['after'].items()}
        for path, value in expected.items():
            if not owned_target(path, roots) or snapshot(path) != value:
                raise Failure('Edição posterior detectada na paleta GTK4: ' + str(path))
    files, sources = {}, {}
    for root in roots:
        entry = root/'gtk-4.0/gtk.css'
        original = decode(originals[entry]) if entry in originals else entry.read_bytes()
        generated, hashes = mirror_css(root, entry, original, palette)
        files.update(generated); sources[str(root)] = hashes
    signature = sha(json.dumps({'roles': palette, 'sources': sources}, sort_keys=True).encode())
    if previous and signature == previous['palette_signature']:
        no_links(selection_journal)
        if not selection_journal.is_file() or json.loads(selection_journal.read_text()).get('status') != 'applied':
            raise Failure('Há recarga nativa GTK4 interrompida; confira o recibo antes de continuar.')
        # GTK2 may have rebuilt its RC after a Global Theme's native GTK
        # selection, even when this family's GTK4 colors match its last use.
        if not force_reload:
            return {'status': 'unchanged', 'theme': current}
    for path in files:
        if path not in originals: originals[path] = snapshot(path)
        if path not in expected and path not in {root/'gtk-4.0/gtk.css' for root in roots} and path.exists():
            raise Failure('Destino GTK4 existente sem recibo: ' + str(path))
    native_files = gtk_paths(config, home)
    native_before = {path: snapshot(path) for path in native_files}
    settings_before = settings_call()
    next_theme = theme+'-Reload' if current == theme else theme
    target_set = set(files)|{control}
    def allowed(path, phase): return path in target_set and phase in (0, 2)
    def no_system(_entries): raise Failure('A paleta GTK4 não possui operações administrativas.')
    tx = Transaction(base/'transactions', no_system, allowed)
    record = dict(identity, palette_signature=signature, sources=sources,
        originals={str(path): value for path, value in originals.items()},
        after={str(path): image(value, snapshot(path).get('mode', 0o644)) for path, value in files.items()})
    changes = [Change(path, value, 2 if path.name == 'gtk.css' else 0,
        snapshot(path).get('mode', 0o644), snapshot(path)) for path, value in files.items()]
    changes.append(Change(control, (json.dumps(record, sort_keys=True)+'\n').encode(), 2, 0o600, control_before))
    if dry:
        tx.install(changes, dry=True)
        return {'status': 'ready', 'theme': next_theme, 'files': len(files)}
    with tx.locked():
        # Recheck the native selection immediately before committing owned
        # resources. A parallel manual GTK choice always wins.
        if notify_call() != current: raise Failure('A seleção GTK mudou antes da recarga.')
        atomic(selection_journal, (json.dumps({'status': 'prepared', 'theme_before': current,
            'theme_after': next_theme, 'palette_signature': signature,
            'gsettings_before': settings_before,
            'files': {str(path): value for path, value in native_before.items()}})+'\n').encode())
        receipt = tx.install(changes)
        try:
            if sha(css.read_bytes()) != sha(contents):
                raise Failure('A exportação GTK mudou durante a preparação da paleta.')
            notify_call(next_theme)
            if notify_call() != next_theme: raise Failure('O KDE não confirmou a recarga GTK4.')
            wait_for_theme_files(native_files, next_theme)
            atomic(selection_journal, (json.dumps({'status': 'applied', 'theme': next_theme,
                'palette_signature': signature, 'receipt': str(receipt) if receipt is not None else None})+'\n').encode())
        except BaseException as error:
            errors = restore_previous(native_before, theme=current, settings=settings_before,
                notify_call=notify_call, settings_call=settings_call)
            if receipt is not None:
                try: tx.restore()
                except BaseException as restore_error: errors.append(str(restore_error))
            atomic(base/'last-error.json', (json.dumps({'error': str(error), 'recovery_errors': errors})+'\n').encode())
            atomic(selection_journal, (json.dumps({'status': 'recovery_needed' if errors else 'failed_restored',
                'error': str(error), 'recovery_errors': errors})+'\n').encode())
            if errors: raise Failure('Recarga GTK4 falhou; recuperação incompleta: '+'; '.join(errors)) from error
            raise
    return {'status': 'reloaded', 'theme': next_theme, 'receipt': str(receipt) if receipt is not None else None}


def restore(data, config, state, home, theme, *, dry=False):
    roots = roots_for(data, home, theme)
    control = state/'irixium-gtk4-palette'/theme/'control.json'
    no_links(control)
    record = json.loads(control.read_text())
    if record.get('uid') != os.getuid() or record.get('roots') != [str(root) for root in roots]:
        raise Failure('Registro GTK4 não corresponde a este perfil.')
    for path, expected in record['after'].items():
        file = Path(path)
        if not owned_target(file, roots) or snapshot(file) != expected:
            raise Failure('Edição posterior detectada; restauração GTK4 recusada.')
    changes = []
    for path, before in record['originals'].items():
        file = Path(path)
        if not owned_target(file, roots): raise Failure('Backup GTK4 fora do tema.')
        changes.append(Change(file, decode(before), 2, before.get('mode', 0o644), snapshot(file)))
    changes.append(Change(control, None, 2, 0o600, snapshot(control)))
    targets = {change.path for change in changes}
    tx = Transaction(control.parent/'transactions', lambda _: (_ for _ in ()).throw(Failure('Sem operações administrativas.')),
        lambda path, phase: path in targets and phase in (0, 2))
    if dry: tx.install(changes, dry=True)
    else:
        with tx.locked(): tx.install(changes)
    result = {'status': 'restore_ready' if dry else 'restored'}
    if dry:
        result['overlays'] = [{'path': str(change.path), 'before': change.expected,
            'after': image(change.data, change.mode)} for change in changes if change.path != control]
    return result
