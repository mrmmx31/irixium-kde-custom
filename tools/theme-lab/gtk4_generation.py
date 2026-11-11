# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK4 push snapshots with palette and artifact provenance."""
import json
from pathlib import Path
import backend
from gtk4_buttons import write_button_css
from gtk4_canvas import canvas_css
from gtk4_scene_contract import push_records


def _validate_capabilities(allow_toggle, allow_scrollbar, allow_check):
    if any(type(value) is not bool for value in (allow_toggle, allow_scrollbar, allow_check)):
        raise ValueError('GTK4 toggle capability must be explicit boolean')
    if allow_scrollbar and (allow_toggle or allow_check):
        raise ValueError('GTK4 scrollbar and button capabilities are mutually exclusive')


def generate_snapshot(root, folder, model, project_hash, kdeglobals, *,
                      allow_toggle=False, allow_scrollbar=False, allow_check=False):
    _validate_capabilities(allow_toggle, allow_scrollbar, allow_check)
    if allow_scrollbar:
        from gtk4_scrollbar_snapshot import generate_snapshot as generate_scrollbar
        return generate_scrollbar(root, folder, model, project_hash, kdeglobals)
    if allow_toggle or allow_check:
        from gtk4_toggle_session import button_records
        button_records(model)
    else:
        if not push_records(model):
            raise ValueError('GTK4 push preview requires a visible push control')
    recipe = model['recipes']['gtk4']
    builder = backend.load_builder(root)
    for key in backend.DEFAULT_ROLES:
        if recipe['palette'][key] not in backend.ROLE_FAMILIES:
            raise backend.Unavailable('GTK4 role unavailable: ' + recipe['palette'][key])
    _current, selected = backend.selected_palette(model, kdeglobals, root)
    colors, origin = backend.native_roles(root, Path(selected['path']), builder.art, selected['sha256'])
    origin = dict(origin, selection_scope='Private GTK4 recipe only; no host/profile scheme change')
    folder = backend.private_output(folder, root)
    canvas_class, canvas_source = canvas_css(builder.art, colors)
    with backend.recipe_rules(builder, recipe['palette']):
        base = write_button_css(builder, recipe, colors, folder / 'gtk4-assets')
        if allow_toggle:
            from gtk4_toggles import write_toggle_css
            toggle = write_toggle_css(builder, recipe, colors, folder / 'gtk4-toggle-assets', base)
        else:
            toggle = None
        if allow_check:
            from gtk4_checks import write_check_css
            check = write_check_css(builder, recipe, colors, folder / 'gtk4-check-assets')
        else:
            check = None
        if toggle or check:
            imported = [toggle['css'] if toggle else base['css']]
            if check: imported.append(check['css'])
            combined = folder / 'gtk4-buttons.css'
            combined.write_text(''.join('@import url("' + Path(css).as_uri() + '");\n' for css in imported),
                                encoding='utf-8')
            generated = dict(toggle or base, css=str(combined),
                             push_style_class=base['style_class'],
                             private_toggle_session=allow_toggle,
                             private_check_session=allow_check)
            if check:
                generated['check_style_class'] = check['style_class']
                generated['check_css'] = check['css']
        else:
            generated = base
    generated.setdefault('private_toggle_session', allow_toggle)
    generated.setdefault('private_check_session', allow_check)
    with Path(generated['css']).open('a', encoding='utf-8') as css:
        css.write(canvas_source)
    backend.write_json(folder / 'PROJECT.json', model)
    backend.write_json(folder / 'GTK4-NATIVE-COLORS.json', {'colors':colors,'origin':origin})
    manifest = {str(p.relative_to(folder)):backend.sha(backend.read_file(p))
                for p in sorted(folder.rglob('*')) if p.is_file()}
    translated = ([record['id'] for record in button_records(model)]
                  if allow_toggle or allow_check else ['push'])
    receipt = dict(generated, family='gtk4', status='partially_generated',
                   project_sha256=project_hash, canvas_class=canvas_class,
                   recipe_sha256=backend.sha(json.dumps(recipe,sort_keys=True).encode()),
                   recipe_applied=False,
                   scope='Private GTK4 button recipe snapshot; native application verified separately',
                   selected_scheme=selected, palette=origin,
                   palette_inputs=[selected,origin['helper'],origin['helper_source']],
                   translated_controls=translated,
                   artifacts=manifest, host_changed=False, picked_used=False)
    if not backend.palette_inputs_current(receipt):
        raise backend.Unavailable('GTK4 palette changed during generation')
    backend.write_json(folder / 'GTK4-PROPOSAL.json', receipt)
    return receipt


