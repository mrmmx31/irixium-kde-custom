# SPDX-License-Identifier: GPL-3.0-or-later
"""Process-local GTK2 preview canvas colors from effective KDE window roles."""


def canvas_rc(art, palette):
    lines = ['# Canvas uses effective KDE window roles; no reference RGB fallback.']
    for role in ('window', 'window-fg'):
        for name in art.ROLES[role]:
            if name not in palette:
                raise ValueError('GTK2 canvas missing effective role: ' + name)
    for name, disabled in (('theme-lab-gtk2-canvas', False), ('theme-lab-gtk2-canvas-insensitive', True)):
        lines.append('style "' + name + '" {')
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            index = 2 if disabled or state == 'INSENSITIVE' else 0
            for field, role in (('bg', 'window'), ('fg', 'window-fg')):
                rgb = art._rgb(palette[art.ROLES[role][index]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines.append('}')
    lines += ['widget "*themeLabCanvasWindow" style : highest "theme-lab-gtk2-canvas"',
              'widget "*themeLabCanvas" style : highest "theme-lab-gtk2-canvas"',
              'widget "*themeLabCanvasInsensitiveWindow" style : highest "theme-lab-gtk2-canvas-insensitive"',
              'widget "*themeLabCanvasInsensitive" style : highest "theme-lab-gtk2-canvas-insensitive"', '']
    return '\n'.join(lines)


def canvas_sensitivity(window, _property=None):
    """GtkWindow draws its background with NORMAL even when insensitive.

    Select its disabled window-role style by name; no RGB or stored child
    reference. A persistent Window/Plug can therefore replace its content.
    """
    disabled = not window.get_sensitive()
    window.set_name('themeLabCanvasInsensitiveWindow' if disabled else 'themeLabCanvasWindow')
    child = window.get_child()
    if child is not None:
        child.set_name('themeLabCanvasInsensitive' if disabled else 'themeLabCanvas')
    window.queue_draw()
