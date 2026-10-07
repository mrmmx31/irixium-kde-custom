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


def cursor_compat_sources(root=None):
    """Legacy libXcursor/KCM discovery uses ~/.icons on some distributions.

    An explicit root supports isolated validation without repurposing HOME.
    These are compatibility destinations, not duplicate repository sources.
    """
    root = Path(root).expanduser().absolute() if root is not None else Path.home()/'.icons'
    return [(ROOT/e['source'], root/Path(e['destination']).name)
            for e in catalog()['components'] if e['source'].startswith('cursors/')]
