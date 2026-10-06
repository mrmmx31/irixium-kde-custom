#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build reviewable Kvantum archives, never install, publish, or run theme code.

Python 3.10+, standard library only. Inputs come from a strict allowlist. The
standalone theme and the corresponding editable source are separate archives.
No font binaries, global KDE configuration, logs, Git metadata or Qt Quick patch
are included. SHA-256 checks integrity, not authorship or a digital signature.
"""
from __future__ import annotations

import argparse
import configparser
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

THEME = 'IrixClassic'
SUPPORTED_VERSION = '0.7.1'
REPO = Path(__file__).absolute().parents[2]
DATE = (1980, 1, 1, 0, 0, 0)
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_ENTRIES = 200
THEME_FILES = frozenset({'IrixClassic.kvconfig', 'IrixClassic.svg',
                         'LICENSE', 'ORIGEM.json', 'README.md'})
FONT_SUFFIXES = {'.ttf', '.otf', '.woff', '.woff2', '.pfa', '.pfb', '.bdf', '.pcf', '.ttc'}


class Failure(RuntimeError):
    """Refuse invalid inputs before publishing output files."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def no_links(path: Path) -> None:
    if not path.is_absolute() or '..' in path.parts:
        raise Failure('Caminho absoluto sem .. necessário.')
    for item in (path, *path.parents):
        if item.is_symlink():
            raise Failure('Link simbólico recusado: ' + str(item))


def safe_name(name: str) -> bool:
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        return False
    p = PurePosixPath(name)
    return (not p.is_absolute() and name == p.as_posix()
            and all(x not in ('', '.', '..', '.git', '__pycache__') for x in name.split('/'))
            and not any(ord(x) < 32 for x in name)
            and p.suffix.lower() not in FONT_SUFFIXES)


def read_file(root: Path, rel: str) -> bytes:
    if not safe_name(rel):
        raise Failure('Nome de arquivo recusado: ' + repr(rel))
    path = root / rel
    no_links(path)
    if not path.is_file() or path.stat().st_size > MAX_FILE:
        raise Failure('Arquivo ausente, irregular ou excessivo: ' + rel)
    data = path.read_bytes()
    if len(data) > MAX_FILE:
        raise Failure('Arquivo cresceu durante a leitura: ' + rel)
    # Suffix filtering is not enough for an accidentally renamed font file.
    if data[:4] in (b'OTTO', b'wOFF', b'wOF2', b'ttcf', b'\x00\x01\x00\x00'):
        raise Failure('Binário de fonte recusado: ' + rel)
    return data


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Failure('Chave JSON duplicada: ' + key)
        result[key] = value
    return result


def document(data: bytes) -> dict:
    try:
        value = json.loads(data.decode('utf-8'), object_pairs_hook=unique_pairs)
    except (UnicodeError, ValueError) as exc:
        raise Failure('JSON inválido.') from exc
    if not isinstance(value, dict):
        raise Failure('Objeto JSON necessário.')
    return value


def check_theme(files: dict[str, bytes]) -> str:
    doc = document(files['MANIFEST.json'])
    if doc.get('version') != SUPPORTED_VERSION:
        raise Failure('Esta consolidação aceita somente ' + SUPPORTED_VERSION + '; use o registro de lançamento correspondente.')
    expected = doc.get('files')
    if not isinstance(expected, dict) or set(expected) != THEME_FILES:
        raise Failure('Manifesto do tema fora da lista de arquivos revisada.')
    for name, expected_hash in expected.items():
        if not isinstance(expected_hash, str) or not re.fullmatch('[0-9a-f]{64}', expected_hash):
            raise Failure('SHA-256 inválido no manifesto: ' + name)
        if name not in files or digest(files[name]) != expected_hash:
            raise Failure('Conteúdo divergente do manifesto: ' + name)
    cfg = configparser.ConfigParser(interpolation=None, strict=True)
    cfg.optionxform = str
    try:
        cfg.read_string(files['IrixClassic.kvconfig'].decode('utf-8'))
        author = cfg['%General']['author']
    except (UnicodeError, configparser.Error, KeyError) as exc:
        raise Failure('Configuração Kvantum inválida.') from exc
    if author != 'mrmmx31':
        raise Failure('Identificação pública do mantenedor inesperada.')
    raw = files['IrixClassic.svg']
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise Failure('SVG com DTD/entidades recusado.')
    try:
        svg = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise Failure('SVG inválido.') from exc
    if svg.tag != '{http://www.w3.org/2000/svg}svg':
        raise Failure('Raiz SVG inválida.')
    for node in svg.iter():
        local = node.tag.rsplit('}', 1)[-1]
        if local in ('script', 'image', 'foreignObject', 'font', 'font-face', 'style', 'text'):
            raise Failure('SVG desta candidata não deve conter recursos incorporados: ' + local)
        for key, value in node.attrib.items():
            if key.rsplit('}', 1)[-1] in ('href', 'src') and not value.startswith('#'):
                raise Failure('Recurso externo no SVG.')
    return doc['version']


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8')


