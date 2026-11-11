# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK2 generation/provenance; scene integration is a separate gate."""
from pathlib import Path
from gtk2_recipe import paint_scrollbars


def generate_scrollbar_snapshot(api, root, folder, model, kdeglobals):
    recipe = model['recipes']['gtk2']
    from scene_contract import scene
    visible_rows = scene(model, 'gtk2')
    # The scene contract applies both category and per-control visibility.
    # Do not emit a recipe for a control that the selected scene cannot show.
    requested = {row['id'] for row in visible_rows}
    builder = api.load_builder(root)
    for key in api.DEFAULT_ROLES:
        if recipe['palette'][key] not in api.ROLE_FAMILIES:
            raise api.Unavailable('GTK2: papel sem tradução nativa: ' + recipe['palette'][key])
    # Never silently fall back to another engine: pixmap determines how these
    # masks are composed and has already been tested with real GtkRange input.
    engines = [p for pattern in ('/usr/lib/*/gtk-2.0/*/engines/libpixmap.so',
                                '/usr/lib/gtk-2.0/*/engines/libpixmap.so',
                                '/usr/lib64/gtk-2.0/*/engines/libpixmap.so')
               for p in Path('/').glob(pattern.lstrip('/')) if p.is_file()]
    if not engines:
        raise api.Unavailable('GTK2: engine pixmap indisponível; geração preservada como pendente.')
    current, selected = api.selected_palette(model, kdeglobals, root)
    colors, origin = api.native_roles(root, Path(selected['path']), builder.art, selected['sha256'])
    for role, family in api.ROLE_FAMILIES.items():
        if current.has_section(role.split('/', 1)[0]):
            rgb = api.rgb_role(current, role)
            effective = builder.art._rgb(colors[builder.art.ROLES[family][0]])
            if any(abs(a - b) > 1 for a, b in zip(rgb, effective)):
                raise api.Unavailable('GTK2: papéis efetivos não correspondem à origem: ' + role)
    progress_style_id = None
    entry_style_id = None
    text_style_id = None
    combo_style_id = None
    spin_style_id = None
    scale_style_id = None
    arrow_style_id = None
    list_style_id = None
    frame_style_id = None
    with api.recipe_rules(builder, recipe['palette']):
        if requested & {'scroll_h', 'scroll_v'}:
            generated = paint_scrollbars(builder, recipe, colors, folder / 'gtk2-scrollbars')
        else:
            from gtk2_canvas import canvas_rc
            canvas_directory = folder / 'gtk2-scrollbars'
            canvas_directory.mkdir(parents=True, exist_ok=True)
            canvas_file = canvas_directory / 'gtk2-canvas.rc'
            canvas_file.write_text(canvas_rc(builder.art, colors), encoding='utf-8')
            generated = {'rc': str(canvas_file), 'assets': []}
        rc = Path(generated['rc'])
        translated_set = {control for control in ('scroll_h', 'scroll_v')
                          if control in requested}

        def append_fragment(fragment):
            rc.write_text(
                rc.read_text(encoding='utf-8') +
                Path(fragment['rc']).read_text(encoding='utf-8'),
                encoding='utf-8')
            generated['assets'] = list(dict.fromkeys(
                generated['assets'] + fragment['assets']))

        # Older range-only fixture recipes lack command padding/font. They
        # remain range-only snapshots; never invent missing button geometry.
        has_control_geometry = all(
            key in recipe['geometry']
            for key in ('shadow_px', 'control_padding_px', 'font_px'))
        if has_control_geometry:
            from gtk2_buttons import paint_button
            if 'push' in requested:
                button = paint_button(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(button)
                translated_set.add('push')
            if 'toggle' in requested:
                from gtk2_toggles import paint_toggle
                toggle = paint_toggle(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(toggle)
                translated_set.add('toggle')
            if 'radio' in requested:
                from gtk2_radios import paint_radio
                radio = paint_radio(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(radio)
                translated_set.add('radio')
            if 'check' in requested:
                from gtk2_checks import paint_check
                check = paint_check(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(check)
                translated_set.add('check')
            if 'progress' in requested:
                from gtk2_progress import paint_progress
                progress = paint_progress(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(progress)
                translated_set.add('progress')
                progress_style_id = progress['style_id']
            if 'entry' in requested:
                from gtk2_entries import paint_entry
                entry = paint_entry(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(entry)
                translated_set.add('entry')
                entry_style_id = entry['style_id']
            if 'text' in requested:
                from gtk2_text import paint_text
                text = paint_text(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(text)
                translated_set.add('text')
                text_style_id = text['style_id']
            if 'combo' in requested:
                from gtk2_combos import paint_combo
                combo = paint_combo(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(combo)
                translated_set.add('combo')
                combo_style_id = combo['style_id']
            if 'spin' in requested:
                from gtk2_spins import paint_spin
                spin = paint_spin(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(spin)
                translated_set.add('spin')
                spin_style_id = spin['style_id']
            if requested & {'scale_h', 'scale_v'}:
                from gtk2_scales import paint_scale
                scales = paint_scale(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(scales)
                translated_set.update(requested & {'scale_h', 'scale_v'})
                scale_style_id = scales['style_id']
            if 'arrow' in requested:
                from gtk2_arrows import paint_arrow
                arrow = paint_arrow(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(arrow)
                translated_set.add('arrow')
                arrow_style_id = arrow['style_id']
            if 'list' in requested:
                from gtk2_lists import paint_list
                listing = paint_list(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(listing)
                translated_set.add('list')
                list_style_id = listing['style_id']
            if 'frame' in requested:
                from gtk2_frames import paint_frame
                frame = paint_frame(builder, recipe, colors, folder / 'gtk2-scrollbars')
                append_fragment(frame)
                translated_set.add('frame')
                frame_style_id = frame['style_id']
        from scene_contract import CONTROLS
        translated = [control for control in CONTROLS if control in translated_set]
    scene_controls = [row['id'] for row in visible_rows]
    untranslated = [control for control in scene_controls if control not in translated_set]
    sources = [root / 'tools/theme-lab/backend.py', root / 'tools/theme-lab/scene_contract.py',
               root / 'tools/theme-lab/gtk2_frames.py', root / 'tools/theme-lab/frame_control_gtk2.py', root / 'tools/theme-lab/gtk2_lists.py', root / 'tools/theme-lab/list_control_gtk2.py', root / 'tools/theme-lab/gtk2_recipe.py', root / 'tools/theme-lab/gtk2_rc_fragments.py',
               root / 'tools/theme-lab/gtk2_canvas.py', root / 'tools/theme-lab/gtk2_buttons.py',
               root / 'tools/theme-lab/gtk2_toggles.py', root / 'tools/theme-lab/gtk2_radios.py',
               root / 'tools/theme-lab/gtk2_arrows.py', root / 'tools/theme-lab/gtk2_scales.py', root / 'tools/theme-lab/gtk2_spins.py', root / 'tools/theme-lab/gtk2_combos.py', root / 'tools/theme-lab/gtk2_text.py', root / 'tools/theme-lab/gtk2_entries.py', root / 'tools/theme-lab/gtk2_indicators.py', root / 'tools/theme-lab/gtk2_progress.py', root / 'tools/theme-lab/gtk2_checks.py', Path(__file__),
               root / 'tools/domainos_motif_art.py', root / 'gtk/tools/build_kde_domainos.py',
               root / 'tools/domainos_scrollbar_rules.json']
    receipt = dict(generated, status='partially_generated', family='gtk2', recipe=recipe,
                   rc_sha256=api.sha(api.read_file(Path(generated['rc']))),
                   asset_sha256={name: api.sha((folder / 'gtk2-scrollbars' / name).read_bytes())
                                 for name in generated['assets']},
                   recipe_applied=False, scene_controls=scene_controls,
                   translated_controls=translated, untranslated_controls=untranslated,
                   scene_integrated=False, historical_fidelity_claimed=False,
                   progress_style_id=progress_style_id, entry_style_id=entry_style_id, text_style_id=text_style_id, combo_style_id=combo_style_id, spin_style_id=spin_style_id, scale_style_id=scale_style_id, arrow_style_id=arrow_style_id, list_style_id=list_style_id, frame_style_id=frame_style_id,
                   selected_scheme=selected, palette=origin,
                   palette_inputs=[selected, origin['helper'], origin['helper_source']],
                   engine={'path': str(engines[0]), 'sha256': api.sha(engines[0].read_bytes())},
                   sources={str(p.relative_to(root)): api.sha(api.read_file(p)) for p in sources},
                   limitations=['Somente translated_controls recebem fragmentos; controles visíveis sem geometria suficiente permanecem explicitamente em untranslated_controls.',
                                'Aplicação nas prévias é verificada separadamente.',
                                'Cores são snapshot dos papéis KDE; gerar novamente após trocar esquema.'],
                   host_changed=False, picked_used=False)
    if not api.palette_inputs_current(receipt):
        raise api.Unavailable('GTK2: origem mudou durante a geração; aplique novamente.')
    api.write_json(folder / 'GTK2-NATIVE-COLORS.json', {'colors': colors, 'origin': origin})
    api.write_json(folder / 'GTK2-SCROLLBAR-PROPOSAL.json', receipt)
    return receipt
