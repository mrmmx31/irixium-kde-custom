# SPDX-License-Identifier: GPL-3.0-or-later
"""Backend routing for the explicitly supported GTK4 recipe subset."""
from pathlib import Path
import backend
from gtk4_generation import generate_snapshot, verify_snapshot
from scene_contract import CONTROLS, scene
from gtk4_scene_contract import push_records
from gtk4_toggle_session import button_records
from gtk4_scrollbar_session import scrollbar_records

BUTTONS = ('push', 'toggle', 'check')
SCROLLBARS = ('scroll_h', 'scroll_v')
TRANSLATED_CONTROLS = BUTTONS + SCROLLBARS


def control_capability(identifier):
    """Return one catalog row without claiming an unavailable translation."""
    if identifier not in CONTROLS:
        raise ValueError('GTK4 catalog control is unknown: ' + repr(identifier))
    if identifier in BUTTONS:
        renderer_name = 'buttons'
    elif identifier in SCROLLBARS:
        renderer_name = 'scrollbar'
    else:
        renderer_name = None
    return {
        'id': identifier,
        'index': CONTROLS.index(identifier),
        'status': 'translated' if renderer_name else 'unavailable',
        'renderer': renderer_name,
    }


def adapter_capability():
    """Describe recipe translators, not the wider native GTK4 gallery."""
    supported = set(TRANSLATED_CONTROLS)
    return {
        'catalog_controls': list(CONTROLS),
        'catalog_count': len(CONTROLS),
        'supported_controls': list(TRANSLATED_CONTROLS),
        'supported_count': len(TRANSLATED_CONTROLS),
        'unsupported_controls': [control for control in CONTROLS
                                 if control not in supported],
        'controls': [control_capability(control) for control in CONTROLS],
        'coverage': f'{len(TRANSLATED_CONTROLS)}/{len(CONTROLS)}',
        'scope': ('DomainOS recipe translators only; the wider native GTK4 '
                  'gallery is not a DomainOS translation.'),
    }


def _visible(model):
    return scene(model, 'gtk4')


def renderer(model):
    records = _visible(model)
    identifiers = {record['id'] for record in records}
    selected = model['recipes']['gtk4']['selected_control']
    selected_id = next((record['id'] for record in records
                        if record['index'] == selected), None)
    if selected_id in SCROLLBARS:
        scrollbar_records(model)
        return 'scrollbar'
    if selected_id in BUTTONS:
        button_records(model)
        return 'buttons'
    if selected_id is not None:
        raise backend.Unavailable(
            f'GTK4: controle selecionado visível {selected_id!r} sem tradutor '
            'DomainOS; cobertura atual: 5/16 (push, toggle, check, scroll_h e '
            'scroll_v). A galeria GTK4 ampla não é uma tradução DomainOS.')
    if identifiers.intersection(BUTTONS):
        button_records(model)
        return 'buttons'
    if identifiers.intersection(SCROLLBARS):
        scrollbar_records(model)
        return 'scrollbar'
    raise backend.Unavailable(
        'GTK4: nenhum controle visível possui tradutor DomainOS; cobertura '
        'atual: 5/16 (push, toggle, check, scroll_h e scroll_v).')


def needs_toggle(model):
    return renderer(model) == 'buttons' and 'toggle' in {record['id'] for record in _visible(model)}


def needs_check(model):
    return renderer(model) == 'buttons' and 'check' in {record['id'] for record in _visible(model)}


def needs_scrollbar(model):
    return renderer(model) == 'scrollbar'


def generate(root, folder, model, source_digest, kdeglobals):
    mode = renderer(model)
    allow_toggle = needs_toggle(model)
    allow_scrollbar = mode == 'scrollbar'
    allow_check = needs_check(model)
    # The worker opens the saved normalized scene. Its byte identity can
    # differ from the user's input file (whitespace/defaults, for example).
    saved_digest = backend.sha(backend.read_file(folder / 'PROJECT.json'))
    snapshot = folder / 'gtk4-snapshot'
    receipt = generate_snapshot(root, snapshot, model, saved_digest, kdeglobals,
                                allow_toggle=allow_toggle,
                                allow_scrollbar=allow_scrollbar,
                                allow_check=allow_check)
    return dict(receipt, snapshot=str(snapshot),
                source_project_sha256=source_digest,
                preview_project_sha256=saved_digest,
                adapter_capability=adapter_capability())


def verify(root, receipt, model):
    declared_capability = receipt.get('adapter_capability')
    if (declared_capability is not None and
            declared_capability != adapter_capability()):
        raise ValueError('GTK4 adapter capability metadata mismatch')
    snapshot = Path(receipt['snapshot'])
    saved, digest = backend.project(snapshot / 'PROJECT.json')
    if saved != model or digest != receipt['preview_project_sha256']:
        raise ValueError('GTK4 preview saved scene identity mismatch')
    capability = renderer(model)
    verify_snapshot(root, snapshot, model, digest,
                    allow_toggle=needs_toggle(model),
                    allow_scrollbar=capability == 'scrollbar',
                    allow_check=needs_check(model))


def command(root, receipt, model, events, kdeglobals):
    verify(root, receipt, model)
    argv=['/usr/bin/python3', '-B', str(root / 'tools/theme-lab/preview_gtk4.py'),
            '--root', str(root), '--project', str(Path(receipt['snapshot']) / 'PROJECT.json'),
            '--snapshot', receipt['snapshot'], '--events-dir', str(events),
            '--kdeglobals', str(kdeglobals)]
    capability = renderer(model)
    if needs_toggle(model):argv+=['--private-toggle-session']
    if needs_check(model):argv+=['--private-check-session']
    if capability == 'scrollbar':argv+=['--private-scrollbar-session']
    return argv
