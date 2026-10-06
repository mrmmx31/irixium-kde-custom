#!/usr/bin/env python3
"""Shared, read-only icon-theme inspection. Python >= 3.10; standard library.
SPDX-License-Identifier: MIT
"""
from __future__ import annotations
import configparser
import json
import os
import re
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path, PurePosixPath

IMAGE_EXT = {'.png', '.svg', '.xpm'}
CONTEXTS = {'actions':'Actions','animations':'Animations','apps':'Applications',
            'categories':'Categories','devices':'Devices','emblems':'Emblems',
            'emotes':'Emotes','mimetypes':'MimeTypes','places':'Places','status':'Status'}


def parse_index(path: Path) -> configparser.ConfigParser:
    cp = configparser.ConfigParser(interpolation=None, strict=True)
    cp.optionxform = str
    with path.open(encoding='utf-8-sig') as stream:
        cp.read_file(stream)
    if 'Icon Theme' not in cp:
        raise ValueError('index.theme sem [Icon Theme].')
    return cp


def directory_names(cp: configparser.ConfigParser) -> list[str]:
    header = cp['Icon Theme']
    return list(dict.fromkeys(p.strip() for key in ('Directories', 'ScaledDirectories')
                             for p in header.get(key, '').split(',') if p.strip()))


def safe_rel(value: str) -> bool:
    p = PurePosixPath(value)
    return bool(value) and not p.is_absolute() and '..' not in p.parts and '\\' not in value


def safe_target(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
        return True
    except (ValueError, OSError, RuntimeError):
        return False


def walk_files(root: Path):
    # Never traverse a directory symlink (whether internal or external).
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs[:]):
            p = Path(base)/name
            if p.is_symlink():
                dirs.remove(name)
                yield p, True
        for name in sorted(files):
            yield Path(base)/name, False


def png_size(path: Path) -> tuple[int, int]:
    """Check PNG signature, every chunk CRC and IHDR/IEND; no pixel decoding."""
    data = path.read_bytes()
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Não é PNG: pode ser link convertido em texto ao descompactar.')
    offset = 8
    size = None
    ended = False
    while offset + 12 <= len(data):
        count = struct.unpack('>I', data[offset:offset+4])[0]
        tag = data[offset+4:offset+8]
        end = offset + 8 + count
        if end+4 > len(data):
            raise ValueError('PNG truncado.')
        chunk = data[offset+8:end]
        crc = struct.unpack('>I', data[end:end+4])[0]
        if zlib.crc32(tag+chunk) & 0xffffffff != crc:
            raise ValueError('CRC de PNG inválido.')
        if size is None:
            if tag != b'IHDR' or count != 13:
                raise ValueError('Cabeçalho IHDR inválido.')
            size = struct.unpack('>II', chunk[:8])
            if min(size) <= 0:
                raise ValueError('PNG com dimensão inválida.')
        if tag == b'IEND':
            if count:
                raise ValueError('IEND inválido.')
            ended = True
            if end+4 != len(data):
                raise ValueError('Conteúdo inesperado após IEND.')
            break
        offset = end + 4
    if not ended or size is None:
        raise ValueError('PNG incompleto.')
    return size


def inspect_svg(path: Path) -> tuple[float, float] | None:
    data = path.read_text(encoding='utf-8-sig')
    if '<!ENTITY' in data.upper() or '<!DOCTYPE' in data.upper():
        raise ValueError('SVG com DTD/entidades: requer revisão manual.')
    tree = ET.fromstring(data)
    if tree.tag.split('}')[-1] != 'svg':
        raise ValueError('Raiz XML não é svg.')
    for elem in tree.iter():
        if elem.tag.split('}')[-1] in ('script','foreignObject'):
            raise ValueError('SVG não autocontido: script/foreignObject.')
        for name, value in elem.attrib.items():
            if name.split('}')[-1] == 'href' and not value.startswith('#'):
                raise ValueError('SVG com referência externa/embutida; revisão manual.')
    # URL paints may reference internal IDs only.
    if any(not value.strip(" '\"").startswith('#') for value in re.findall(r'url\(([^)]*)\)', data)):
        raise ValueError('SVG com url() externa.')
    vb = tree.get('viewBox')
    if vb:
        values = [float(n) for n in vb.replace(',', ' ').split()]
        if len(values) != 4 or min(values[2:]) <= 0:
            raise ValueError('viewBox inválido.')
        return values[2], values[3]
    return None


