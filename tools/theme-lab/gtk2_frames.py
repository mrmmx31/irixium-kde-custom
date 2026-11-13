# SPDX-License-Identifier: GPL-3.0-or-later
"""Unlabelled GtkFrame with a content label, using a KDE window-role bevel.

This is a standalone catalogue component, not the scrollbar fitting override.
"""
import hashlib
import json
from pathlib import Path
from gtk2_buttons import geometry


def geometry_lines(recipe):
    shadow, _, font = geometry(recipe)
    return ['  xthickness = ' + str(shadow), '  ythickness = ' + str(shadow),
            '  font_name = "' + str(font) + 'px"']


def snapshots(builder, recipe, palette):
    shadow, _, _ = geometry(recipe)
    art = builder.art
    for role in ('window', 'window-fg'):
        for key in art.ROLES[role]:
            if key not in palette:
                raise ValueError('GTK2 frame missing effective role: ' + key)
    images = {}
    for variant, index in (('normal', 0), ('backdrop', 1), ('disabled', 2)):
        effective = dict(palette)
        for keys in art.ROLES.values():
            if keys[index] in palette:
                effective[keys[0]] = palette[keys[index]]
        # The Theme Lab reference is XmFrame with XmSHADOW_IN: dark
        # upper/left edges and light lower/right edges. Keep the bevel
        # direction separate from the shared frame thickness.
        mask = art.bevel(art.blank(2 * shadow + 1, 2 * shadow + 1, 'face'),
                         thickness=shadow, down=True)
        payload = builder.png(mask, 'window', effective)
        name = 'frame-' + variant + '-' + hashlib.sha256(payload).hexdigest()[:16] + '.png'
        images[variant] = name, payload
    return images


def image_rule(state, image, shadow):
    return ('    image { function = SHADOW detail = "frame" state = ' + state +
            ' file = "' + image + '" border = { ' + ', '.join([str(shadow)] * 4) +
            ' } stretch = TRUE }')


def paint_frame(builder, recipe, palette, destination):
    shadow, _, _ = geometry(recipe)
    images = snapshots(builder, recipe, palette)
    inputs = {key:palette[key] for role in ('window', 'window-fg') for key in builder.art.ROLES[role]}
    identity = hashlib.sha256(json.dumps([geometry_lines(recipe), sorted(inputs.items()),
                sorted(name for name, _ in images.values())], sort_keys=True).encode()).hexdigest()[:16]
    lines = ['# Native unlabelled GtkFrame; content label, raised window-role border.']
    for prefix, variant in (('themeLabFrame','normal'), ('themeLabBackdropFrame','backdrop'),
                            ('themeLabInsensitiveFrame','disabled')):
        style = prefix + '-' + identity
        lines += ['style "' + style + '" {'] + geometry_lines(recipe)
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            index = 2 if variant == 'disabled' or state == 'INSENSITIVE' else 1 if variant == 'backdrop' else 0
            for field, role in (('bg','window'), ('fg','window-fg')):
                rgb = builder.art._rgb(palette[builder.art.ROLES[role][index]])
                lines.append('  ' + field + '[' + state + '] = "#%02x%02x%02x"' % rgb)
        lines += ['  engine "pixmap" {']
        for state in ('NORMAL', 'PRELIGHT', 'ACTIVE', 'SELECTED', 'INSENSITIVE'):
            lines.append(image_rule(state, images['disabled' if state=='INSENSITIVE' else variant][0], shadow))
        lines += ['  }', '}']
        for suffix in ('','Content'):
            lines.append('widget "*' + prefix + suffix + '_' + identity + '" style : highest "' + style + '"')
    destination = Path(destination);destination.mkdir(parents=True,exist_ok=True)
    for name, payload in images.values():(destination/name).write_bytes(payload)
    rc=destination/'frame.gtkrc';rc.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return {'rc':str(rc),'assets':[name for name,_ in images.values()],
            'translated_control':'frame','style_id':identity,
            'padding_scope':'Native child alignment padding, not scrollbar spacing'}


def selected_fragment(recipe,state,builder,palette):
    if state not in ('normal','disabled','backdrop','hover'):
        raise ValueError('GTK2 frame: unsupported forced state: '+state)
    variant='disabled' if state=='disabled' else 'backdrop' if state=='backdrop' else 'normal'
    shadow,_,_=geometry(recipe)
    image=snapshots(builder,recipe,palette)[variant][0]
    gtk_state='INSENSITIVE' if state=='disabled' else 'PRELIGHT' if state=='hover' else 'NORMAL'
    return '\n'.join(['# Standalone unlabelled GtkFrame, not scrollbar fitting.',
                     'style "theme-lab-gtk2-frame-fragment" {']+geometry_lines(recipe)+
                    ['  engine "pixmap" {',image_rule(gtk_state,image,shadow),'  }','}',''])
