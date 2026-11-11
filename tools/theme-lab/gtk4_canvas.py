# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK4 preview canvas colors derived from effective KDE window roles."""
import hashlib
import json


def canvas_css(art, palette):
    roles = ('window', 'window-fg')
    effective = {}
    for role in roles:
        for key in art.ROLES[role]:
            if key not in palette:
                raise ValueError('GTK4 canvas missing effective KDE role: ' + key)
            art._rgb(palette[key])
            effective[key] = palette[key]
    identity = hashlib.sha256(json.dumps(effective, sort_keys=True).encode()).hexdigest()[:16]
    name = 'theme-lab-gtk4-canvas-' + identity
    css = []
    for state, index in (('', 0), (':backdrop', 1), (':disabled', 2)):
        face = palette[art.ROLES['window'][index]]
        text = palette[art.ROLES['window-fg'][index]]
        css.append('.' + name + state + ' { background-color: ' + face +
                   '; color: ' + text + '; background-image: none; }')
    return name, '\n'.join(css) + '\n'
