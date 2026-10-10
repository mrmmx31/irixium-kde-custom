#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read KDE's native Qt palette in a separate QGuiApplication, without QStyle."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys

from theme_transaction import Failure


def read(config):
    from theme_companion_bridge import native_palette_signature
    before = native_palette_signature(config)
    environment = dict(os.environ, XDG_CONFIG_HOME=str(config),
        QT_QPA_PLATFORM='offscreen', QT_QPA_PLATFORMTHEME='kde',
        XDG_CURRENT_DESKTOP='KDE', KDE_SESSION_VERSION='6')
    environment['XDG_CONFIG_DIRS'] = str(config/'kdedefaults') + ':' + (
        environment.get('XDG_CONFIG_DIRS') or '/etc/xdg')
    # App-specific overrides are not the palette selected in System Settings.
    for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'QT_STYLE_OVERRIDE',
                'KDE_COLOR_SCHEME_PATH', 'QT_PLUGIN_PATH',
                'QT_QPA_PLATFORM_PLUGIN_PATH', 'QT_QPA_GENERIC_PLUGINS'):
        environment.pop(key, None)
    output = subprocess.run(['/usr/bin/python3', '-B', str(Path(__file__).resolve()), '--read'],
        env=environment, capture_output=True, text=True, timeout=20, check=True)
    result = json.loads(output.stdout)
    if not result.get('checks') or not all(result['checks'].values()):
        raise Failure('Não foi possível ler a paleta nativa do KDE sem o Kvantum.')
    if native_palette_signature(config) != before:
        raise Failure('As cores do KDE mudaram durante a leitura; execute novamente.')
    result['source_signature'] = before
    return result


def child():
    from PyQt6.QtCore import qVersion
    from PyQt6.QtGui import QGuiApplication, QPalette
    app = QGuiApplication(['irix-native-kde-palette'])
    palette = app.palette()
    roles = [role for role in QPalette.ColorRole if role.name not in ('NoRole', 'NColorRoles')]
    values = {group: {role.name: palette.color(getattr(QPalette.ColorGroup, group), role).name()
        for role in roles} for group in ('Active', 'Inactive', 'Disabled')}
    maps = Path('/proc/self/maps').read_text()
    checks = {'kde_platform_loaded': 'KDEPlasmaPlatformTheme6.so' in maps,
        'kvantum_not_loaded': 'libkvantum.so' not in maps.lower(),
        'no_widget_palette_injection': type(app).__name__ == 'QGuiApplication'
            and 'PyQt6.QtWidgets' not in sys.modules}
    print(json.dumps({'palette': values, 'qt_version': qVersion(), 'checks': checks}))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    if sys.argv[1:] != ['--read']:
        sys.exit('Use apply_kvantum_colors.py para aplicar as cores.')
    sys.exit(child())
