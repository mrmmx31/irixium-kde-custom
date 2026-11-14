#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Report package integrity and concrete Theme Lab family capabilities."""
from __future__ import annotations

import argparse
import ctypes.util
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import backend
from x11_session import verify_local_x11


def _relative(root: Path, name: str) -> Path:
    pure = PurePosixPath(name)
    if pure.is_absolute() or '..' in pure.parts or not pure.parts:
        raise ValueError('Manifesto contém caminho inseguro: ' + name)
    path = root.joinpath(*pure.parts)
    if path.is_symlink():
        raise ValueError('Manifesto aponta para link simbólico: ' + name)
    return path


def _integrity(root: Path) -> dict:
    source = root / 'THEME-LAB-PACKAGE.json'
    if not source.is_file():
        return {'status': 'development_tree', 'verified': False,
                'reason': 'Manifesto de pacote ausente; recursos ainda podem ser diagnosticados.'}
    data = json.loads(source.read_text(encoding='utf-8'))
    if data.get('schema') != 1 or not isinstance(data.get('files'), dict):
        raise ValueError('Manifesto de pacote incompatível.')
    failures = []
    for name, expected in data['files'].items():
        path = _relative(root, name)
        if not path.is_file():
            failures.append({'path': name, 'reason': 'missing'})
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append({'path': name, 'reason': 'sha256_mismatch'})
    return {'status': 'ok' if not failures else 'failed', 'verified': not failures,
            'checked_files': len(data['files']), 'failures': failures}


def _dependency(root: Path, record: dict) -> dict:
    resources = []
    for name in record.get('resources', []):
        try:
            path = _relative(root, name)
            resources.append({'path': name, 'available': path.is_file()})
        except ValueError as error:
            resources.append({'path': name, 'available': False, 'reason': str(error)})
    modules = [{'name': name, 'available': importlib.util.find_spec(name) is not None}
               for name in record.get('python_modules', [])]
    libraries = [{'name': name, 'available': ctypes.util.find_library(name) is not None}
                 for name in record.get('libraries', [])]
    commands = [{'name': name, 'available': bool(shutil.which(name) if '/' not in name else Path(name).is_file())}
                for name in record.get('commands', [])]
    optional = [{'name': name, 'available': shutil.which(name) is not None}
                for name in record.get('commands_optional', [])]
    system_glob = record.get('system_resource_glob')
    system_resources = sorted(str(path) for path in Path('/').glob(system_glob.lstrip('/'))) if system_glob else []
    required = resources + modules + libraries + commands
    return {'available': all(item['available'] for item in required),
            'resources': resources, 'python_modules': modules, 'libraries': libraries,
            'commands': commands, 'optional_commands': optional,
            'system_resources': system_resources, 'limitation': record.get('limitation')}


def diagnose(root: Path) -> dict:
    root = root.resolve(strict=True)
    dependencies = json.loads((root / 'tools/theme-lab/runtime-dependencies.json').read_text(encoding='utf-8'))
    if dependencies.get('schema') != 1:
        raise ValueError('Declaração de dependências incompatível.')
    capabilities = backend.probe(root)['families']
    shared = _dependency(root, dependencies['shared'])
    families = {}
    for name, record in dependencies['families'].items():
        declared = _dependency(root, record)
        capability = capabilities.get(name, {'available': False, 'reason': 'Família não consultada.'})
        families[name] = {
            'package_ready': shared['available'] and declared['available'],
            'declared': declared,
            'runtime': capability,
        }
    if os.environ.get('DISPLAY'):
        try:
            session = {'status': 'ok', **verify_local_x11()}
        except ValueError as error:
            session = {'status': 'unavailable', 'reason': str(error)}
    else:
        session = {'status': 'not_requested', 'reason': 'DISPLAY não definido.'}
    return {'status': 'ok', 'root': str(root), 'integrity': _integrity(root),
            'shared': shared, 'families': families, 'x11_session': session,
            'personal_profile_written': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=HERE.parents[1])
    args = parser.parse_args()
    try:
        result = diagnose(args.root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({'status': 'error', 'reason': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result['integrity']['status'] != 'failed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
