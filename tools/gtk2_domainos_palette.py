# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepare own SR10.4 GTK2 pixmaps with KDE colors; select/write nothing."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import re

import domainos_motif_art as art
from gtk2_palette import PreparedPalette, exported_palette
from theme_transaction import Failure, no_links

ASSET = re.compile(r'((?:overlay_)?file)\s*=\s*"\.\./common/assets/([a-z0-9-]+)\.png"')
ENTRY_FACE_FACTOR = 0.847


def png(pixels, family, palette, *, disabled=False):
    from PIL import Image
    image = Image.new('RGBA', (len(pixels[0]), len(pixels)))
    for y, row in enumerate(pixels):
        for x, token in enumerate(row):
            if token is not None:
                value = art.evaluate(art.pixel_plan(family, token, disabled=disabled), palette)
                image.putpixel((x, y), tuple(int(value[n:n+2], 16) for n in (1, 3, 5))+(255,))
    buffer = io.BytesIO(); image.save(buffer, format='PNG', optimize=True)
    return buffer.getvalue()


def repair_normal_horizontal_stepper_corners(rendered):
    """Keep the clipped horizontal normal stepper relief in its trough.

    GTK2 allocates horizontal steppers as 15x11 cells inside a 15px scrollbar;
    the horizontal trough supplies the remaining four corner pixels. Use the
    palette-rendered normal stepper cells as their source so this underlay
    stays aligned with the current KDE roles rather than fixed RGB values.
    """
    from PIL import Image

    names = (
        'scroll-trough-normal.png',
        'scrollbar-stepper-left-normal.png',
        'scrollbar-stepper-right-normal.png',
    )
    if any(name not in rendered for name in names):
        raise Failure('Assets necessários para os cantos normais GTK2 ausentes.')
    images = {}
    for name in names:
        try:
            images[name] = Image.open(io.BytesIO(rendered[name])).convert('RGBA')
        except (OSError, ValueError) as error:
            raise Failure('Asset normal inválido ao fechar cantos GTK2: '+name) from error
    trough = images['scroll-trough-normal.png']
    left = images['scrollbar-stepper-left-normal.png']
    right = images['scrollbar-stepper-right-normal.png']
    if trough.size != (24, 24) or left.size != (15, 15) or right.size != (15, 15):
        raise Failure('Dimensões inesperadas nos assets normais de canto GTK2.')
    for target, source, point in (
        ((2, 22), left, (0, 13)),
        ((3, 22), left, (1, 13)),
        ((2, 23), left, (0, 14)),
        ((21, 1), right, (14, 1)),
    ):
        trough.putpixel(target, source.getpixel(point))
    output = io.BytesIO()
    trough.save(output, format='PNG', optimize=True)
    rendered['scroll-trough-normal-horizontal.png'] = output.getvalue()


def native_cross_axis_trough(payload, orientation, palette):
    """Build role-colored five-pixel GTK2 junction caps at native thickness."""
    from PIL import Image

    if orientation not in ('horizontal', 'vertical'):
        raise Failure('Orientação inválida para asset de trilho GTK2.')
    try:
        source = Image.open(io.BytesIO(payload)).convert('RGBA')
    except (OSError, ValueError) as error:
        raise Failure('Asset de trilho GTK2 inválido.') from error
    if source.size != (24, 24):
        raise Failure('O asset-base do trilho GTK2 deve medir 24x24.')
    target = Image.new('RGBA', (24, 15) if orientation == 'horizontal' else (15, 24))
    if orientation == 'horizontal':
        target.paste(source.crop((0, 0, 24, 2)), (0, 0))
        target.paste(source.crop((0, 2, 24, 13)), (0, 2))
        target.paste(source.crop((0, 22, 24, 24)), (0, 13))
        starts, ends = ('horizontal_start_rows', 'horizontal_end_rows')
    else:
        target.paste(source.crop((0, 0, 2, 24)), (0, 0))
        target.paste(source.crop((2, 0, 13, 24)), (2, 0))
        target.paste(source.crop((22, 0, 24, 24)), (13, 0))
        starts, ends = ('vertical_start_rows', 'vertical_end_rows')
    patterns = art.gtk2_stepper_trough_junctions()
    def color(token):
        value = art.evaluate(art.pixel_plan('button', token), palette)
        return tuple(int(value[index:index+2], 16) for index in (1,3,5)) + (255,)
    if orientation == 'horizontal':
        for y, row in enumerate(patterns[starts]):
            for x, token in enumerate(row): target.putpixel((x, y), color(token))
        for y, row in enumerate(patterns[ends]):
            for x, token in enumerate(row): target.putpixel((19 + x, y), color(token))
    else:
        for y, row in enumerate(patterns[starts]):
            for x, token in enumerate(row): target.putpixel((x, y), color(token))
        for y, row in enumerate(patterns[ends]):
            for x, token in enumerate(row): target.putpixel((x, 19 + y), color(token))
    output = io.BytesIO()
    target.save(output, format='PNG', optimize=True)
    return output.getvalue()


