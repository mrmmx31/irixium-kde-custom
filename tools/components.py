# SPDX-License-Identifier: GPL-3.0-or-later
"""Single inventory for installation and dependency auditing."""
import json
from pathlib import Path
from theme_transaction import Failure

ROOT = Path(__file__).resolve().parents[1]
PROFILES = frozenset(('classic', 'moderno', 'domainos'))
INDEPENDENT_SCOPE = 'Independent DomainOS four-component user install'


def catalog():
    doc = json.loads((ROOT/'components.json').read_text())
    names = set(doc.get('profiles', {}))
    independent = doc.get('scope') == INDEPENDENT_SCOPE
    if doc.get('format') != 1 or (names != PROFILES if not independent else
            doc.get('profiles') != {'classic': {}, 'moderno': {}}):
        raise Failure('Inventário incompatível.')
    if independent:
        expected = {
            ('data', 'plasma/plasmoids/org.irixclassic.domainos.panel'),
            ('data', 'plasma/plasmoids/org.irixclassic.grosview'),
            ('data', 'plasma/desktoptheme/IrixClassicDomainOS'),
            ('data', 'color-schemes/DomainOS-SR10-4.colors')}
        if {(e.get('root'), e.get('destination')) for e in doc.get('components', [])} != expected:
            raise Failure('Inventário DomainOS independente fora do escopo.')
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


def source_for(destination, *, root='data', doc=None):
    """Resolve a profile resource through the inventory, never its profile name."""
    matches = [entry for entry in (doc or catalog())['components']
               if entry['root'] == root and entry['destination'] == destination]
    if len(matches) != 1:
        raise Failure('Componente não declarado no inventário: ' + destination)
    return ROOT/matches[0]['source']


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


def decoration_sources():
    """All optional KWin packages share manifest validation with both defaults."""
    return [ROOT/e['source'] for e in catalog()['components']
            if e['root'] == 'data' and e['destination'].startswith('kwin/decorations/')]


def gtk_compat_sources(root=None):
    """GTK2 searches ~/.themes and the system theme directory, not XDG_DATA_HOME."""
    root = Path(root).expanduser().absolute() if root is not None else Path.home()/'.themes'
    return [(ROOT/e['source'], root/Path(e['destination']).name)
            for e in catalog()['components']
            if e['root'] == 'data' and e['destination'].startswith('themes/')]