def archive(root_name: str, files: dict[str, bytes], version: str, kind: str) -> bytes:
    if '/' in root_name or not safe_name(root_name) or not files or len(files) >= MAX_ENTRIES:
        raise Failure('Estrutura de pacote inválida.')
    if 'PACOTE.json' in files or not all(safe_name(x) for x in files):
        raise Failure('Lista de arquivos inválida.')
    if sum(map(len, files.values())) > MAX_TOTAL:
        raise Failure('Pacote excede o limite de tamanho.')
    meta = {'format': 1, 'kind': kind, 'theme': THEME, 'theme_version': version,
            'channel': 'stable', 'stable_approved': True,
            'maintainer': 'mrmmx31', 'signed': False,
            'files': {name: {'sha256': digest(data), 'bytes': len(data)}
                      for name, data in sorted(files.items())}}
    data_files = dict(files)
    data_files['PACOTE.json'] = json_bytes(meta)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name, data in sorted(data_files.items()):
            zi = zipfile.ZipInfo(root_name + '/' + name, DATE)
            zi.create_system = 3
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = (stat.S_IFREG | (0o755 if name.endswith('.sh') else 0o644)) << 16
            output.writestr(zi, data, compresslevel=9)
    result = stream.getvalue()
    verify_archive(result)
    return result


