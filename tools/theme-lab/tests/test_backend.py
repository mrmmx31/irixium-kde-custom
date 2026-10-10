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


def model():
    geometry = dict(zip(backend.GEOMETRY, (15, 2, 11, 11, 1, 4, 2, 4, 13)))
    palette = dict(backend.DEFAULT_ROLES, **backend.FACTORS)
    return {'schema_version': 1, 'kind': 'theme_lab_project', 'name': 'Artificial project',
            'reference': '', 'selected_family': 'gtk3', 'native_measured': geometry.copy(),
            'recipes': {family: {'geometry': geometry.copy(), 'palette': palette.copy(), 'notes': ''}
                        for family in backend.FAMILIES},
            'picked': {'valid': True, 'rgb16': [65535, 0, 0], 'rgb8': [255, 0, 0], 'purpose': 'evidence_only'}}


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='theme-lab-backend-')
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def kde(self):
        path = self.work / 'kdeglobals'
        path.write_text('[Colors:Button]\nBackgroundNormal=120,90,70\nForegroundNormal=30,20,10\n'
                        '[Colors:Window]\nBackgroundNormal=80,100,120\nForegroundNormal=10,20,30\n'
                        '[Colors:View]\nBackgroundNormal=40,50,60\nForegroundNormal=200,210,220\n'
                        '[Colors:Selection]\nBackgroundNormal=50,80,110\nForegroundNormal=220,230,240\n')
        return path

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
        self.assertEqual(receipt['state'], 'disabled')
        self.assertEqual(receipt['source'], receipt['text'])
        self.assertIn('scrollbar.horizontal', receipt['source'])
        self.assertNotIn('scrollbar.vertical', receipt['source'])
        self.assertNotIn('spinbutton', receipt['source'])
        self.assertIn('@insensitive_bg_color_breeze', receipt['source'])
        self.assertIn('mix(@insensitive_bg_color_breeze, #ffffff, 0.37)', receipt['source'])
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
        self.assertNotIn('theme-lab-arrow', backend.snippet(ROOT, data, control='push')['source'])

    def test_alternate_gtk3_scheme_refuses_unavailable_native_reader_instead_of_current_export(self):
        scheme, environment = self.native_scheme()
        data = model(); data['color_scheme'] = scheme.stem
        output = self.work / 'alternate'; output.mkdir(mode=0o700)
        with patch.dict(os.environ, environment), patch.object(backend, 'native_roles', side_effect=backend.Unavailable('Leitor nativo não compilado')):
            with self.assertRaisesRegex(backend.Unavailable, 'Leitor nativo não compilado'):
                backend.generate_gtk3(ROOT, output, data, self.kde())
        self.assertFalse((output / 'data').exists())

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
    def test_native_reader_rejects_missing_wm_colour_and_symlink(self):
        scheme = self.kde(); builder = backend.load_builder(ROOT)
        # GTKConfig's invalid QColor when neither Header nor WM is present
        # must not be serialized as an artificial black control colour.
        with self.assertRaisesRegex(backend.Unavailable, 'invalid colour'):
            backend.native_roles(ROOT, scheme, builder.art, backend.sha(scheme.read_bytes()))
        link = self.work / 'linked.colors'; link.symlink_to(scheme)
        with self.assertRaises(OSError):
            backend.native_roles(ROOT, link, builder.art, backend.sha(scheme.read_bytes()))

    def test_output_refuses_canonical_theme_and_symlink(self):
        with self.assertRaisesRegex(ValueError, 'saída privada'):
            backend.private_output(ROOT / 'gtk/DomainOS-SR10-4', ROOT)
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

    def test_one_private_gtk3_generation_translates_geometry_state_roles_and_factors(self):
        data = model(); recipe = data['recipes']['gtk3']
        recipe['geometry'].update(arrow_px=13, bar_px=17, thumb_cross_px=13, control_padding_px=5, font_px=15)
        recipe['palette'].update(face_role='Colors:Window/BackgroundNormal', text_role='Colors:Window/ForegroundNormal', light=.4, shade=.3, trough=.18)
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
        # Invalidate only the input snapshot, proving stale exported palette is
        # rejected before another generated theme or host write is attempted.
        kde.write_text(kde.read_text().replace('120,90,70', '150,90,70'))
        other = self.work / 'stale'; other.mkdir(mode=0o700)
        with self.assertRaisesRegex(backend.Unavailable, 'não corresponde'):
            backend.generate_gtk3(ROOT, other, data, kde)
        self.assertFalse((other / 'data').exists())


if __name__ == '__main__':
    unittest.main()
