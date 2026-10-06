#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate shipped dependencies and optionally compare the current user's install."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import sys

from components import ROOT, catalog, sources
from install_suite import roots
from user_bundle import validate_source


def hashes(root):
    if not root.exists():
        return {}
    if root.is_file():
        return {'@file': hashlib.sha256(root.read_bytes()).hexdigest()}
    validate_source(root)
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()
            and p.name not in ('icon-theme.cache', '.icon-theme.cache')}


def preference(config, file, group, key):
    value = None
    for path in (config/'kdedefaults'/file, config/file):
        if not path.is_file():
            continue
        cfg = configparser.ConfigParser(interpolation=None, strict=False)
        cfg.optionxform = str
        cfg.read(path)
        if cfg.has_option(group, key):
            value = cfg.get(group, key)
    return value


def sound_module():
    sys.path.insert(0, str(ROOT/'sons/tools'))
    import irix_sounds
    return irix_sounds


def audit(local=False, require_sounds=False):
    doc = catalog()
    data, config, _ = roots()
    failures, components = [], []
    for source, dest in sources(data, config):
        record = {'source': source.relative_to(ROOT).as_posix(), 'files': 0}
        if not source.exists():
            failures.append('Fonte ausente: '+record['source'])
        else:
            expected = hashes(source)
            record['files'] = len(expected)
            if local:
                actual = hashes(dest)
                differences = sorted(p for p in set(expected)|set(actual)
                                     if expected.get(p) != actual.get(p))
                if dest.name == 'irixium_irix_classic_v4' and 'metadata.json' in differences:
                    original = json.loads((source/'metadata.json').read_text())
                    installed = json.loads((dest/'metadata.json').read_text()) if (dest/'metadata.json').exists() else {}
                    original['KPlugin']['Id'] = dest.name
                    if installed == original:
                        differences.remove('metadata.json')
                record['local_differences'] = differences
                if differences:
                    failures.append('Instalação diferente: '+record['source'])
        components.append(record)
    for folder in ('decorations/classic', 'decorations/modern'):
        expected = json.loads((ROOT/folder/'MANIFEST.json').read_text())['package']
        if hashes(ROOT/folder/'package') != expected:
            failures.append('Manifesto divergente: '+folder)
    for name, profile in doc['profiles'].items():
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.optionxform = str
        cfg.read(ROOT/'look-and-feel'/profile['global']/'contents/defaults')
        bindings = [('kdeglobals][General', 'ColorScheme', 'Irixium'),
                    ('kdeglobals][Icons', 'Theme', profile['icons']),
                    ('plasmarc][Theme', 'name', profile['plasma']),
                    ('kcminputrc][Mouse', 'cursorTheme', 'sgi'),
                    ('kwinrc][org.kde.kdecoration2', 'theme', profile['decoration']),
                    ('Wallpaper', 'Image', profile['wallpaper']),
                    ('KSplash', 'Theme', profile['global'])]
        for group, key, value in bindings:
            if cfg.get(group, key, fallback=None) != value:
                failures.append(f'Dependência incoerente: {name}/{group}/{key}')
        required = [ROOT/'plasma'/profile['plasma']/'metadata.desktop',
                    ROOT/'icons'/('themes' if name=='classic' else '')/profile['icons']/'index.theme',
                    ROOT/'kvantum'/profile['kvantum']/(profile['kvantum']+'.kvconfig'),
                    ROOT/'wallpapers'/profile['wallpaper']/'metadata.json',
                    ROOT/'look-and-feel'/profile['global']/'contents/splash/Splash.qml',
                    ROOT/'gtk/gtk-3.0/gtk.css', ROOT/'gtk/gtk-4.0/gtk.css',
                    ROOT/'colors/Irixium.colors', ROOT/'cursors/sgi/index.theme']
        failures.extend('Dependência ausente: '+str(p.relative_to(ROOT)) for p in required if not p.is_file())
    sounds = {'audio_in_repository': False, 'automatic_download': False,
              'installer': doc['sounds']['installer'], 'theme': doc['sounds']['theme']}
    if local or require_sounds:
        module = sound_module()
        c = module.catalog()
        cache, dest, _, sound_config = module.locations()
        sounds.update(module.verify(c, cache, dest, sound_config))
        if require_sounds and not sounds['installed']:
            failures.append('Sons ausentes: forneça os originais com sons/instalar.sh --origem DIRETORIO.')
    selection = None
    if local:
        selected = preference(config, 'kdeglobals', 'KDE', 'LookAndFeelPackage')
        for name, profile in doc['profiles'].items():
            if profile['global'] != selected:
                continue
            checks = [('kdeglobals', 'Icons', 'Theme', profile['icons']),
                      ('kdeglobals', 'General', 'ColorScheme', 'Irixium'),
                      ('plasmarc', 'Theme', 'name', profile['plasma']),
                      ('kwinrc', 'org.kde.kdecoration2', 'theme', profile['decoration']),
                      ('kcminputrc', 'Mouse', 'cursorTheme', 'sgi'),
                      ('Kvantum/kvantum.kvconfig', 'General', 'theme', profile['kvantum']),
                      ('gtk-3.0/settings.ini', 'Settings', 'gtk-theme-name', profile['gtk']),
                      ('gtk-4.0/settings.ini', 'Settings', 'gtk-theme-name', profile['gtk'])]
            if require_sounds:
                checks.append(('kdeglobals', 'Sounds', 'Theme', doc['sounds']['theme']))
            mismatches = [{'file':file, 'group':group, 'key':key, 'expected':expected,
                           'actual':preference(config,file,group,key)}
                          for file,group,key,expected in checks
                          if preference(config,file,group,key) != expected]
            selection = {'profile': name, 'mismatches': mismatches}
            if mismatches:
                failures.append('Seleção do tema global não corresponde a todas as dependências.')
    return {'components': components, 'profiles': doc['profiles'], 'sounds': sounds,
            'active_selection': selection,
            'failures': failures, 'status': 'failed' if failures else 'passed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--exigir-sons', action='store_true')
    parser.add_argument('--saida', type=Path)
    args = parser.parse_args()
    report = audit(args.local, args.exigir_sons)
    output = json.dumps(report, ensure_ascii=False, indent=2)+'\n'
    if args.saida:
        args.saida.write_text(output)
    print(output, end='')
    return bool(report['failures'])


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        sys.exit(f'ERRO: {exc}')