def verify_archive(data: bytes) -> dict:
    if len(data) > MAX_TOTAL:
        raise Failure('ZIP excessivo.')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()
            names = [i.filename for i in infos]
            if not infos or len(infos) > MAX_ENTRIES or len(names) != len(set(names)):
                raise Failure('ZIP vazio, excessivo ou com nomes duplicados.')
            if not all(safe_name(x) and '/' in x for x in names):
                raise Failure('Caminho inseguro no ZIP.')
            roots = {x.split('/')[0] for x in names}
            if len(roots) != 1:
                raise Failure('O ZIP deve ter uma única pasta raiz.')
            root = next(iter(roots))
            if sum(i.file_size for i in infos) > MAX_TOTAL or any(i.file_size > MAX_FILE for i in infos):
                raise Failure('Conteúdo descompactado excessivo.')
            for i in infos:
                mode = (i.external_attr >> 16) & 0xffff
                if i.flag_bits & 1 or i.is_dir() or stat.S_ISLNK(mode):
                    raise Failure('ZIP com criptografia, diretório explícito ou link recusado.')
                if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                    raise Failure('Tipo de arquivo não regular no ZIP.')
            meta = document(z.read(root + '/PACOTE.json'))
            if (meta.get('format') != 1 or meta.get('theme') != THEME
                    or meta.get('theme_version') != SUPPORTED_VERSION
                    or meta.get('channel') != 'stable' or meta.get('stable_approved') is not True
                    or meta.get('kind') not in ('kvantum-theme', 'source-and-user-installer')):
                raise Failure('Identificação de pacote não suportada.')
            entries = meta.get('files')
            if not isinstance(entries, dict) or not all(safe_name(x) for x in entries):
                raise Failure('Manifesto de pacote inválido.')
            if set(names) != {root + '/' + x for x in entries} | {root + '/PACOTE.json'}:
                raise Failure('ZIP contém arquivo ausente ou não declarado.')
            extracted = {}
            for rel, m in entries.items():
                if (not isinstance(m, dict) or set(m) != {'sha256', 'bytes'}
                        or type(m['bytes']) is not int or not 0 <= m['bytes'] <= MAX_FILE
                        or not isinstance(m['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', m['sha256'])):
                    raise Failure('Registro de arquivo inválido: ' + rel)
                content = z.read(root + '/' + rel)
                if len(content) != m['bytes'] or digest(content) != m['sha256']:
                    raise Failure('Hash/tamanho divergente: ' + rel)
                if content[:4] in (b'OTTO', b'wOFF', b'wOF2', b'ttcf', b'\x00\x01\x00\x00'):
                    raise Failure('Binário de fonte no ZIP: ' + rel)
                extracted[rel] = content
            if meta['kind'] == 'kvantum-theme':
                if set(extracted) != THEME_FILES | {'MANIFEST.json', 'LEIA-ME-INSTALACAO.md'}:
                    raise Failure('Tema deve conter apenas o par Kvantum e documentação revisada.')
                check_theme(extracted)
            else:
                prefix = 'kvantum/IrixClassic/'
                check_theme({k[len(prefix):]: v for k, v in extracted.items() if k.startswith(prefix)})
            return {'kind': meta['kind'], 'theme_version': meta['theme_version'], 'files': len(infos),
                    'sha256': digest(data), 'bytes': len(data), 'integrity': 'verified', 'signed': False}
    except (zipfile.BadZipFile, KeyError, RuntimeError, OSError) as exc:
        if isinstance(exc, Failure):
            raise
        raise Failure('Não foi possível validar o ZIP: ' + str(exc)) from exc


def build_plan(repo: Path) -> tuple[dict[str, bytes], dict]:
    no_links(repo)
    base = 'kvantum/IrixClassic/'
    files = {name: read_file(repo, base + name) for name in THEME_FILES | {'MANIFEST.json'}}
    version = check_theme(files)
    policy = document(read_file(repo, 'distribuicao/LANCAMENTO.json'))
    if (policy.get('theme_version') != version or policy.get('channel') != 'stable'
            or policy.get('stable_approved') is not True):
        raise Failure('A versão estável exige um registro explícito de promoção.')
    from promotion_contract import validate
    validate(repo, policy)
    spec = document(read_file(repo, 'distribuicao/ARQUIVOS.json'))
    entries = spec.get('source_files')
    if not isinstance(entries, list) or not entries or len(entries) != len(set(entries)):
        raise Failure('Lista de código-fonte inválida/duplicada.')
    if len(entries) >= MAX_ENTRIES or not all(safe_name(p) for p in entries):
        raise Failure('Caminho recusado na lista de código-fonte.')
    required = {base + n for n in THEME_FILES | {'MANIFEST.json'}}
    required |= {'kvantum/tools/build_classic.py', 'distribuicao/ARQUIVOS.json',
                 'distribuicao/tools/build_kvantum.py', 'distribuicao/LANCAMENTO.json',
                 'tools/install_kvantum_classic.py', 'tools/theme_transaction.py'}
    if not required.issubset(entries):
        raise Failure('Código-fonte correspondente incompleto.')
    source = {}
    for rel in entries:
        if (rel.startswith(('kvantum/Irixium/', 'aurorae/', 'classic-', 'gtk/'))
                or 'qtquick_scrollbar_fix' in rel or 'system_theme_writer' in rel
                or 'corrigir-pressao' in rel or rel.endswith(('.log', '.stderr', '.env'))):
            raise Failure('Arquivo fora do escopo de distribuição: ' + rel)
        source[rel] = read_file(repo, rel)
    for rel in required & set(source):
        if rel.startswith(base) and source[rel] != files[rel[len(base):]]:
            raise Failure('Arquivo do tema mudou durante a leitura.')
    theme_doc = read_file(repo, 'distribuicao/INSTALACAO-TEMA.md')
    files['LEIA-ME-INSTALACAO.md'] = theme_doc
    source['LEIA-ME.md'] = read_file(repo, 'distribuicao/INSTALACAO-CODIGO.md')
    source['LICENSE'] = files['LICENSE']
    theme_name = f'IrixClassic-{version}-kvantum.zip'
    code_name = f'IrixClassic-{version}-codigo.zip'
    outputs = {theme_name: archive(THEME, files, version, 'kvantum-theme'),
               code_name: archive(f'IrixClassic-{version}-codigo', source, version, 'source-and-user-installer')}
    info = {'format': 1, 'theme_version': version, 'distribution_revision': policy.get('distribution_revision', 'r1'),
            'channel': 'stable', 'stable_approved': True, 'signed': False,
            'qtquick_fix_included': False, 'modern_theme_included': False,
            'sources': {k: digest(v) for k, v in sorted(source.items())},
            'packages': {n: verify_archive(b) for n, b in sorted(outputs.items())},
            'pending_acceptance': policy.get('pending_acceptance', [])}
    outputs['SHA256SUMS'] = ''.join(digest(v) + '  ' + n + '\n' for n, v in sorted(outputs.items())).encode('ascii')
    outputs['DISTRIBUICAO.json'] = json_bytes(info)
    return outputs, info


def write_outputs(output: Path, outputs: dict[str, bytes], repo: Path) -> None:
    no_links(output)
    if output == repo or repo in output.parents:
        raise Failure('Escolha uma pasta de saída fora do clone/código-fonte.')
    if output.exists():
        raise Failure('A pasta de saída já existe; escolha uma pasta nova.')
    no_links(output.parent)
    if not output.parent.is_dir():
        raise Failure('O diretório pai da saída deve existir.')
    # Finish every staged file before claiming the output directory. Nothing is
    # overwritten. If transfer fails, remove only files this invocation created.
    with tempfile.TemporaryDirectory(prefix='.irix-package-', dir=output.parent) as tmp:
        stage = Path(tmp)
        for name, data in outputs.items():
            p = stage / name
            with p.open('xb') as f:
                f.write(data); f.flush(); os.fsync(f.fileno())
            p.chmod(0o644)
        output.mkdir(mode=0o755, exist_ok=False)
        moved = []
        try:
            for name in sorted(outputs, key=lambda n: (n == 'DISTRIBUICAO.json', n)):
                os.replace(stage / name, output / name)
                moved.append(name)
        except BaseException:
            for name in moved:
                (output / name).unlink(missing_ok=True)
            try:
                output.rmdir()
            except OSError:
                pass
            raise


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--verificar', action='store_true', help='Valida e prepara em memória; não escreve.')
    modes.add_argument('--saida', type=Path, help='Pasta nova, fora do clone; seu diretório pai deve existir.')
    modes.add_argument('--verificar-zip', type=Path, help='Valida sem extrair nem executar o conteúdo.')
    a = p.parse_args(argv)
    if a.verificar_zip:
        path = a.verificar_zip.expanduser().absolute()
        no_links(path)
        if not path.is_file() or path.stat().st_size > MAX_TOTAL:
            raise Failure('Arquivo ZIP ausente/excessivo.')
        print(json.dumps(verify_archive(path.read_bytes()), indent=2, ensure_ascii=False))
        return 0
    outputs, info = build_plan(REPO)
    if a.verificar:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        print('Verificação concluída. Nenhum arquivo instalado, publicado ou alterado.', file=sys.stderr)
    else:
        write_outputs(a.saida.expanduser().absolute(), outputs, REPO)
        print('Pacotes estáveis gerados em:', a.saida)
        for n in outputs:
            print('  ' + n)
        print('Nenhuma instalação, ativação, publicação, tag ou commit foi executado.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Failure, OSError, ValueError, TypeError) as exc:
        print('ERRO:', exc, file=sys.stderr)
        sys.exit(1)
