#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Theme Lab scope, palette provenance and private GTK3 translation checks.

These use artificial named-role inputs, never initialize a GUI, and make no
claim about historical visual fidelity or approval of another toolkit.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'backend.py'
ROOT = SOURCE.parents[2]
spec = importlib.util.spec_from_file_location('theme_lab_backend_test', SOURCE)
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


def temporary_directory(prefix='theme-lab-backend-'):
    root = Path.home() / 'tempia/domainos-theme-work'
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix=prefix, dir=root)


def model():
    geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
    palette = dict(backend.DEFAULT_ROLES, **backend.FACTORS)
    return {'schema_version': 1, 'kind': 'theme_lab_project', 'name': 'Artificial project',
            'reference': '', 'selected_family': 'gtk3', 'native_measured': geometry.copy(),
            'recipes': {family: {'geometry': geometry.copy(), 'palette': palette.copy(), 'notes': ''}
                        for family in backend.FAMILIES},
            'picked': {'valid': True, 'rgb16': [65535, 0, 0], 'rgb8': [255, 0, 0], 'purpose': 'evidence_only'}}


class BackendTests(unittest.TestCase):
    def test_gtk3_combo_arrow_uses_directional_relief_and_native_active_state(self):
        builder=backend.load_builder(ROOT)
        geometry=model()['recipes']['gtk3']['geometry']
        assets=builder.gtk3_assets(geometry=geometry)
        normal=builder.gtk3_arrow('normal','down',geometry=geometry)
        pressed=builder.gtk3_arrow('pressed','down',geometry=geometry)
        generic=builder.art.triangle('normal','down')
        self.assertEqual(assets['gtk3-combobox-arrow-normal'][0],normal)
        self.assertEqual(assets['gtk3-combobox-arrow-pressed'][0],pressed)
        self.assertEqual(assets['gtk3-combobox-arrow-disabled'][0],normal)
        self.assertNotEqual(normal,generic)
        with temporary_directory(prefix='theme-lab-assets-') as directory:
            manifest=builder.masks(Path(directory),geometry=geometry)
            css=builder.common_css(manifest)
        self.assertIn('combobox arrow',css)
        self.assertIn('adaptive/gtk3-combobox-arrow-normal-',css)
        self.assertIn('button.combo:active arrow',css)
        self.assertIn('adaptive/gtk3-combobox-arrow-pressed-',css)
        self.assertIn('combobox arrow:disabled',css)

    def test_fitting_states_preserve_native_masks_and_geometry(self):
        data=model();recipe=data['recipes']['gtk3'];recipe['selected_control']=10;recipe['selected_scroll_part']=4
        builder=backend.load_builder(ROOT);geometry=recipe['geometry'];base=builder.gtk3_assets(geometry=geometry)
        recipe['scrollbar_parts']={'fitting':{'state_relief':{'normal':'raised','disabled':'flat','backdrop':'sunken'}}}
        before=copy.deepcopy(data)
        with backend.piece_assets(builder,recipe,geometry):assets=builder.gtk3_assets(geometry=geometry)
        for key,value in base.items():self.assertEqual(assets[key],value,key)
        self.assertEqual(set(token for row in assets['gtk3-lab-fitting-disabled'][0] for token in row),{'face'})
        for state in ('normal','disabled','backdrop'):
            snippet=backend.snippet(ROOT,data,recipe_state=state)
            self.assertIn('gtk3-lab-fitting-'+state,snippet['source'])
        for state in ('pressed','hover','focus'):
            with self.assertRaisesRegex(backend.Unavailable,'GtkViewport'):backend.snippet(ROOT,data,recipe_state=state)
        self.assertEqual(data,before)
        recipe['scrollbar_parts']['fitting']['state_relief']['hover']='flat'
        with self.assertRaises(backend.Unavailable):backend.require_scroll_parts_adapter(recipe)

    def test_thumb_relief_states_preserve_others_and_input(self):
        data=model();recipe=data['recipes']['gtk3'];recipe['selected_control']=10;recipe['selected_scroll_part']=3
        builder=backend.load_builder(ROOT);geometry=recipe['geometry'];base=builder.gtk3_assets(geometry=geometry)
        recipe['scrollbar_parts']={'thumb':{'state_relief':{'normal':'sunken','pressed':'flat','disabled':'raised','backdrop':'flat','hover':'sunken'}}}
        before=copy.deepcopy(data)
        with backend.piece_assets(builder,recipe,geometry):assets=builder.gtk3_assets(geometry=geometry)
        for key,value in base.items():self.assertEqual(assets[key],value,key)
        for state in recipe['scrollbar_parts']['thumb']['state_relief']:
            self.assertIn('gtk3-lab-thumb-'+state,assets)
            self.assertEqual(assets['gtk3-lab-thumb-'+state][2],geometry['shadow_px'])
            result=backend.snippet(ROOT,data,recipe_state=state)
            self.assertIn('gtk3-lab-thumb-'+state,result['source'])
        self.assertEqual(data,before)
        recipe['scrollbar_parts']['thumb']['state_relief']['focus']='flat'
        with self.assertRaises(backend.Unavailable):backend.require_scroll_parts_adapter(recipe)

    def test_enclosing_trough_relief_states_preserve_other_masks_and_geometry(self):
        data=model();recipe=data['recipes']['gtk3'];recipe['selected_control']=10
        recipe['selected_scroll_part']=2
        builder=backend.load_builder(ROOT);geometry=recipe['geometry']
        base=builder.gtk3_assets(geometry=geometry)
        recipe['scrollbar_parts']={'trough':{'state_relief':{'normal':'raised','disabled':'flat','backdrop':'sunken'}}}
        original=copy.deepcopy(data)
        with backend.piece_assets(builder,recipe,geometry):
            assets=builder.gtk3_assets(geometry=geometry)
        for key,value in base.items():self.assertEqual(assets[key],value,key)
        self.assertEqual(assets['gtk3-lab-trough-normal'][0],
            builder.art.bevel(builder.art.blank(len(base['gtk3-trough-frame'][0]),len(base['gtk3-trough-frame'][0]),'face'),thickness=2,down=False))
        self.assertEqual(set(token for row in assets['gtk3-lab-trough-disabled'][0] for token in row),{'face'})
        for state in ('normal','disabled','backdrop'):
            snippet=backend.snippet(ROOT,data,recipe_state=state)
            self.assertIn('gtk3-lab-trough-'+state,snippet['source'])
        for state in ('pressed','hover','focus'):
            with self.assertRaisesRegex(backend.Unavailable,'Moldura contínua'):
                backend.snippet(ROOT,data,recipe_state=state)
        self.assertEqual(data,original)
        for state in ('pressed','hover','focus'):
            recipe['scrollbar_parts']['trough']['state_relief']={state:'flat'}
            with self.assertRaises(backend.Unavailable):backend.require_scroll_parts_adapter(recipe)

    def test_isolated_arrow_button_relief_has_six_states_and_no_range_changes(self):
        data=model();recipe=data['recipes']['gtk3'];recipe['selected_control']=10
        recipe['selected_scroll_part']=1
        builder=backend.load_builder(ROOT);geometry=recipe['geometry']
        base=builder.gtk3_assets(geometry=geometry)
        manifest=backend.mask_metadata(builder,geometry,recipe)
        common,before=backend.gtk3_sources(builder,manifest,recipe,geometry)
        overrides=dict(zip(backend.PART_STATE_IDS,('raised','sunken','flat','raised','flat','sunken')))
        recipe['scrollbar_parts']={'arrow_button':{'state_relief':overrides}}
        original=copy.deepcopy(data)
        backend.require_scroll_parts_adapter(recipe)
        with backend.piece_assets(builder,recipe,geometry):
            self.assertEqual(builder.gtk3_assets(geometry=geometry),base)
        common_after,after=backend.gtk3_sources(builder,manifest,recipe,geometry)
        self.assertEqual(common_after,common)
        self.assertTrue(after.startswith(before))
        extra=after[len(before):]
        for selector,body in backend.re.findall(r'([^{}]+)\{([^{}]+)\}',extra):
            self.assertTrue(selector.strip().startswith('button.theme-lab-arrow'))
            self.assertIn('border-color:',body)
            self.assertNotIn('background-image:',body)
            self.assertNotIn('width:',body)
            self.assertIn('@theme_button_background_',body)
        for state in backend.PART_STATE_IDS:
            result=backend.snippet(ROOT,data,recipe_state=state)
            self.assertEqual(result['state'],state)
            self.assertEqual(result['control'],'arrow')
        focus=backend.snippet(ROOT,data,recipe_state='focus')['source']
        self.assertIn('button.theme-lab-arrow:not(:backdrop):focus:not(:hover):not(:active):not(:disabled)',focus)
        self.assertNotIn(':not(:focus)',focus)
        self.assertEqual(data,original)

    def test_piece_state_snippet_is_independent_of_native_preview_state(self):
        data=model();recipe=data['recipes']['gtk3']
        recipe['selected_control']=10;recipe['edit_state']=0
        recipe['scrollbar_parts']={'arrow':{'state_relief':{'normal':'flat','pressed':'sunken'}}}
        original=copy.deepcopy(data)
        pressed=backend.snippet(ROOT,data,recipe_state='pressed')
        normal=backend.snippet(ROOT,data,recipe_state='normal')
        self.assertEqual(pressed['state'],'pressed')
        self.assertIn('gtk3-lab-stepper-left-pressed',pressed['source'])
        self.assertNotIn('gtk3-lab-stepper-left-normal',pressed['source'])
        self.assertIn('gtk3-lab-stepper-left-normal',normal['source'])
        self.assertNotIn('gtk3-lab-stepper-left-pressed',normal['source'])
        for state in ('focus','invalid'):
            with self.assertRaisesRegex(backend.Unavailable,'ainda não traduzido'):
                backend.snippet(ROOT,data,recipe_state=state)
        self.assertEqual(data,original)

    def setUp(self):
        self.temporary = temporary_directory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def kde(self):
        path = self.work / 'kdeglobals'
        path.write_text('[Colors:Button]\nBackgroundNormal=120,90,70\nForegroundNormal=30,20,10\n'
                        '[Colors:Window]\nBackgroundNormal=80,100,120\nForegroundNormal=10,20,30\n'
                        '[Colors:View]\nBackgroundNormal=40,50,60\nForegroundNormal=200,210,220\n'
                        '[Colors:Selection]\nBackgroundNormal=50,80,110\nForegroundNormal=220,230,240\n')
        return path

    def test_anchor_persistence_types_and_pending_runtime(self):
        data=model();data['schema_version']=2
        anchors=[0]*16;anchors[10]=1
        data['recipes']['gtk3']['length_anchor']=anchors
        path=self.work/'anchors.json';path.write_text(json.dumps(data))
        loaded,_=backend.project(path)
        self.assertEqual(loaded['recipes']['gtk3']['length_anchor'],anchors)
        backend.require_scroll_parts_adapter(loaded['recipes']['gtk3'])
        backend.require_scroll_parts_adapter(loaded['recipes']['gtk3'],'motif')
        backend.require_scroll_parts_adapter(loaded['recipes']['gtk3'],'gtk2')
        with self.assertRaisesRegex(backend.Unavailable,'posicionamento nativo'):
            backend.require_scroll_parts_adapter(loaded['recipes']['gtk3'],'gtk4')
        for value in ([0]*15,[True]+[0]*15,[1]+[0]*15,[0]*10+[2]+[0]*5):
            data['recipes']['gtk3']['length_anchor']=value;path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'length_anchor'):backend.project(path)
        data['recipes']['gtk3']['length_anchor']=anchors;data['schema_version']=1
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'schema_version=2'):backend.project(path)

    def test_control_palette_overrides_are_validated_and_kept_out_of_family_default(self):
        data=model();data['schema_version']=3
        recipe=data['recipes']['gtk3']
        override=dict(recipe['palette'])
        override.update(face_role='Colors:Window/BackgroundNormal',light=.31)
        recipe['control_palettes']={'arrow':override}
        path=self.work/'control-palettes.json';path.write_text(json.dumps(data))
        loaded,_=backend.project(path)
        receipt=backend.snippet(ROOT,loaded,control='arrow')
        self.assertEqual(receipt['palette_source'],'control_override')
        self.assertEqual(receipt['palette_control'],'arrow')
        self.assertEqual(receipt['palette_rules']['face_role'],'Colors:Window/BackgroundNormal')
        self.assertEqual(receipt['palette_rules']['light'],.31)
        self.assertIn('face: Colors:Window/BackgroundNormal',receipt['source'])
        self.assertEqual(loaded['recipes']['gtk3']['palette']['face_role'],
                         backend.DEFAULT_ROLES['face_role'])
        recipe['control_palettes']={'unknown-control':override};path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'IDs do catálogo'):backend.project(path)
        recipe['control_palettes']={'arrow':dict(override,face_role='#78a0d5')};path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'Papel KDE inválido'):backend.project(path)

    def test_gtk3_full_export_translates_unambiguous_per_control_roles(self):
        data=model(); data['schema_version']=3
        recipe=data['recipes']['gtk3']
        override=dict(recipe['palette'])
        override.update(face_role='Colors:Window/BackgroundNormal',
                        text_role='Colors:Window/ForegroundNormal',
                        view_role='Colors:Window/BackgroundNormal',
                        selection_role='Colors:Window/ForegroundNormal',
                        light=.31,shade=.27,trough=.19)
        recipe['control_palettes']={'check':override}
        builder=backend.load_builder(ROOT)
        geometry=dict(builder.gtk3_scrollbar_rules()['geometry'],
                      **{key:recipe['geometry'][key] for key in backend.GEOMETRY[:7]})
        manifest=backend.mask_metadata(builder,geometry,recipe)
        css, receipt=backend.gtk3_control_palette_overrides(builder,manifest,recipe,geometry)
        self.assertEqual(receipt['status'],'applied')
        self.assertEqual(receipt['controls'],['check'])
        self.assertTrue(receipt['selectors'])
        self.assertIn('check:checked',css)
        self.assertIn('@theme_bg_color_breeze',css)
        self.assertEqual(recipe['palette'],dict(backend.DEFAULT_ROLES,**backend.FACTORS))
        self.assertEqual(recipe['control_palettes']['check']['light'],.31)

    def test_gtk3_shared_button_palettes_are_scoped_to_native_control_nodes(self):
        data=model(); data['schema_version']=3
        recipe=data['recipes']['gtk3']
        roles=('Colors:Window/BackgroundNormal','Colors:View/BackgroundNormal',
               'Colors:Button/BackgroundNormal','Colors:Selection/BackgroundNormal',
               'Colors:View/BackgroundNormal')
        controls=('push','toggle','combo','spin','arrow')
        recipe['control_palettes']={control:dict(recipe['palette'],face_role=role,
            light=.25+index*.05) for index,(control,role) in enumerate(zip(controls,roles))}
        builder=backend.load_builder(ROOT)
        geometry=dict(builder.gtk3_scrollbar_rules()['geometry'],
                      **{key:recipe['geometry'][key] for key in backend.GEOMETRY[:7]})
        manifest=backend.mask_metadata(builder,geometry,recipe)
        css,receipt=backend.gtk3_control_palette_overrides(builder,manifest,recipe,geometry)
        self.assertEqual(receipt['status'],'applied')
        self.assertEqual(receipt['controls'],sorted(controls))
        self.assertEqual(receipt['color_source'],'selected KDE semantic roles and illumination factors')
        self.assertIn('button:not(.toggle):not(.combo):not(.up):not(.down):not(.theme-lab-arrow)',css)
        self.assertIn('button.toggle:checked',css)
        self.assertIn('combobox > box > button.combo',css)
        self.assertIn('spinbutton > button',css)
        self.assertIn('button.theme-lab-arrow',css)
        for selector in receipt['selectors']:
            owners=[candidate for candidate in controls if backend.control_selector(selector,candidate)]
            self.assertEqual(len(owners),1,(selector,owners))
        self.assertIn('@theme_button_background_normal_breeze',css)
        self.assertNotRegex(css,r'(?im)^\s*(?:color|background-color|border-color)\s*:\s*#[0-9a-f]{3,8}\b')

    def test_gtk3_directional_palette_overrides_are_orientation_scoped(self):
        data=model(); data['schema_version']=3
        recipe=data['recipes']['gtk3']; base=recipe['palette']
        recipe['control_palettes']={
            'scale_h':dict(base,face_role='Colors:Window/BackgroundNormal'),
            'scale_v':dict(base,face_role='Colors:View/BackgroundNormal'),
            'scroll_h':dict(base,face_role='Colors:Window/BackgroundNormal'),
            'scroll_v':dict(base,face_role='Colors:View/BackgroundNormal')}
        builder=backend.load_builder(ROOT)
        geometry=dict(builder.gtk3_scrollbar_rules()['geometry'],
                      **{key:recipe['geometry'][key] for key in backend.GEOMETRY[:7]})
        manifest=backend.mask_metadata(builder,geometry,recipe)
        css,receipt=backend.gtk3_control_palette_overrides(builder,manifest,recipe,geometry)
        self.assertEqual(receipt['controls'],['scale_h','scale_v','scroll_h','scroll_v'])
        self.assertIn('scale.horizontal trough',css)
        self.assertIn('scale.vertical trough',css)
        self.assertIn('scrollbar.horizontal trough',css)
        self.assertIn('scrollbar.vertical trough',css)
        self.assertNotIn('scrolledwindow',css)
        self.assertNotRegex(css,r'(?m)^scale\s')
        self.assertNotRegex(css,r'(?m)^scrollbar\s')

    def test_state_relief_preserved_without_silent_paint_fallback(self):
        data=model();data['schema_version']=2
        recipe=data['recipes']['gtk3']
        recipe['scrollbar_parts']={'arrow':{'glyph_px':7,'state_relief':{'normal':'raised','pressed':'sunken'}},
                                   'thumb':{'state_relief':{'focus':'flat'}}}
        original=copy.deepcopy(data)
        path=self.work/'states.json';path.write_text(json.dumps(data))
        loaded,_=backend.project(path)
        self.assertEqual(loaded['recipes']['gtk3']['scrollbar_parts'],recipe['scrollbar_parts'])
        self.assertEqual(loaded['recipes']['gtk3']['geometry'],recipe['geometry'])
        with self.assertRaisesRegex(backend.Unavailable,'relevo por estado'):
            backend.require_scroll_parts_adapter(loaded['recipes']['gtk3'])
        self.assertEqual(data,original)
        for bad in ({'hover':'unknown'},{'unknown':'raised'},{'focus':True}):
            recipe['scrollbar_parts']['arrow']['state_relief']=bad
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'Estado/relevo'):backend.project(path)

    def test_arrow_state_relief_only_changes_symbolic_glyph(self):
        builder=backend.load_builder(ROOT)
        recipe=model()['recipes']['gtk3']
        baseline=builder.gtk3_assets(geometry=recipe['geometry'])
        recipe['scrollbar_parts']={'arrow':{'state_relief':{'normal':'flat','pressed':'sunken'}}}
        with backend.piece_assets(builder,recipe,recipe['geometry']):
            assets=builder.gtk3_assets(geometry=recipe['geometry'])
        for key,value in baseline.items():self.assertEqual(assets[key],value,key)
        for direction in ('up','down','left','right'):
            normal=baseline['gtk3-stepper-'+direction+'-normal'][0]
            flat=assets['gtk3-lab-stepper-'+direction+'-normal'][0]
            pressed=assets['gtk3-lab-stepper-'+direction+'-pressed'][0]
            self.assertEqual([[bool(x) for x in row] for row in normal],
                             [[bool(x) for x in row] for row in flat])
            self.assertEqual({x for row in flat for x in row if x},{'face'})
            self.assertEqual(pressed,[[{'light':'dark','dark':'light'}.get(x,x) for x in row] for row in normal])
        manifest=backend.mask_metadata(builder,recipe['geometry'],recipe)
        _,css=backend.gtk3_sources(builder,manifest,recipe,recipe['geometry'])
        self.assertIn('gtk3-lab-stepper-down-pressed',css)
        self.assertIn(':not(:active):not(:hover):not(:focus):not(:disabled):not(:backdrop)',css)
        self.assertIn('scrollbar.vertical:not(:disabled):backdrop button.down:active:not(:disabled)',css)
        for selector, body in backend.re.findall(r'([^{}]+)\{([^{}]+)\}',css):
            if 'gtk3-lab-stepper-' in body:
                self.assertRegex(body,r'background-color: [^;]*@theme_button_background_[a-z_]+_breeze')
                self.assertIn('-gtk-recolor(',body)
        pressed_selector='scrollbar.vertical:not(:disabled) button.down:active:not(:disabled)'
        self.assertFalse(backend.state_selector(pressed_selector,'normal'))
        self.assertTrue(backend.state_selector(pressed_selector,'pressed'))
        self.assertEqual(builder.gtk3_assets(geometry=recipe['geometry']),baseline)
        recipe['scrollbar_parts']['arrow']['state_relief']['focus']='raised'
        with self.assertRaises(backend.Unavailable):backend.require_scroll_parts_adapter(recipe)

    def test_arrow_context_relief_uses_each_native_palette_without_normal_leak(self):
        builder=backend.load_builder(ROOT);data=model();recipe=data['recipes']['gtk3']
        recipe['selected_control']=11
        recipe['scrollbar_parts']={'arrow':{'state_relief':{'disabled':'raised','backdrop':'sunken'}}}
        backend.require_scroll_parts_adapter(recipe)
        manifest=backend.mask_metadata(builder,recipe['geometry'],recipe)
        _,css=backend.gtk3_sources(builder,manifest,recipe,recipe['geometry'])
        self.assertIn('scrollbar.vertical:disabled:not(:backdrop) button.down:disabled',css)
        self.assertIn('scrollbar.vertical:disabled:backdrop button.down:disabled',css)
        # Existing shared role contract keeps disabled face/shadows tied to
        # the contextual Button face; insensitive ink is a separate role.
        self.assertIn(builder.state_css('button',3)('face'),css)
        self.assertIn('scrollbar.vertical:not(:disabled):backdrop button.down:not(:active)',css)
        normal=backend.snippet(ROOT,data,recipe_state='normal')['source']
        self.assertNotIn('gtk3-lab-stepper-down-disabled',normal)
        self.assertNotIn('gtk3-lab-stepper-down-backdrop',normal)
        for state in ('disabled','backdrop'):
            source=backend.snippet(ROOT,data,recipe_state=state)['source']
            self.assertIn('gtk3-lab-stepper-down-'+state,source)
            self.assertNotIn('gtk3-lab-stepper-down-'+('backdrop' if state=='disabled' else 'disabled'),source)

    def test_hover_arrow_is_inspected_separately_from_normal_and_pressed(self):
        data=model();recipe=data['recipes']['gtk3'];recipe['selected_control']=10
        recipe['scrollbar_parts']={'arrow':{'state_relief':{'hover':'flat'}}}
        source=backend.snippet(ROOT,data,recipe_state='hover')['source']
        self.assertIn('gtk3-lab-stepper-left-hover',source)
        self.assertIn('button.up:hover:not(:active):not(:focus):not(:disabled)',source)
        for state in ('normal','pressed','disabled'):
            self.assertNotIn('gtk3-lab-stepper-left-hover',backend.snippet(ROOT,data,recipe_state=state)['source'])

    def test_piece_recipe_roundtrip_and_adapter_limit(self):
        data = model()
        data['schema_version'] = 2
        data['recipes']['gtk3']['scrollbar_parts'] = {'arrow': {'glyph_px': 7}}
        original = copy.deepcopy(data)
        path = self.work / 'parts.json'
        path.write_text(json.dumps(data))
        loaded, _ = backend.project(path)
        self.assertEqual(loaded['recipes']['gtk3']['scrollbar_parts'], {'arrow': {'glyph_px': 7}})
        self.assertEqual(loaded['recipes']['gtk3']['geometry'], original['recipes']['gtk3']['geometry'])
        backend.snippet(ROOT, loaded)
        pending=copy.deepcopy(loaded)
        pending['selected_family']='gtk2'
        pending['recipes']['gtk2']['scrollbar_parts']={'fitting': {'inset_px': 1}}
        with self.assertRaisesRegex(backend.Unavailable, 'tradução nativa'):
            backend.snippet(ROOT, pending)
        for bad in ({'arrow': {'glyph_px': True}}, {'unknown': {}},
                    {'arrow': {'glyph_px': 129}}, {'trough': {'glyph_px': 7}}):
            with self.subTest(bad=bad):
                data['recipes']['gtk3']['scrollbar_parts'] = bad
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    backend.project(path)
        data = original
        data['schema_version'] = 1
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'schema_version=2'):
            backend.project(path)

    def test_fitting_preserves_all_existing_masks_and_bar_geometry(self):
        builder = backend.load_builder(ROOT)
        recipe = model()['recipes']['gtk3']
        geometry = recipe['geometry']
        before = backend.mask_metadata(builder, geometry, recipe)
        recipe['scrollbar_parts'] = {'fitting': {'gap_px': 7, 'inset_px': 1}}
        after = backend.mask_metadata(builder, geometry, recipe)
        for key, value in before['assets'].items():
            self.assertEqual(after['assets'][key], value, key)
        self.assertEqual(set(after['assets']) - set(before['assets']), {'gtk3-lab-view-frame'})
        self.assertEqual(after['assets']['gtk3-lab-view-frame']['border'], 1)
        _, css = backend.gtk3_sources(builder, after, recipe, geometry)
        self.assertIn('-GtkScrolledWindow-scrollbar-spacing: 7', css)
        self.assertIn('gtk3-lab-view-frame', css)
        self.assertEqual(recipe['geometry'], model()['recipes']['gtk3']['geometry'])
        recipe['scrollbar_parts'] = {'fitting': {'gap_px': 0, 'inset_px': 0}}
        zero = backend.mask_metadata(builder, geometry, recipe)
        self.assertEqual(zero['assets']['gtk3-lab-view-frame']['border'], 0)
        backend.gtk3_sources(builder, zero, recipe, geometry)

    def test_arrow_overrides_only_masks_inside_fixed_allocation(self):
        builder = backend.load_builder(ROOT)
        recipe = model()['recipes']['gtk3']
        geometry = recipe['geometry']
        before = builder.gtk3_assets(geometry=geometry)
        recipe['scrollbar_parts'] = {'arrow': {'glyph_px': 7, 'shadow_px': 1}}
        with backend.piece_assets(builder, recipe, geometry):
            after = builder.gtk3_assets(geometry=geometry)
            for name in before:
                if not name.startswith('gtk3-stepper-'):
                    self.assertEqual(before[name], after[name])
                    continue
                self.assertEqual(len(after[name][0]), 11)
                self.assertEqual(len(after[name][0][0]), 11)
                occupied = [(x,y) for y,row in enumerate(after[name][0]) for x,t in enumerate(row) if t]
                self.assertEqual((min(x for x,y in occupied),max(x for x,y in occupied)), (2,8))
                self.assertEqual((min(y for x,y in occupied),max(y for x,y in occupied)), (2,8))
                self.assertNotEqual(before[name], after[name])
        self.assertEqual(before,builder.gtk3_assets(geometry=geometry))
        recipe['scrollbar_parts']['arrow']['glyph_px'] = 13
        with self.assertRaisesRegex(ValueError, 'espaço reservado'):
            backend.require_scroll_parts_adapter(recipe)
        with self.assertRaisesRegex(backend.Unavailable, 'tradução nativa'):
            backend.require_scroll_parts_adapter(recipe, 'motif')

    def test_standalone_arrow_button_changes_no_range_rule_or_mask(self):
        data=model();recipe=data['recipes']['gtk3'];recipe['selected_control']=12
        recipe['scrollbar_parts']={'arrow': {'glyph_px':7}}
        builder=backend.load_builder(ROOT);geometry=recipe['geometry']
        with backend.piece_assets(builder,recipe,geometry):
            masks=builder.gtk3_assets(geometry=geometry)
        manifest=backend.mask_metadata(builder,geometry,recipe)
        common,before=backend.gtk3_sources(builder,manifest,recipe,geometry)
        recipe['scrollbar_parts']['arrow_button']={'padding_px':1,'shadow_px':1}
        backend.require_scroll_parts_adapter(recipe)
        with backend.piece_assets(builder,recipe,geometry):
            self.assertEqual(masks,builder.gtk3_assets(geometry=geometry))
        common_after,after=backend.gtk3_sources(builder,manifest,recipe,geometry)
        self.assertEqual(common,common_after)
        import re
        def rules(css):
            return dict(re.findall(r'([^{}]+)\{([^{}]*)\}',css))
        a,b=rules(before),rules(after)
        self.assertEqual(a.keys(),b.keys())
        changed=[selector.strip() for selector in a if a[selector]!=b[selector]]
        self.assertTrue(changed)
        self.assertTrue(all(selector.startswith('button.theme-lab-arrow') for selector in changed))
        source=backend.snippet(ROOT,data)['source']
        self.assertIn('moldura 1px; espaço interno 1px',source)
        self.assertIn('min-width: 11px;',source)
        self.assertIn('border-width: 1px;',source)
        self.assertIn('padding: 1px;',source)
        for value in (4,128):
            recipe['scrollbar_parts']['arrow_button']['padding_px']=value
            with self.assertRaisesRegex(ValueError,'sem cobrir'):
                backend.require_scroll_parts_adapter(recipe)

    def test_trough_recipe_preserves_viewport_arrows_thumb_and_button(self):
        builder = backend.load_builder(ROOT)
        data = model()
        recipe = data['recipes']['gtk3']
        geometry = recipe['geometry']
        original = builder.gtk3_assets(geometry=geometry)
        baseline = backend.mask_metadata(builder, geometry, recipe)
        common_before, css_before = backend.gtk3_sources(builder, baseline, recipe, geometry)
        recipe['scrollbar_parts'] = {'trough': {'thickness_px': 17, 'shadow_px': 1}}
        backend.require_scroll_parts_adapter(recipe)
        with backend.piece_assets(builder, recipe, geometry):
            actual = builder.gtk3_assets(geometry=geometry)
            self.assertEqual(set(actual) - set(original), {'gtk3-lab-trough-frame'})
            for name in original:
                self.assertEqual(actual[name], original[name], name)
            self.assertEqual(actual['gtk3-lab-trough-frame'][2], 1)
        self.assertEqual(builder.gtk3_assets(geometry=geometry), original)
        manifest = backend.mask_metadata(builder, geometry, recipe)
        common_after, css_after = backend.gtk3_sources(builder, manifest, recipe, geometry)
        self.assertEqual(common_before, common_after)
        import re
        def rules(css):
            return {selector.strip(): props for selector, props in re.findall(r'([^{}]+)\{([^{}]*)\}', css)}
        before, after = rules(css_before), rules(css_after)
        for selector in before:
            if selector.startswith('scrollbar') and selector.endswith('contents'):
                continue
            self.assertEqual(before[selector], after[selector], selector)
        self.assertEqual(after['scrollbar.vertical trough'].strip(), 'min-width: 15px;')
        self.assertEqual(after['scrollbar.horizontal trough'].strip(), 'min-height: 15px;')
        self.assertIn('border-width: 1px;', after['scrollbar contents'])
        self.assertIn('gtk3-lab-trough-frame', after['scrollbar contents'])
        self.assertEqual(before['scrolledwindow > viewport'], after['scrolledwindow > viewport'])
        self.assertEqual(recipe['geometry'], model()['recipes']['gtk3']['geometry'])

    def test_trough_constraints_reject_clipping_and_allow_inherited_frame(self):
        recipe = model()['recipes']['gtk3']
        for parameters in ({'thickness_px': 14}, {'shadow_px': 3}, {'thickness_px': 0}):
            recipe['scrollbar_parts'] = {'trough': parameters}
            with self.subTest(parameters=parameters), self.assertRaisesRegex(ValueError, 'sem cortar'):
                backend.require_scroll_parts_adapter(recipe)
        for parameters in ({'thickness_px': 17}, {'shadow_px': 1}, {'shadow_px': 0}):
            recipe['scrollbar_parts'] = {'trough': parameters}
            backend.require_scroll_parts_adapter(recipe)

    def test_thumb_geometry_masks_and_neighbor_isolation(self):
        builder = backend.load_builder(ROOT)
        recipe = model()['recipes']['gtk3']
        geometry = recipe['geometry']
        baseline = builder.gtk3_assets(geometry=geometry)
        recipe['scrollbar_parts'] = {'thumb': {'cross_px': 9, 'shadow_px': 1, 'gap_px': 3}}
        backend.require_scroll_parts_adapter(recipe)
        with backend.piece_assets(builder, recipe, geometry):
            actual = builder.gtk3_assets(geometry=geometry)
            changed = [name for name in baseline if actual[name] != baseline[name]]
            self.assertEqual(changed, ['gtk3-thumb-frame'])
            self.assertEqual(actual['gtk3-thumb-frame'][2], 1)
        self.assertEqual(builder.gtk3_assets(geometry=geometry), baseline)
        manifest = backend.mask_metadata(builder, geometry, recipe)
        _, css = backend.gtk3_sources(builder, manifest, recipe, geometry)
        self.assertIn('margin-left: 1px;', css)
        self.assertIn('margin-top: 1px;', css)
        self.assertIn('margin-bottom: 3px;', css)
        self.assertIn('min-width: 7px;', css)
        self.assertIn('min-height: 18px;', css)
        for parameters in ({'cross_px': 13}, {'cross_px': 8}, {'shadow_px': 6}, {'cross_px': 0}):
            recipe['scrollbar_parts'] = {'thumb': parameters}
            with self.subTest(parameters=parameters), self.assertRaisesRegex(ValueError, 'margens inteiras'):
                backend.require_scroll_parts_adapter(recipe)

    def test_thumb_combines_with_wider_trough_without_changing_other_masks(self):
        builder = backend.load_builder(ROOT)
        recipe = model()['recipes']['gtk3']
        recipe['scrollbar_parts'] = {'trough': {'thickness_px': 17, 'shadow_px': 1}}
        with backend.piece_assets(builder, recipe, recipe['geometry']):
            before = builder.gtk3_assets(geometry=recipe['geometry'])
        recipe['scrollbar_parts']['thumb'] = {'cross_px': 13, 'shadow_px': 1}
        backend.require_scroll_parts_adapter(recipe)
        with backend.piece_assets(builder, recipe, recipe['geometry']):
            after = builder.gtk3_assets(geometry=recipe['geometry'])
        self.assertEqual(set(before), set(after))
        for name in before:
            if name != 'gtk3-thumb-frame':
                self.assertEqual(before[name], after[name])

    def test_palette_uses_selected_roles_factors_and_ignores_pick(self):
        data = model()
        data['recipes']['gtk3']['palette'].update(face_role='Colors:Window/BackgroundNormal', light=.25, shade=.5)
        values = backend.palette_values(data, self.kde())
        self.assertEqual(values['rgb8'][0], [80, 100, 120])
        self.assertEqual(values['rgb8'][4], [124, 139, 154])
        self.assertEqual(values['rgb8'][5], [40, 50, 60])
        self.assertEqual(values['rgb16'][0], [80*257, 100*257, 120*257])
        self.assertFalse(values['picked_used'])
        self.assertEqual(values['origin']['sha256'], backend.sha(self.kde().read_bytes()))

    def test_shell_header_palette_uses_header_roles_and_dynamic_fallback(self):
        path = self.kde()
        path.write_text(path.read_text() +
                        '[Colors:Header]\nBackgroundNormal=11,22,33\n'
                        'ForegroundNormal=244,233,222\n')
        values = backend.palette_values(None, path)
        self.assertEqual(values['header_rgb8'][0], [11, 22, 33])
        self.assertEqual(values['header_rgb8'][1], [244, 233, 222])
        self.assertEqual(values['header_rgb8'][3], [50, 80, 110])
        self.assertEqual(values['header_roles'], {
            'face': 'Colors:Header/BackgroundNormal',
            'text': 'Colors:Header/ForegroundNormal'})
        self.assertNotEqual(values['header_rgb8'][0], values['rgb8'][0])

        path.write_text(path.read_text().split('[Colors:Header]', 1)[0])
        fallback = backend.palette_values(None, path)
        self.assertEqual(fallback['header_rgb8'][0], [80, 100, 120])
        self.assertEqual(fallback['header_rgb8'][1], [10, 20, 30])
        self.assertEqual(fallback['header_roles'], {
            'face': 'Colors:Window/BackgroundNormal',
            'text': 'Colors:Window/ForegroundNormal'})

        partial = self.kde()
        partial.write_text(partial.read_text() +
                           '[Colors:Header]\nBackgroundNormal=11,22,33\n')
        partial_values = backend.palette_values(None, partial)
        self.assertEqual(partial_values['header_rgb8'][0], [80, 100, 120])
        self.assertEqual(partial_values['header_rgb8'][1], [10, 20, 30])
        self.assertEqual(partial_values['header_roles'], {
            'face': 'Colors:Window/BackgroundNormal',
            'text': 'Colors:Window/ForegroundNormal'})

    def test_reference_palette_keeps_motif_recipe_and_selected_scheme(self):
        data = model()
        data['recipes']['gtk3']['palette'].update(face_role='Colors:Window/BackgroundNormal', light=.25)
        original = json.dumps(data, sort_keys=True)
        path = self.kde()
        edited = backend.palette_values(data, path)
        reference = backend.palette_values(data, path, family='motif')
        self.assertEqual(edited['rgb8'][0], [80, 100, 120])
        self.assertEqual(reference['rgb8'][0], [120, 90, 70])
        self.assertEqual(reference['factors']['light'], backend.FACTORS['light'])
        path.write_text(path.read_text().replace('120,90,70', '40,50,60'))
        self.assertEqual(backend.palette_values(data, path, family='motif')['rgb8'][0], [40, 50, 60])
        self.assertEqual(json.dumps(data, sort_keys=True), original)

    def test_missing_role_refuses_historical_fallback(self):
        path = self.work / 'kdeglobals'
        path.write_text('[General]\nColorScheme=Anything\n')
        with self.assertRaisesRegex(backend.Unavailable, 'Papel KDE ausente'):
            backend.palette_values(model(), path)

    def test_schema_rejects_invalid_project_but_keeps_zero_padding(self):
        data = model()
        data['recipes']['gtk5']['geometry']['control_padding_px'] = 0
        path = self.work / 'project.json'; path.write_text(json.dumps(data))
        loaded, _ = backend.project(path)
        self.assertEqual(loaded['recipes']['gtk5']['geometry']['control_padding_px'], 0)
        data['recipes']['gtk3']['palette']['light'] = float('nan')
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Fator de iluminação'):
            backend.project(path)

    def test_optional_layout_fields_default_and_reject_paths_or_invalid_selection(self):
        data = model(); path = self.work / 'project.json'
        path.write_text(json.dumps(data)); loaded, _ = backend.project(path)
        self.assertEqual(loaded['color_scheme'], '')
        self.assertEqual(loaded['recipes']['gtk3']['selected_control'], 0)
        self.assertEqual(loaded['recipes']['gtk3']['positions'][15], [496, 256])
        for field, value in (('color_scheme', '../outside'), ('color_scheme', '/tmp/arbitrary.colors')):
            invalid = copy.deepcopy(data); invalid[field] = value
            path.write_text(json.dumps(invalid))
            with self.assertRaisesRegex(ValueError, 'ID portátil'):
                backend.project(path)
        for key, value in (('selected_control', 16), ('edit_state', 4), ('positions', [[0, 0]])):
            invalid = copy.deepcopy(data); invalid['recipes']['gtk3'][key] = value
            path.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                backend.project(path)

    def test_separate_preview_project_preference_compatible_and_strict(self):
        path = self.work / 'separate-project.json'
        for schema in (1, 2):
            data = model(); data['schema_version'] = schema
            path.write_text(json.dumps(data))
            loaded, _ = backend.project(path)
            self.assertIs(loaded['separate_preview'], False)
            for value in (False, True):
                data['separate_preview'] = value
                original = copy.deepcopy(data)
                path.write_text(json.dumps(data))
                loaded, _ = backend.project(path)
                self.assertIs(loaded['separate_preview'], value)
                self.assertEqual(data, original)
                self.assertEqual(loaded['recipes']['gtk3']['geometry'], data['recipes']['gtk3']['geometry'])
            for value in (0, 1, None, 'true', [], {}):
                data['separate_preview'] = value
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, 'separate_preview'):
                    backend.project(path)

    def scheme_locations(self):
        user, system, root = (self.work / name for name in ('user', 'system', 'repo'))
        for directory in (user / 'color-schemes', system / 'color-schemes', root / 'colors'):
            directory.mkdir(parents=True)
        return user, system, root

    def test_scheme_catalog_precedence_and_selected_scheme_roles_do_not_write_profile(self):
        user, system, root = self.scheme_locations()
        current = self.kde(); before = current.read_bytes()
        definition = before.decode().replace('120,90,70', '90,120,170')
        chosen = user / 'color-schemes/Artificial.colors'
        chosen.write_text('[General]\nName=Artificial user scheme\n' + definition)
        (system / 'color-schemes/Artificial.colors').write_text(before.decode())
        (root / 'colors/Artificial.colors').write_text(before.decode())
        (root / 'colors/RepositoryOnly.colors').write_text(before.decode())
        (user / 'color-schemes/Linked.colors').symlink_to(chosen)
        env = {'XDG_DATA_HOME': str(user), 'XDG_DATA_DIRS': str(system)}
        with patch.dict(os.environ, env):
            catalog = backend.schemes(root, current)
            items = {item['id']: item for item in catalog['schemes']}
            self.assertEqual(items['']['path'], str(current))
            self.assertEqual(items['Artificial']['origin'], 'xdg_user_color_scheme')
            self.assertEqual(items['Artificial']['name'], 'Artificial user scheme')
            self.assertEqual(items['RepositoryOnly']['origin'], 'repository_color_scheme')
            self.assertNotIn('Linked', items)
            self.assertTrue(catalog['skipped'])
            data = model(); data['color_scheme'] = 'Artificial'
            selected = backend.palette_values(data, current, root)
            self.assertEqual(selected['rgb8'][0], [90, 120, 170])
            self.assertEqual(selected['origin']['scheme_id'], 'Artificial')
            self.assertEqual(selected['origin']['sha256'], backend.sha(chosen.read_bytes()))
            self.assertFalse(selected['effective_gtk_states_exported'])
            self.assertFalse(selected['private_kde_profile_changed'])
            data['color_scheme'] = 'Missing'
            with self.assertRaisesRegex(backend.Unavailable, 'não encontrado'):
                backend.palette_values(data, current, root)
        self.assertEqual(current.read_bytes(), before)
        self.assertFalse((self.work / 'gtk-3.0/colors.css').exists())

    def test_control_snippet_uses_real_recipe_subset_and_role_expressions(self):
        data = model(); recipe = data['recipes']['gtk3']
        recipe.update(selected_control=10, edit_state=2)
        recipe['palette'].update(face_role='Colors:Window/BackgroundNormal', light=.37)
        receipt = backend.snippet(ROOT, data)
        self.assertEqual(receipt['control'], 'scroll_h')
        self.assertEqual(receipt['palette_source'],'family_default')
        self.assertEqual(receipt['state'], 'disabled')
        self.assertEqual(receipt['source'], receipt['text'])
        self.assertIn('scrollbar.horizontal', receipt['source'])
        self.assertNotIn('scrollbar.vertical', receipt['source'])
        self.assertNotIn('spinbutton', receipt['source'])
        self.assertIn('@insensitive_bg_color_breeze', receipt['source'])
        self.assertIn('mix(@insensitive_bg_color_breeze, #ffffff, 0.37)', receipt['source'])
        self.assertIn('Sufixo _breeze é alias do exportador', receipt['source'])
        self.assertNotIn('@define-color', receipt['source'])
        self.assertFalse(receipt['recipe_applied'])
        recipe.update(selected_control=2, edit_state=1)
        selected = backend.snippet(ROOT, data)
        self.assertEqual(selected['control'], 'check')
        self.assertEqual(selected['state'], 'pressed')
        self.assertIn('check:checked', selected['source'])
        self.assertNotIn('radio', selected['source'])
        for control in backend.CONTROLS:
            item = backend.snippet(ROOT, data, control=control)
            self.assertEqual(item['control'], control)
            self.assertIn('{', item['source'])
        pending = backend.snippet(ROOT, data, family='gtk5', control='entry')
        self.assertEqual(pending['status'], 'not_implemented')
        self.assertEqual(json.loads(pending['source'])['control'], 'entry')
        self.assertFalse(pending['recipe_applied'])

    def native_scheme(self):
        user = self.work / 'native-user'; directory = user / 'color-schemes'
        directory.mkdir(parents=True)
        scheme = directory / 'ArtificialNative.colors'
        contents = self.kde().read_text()
        contents += ('[Colors:Tooltip]\nBackgroundNormal=170,180,190\nForegroundNormal=20,30,40\n'
                     '[Colors:Header]\nBackgroundNormal=150,160,170\nForegroundNormal=230,210,200\n'
                     '[Colors:Button][Inactive]\nBackgroundNormal=71,81,91\nForegroundNormal=51,61,71\n'
                     '[Colors:Header][Inactive]\nBackgroundNormal=111,121,131\nForegroundNormal=90,100,110\n'
                     '[ColorEffects:Inactive]\nEnable=false\nChangeSelectionColor=false\n'
                     '[ColorEffects:Disabled]\nEnable=true\nIntensityEffect=1\nIntensityAmount=0.3\n'
                     'ColorEffect=0\nContrastEffect=1\nContrastAmount=0.6\n')
        scheme.write_text(contents)
        return scheme, {'XDG_DATA_HOME': str(user), 'XDG_DATA_DIRS': str(self.work / 'no-system')}

    def test_private_arrow_has_intrinsic_geometry_and_all_named_role_states(self):
        data = model(); recipe = data['recipes']['gtk3']
        recipe.update(selected_control=12)
        recipe['geometry'].update(arrow_px=13, bar_px=17, thumb_cross_px=13)
        recipe['palette'].update(face_role='Colors:Window/BackgroundNormal', light=.37)
        states = ('normal', 'pressed', 'disabled', 'backdrop')
        roles = ('@theme_bg_color_breeze', '@theme_bg_color_breeze',
                 '@insensitive_bg_color_breeze', '@theme_unfocused_bg_color_breeze')
        for index, (state, role) in enumerate(zip(states, roles)):
            recipe['edit_state'] = index
            result = backend.snippet(ROOT, data)
            css = result['source']
            with self.subTest(state=state):
                self.assertEqual(result['state'], state)
                self.assertIn('button.theme-lab-arrow', css)
                self.assertIn(role, css)
                self.assertIn('min-width: 13px;', css)
                self.assertIn('min-height: 13px;', css)
                self.assertIn('background-size: 13px 13px;', css)
                self.assertIn('border-width: 2px;', css)
                self.assertIn('padding: 0;', css)
                self.assertNotIn('combobox', css)
                self.assertNotIn('menuitem', css)
                self.assertNotIn('expander', css)
                self.assertNotIn('@define-color', css)
                self.assertNotIn('140px', css)
        recipe['edit_state'] = 1
        self.assertIn('gtk3-stepper-down-pressed-', backend.snippet(ROOT, data)['source'])
        recipe['edit_state'] = 2
        self.assertIn('gtk3-stepper-down-disabled-', backend.snippet(ROOT, data)['source'])
        push_source = backend.snippet(ROOT, data, control='push')['source']
        self.assertNotIn('button.theme-lab-arrow', push_source)
        self.assertIn(':not(.theme-lab-arrow)', push_source)

    def test_alternate_gtk3_scheme_refuses_unavailable_native_reader_instead_of_current_export(self):
        scheme, environment = self.native_scheme()
        data = model(); data['color_scheme'] = scheme.stem
        output = self.work / 'alternate'; output.mkdir(mode=0o700)
        with patch.dict(os.environ, environment), patch.object(backend, 'native_roles', side_effect=backend.Unavailable('Leitor nativo não compilado')):
            with self.assertRaisesRegex(backend.Unavailable, 'Leitor nativo não compilado'):
                backend.generate_gtk3(ROOT, output, data, self.kde())
        self.assertFalse((output / 'data').exists())

    @unittest.skipUnless((ROOT / 'tools/theme-lab/build/theme-lab-colors').is_file(), 'Build the optional native KDE reader first')
    def test_current_gtk3_scheme_uses_native_kde_roles_when_private_gtk_export_is_absent(self):
        _, environment = self.native_scheme()
        data = model()
        current = self.kde()
        before = current.read_bytes()
        output = self.work / 'current-native-generated'; output.mkdir(mode=0o700)
        with patch.dict(os.environ, environment):
            receipt = backend.generate_gtk3(ROOT, output, data, current)
        self.assertTrue(receipt['recipe_applied'])
        self.assertIn('Receita GTK3 privada gerada', receipt['reason'])
        self.assertEqual(receipt['selected_scheme']['kind'], 'current_kdeglobals_roles')
        self.assertEqual(receipt['palette']['kind'], 'native_kcolorscheme_selected_file')
        self.assertEqual(receipt['palette']['sha256'], backend.sha(before))
        self.assertTrue((output / 'GTK3-NATIVE-COLORS.json').is_file())
        self.assertTrue(backend.palette_inputs_current(receipt))
        self.assertEqual(current.read_bytes(), before)
        self.assertFalse((self.work / 'gtk-3.0/colors.css').exists())

    @unittest.skipUnless((ROOT / 'tools/theme-lab/build/theme-lab-colors').is_file(), 'Build the optional native KDE reader first')
    def test_native_kde_states_and_alternate_gtk3_generation_do_not_use_current_export(self):
        scheme, environment = self.native_scheme(); before = scheme.read_bytes()
        data = model(); data['color_scheme'] = scheme.stem
        builder = backend.load_builder(ROOT)
        colors, origin = backend.native_roles(ROOT, scheme, builder.art, backend.sha(before))
        required = {name for names in builder.art.ROLES.values() for name in names}
        self.assertEqual(set(colors), required)
        self.assertEqual(origin['gtkconfig_policy_version'], '6.3.4')
        self.assertEqual(colors['theme_button_background_normal_breeze'], '#785a46')
        self.assertEqual(colors['theme_button_background_backdrop_breeze'], '#47515b')
        self.assertNotEqual(colors['theme_button_background_insensitive_breeze'], '#785a46')
        for family in ('window', 'view', 'selection', 'button', 'button-fg', 'focus'):
            names = builder.art.ROLES[family]
            self.assertEqual(colors[names[2]], colors[names[3]])
        self.assertEqual(colors['theme_header_foreground_insensitive_breeze'], '#5a646e')
        self.assertEqual(colors['theme_titlebar_foreground_insensitive_backdrop_breeze'], '#5a646e')
        self.assertEqual(colors['theme_header_background_backdrop_breeze'], '#6f7983')
        current = self.kde(); current_before = current.read_bytes()
        # No current colors.css exists: the selected scheme's effective states
        # must be produced through KColorScheme rather than borrowed from it.
        output = self.work / 'native-generated'; output.mkdir(mode=0o700)
        with patch.dict(os.environ, environment):
            receipt = backend.generate_gtk3(ROOT, output, data, current)
        self.assertTrue(receipt['recipe_applied'])
        self.assertIsNone(receipt['kdeglobals'])
        self.assertEqual(receipt['palette']['sha256'], backend.sha(before))
        self.assertEqual(receipt['selected_scheme']['scheme_id'], scheme.stem)
        self.assertTrue(backend.palette_inputs_current(receipt))
        theme = Path(receipt['theme_path'])
        defined = dict(backend.re.findall(r'^@define-color (\w+) (#[0-9a-f]{6});$', (theme / 'common/gtk.css').read_text(), backend.re.M))
        self.assertEqual(defined, colors)
        self.assertTrue((output / 'GTK3-NATIVE-COLORS.json').is_file())
        self.assertEqual(current.read_bytes(), current_before)
        self.assertEqual(scheme.read_bytes(), before)
        # Changing the current desktop palette cannot stale an alternate
        # recipe; changing its selected scheme must stale it immediately.
        current.write_text(current_before.decode().replace('120,90,70', '150,90,70'))
        self.assertTrue(backend.palette_inputs_current(receipt))
        scheme.write_text(before.decode().replace('120,90,70', '151,91,71'))
        self.assertFalse(backend.palette_inputs_current(receipt))

    @unittest.skipUnless((ROOT / 'tools/theme-lab/build/theme-lab-colors').is_file(), 'Build the optional native KDE reader first')
    def test_alternate_gtk3_scheme_uses_kde_default_for_omitted_header_role(self):
        scheme, environment = self.native_scheme()
        text = scheme.read_text()
        text = text.replace('[Colors:Header]\nBackgroundNormal=150,160,170\n',
                            '[Colors:Header]\nBackgroundAlternate=150,160,170\n')
        text += ('[WM]\nactiveBackground=181,91,71\nactiveForeground=241,231,221\n'
                 'inactiveBackground=91,101,111\ninactiveForeground=211,201,191\n')
        scheme.write_text(text)
        self.assertNotIn('BackgroundNormal=', text.split('[Colors:Header]', 1)[1].split('[', 1)[0])
        data = model(); data['color_scheme'] = scheme.stem
        current = self.kde()
        output = self.work / 'missing-header-role'; output.mkdir(mode=0o700)
        with patch.dict(os.environ, environment):
            receipt = backend.generate_gtk3(ROOT, output, data, current)
        self.assertTrue(receipt['recipe_applied'])
        self.assertEqual(receipt['selected_scheme']['scheme_id'], scheme.stem)
        self.assertTrue(receipt['palette_inputs'])
        native = json.loads((output / 'GTK3-NATIVE-COLORS.json').read_text())
        colors = native['colors']
        self.assertEqual(colors['theme_header_background_breeze'], colors['theme_bg_color_breeze'])
        self.assertEqual(colors['theme_titlebar_background_breeze'], '#b55b47')
        self.assertEqual(colors['theme_titlebar_foreground_breeze'], '#e6d2c8')
        self.assertIn('per-colour', native['origin']['titlebar'])

    @unittest.skipUnless((ROOT / 'tools/theme-lab/build/theme-lab-colors').is_file(), 'Build the optional native KDE reader first')
    def test_native_reader_falls_back_to_window_roles_and_rejects_symlink(self):
        scheme = self.kde(); builder = backend.load_builder(ROOT)
        # Missing Header and WM roles remain dynamic by following the selected
        # scheme's effective Window roles instead of serializing invalid RGB.
        colors, origin = backend.native_roles(ROOT, scheme, builder.art, backend.sha(scheme.read_bytes()))
        self.assertEqual(colors['theme_header_background_breeze'], colors['theme_bg_color_breeze'])
        self.assertEqual(colors['theme_titlebar_background_breeze'], colors['theme_bg_color_breeze'])
        self.assertIn('Window palette', origin['titlebar'])
        link = self.work / 'linked.colors'; link.symlink_to(scheme)
        with self.assertRaises(OSError):
            backend.native_roles(ROOT, link, builder.art, backend.sha(scheme.read_bytes()))

    def test_output_refuses_canonical_theme_and_symlink(self):
        with self.assertRaisesRegex(ValueError, 'saída privada'):
            backend.private_output(ROOT / 'gtk/DomainOS-SR10-4', ROOT)
        with self.assertRaisesRegex(ValueError, 'saída privada'):
            backend.private_output(Path('/tmp/theme-lab-refused-output'), ROOT)
        link = self.work / 'link'; link.symlink_to(self.work)
        with self.assertRaisesRegex(ValueError, 'links'):
            backend.private_output(link / 'output', ROOT)
        public = self.work / 'public'; public.mkdir(mode=0o755)
        with self.assertRaisesRegex(ValueError, '0700'):
            backend.private_output(public, ROOT)

    def test_preview_rejects_host_before_creating_output(self):
        output = self.work / 'untouched'
        with patch.dict(os.environ, {'IRIX_DOMAINOS_PRIVATE_NAMESPACE': ''}):
            with self.assertRaisesRegex(backend.Unavailable, 'lançador privado'):
                backend.preview(ROOT, output, model(), 'unused', self.kde(), 'gtk3')
        self.assertFalse(output.exists())

    def test_namespace_marker_alone_does_not_authorize_host_preview(self):
        with patch.dict(os.environ, {'IRIX_DOMAINOS_PRIVATE_NAMESPACE': 'bwrap', 'HOME': str(self.work)}):
            with self.assertRaisesRegex(backend.Unavailable, 'lançador privado'):
                backend.private_namespace(ROOT)

    def test_private_gtk3_generation_isolates_five_control_palettes(self):
        data = model(); data['schema_version']=3; recipe = data['recipes']['gtk3']
        recipe['geometry'].update(arrow_px=13, bar_px=17, thumb_cross_px=13, control_padding_px=5, font_px=15)
        recipe['palette'].update(face_role='Colors:Window/BackgroundNormal', text_role='Colors:Window/ForegroundNormal', light=.4, shade=.3, trough=.18)
        role_pairs = {
            'push': ('Colors:Window/BackgroundNormal', 'Colors:Window/ForegroundNormal'),
            'toggle': ('Colors:Button/BackgroundNormal', 'Colors:Button/ForegroundNormal'),
            'combo': ('Colors:View/BackgroundNormal', 'Colors:View/ForegroundNormal'),
            'spin': ('Colors:Selection/BackgroundNormal', 'Colors:Selection/ForegroundNormal'),
            'arrow': ('Colors:Tooltip/BackgroundNormal', 'Colors:Tooltip/ForegroundNormal'),
        }
        recipe['control_palettes'] = {}
        for control, (face, text) in role_pairs.items():
            tailored = dict(recipe['palette'])
            tailored.update(face_role=face, text_role=text, light=.31, shade=.27, trough=.19)
            recipe['control_palettes'][control] = tailored
        builder = backend.load_builder(ROOT)
        original_roles, original_plan = copy.deepcopy(builder.art.ROLES), builder.art.pixel_plan
        # Artificial effective-state export: state values are independently
        # supplied rather than inferred from a normal RGB by the backend.
        colors = {}
        for family, names in builder.art.ROLES.items():
            for index, name in enumerate(names):
                colors.setdefault(name, '#%02x%02x%02x' % (40 + index*10, 60 + index*10, 80 + index*10))
        kde = self.kde()
        config, _ = backend.read_kde(kde)
        for name, family in backend.ROLE_FAMILIES.items():
            if config.has_section(name.split('/', 1)[0]):
                colors[builder.art.ROLES[family][0]] = '#%02x%02x%02x' % backend.rgb_role(config, name)
        export = self.work / 'gtk-3.0/colors.css'; export.parent.mkdir()
        export.write_text(''.join('@define-color ' + name + ' ' + color + ';\n' for name, color in colors.items()))
        output = self.work / 'generated'; output.mkdir(mode=0o700)
        receipt = backend.generate_gtk3(ROOT, output, data, kde)
        theme = Path(receipt['theme_path'])
        self.assertTrue(receipt['recipe_applied'])
        self.assertFalse(receipt['historical_fidelity_claimed'])
        self.assertEqual(receipt['palette']['sha256'], backend.sha(export.read_bytes()))
        self.assertEqual(builder.art.ROLES, original_roles)
        self.assertIs(builder.art.pixel_plan, original_plan)
        css = (theme / 'common/gtk-3.0-overrides.css').read_text()
        common = (theme / 'common/gtk.css').read_text()
        control_export=json.loads((theme/'common/CONTROL-PALETTE-EXPORT.json').read_text())
        self.assertEqual(control_export['status'],'applied')
        self.assertEqual(control_export['controls'], sorted(role_pairs))
        self.assertEqual(receipt['control_palette_export'],control_export)
        self.assertIn('button:not(.toggle):not(.combo):not(.up):not(.down):not(.theme-lab-arrow)', css)
        self.assertIn('button.toggle', css)
        self.assertIn('combobox > box > button.combo', css)
        self.assertIn('spinbutton > button', css)
        self.assertIn('button.theme-lab-arrow', css)
        aliases = {
            'Colors:Window/BackgroundNormal': 'theme_bg_color_breeze',
            'Colors:Window/ForegroundNormal': 'theme_fg_color_breeze',
            'Colors:Button/BackgroundNormal': 'theme_button_background_normal_breeze',
            'Colors:Button/ForegroundNormal': 'theme_button_foreground_normal_breeze',
            'Colors:View/BackgroundNormal': 'theme_base_color_breeze',
            'Colors:View/ForegroundNormal': 'theme_text_color_breeze',
            'Colors:Selection/BackgroundNormal': 'theme_selected_bg_color_breeze',
            'Colors:Selection/ForegroundNormal': 'theme_selected_fg_color_breeze',
            'Colors:Tooltip/BackgroundNormal': 'tooltip_background_breeze',
            'Colors:Tooltip/ForegroundNormal': 'tooltip_text_breeze',
        }
        for face, text in role_pairs.values():
            self.assertIn('@' + aliases[face], css)
            self.assertIn('@' + aliases[text], css)
        self.assertIn('@theme_button_background_normal_breeze',css)
        self.assertIn('min-width: 13px', css)
        self.assertIn('font-size: 15px', css)
        self.assertIn('padding: 5px', css)
        self.assertIn('mix(@theme_bg_color_breeze, #ffffff, 0.4)', css)
        self.assertIn('@insensitive_bg_color_breeze', css)
        self.assertIn(':disabled:backdrop', css)
        self.assertIn('@theme_fg_color_breeze', common)
        manifest = json.loads((theme / 'common/adaptive/MANIFEST.json').read_text())
        self.assertEqual(backend.mask_metadata(builder, recipe['geometry'])['assets'], manifest['assets'])
        self.assertEqual(manifest['assets']['gtk3-stepper-down-normal']['width'], 13)
        self.assertEqual(manifest['assets']['gtk3-stepper-down-pressed']['width'], 13)
        self.assertIn('button.theme-lab-arrow:active:disabled:backdrop', css)
        # The new private consumer reuses generated masks; every referenced
        # arrow layer must exist at the contract's intrinsic dimensions.
        for resource in backend.re.findall(r'url\("?(adaptive/gtk3-stepper-down-[^"\)]+)', css):
            self.assertTrue((theme / 'common' / resource).is_file(), resource)
        defined = dict(backend.re.findall(r'^@define-color (\w+) (#[0-9a-f]{6});$', common, backend.re.M))
        self.assertEqual(defined, colors)
        self.assertFalse((theme / 'gtk-2.0').exists())
        self.assertFalse((theme / 'gtk-4.0').exists())
        # Real generator outputs, artificial effective-role inputs: verify the
        # compact package can reconstruct every translated file byte for byte.
        from artifact_delta import receipt_inventory, package_files, reconstruct_files
        changed = copy.deepcopy(data)
        changed['recipes']['gtk3']['geometry']['control_padding_px'] = 6
        second = self.work / 'changed-generated'; second.mkdir(mode=0o700)
        proposed = backend.generate_gtk3(ROOT, second, changed, kde)
        base_root, base_files = receipt_inventory(output, receipt, backend.read_file)
        _, proposed_files = receipt_inventory(second, proposed, backend.read_file)
        package = self.work / 'compact-package'
        delta = package_files(base_files, proposed_files, package)
        self.assertGreater(len(delta['reuse']), 0)
        self.assertLess(len(delta['payload']), len(delta['files']))
        rebuilt = self.work / 'reconstructed'
        reconstruct_files(delta, package, base_root, rebuilt, backend.read_file)
        self.assertEqual({str(p.relative_to(rebuilt)): p.read_bytes()
                          for p in rebuilt.rglob('*') if p.is_file()}, proposed_files)
        # Invalidate only the input snapshot, proving stale exported palette is
        # rejected before another generated theme or host write is attempted.
        kde.write_text(kde.read_text().replace('120,90,70', '150,90,70'))
        other = self.work / 'stale'; other.mkdir(mode=0o700)
        with self.assertRaisesRegex(backend.Unavailable, 'não corresponde'):
            backend.generate_gtk3(ROOT, other, data, kde)
        self.assertFalse((other / 'data').exists())


if __name__ == '__main__':
    unittest.main()