def audit(root: Path) -> dict:
    root = root.expanduser().resolve(strict=True)
    cp = parse_index(root/'index.theme')
    result = {'theme_path':str(root), 'name':cp['Icon Theme'].get('Name',''),
              'image_entries':0, 'png':0, 'svg':0, 'xpm':0, 'symlinks':0,
              'sprite_sheets':[], 'issues':[]}
    def issue(level: str, code: str, path: str, detail: str):
        result['issues'].append(dict(level=level, code=code, path=path, detail=detail))
    dirs = directory_names(cp)
    header = cp['Icon Theme']
    if not dirs:
        issue('error','empty-index','index.theme','Nenhum diretório declarado.')
    inherit = [x.strip() for x in header.get('Inherits','').split(',') if x.strip()]
    if 'hicolor' in inherit and inherit[-1] != 'hicolor':
        issue('warning','fallback-order','index.theme','hicolor precede outro tema herdado.')
    for group in ('Desktop','Toolbar','MainToolbar','Small','Panel','Dialog'):
        default, sizes = header.get(group+'Default'), header.get(group+'Sizes')
        if default and sizes and default not in sizes.split(','):
            issue('warning','default-not-in-sizes','index.theme',f'{group}: padrão {default} ausente de {sizes}.')
    for d in dirs:
        if not safe_rel(d):
            issue('error','unsafe-directory',d,'Caminho deve ser relativo e ficar dentro do tema.'); continue
        if not (root/d).is_dir() or not safe_target(root/d,root):
            issue('error','missing-directory',d,'Diretório declarado ausente/externo.'); continue
        if d not in cp:
            issue('error','missing-section',d,'Seção do diretório ausente.'); continue
        sect = cp[d]
        try:
            if sect.getint('Size') <= 0 or sect.getint('Scale',fallback=1) <= 0:
                raise ValueError('Size/Scale deve ser positivo.')
            typ = sect.get('Type','Threshold')
            if typ not in ('Fixed','Scalable','Threshold'):
                raise ValueError('Type inválido.')
            if typ == 'Scalable':
                low = sect.getint('MinSize', fallback=sect.getint('Size'))
                high = sect.getint('MaxSize', fallback=sect.getint('Size'))
                if low <= 0 or low > high:
                    raise ValueError('Intervalo MinSize/MaxSize inválido.')
        except (ValueError, TypeError) as exc:
            issue('error','invalid-size',d,str(exc))
    dir_ext = {}
    for file, dirlink in walk_files(root):
        rel = file.relative_to(root).as_posix()
        if file.is_symlink():
            result['symlinks'] += 1
            if dirlink:
                issue('error','directory-symlink',rel,'Diretório simbólico não percorrido.'); continue
            if not safe_target(file,root):
                issue('error','unsafe-or-broken-link',rel,os.readlink(file)); continue
            if Path(os.readlink(file)).is_absolute():
                issue('warning','absolute-link',rel,'Link absoluto interno; não é portátil.')
        if file.suffix.lower() not in IMAGE_EXT:
            continue
        result['image_entries'] += 1
        ext = file.suffix.lower()
        result[ext[1:]] += 1
        directory = file.parent.relative_to(root).as_posix()
        dir_ext.setdefault(directory,set()).add(ext)
        if directory not in dirs:
            issue('warning','unlisted-directory',rel,'Imagem fora de diretório declarado.'); continue
        try:
            if ext == '.png':
                width, height = png_size(file)
                sect = cp[directory] if directory in cp else {}
                if sect.get('Context') == 'Animations' and width != height:
                    result['sprite_sheets'].append(rel)
                    continue  # A sprite sheet is not a malformed square icon.
                try:
                    target = int(sect.get('Size',0))*int(sect.get('Scale',1))
                except ValueError:
                    continue
                if sect.get('Type','Threshold') == 'Fixed' and target > 0 and (width,height) != (target,target):
                    issue('error','png-size-mismatch',rel,f'{width}x{height}, esperado {target}x{target}.')
            elif ext == '.svg':
                viewbox = inspect_svg(file)
                if viewbox is None:
                    issue('warning','svg-no-viewbox',rel,'SVG sem viewBox; revisar proporcionalidade.')
                elif viewbox[0] != viewbox[1]:
                    issue('warning','svg-nonsquare',rel,f'viewBox {viewbox}; pode ser intencional.')
        except (OSError,ValueError,ET.ParseError) as exc:
            issue('error','invalid-image',rel,str(exc))
    for d, extensions in dir_ext.items():
        if d in cp and cp[d].get('Type') == 'Scalable' and '.svg' not in extensions:
            issue('warning','raster-scalable',d,'Diretório raster anunciado escalável: permitido, mas não cria detalhe vetorial.')
    result['errors'] = sum(i['level']=='error' for i in result['issues'])
    result['warnings'] = sum(i['level']=='warning' for i in result['issues'])
    return result


def write_report(report: dict, destination: Path | None):
    text = json.dumps(report, indent=2, ensure_ascii=False)+'\n'
    if destination:
        destination = destination.expanduser()
        if destination.exists():
            raise FileExistsError(f'Relatório já existe, não sobrescrito: {destination}')
        with destination.open('x',encoding='utf-8') as stream:
            stream.write(text)
    return text
