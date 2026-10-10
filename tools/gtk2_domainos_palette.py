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


def rc_colors(text, palette):
    if 'style "domainos-default"' not in text or 'engine "pixmap"' not in text:
        raise Failure('O RC não é a reconstrução Motif DomainOS reconhecida.')
    current, output = 'window', []
    for line in text.splitlines():
        style = re.match(r'style "domainos-([a-z-]+)"', line)
        if style: current = {'button': 'button', 'header': 'header'}.get(style[1], 'window')
        match = re.fullmatch(r'(\s*)(bg|fg|base|text)\[(NORMAL|PRELIGHT|ACTIVE|SELECTED|INSENSITIVE)\]\s*=\s*"#[0-9a-fA-F]{6}"', line)
        if match:
            indent, field, state = match.groups()
            family = 'view' if field in ('base', 'text') else 'selection' if state == 'SELECTED' else current
            token = 'ink' if field in ('fg', 'text') else 'face'
            color = art.evaluate(art.pixel_plan(family, token, disabled=state == 'INSENSITIVE'), palette)
            line = indent+field+'['+state+'] = "'+color+'"'
        output.append(line)
    return '\n'.join(output)+'\n'


def prepare_domainos(theme: Path, colors: bytes, destination: Path) -> PreparedPalette:
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
    image_plans = art.assets()
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
    adapted = rc_colors(text, palette)
    adapted = ASSET.sub(lambda match: match[1]+' = '+json.dumps('assets/'+match[2]+'.png'), adapted)
    if '../common/assets/' in adapted: raise Failure('Referência de pixmap DomainOS não reconhecida.')
    rcbytes = ('# KDE native roles; original DomainOS Motif geometry.\n'+adapted).encode()
    identity = {'format': 1, 'theme': art.NAME, 'source_rc_sha256': hashlib.sha256(raw).hexdigest(),
        'source_assets': source_hashes, 'roles': palette, 'rendered_rc_sha256': hashlib.sha256(rcbytes).hexdigest(),
        'rendered_assets': {name: hashlib.sha256(payload).hexdigest() for name, payload in rendered.items()}}
    token = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    directory = destination/token; gtkrc = directory/'gtkrc'
    files = {directory/'assets'/name: payload for name, payload in rendered.items()}
    files[gtkrc] = rcbytes
    manifest = dict(identity, id=token, asset_count=len(rendered),
        generated={str(path.relative_to(directory)): hashlib.sha256(payload).hexdigest() for path, payload in files.items()},
        limits=['Native GTK2 pixmap engine is required', 'GTK2 has no separate Backdrop state',
                'Existing GTK2 processes require native RC reparsing', 'No extracted HP artwork or font is installed'])
    files[directory/'manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()
    return PreparedPalette(directory, gtkrc, files, manifest)
