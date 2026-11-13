# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK4 scrollbar proposal snapshot; never installs or edits profiles."""
import json
from pathlib import Path

import backend
from gtk4_canvas import canvas_css
from gtk4_scrollbars import write_scrollbar_css


def generate_snapshot(root, folder, model, project_hash, kdeglobals):
    from gtk4_scrollbar_session import scrollbar_records
    scrollbar_records(model)
    recipe = model['recipes']['gtk4']
    builder = backend.load_builder(root)
    for key in backend.DEFAULT_ROLES:
        if recipe['palette'][key] not in backend.ROLE_FAMILIES:
            raise backend.Unavailable('GTK4 role unavailable: ' + recipe['palette'][key])
    _current, selected = backend.selected_palette(model, kdeglobals, root)
    colors, origin = backend.native_roles(root, Path(selected['path']), builder.art,
                                           selected['sha256'])
    folder = backend.private_output(folder, root)
    canvas_class, canvas_source = canvas_css(builder.art, colors)
    with backend.recipe_rules(builder, recipe['palette']):
        generated = write_scrollbar_css(builder, recipe, colors,
                                         folder / 'gtk4-scrollbar-assets')
    with Path(generated['css']).open('a',encoding='utf-8') as stream:
        stream.write(canvas_source)
    backend.write_json(folder / 'PROJECT.json', model)
    backend.write_json(folder / 'GTK4-NATIVE-COLORS.json', {'colors': colors,
                                                             'origin': origin})
    artifacts = {str(path.relative_to(folder)): backend.sha(backend.read_file(path))
                 for path in sorted(folder.rglob('*')) if path.is_file()}
    receipt = dict(generated, family='gtk4', status='partially_generated',
                   canvas_class=canvas_class,
                   project_sha256=project_hash,
                   recipe_sha256=backend.sha(json.dumps(recipe, sort_keys=True).encode()),
                   translated_controls=['scroll_h', 'scroll_v'], recipe_applied=False,
                   scope='Private GtkScrollbar trough/slider CSS snapshot; worker application verified in detached and coupled previews',
                   selected_scheme=selected, palette=origin,
                   palette_inputs=[selected, origin['helper'], origin['helper_source']],
                   artifacts=artifacts, host_changed=False, picked_used=False)
    if not backend.palette_inputs_current(receipt):
        raise backend.Unavailable('GTK4 palette changed during scrollbar generation')
    backend.write_json(folder / 'GTK4-SCROLLBAR-PROPOSAL.json', receipt)
    return receipt


def verify_snapshot(root, folder, model, project_hash):
    from gtk4_scrollbar_session import scrollbar_records
    scrollbar_records(model)
    folder = backend.private_output(Path(folder).absolute(), root)
    receipt = json.loads(backend.read_file(folder / 'GTK4-SCROLLBAR-PROPOSAL.json'))
    expected = backend.sha(json.dumps(model['recipes']['gtk4'], sort_keys=True).encode())
    if (receipt.get('family') != 'gtk4' or receipt.get('project_sha256') != project_hash or
            receipt.get('recipe_sha256') != expected or
            receipt.get('translated_controls') != ['scroll_h', 'scroll_v']):
        raise ValueError('GTK4 scrollbar proposal identity/capability mismatch')
    css=Path(receipt.get('css',''))
    if not css.is_absolute() or not css.is_relative_to(folder) or str(css.relative_to(folder)) not in receipt.get('artifacts',{}):
        raise ValueError('GTK4 scrollbar CSS is not a verified snapshot artifact')
    if json.loads(backend.read_file(folder / 'PROJECT.json')) != model:
        raise ValueError('GTK4 scrollbar proposal project mismatch')
    artifacts = receipt.get('artifacts')
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError('GTK4 scrollbar artifact manifest missing')
    for name, digest in artifacts.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('GTK4 scrollbar artifact outside snapshot')
        target = folder / path
        if any(parent.is_symlink() for parent in (target, *target.parents)):
            raise ValueError('GTK4 scrollbar artifact cannot traverse links')
        if backend.sha(backend.read_file(target)) != digest:
            raise ValueError('GTK4 scrollbar artifact hash mismatch: ' + name)
    if not backend.palette_inputs_current(receipt):
        raise ValueError('GTK4 scrollbar palette inputs are stale')
    return receipt, json.loads(backend.read_file(folder / 'GTK4-NATIVE-COLORS.json'))['colors']