def orient_normal_trough(rc):
    """Select measured horizontal and vertical GTK2 junction-cap assets."""
    rule = re.compile(
        r'(?m)^(\s*image \{ function = BOX  state = NORMAL  detail = "trough"  )'
        r'file = "assets/scroll-trough-normal.png"'
        r'(  border = \{ \d+, \d+, \d+, \d+ \}  stretch = TRUE \})$'
    )
    matches = list(rule.finditer(rc))
    if len(matches) != 1:
        raise Failure('Regra NORMAL do trough GTK2 ausente ou ambígua.')
    prefix, _suffix = matches[0].groups()
    horizontal = (prefix + 'orientation = HORIZONTAL  file = '
                  '"assets/scroll-trough-normal-horizontal.png"'
                  '  border = { 5, 5, 2, 2 }  stretch = TRUE }')
    vertical = (prefix + 'orientation = VERTICAL  file = '
                '"assets/scroll-trough-normal-vertical.png"'
                '  border = { 2, 2, 5, 5 }  stretch = TRUE }')
    return rule.sub(horizontal + '\n' + vertical, rc, count=1)


def repair_active_horizontal_stepper_corners(rendered):
    """Keep four clipped horizontal stepper relief pixels in a separate asset.

    GtkRange exposes horizontal steppers as 15x11 inside the 15px bar. The
    ACTIVE trough is painted first across the range, so its horizontal 9-slice
    end bands can supply the remaining corner pixels. The GTK2 pixbuf engine
    uses the same trough detail for both orientations, so keep the horizontal
    pixels in a distinct asset and leave the vertical asset untouched. Border
    widths 4/4 keep source columns 0..3 and 20..23 at native size. Copy the
    corner shades from the palette-rendered normal stepper cells, never fixed
    RGBs.
    """
    from PIL import Image

    names = (
        'scroll-trough-pressed-horizontal.png',
        'scrollbar-stepper-left-normal.png',
        'scrollbar-stepper-right-normal.png',
    )
    if any(name not in rendered for name in names):
        raise Failure('Assets necessários para fechar os cantos GTK2 ausentes.')
    images = {}
    for name in names:
        try:
            image = Image.open(io.BytesIO(rendered[name])).convert('RGBA')
        except (OSError, ValueError) as error:
            raise Failure('Asset inválido ao fechar cantos GTK2: '+name) from error
        images[name] = image
    trough = images['scroll-trough-pressed-horizontal.png']
    left = images['scrollbar-stepper-left-normal.png']
    right = images['scrollbar-stepper-right-normal.png']
    if trough.size != (24, 24) or left.size != (15, 15) or right.size != (15, 15):
        raise Failure('Dimensões inesperadas nos assets de canto GTK2.')
    for target, source, point in (
        ((2, 22), left, (0, 13)),
        ((3, 22), left, (1, 13)),
        ((2, 23), left, (0, 14)),
        ((21, 1), right, (14, 1)),
    ):
        trough.putpixel(target, source.getpixel(point))
    output = io.BytesIO()
    trough.save(output, format='PNG', optimize=True)
    rendered['scroll-trough-pressed-horizontal.png'] = output.getvalue()


