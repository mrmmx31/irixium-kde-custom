# SPDX-License-Identifier: GPL-3.0-or-later
"""Single inventory for installation and dependency auditing."""
import json
from pathlib import Path
from theme_transaction import Failure

ROOT = Path(__file__).resolve().parents[1]


def catalog():
    doc = json.loads((ROOT/'components.json').read_text())
    if doc.get('format') != 1 or set(doc['profiles']) != {'classic', 'moderno'}:
        raise Failure('Inventário incompatível.')
    seen = set()
    for entry in doc['components']:
        if entry['root'] not in ('data', 'config'):
            raise Failure('Raiz de instalação inválida.')
        for key in ('source', 'destination'):
            path = Path(entry[key])
            if path.is_absolute() or '..' in path.parts or not path.parts:
                raise Failure('Caminho inválido no inventário.')
        dest = (entry['root'], entry['destination'])
        if dest in seen:
            raise Failure('Componente duplicado.')
        seen.add(dest)
    return doc


def sources(data, config):
    bases = {'data': data, 'config': config}
    return [(ROOT/e['source'], bases[e['root']]/e['destination'])
            for e in catalog()['components']]