def verify_snapshot(root, folder, model, project_hash, *,
                    allow_toggle=False, allow_scrollbar=False, allow_check=False):
    _validate_capabilities(allow_toggle, allow_scrollbar, allow_check)
    if allow_scrollbar:
        from gtk4_scrollbar_snapshot import verify_snapshot as verify_scrollbar
        return verify_scrollbar(root, folder, model, project_hash)
    if allow_toggle or allow_check:
        from gtk4_toggle_session import button_records
        button_records(model)
    else:
        if not push_records(model):
            raise ValueError('GTK4 push preview requires a visible push control')
    folder = backend.private_output(Path(folder).absolute(), root)
    receipt = json.loads(backend.read_file(folder / 'GTK4-PROPOSAL.json'))
    if receipt.get('family') != 'gtk4' or receipt.get('project_sha256') != project_hash:
        raise ValueError('GTK4 snapshot/project identity mismatch')
    expected = backend.sha(json.dumps(model['recipes']['gtk4'],sort_keys=True).encode())
    if receipt.get('recipe_sha256') != expected:
        raise ValueError('GTK4 snapshot recipe mismatch')
    if receipt.get('private_toggle_session', False) is not allow_toggle:
        raise ValueError('GTK4 snapshot renderer capability mismatch')
    if receipt.get('private_check_session', False) is not allow_check:
        raise ValueError('GTK4 check snapshot capability mismatch')
    expected_controls = ([record['id'] for record in button_records(model)]
                         if allow_toggle or allow_check else ['push'])
    if receipt.get('translated_controls') != expected_controls:
        raise ValueError('GTK4 snapshot control capability mismatch')
    artifacts = receipt.get('artifacts')
    if not isinstance(artifacts,dict) or not artifacts:
        raise ValueError('GTK4 artifact manifest missing')
    for name, digest in artifacts.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('GTK4 artifact outside snapshot')
        path = folder / relative
        if any(p.is_symlink() for p in (path,*path.parents)):
            raise ValueError('GTK4 artifact cannot traverse links')
        if backend.sha(backend.read_file(path)) != digest:
            raise ValueError('GTK4 artifact hash mismatch: ' + name)
    css = Path(receipt.get('css',''))
    if not css.is_absolute() or not css.is_relative_to(folder) or str(css.relative_to(folder)) not in artifacts:
        raise ValueError('GTK4 CSS is not a verified snapshot artifact')
    for name in ('PROJECT.json','GTK4-NATIVE-COLORS.json'):
        if name not in artifacts:
            raise ValueError('GTK4 required artifact missing: ' + name)
    if json.loads(backend.read_file(folder / 'PROJECT.json')) != model:
        raise ValueError('GTK4 saved project mismatch')
    if not backend.palette_inputs_current(receipt):
        raise ValueError('GTK4 snapshot palette stale')
    colors = json.loads(backend.read_file(folder / 'GTK4-NATIVE-COLORS.json'))['colors']
    if allow_toggle:
        from gtk4_buttons import identity
        stamp = identity(model['recipes']['gtk4'], colors)
        if (receipt.get('style_class') != 'theme-lab-gtk4-toggle-'+stamp or
                receipt.get('push_style_class') != 'theme-lab-gtk4-push-'+stamp):
            raise ValueError('GTK4 toggle snapshot style identity mismatch')
        base = Path(receipt.get('base_css',''))
        if (not base.is_absolute() or not base.is_relative_to(folder) or
                str(base.relative_to(folder)) not in artifacts):
            raise ValueError('GTK4 toggle base CSS is not a verified snapshot artifact')
    if allow_check:
        from gtk4_buttons import identity
        stamp = identity(model['recipes']['gtk4'], colors)
        check_css = Path(receipt.get('check_css', ''))
        if (receipt.get('check_style_class') != 'theme-lab-gtk4-check-' + stamp or
                not check_css.is_absolute() or not check_css.is_relative_to(folder) or
                str(check_css.relative_to(folder)) not in artifacts):
            raise ValueError('GTK4 check snapshot style identity mismatch')
    return receipt, colors


def verify_initial_snapshot(root, folder, model, working_digest, *,
                            allow_toggle=False, allow_scrollbar=False, allow_check=False):
    """Bind a saved normalized snapshot to the same working-scene model.

    C and Python serializers have distinct byte hashes. Accept only a receipt
    bound to either the actual working bytes or the actual saved snapshot
    bytes; verify_snapshot still checks the full artifact manifest and model.
    """
    folder = backend.private_output(Path(folder).absolute(), root)
    saved, saved_digest = backend.project(folder / 'PROJECT.json')
    if saved != model:
        raise ValueError('GTK4 initial snapshot/working scene mismatch')
    _validate_capabilities(allow_toggle, allow_scrollbar, allow_check)
    receipt_name = ('GTK4-SCROLLBAR-PROPOSAL.json' if allow_scrollbar
                    else 'GTK4-PROPOSAL.json')
    receipt = json.loads(backend.read_file(folder / receipt_name))
    bound = receipt.get('project_sha256')
    if bound not in (working_digest, saved_digest):
        raise ValueError('GTK4 initial snapshot has no actual byte identity')
    return verify_snapshot(root, folder, model, bound, allow_toggle=allow_toggle,
                           allow_scrollbar=allow_scrollbar, allow_check=allow_check)


if __name__=='__main__':
    import argparse,re
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--digest',required=True)
    parser.add_argument('--kdeglobals',type=Path)
    parser.add_argument('--private-toggle-session',action='store_true')
    parser.add_argument('--private-check-session',action='store_true')
    parser.add_argument('--private-scrollbar-session',action='store_true')
    args=parser.parse_args()
    backend.private_namespace(args.root.resolve())
    if not re.fullmatch('[0-9a-f]{64}',args.digest):parser.error('Invalid project digest')
    project,_digest=backend.project(args.project)
    generate_snapshot(args.root.resolve(),args.output,project,args.digest,args.kdeglobals,
                      allow_toggle=args.private_toggle_session,
                      allow_scrollbar=args.private_scrollbar_session,
                      allow_check=args.private_check_session)