def repair_active_vertical_trough_corners(rendered):
    """Compose exposed active vertical trough corners from stepper artwork.

    GTK2 paints a 15px-wide stepper cell in a 15px vertical bar, with a
    2px-recessed trough underneath. The active trough's 9-slice exposes three
    upper corner pixels from the up-stepper and one lower corner from the
    down-stepper. Copy only those clipped context pixels from role-rendered
    assets. Leave the arrow cells unchanged: the SR10.4 held transition swaps
    exactly 53 light/shadow pixels inside the down glyph.
    """
    from PIL import Image

    names = (
        'scroll-trough-pressed-vertical.png',
        'scrollbar-stepper-up-normal.png',
        'scrollbar-stepper-down-normal.png',
    )
    if any(name not in rendered for name in names):
        raise Failure('Assets necessários para fechar os cantos verticais GTK2 ausentes.')
    images = {}
    for name in names:
        try:
            image = Image.open(io.BytesIO(rendered[name])).convert('RGBA')
        except (OSError, ValueError) as error:
            raise Failure('Asset inválido ao fechar cantos verticais GTK2: '+name) from error
        images[name] = image
    trough = images['scroll-trough-pressed-vertical.png']
    up = images['scrollbar-stepper-up-normal.png']
    down = images['scrollbar-stepper-down-normal.png']
    if (trough.size != (24, 24) or up.size != (15, 15)
            or down.size != (15, 15)):
        raise Failure('Dimensões inesperadas nos assets verticais GTK2.')
    for target, source in (
        ((22, 2), (13, 0)),
        ((23, 2), (14, 0)),
        ((22, 3), (13, 1)),
    ):
        trough.putpixel(target, up.getpixel(source))
    # Preserve the down-stepper normal/pressed delta as the native 53-pixel
    # glyph relief swap. R434's live SR10.4 hold changed pixels only inside
    # this glyph; applying a trough-face band to row 0 of the pressed cell
    # creates eleven extra transitions outside the arrow.
    trough.putpixel((1, 21), down.getpixel((1, 14)))
    output = io.BytesIO()
    trough.save(output, format='PNG', optimize=True)
    rendered['scroll-trough-pressed-vertical.png'] = output.getvalue()


def orient_active_trough(rc):
    """Select independent ACTIVE trough art for GTK2's inferred orientation."""
    rule = re.compile(
        r'(?m)^(\s*image \{ function = BOX  state = ACTIVE  detail = "trough"  )'
        r'file = "assets/scroll-trough-pressed.png"'
        r'(  border = \{ \d+, \d+, \d+, \d+ \}  stretch = TRUE \})$'
    )
    matches = list(rule.finditer(rc))
    if len(matches) != 1:
        raise Failure('Regra ACTIVE do trough GTK2 ausente ou ambígua.')
    prefix, _suffix = matches[0].groups()
    horizontal = (prefix + 'orientation = HORIZONTAL  file = '
                  '"assets/scroll-trough-pressed-horizontal.png"'
                  '  border = { 4, 4, 2, 2 }  stretch = TRUE }')
    vertical = (prefix + 'orientation = VERTICAL  file = '
                '"assets/scroll-trough-pressed-vertical.png"'
                '  border = { 2, 2, 4, 4 }  stretch = TRUE }')
    return rule.sub(horizontal + '\n' + vertical, rc, count=1)


def repair_insensitive_stepper_corners(rendered):
    """Compose clipped INSENSITIVE stepper corners from KDE-role assets.

    GTK2 paints a 15x11 stepper inside a 15px scrollbar. The remaining four
    pixels are supplied by the insensitive trough. Keep separate horizontal
    and vertical underlays so their relief corners come from the matching
    directional, disabled stepper cells. Every source is already rendered
    from the selected KDE roles; no static color is introduced.
    """
    from PIL import Image

    mappings = {
        'scroll-trough-disabled-horizontal.png': (
            ('scrollbar-stepper-left-disabled.png', (2, 22), (0, 13)),
            ('scrollbar-stepper-left-disabled.png', (3, 22), (1, 13)),
            ('scrollbar-stepper-left-disabled.png', (2, 23), (0, 14)),
            ('scrollbar-stepper-right-disabled.png', (21, 1), (14, 1)),
        ),
        'scroll-trough-disabled-vertical.png': (
            ('scrollbar-stepper-up-disabled.png', (22, 2), (13, 0)),
            ('scrollbar-stepper-up-disabled.png', (23, 2), (14, 0)),
            ('scrollbar-stepper-up-disabled.png', (22, 3), (13, 1)),
            ('scrollbar-stepper-down-disabled.png', (1, 21), (1, 14)),
        ),
    }
    for trough_name, patches in mappings.items():
        required = {trough_name, *(name for name, _, _ in patches)}
        if not required.issubset(rendered):
            raise Failure('Assets necessários para fechar cantos INSENSITIVE GTK2 ausentes: '
                          + ', '.join(sorted(required - rendered.keys())))
        images = {}
        for name in required:
            try:
                images[name] = Image.open(io.BytesIO(rendered[name])).convert('RGBA')
            except (OSError, ValueError) as error:
                raise Failure('Asset INSENSITIVE GTK2 inválido: ' + name) from error
        trough = images[trough_name]
        if trough.size != (24, 24) or any(images[name].size != (15, 15)
                                          for name in required - {trough_name}):
            raise Failure('Dimensões inesperadas nos assets INSENSITIVE GTK2.')
        for source_name, target, source in patches:
            trough.putpixel(target, images[source_name].getpixel(source))
        output = io.BytesIO()
        trough.save(output, format='PNG', optimize=True)
        rendered[trough_name] = output.getvalue()


def orient_insensitive_trough(rc):
    """Use independently composed INSENSITIVE troughs for each GTK2 axis."""
    rule = re.compile(
        r'(?m)^(\s*image \{ function = BOX  state = INSENSITIVE  detail = "trough"  )'
        r'file = "assets/scroll-trough-disabled.png"'
        r'(  border = \{ \d+, \d+, \d+, \d+ \}  stretch = TRUE \})$'
    )
    matches = list(rule.finditer(rc))
    if len(matches) != 1:
        raise Failure('Regra INSENSITIVE do trough GTK2 ausente ou ambígua.')
    prefix, _suffix = matches[0].groups()
    horizontal = (prefix + 'orientation = HORIZONTAL  file = '
                  '"assets/scroll-trough-disabled-horizontal.png"'
                  '  border = { 4, 4, 2, 2 }  stretch = TRUE }')
    vertical = (prefix + 'orientation = VERTICAL  file = '
                '"assets/scroll-trough-disabled-vertical.png"'
                '  border = { 2, 2, 4, 4 }  stretch = TRUE }')
    return rule.sub(horizontal + '\n' + vertical, rc, count=1)


def same_pixels(original, expected):
    """PNG encoders may differ by platform; authorize the original pixels.

    The published manifest still checks the source bytes. The independent art
    check compares decoded dimensions and RGBA values so a different zlib or
    Pillow version cannot make an unchanged theme fail on another computer.
    """
    from PIL import Image
    try:
        with Image.open(io.BytesIO(expected)) as reference:
            size, values = reference.size, reference.convert('RGBA').tobytes()
        with Image.open(io.BytesIO(original)) as actual:
            if actual.size != size or actual.format != 'PNG': return False
            return actual.convert('RGBA').tobytes() == values
    except (OSError, ValueError):
        return False


def iconview_selected_colors(palette):
    """Use KDE's active selection face and ink for selected IconView cells.

    The source VUE label uses reverse video, but this GTK theme must preserve
    the selected scheme's semantic Selection roles rather than pinning the
    historical black/white pixels or deriving ad-hoc View colors.
    """
    face = art.evaluate(art.pixel_plan('selection', 'face'), palette)
    ink = art.evaluate(art.pixel_plan('selection', 'ink'), palette)
    return face, ink


def rc_colors(text, palette, *, engine_name='domainos-pixbuf'):
    if ('style "domainos-default"' not in text
            or not re.search(r'(?m)^\s*engine "(?:pixmap|domainos-pixbuf)"\s*\{', text)):
        raise Failure('O RC não é a reconstrução Motif DomainOS reconhecida.')
    if engine_name not in ('pixmap', 'domainos-pixbuf'):
        raise Failure('Engine GTK2 DomainOS inválido.')
    current, current_style, output = 'window', 'default', []
    for line in text.splitlines():
        style = re.match(r'style "domainos-([a-z-]+)"', line)
        if style:
            current_style = style[1]
            current = {'button': 'button', 'header': 'header',
                       'iconview': 'view'}.get(current_style, 'window')
        match = re.fullmatch(r'(\s*)(bg|fg|base|text)\[(NORMAL|PRELIGHT|ACTIVE|SELECTED|INSENSITIVE)\]\s*=\s*"#[0-9a-fA-F]{6}"', line)
        if match:
            indent, field, state = match.groups()
            # GtkIconView's selected cell renderers consume SELECTED palette
            # entries, while the view surface uses View roles in every other
            # GtkStateType. Its rubberband falls back to base[SELECTED].
            if current_style == 'iconview' and state == 'SELECTED':
                # Keep this GTK selection attached to the active semantic
                # KDE Selection roles; historical reverse video is evidence,
                # not permission to pin or synthesize a final color pair.
                selected_face, selected_ink = iconview_selected_colors(palette)
                color = selected_ink if field in ('fg', 'text') else selected_face
            elif current_style == 'iconview':
                family = 'view'
                token = 'ink' if field in ('fg', 'text') else 'face'
                color = art.evaluate(art.pixel_plan(family, token, disabled=state == 'INSENSITIVE'), palette)
            else:
                family = 'view' if field in ('base', 'text') else 'selection' if state == 'SELECTED' else current
                token = 'ink' if field in ('fg', 'text') else 'face'
                color = art.evaluate(art.pixel_plan(family, token, disabled=state == 'INSENSITIVE'), palette)
            line = indent+field+'['+state+'] = "'+color+'"'
        output.append(line)
    # GtkTooltip is a separate KDE color set. The historical RC has no
    # dedicated tooltip style, so inheriting domainos-default would silently
    # paint hints with Window colors even though GTKConfig exports Tooltip
    # roles. Keep the style in the generated RC and bind it at highest
    # precedence, just like the native GTK2 tooltip widget tree.
    # In the SR10.4 VUE File Finder, secondaryColorSetId 5 selects the active
    # CoralReef blue. The repository's palette provenance maps VUE set 5 to
    # KDE Header/Selection; the live entry face is a 0.847 shade of that role.
    # Recompute from the current role on each palette export, never from a
    # captured final RGB.
    entry_face = art.tone(
        palette[art.ROLES['header'][0]], 1.0-ENTRY_FACE_FACTOR, '#000000')
    output.extend([
        '',
        # Native SR10.4 text selection in the VUE File Finder is reverse video:
        # the selected glyph uses the field face as its ink and the field ink
        # as its face. Bind only GtkEntry (including input subclasses); lists,
        # menus and other selected widgets continue using the KDE Selection
        # roles above. Both inverted colors come from the active KDE view roles.
        'style "domainos-entry" = "domainos-default" {',
        '  base[NORMAL] = "'+entry_face+'"',
        '  base[PRELIGHT] = "'+entry_face+'"',
        '  base[ACTIVE] = "'+entry_face+'"',
        '  bg[SELECTED] = "'+palette[art.ROLES['view-fg'][0]]+'"',
        '  fg[SELECTED] = "'+palette[art.ROLES['view'][0]]+'"',
        '  base[SELECTED] = "'+palette[art.ROLES['view-fg'][0]]+'"',
        '  text[SELECTED] = "'+palette[art.ROLES['view'][0]]+'"',
        '}',
        'widget_class "*GtkEntry" style : highest "domainos-entry"',
        '',
        'style "domainos-tooltip" {',
        '  bg[NORMAL] = "'+palette['tooltip_background_breeze']+'"',
        '  fg[NORMAL] = "'+palette['tooltip_text_breeze']+'"',
        '}',
        'widget "*gtk-tooltip*" style : highest "domainos-tooltip"',
    ])
    rendered = '\n'.join(output)+'\n'
    engine_rule = re.compile(r'(?m)^(\s*)engine "(?:pixmap|domainos-pixbuf)"(\s*\{)')
    if len(engine_rule.findall(rendered)) != 1:
        raise Failure('O RC precisa conter exatamente uma declaração de engine GTK2.')
    rendered = engine_rule.sub(lambda match: match[1]+'engine "'+engine_name+'"'+match[2],
                               rendered, count=1)
    # GTK2 can retain a pixmap-engine style for an already-open widget when
    # the RC is reparsed under the same style name. Give each effective
    # palette a deterministic style namespace so a native RC reload builds
    # fresh pixmap styles. The suffix is derived from current KDE roles, not
    # from a fixed color or per-user path.
    palette_id = hashlib.sha256(
        json.dumps(palette, sort_keys=True, separators=(',', ':')).encode('utf-8')
    ).hexdigest()[:10]
    rendered = re.sub(
        r'\bdomainos-(?!pixbuf\b)([a-z-]+)\b',
        lambda match: 'domainos-'+match.group(1)+'-'+palette_id,
        rendered,
    )
    return rendered


def prepare_domainos(theme: Path, colors: bytes, destination: Path, *,
                     engine_name='pixmap') -> PreparedPalette:
    theme, destination = Path(theme), Path(destination)
    no_links(theme); no_links(destination)
    rc = theme/'gtk-2.0/gtkrc'; manifest_file = theme/'MANIFEST.json'
    no_links(rc); no_links(manifest_file)
    raw = rc.read_bytes()
    if len(raw) > 256*1024: raise Failure('RC DomainOS inesperadamente grande.')
    try:
        source_manifest = json.loads(manifest_file.read_text())['files']
        text = raw.decode('utf-8')
    except (ValueError, KeyError, UnicodeError) as error:
        raise Failure('Origem GTK DomainOS inválida.') from error
    if source_manifest.get('gtk-2.0/gtkrc') != hashlib.sha256(raw).hexdigest():
        raise Failure('RC DomainOS editado após geração.')
    palette = exported_palette(colors)
    required = {names[state] for names in art.ROLES.values() for state in (0, 2)}
    missing = sorted(required.difference(palette))
    invalid = sorted(name for name in required if name in palette and
                     not re.fullmatch(r'#[0-9a-fA-F]{6}', str(palette[name])))
    if missing or invalid:
        detail = ', '.join(missing or invalid)
        raise Failure('Exportação KDE sem papéis nativos completos para GTK2 DomainOS: '+detail)
    image_plans = art.gtk2_assets()
    rendered, source_hashes = {}, {}
    names = {match[2] for match in ASSET.finditer(text)}
    if not names: raise Failure('RC DomainOS sem fechamento de pixmaps.')
    for name in sorted(names):
        if name not in image_plans: raise Failure('Pixmap DomainOS desconhecido: '+name)
        path = theme/'common/assets'/(name+'.png'); no_links(path)
        original = path.read_bytes()
        relative = str(path.relative_to(theme))
        if source_manifest.get(relative) != hashlib.sha256(original).hexdigest():
            raise Failure('Pixmap DomainOS editado após geração: '+name)
        pixels, family, _border = image_plans[name]
        expected = png(pixels, family, art.DEFAULT, disabled=name.endswith('-disabled'))
        if not same_pixels(original, expected):
            raise Failure('Pixmap não pertence ao desenho original DomainOS: '+name)
        source_hashes[name+'.png'] = hashlib.sha256(original).hexdigest()
        rendered[name+'.png'] = png(pixels, family, palette, disabled=name.endswith('-disabled'))
    rendered['scroll-trough-normal-horizontal.png'] = rendered['scroll-trough-normal.png']
    repair_normal_horizontal_stepper_corners(rendered)
    rendered['scroll-trough-normal-horizontal.png'] = native_cross_axis_trough(
        rendered['scroll-trough-normal-horizontal.png'], 'horizontal', palette)
    rendered['scroll-trough-normal-vertical.png'] = native_cross_axis_trough(
        rendered['scroll-trough-normal.png'], 'vertical', palette)
    rendered['scroll-trough-pressed-horizontal.png'] = rendered['scroll-trough-pressed.png']
    repair_active_horizontal_stepper_corners(rendered)
    rendered['scroll-trough-pressed-vertical.png'] = rendered['scroll-trough-pressed.png']
    repair_active_vertical_trough_corners(rendered)
    rendered['scroll-trough-disabled-horizontal.png'] = rendered['scroll-trough-disabled.png']
    rendered['scroll-trough-disabled-vertical.png'] = rendered['scroll-trough-disabled.png']
    repair_insensitive_stepper_corners(rendered)
    adapted = rc_colors(text, palette, engine_name=engine_name)
    adapted = ASSET.sub(lambda match: match[1]+' = '+json.dumps('assets/'+match[2]+'.png'), adapted)
    adapted = orient_normal_trough(adapted)
    adapted = orient_active_trough(adapted)
    adapted = orient_insensitive_trough(adapted)
    if '../common/assets/' in adapted: raise Failure('Referência de pixmap DomainOS não reconhecida.')
    rcbytes = ('# KDE native roles; original DomainOS Motif geometry.\n'+adapted).encode()
    identity = {'format': 1, 'theme': art.NAME, 'source_rc_sha256': hashlib.sha256(raw).hexdigest(),
        'source_assets': source_hashes, 'roles': palette, 'gtk2_engine': engine_name,
        'rendered_rc_sha256': hashlib.sha256(rcbytes).hexdigest(),
        'rendered_assets': {name: hashlib.sha256(payload).hexdigest() for name, payload in rendered.items()}}
    token = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    directory = destination/token; gtkrc = directory/'gtkrc'
    files = {directory/'assets'/name: payload for name, payload in rendered.items()}
    files[gtkrc] = rcbytes
    manifest = dict(identity, id=token, asset_count=len(rendered),
        generated={str(path.relative_to(directory)): hashlib.sha256(payload).hexdigest() for path, payload in files.items()},
        limits=[f'GTK2 {engine_name} engine is required', 'GTK2 has no separate Backdrop state',
                'Existing GTK2 processes require native RC reparsing', 'No extracted HP artwork or font is installed'])
    files[directory/'manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()
    return PreparedPalette(directory, gtkrc, files, manifest)
