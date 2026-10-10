# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify DomainOS's independent color/geometry and generated resource closure."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
sys.path.insert(0, str(ROOT/'gtk/tools'))
import domainos_motif_art as art
import gtk2_domainos_palette as gtk2
from gtk2_palette import REQUIRED
import kvantum_domainos_palette as kv
import build_kde_domainos as builder
from theme_transaction import Failure


def exported(kind='blue'):
    result = dict(art.DEFAULT)
    for name in REQUIRED:
        result.setdefault(name, '#ffffff' if any(word in name for word in ('fg_', 'foreground', 'text')) else '#78a0d5')
    if kind != 'blue':
        for name in result:
            result[name] = '#343434' if kind == 'dark' else '#e8d070'
            if any(word in name for word in ('fg_', 'foreground', 'text')):
                result[name] = '#eeeeee' if kind == 'dark' else '#151515'
    return result


QT = {group: {role: '#123456' for role in ('Base', 'AlternateBase', 'Shadow')} for group in ('Active', 'Inactive', 'Disabled')}
QT['Disabled']['Base'] = '#778899'
QT['Disabled']['AlternateBase'] = '#99aabb'


def css(palette):
    return ''.join('@define-color '+name+' '+value+';\n' for name, value in sorted(palette.items())).encode()


class MotifArtworkTest(unittest.TestCase):
    def test_bevel_has_two_uniform_bands_without_irix_black_outline(self):
        pixels = art.surface(width=72, height=28)
        self.assertEqual(pixels[0][10], 'light')
        self.assertEqual(pixels[1][10], 'light')
        self.assertEqual(pixels[2][10], 'face')
        self.assertEqual(pixels[25][10], 'face')
        self.assertEqual(pixels[26][10], 'dark')
        self.assertEqual(pixels[27][10], 'dark')
        down = art.surface('pressed', width=72, height=28)
        self.assertEqual(down[0][10], 'dark')
        self.assertEqual(down[27][10], 'light')

    def test_arrows_are_three_dimensional_and_rotation_preserves_pixels(self):
        arrows = [art.triangle(direction=direction) for direction in ('up', 'down', 'left', 'right')]
        for pixels in arrows:
            self.assertEqual((len(pixels), len(pixels[0])), (12, 12))
            self.assertEqual({token for row in pixels for token in row if token}, {'face', 'light', 'dark'})
        self.assertEqual(arrows[1], [list(reversed(row)) for row in reversed(arrows[0])])
        self.assertEqual(arrows[2], [list(row) for row in zip(*arrows[0])])
        self.assertEqual(art.triangle('pressed')[3][4], 'dark')

    def test_thumb_has_no_irix_grip_and_toggles_have_no_static_colored_mark(self):
        pixels, family, border = art.assets()['scroll-thumb-normal']
        self.assertEqual(border, 2)
        self.assertEqual({token for row in pixels[2:-2] for token in row[2:-2]}, {'face'})
        for kind in ('check', 'radio'):
            pixels = art.toggle(kind, selected=True)
            self.assertNotIn('ink', {token for row in pixels for token in row})
            self.assertEqual((len(pixels), len(pixels[0])), (14, 14))

    def test_selected_controls_darken_the_interior_and_invert_relief(self):
        for kind in ('check', 'radio'):
            off, on = art.toggle(kind), art.toggle(kind, selected=True)
            self.assertEqual(off[6][6], 'face')
            self.assertEqual(on[6][6], 'trough')
            self.assertEqual(art.toggle(kind, 'pressed')[6][6], 'trough')
            self.assertEqual(art.evaluate(art.pixel_plan('button', on[6][6]), art.DEFAULT), '#6688b5')
            for scheme in ('dark', 'yellow'):
                palette = exported(scheme)
                self.assertNotEqual(art.evaluate(art.pixel_plan('button', on[6][6]), palette), '#6688b5')

    def test_reference_relief_matches_native_primary_and_secondary_color_sets(self):
        for family, expected in (('button', ('#c4d5ed', '#3e536e', '#6688b5')),
                                 ('header', ('#a3d0e6', '#194b63', '#2a80a9'))):
            actual = tuple(art.evaluate(art.pixel_plan(family, token), art.DEFAULT)
                           for token in ('light', 'dark', 'trough'))
            self.assertEqual(actual, expected)

    def test_inset_view_preserves_its_face_and_uses_container_shadows(self):
        palette = exported()
        palette['theme_base_color_breeze'] = '#456789'
        self.assertEqual(art.evaluate(art.pixel_plan('view', 'face'), palette), '#456789')
        self.assertEqual(art.evaluate(art.pixel_plan('view', 'light'), palette), '#c4d5ed')
        self.assertEqual(art.evaluate(art.pixel_plan('view', 'dark'), palette), '#3e536e')
        self.assertEqual(art.pixel_plan('view', 'light', inactive=True, disabled=True)['role'],
                         art.role('window', inactive=True, disabled=True))

    def test_semantic_roles_do_not_reuse_active_colors_for_inactive_disabled(self):
        palette = exported()
        palette['theme_button_background_backdrop_breeze'] = '#111122'
        palette['theme_button_background_insensitive_breeze'] = '#333344'
        palette['theme_button_background_backdrop_insensitive_breeze'] = '#555566'
        values = [art.evaluate(art.pixel_plan('button', 'face', inactive=inactive, disabled=disabled), palette)
                  for inactive, disabled in ((False, False), (True, False), (False, True), (True, True))]
        self.assertEqual(values, ['#78a0d5', '#111122', '#333344', '#555566'])


class KvantumDomainOSTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT/'kvantum'/art.NAME
        cls.svg = (source/(art.NAME+'.svg')).read_bytes()
        cls.config = (source/(art.NAME+'.kvconfig')).read_bytes()

    def test_canonical_bytes_match_public_generator(self):
        self.assertEqual(self.svg, art.svg())
        self.assertEqual(self.config, art.kvconfig())

    def test_three_schemes_change_paint_without_geometry_or_source_mutation(self):
        results = [kv.render(self.svg, self.config, exported(kind), native_qt_palette=QT) for kind in ('blue', 'dark', 'yellow')]
        self.assertEqual(len({hashlib.sha256(value[0]).hexdigest() for value in results}), 3)
        for svg, config, coverage in results:
            self.assertTrue(coverage['geometryUnchanged'])
            self.assertEqual(art.geometry_sha(self.svg), art.geometry_sha(svg))
            self.assertIn(b'base.color=#123456', config)
            self.assertEqual(len(coverage['config']['backendLimitations']), 2)

    def test_modified_source_and_missing_native_colors_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source changed'):
            kv.render(self.svg+b'\n', self.config, exported(), native_qt_palette=QT)
        palette = exported(); del palette['theme_button_background_backdrop_breeze']
        with self.assertRaisesRegex(ValueError, 'native DomainOS'):
            kv.render(self.svg, self.config, palette, native_qt_palette=QT)

    def test_native_protocol_has_arrow_and_selection_aliases(self):
        ids = {node.get('id') for node in ET.fromstring(self.svg).iter() if node.get('id')}
        for name in ('dm-arrow-up-normal', 'dm-stepper-left-normal', 'dm-check-checked-normal',
                     'dm-radio-checked-focused-inactive', 'dm-check-tristate-normal', 'dm-command-default-top'):
            self.assertIn(name, ids)


class GtkDomainOSTest(unittest.TestCase):
    def test_gtk3_shared_scrollbar_contract_has_no_local_geometry_fallback(self):
        contract = builder.gtk3_scrollbar_rules()
        self.assertEqual(contract['geometry']['origin'], 'measurement_vm')
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'scrollbar-rules.json'
            for label, change in (
                ('missing boundary policy', lambda p: p.pop('range_boundary_arrow')),
                ('unsupported boundary policy', lambda p: p['range_boundary_arrow'].update(color_policy='fixed_native_rgb')),
            ):
                changed = copy.deepcopy(contract)
                change(changed['palette'])
                path.write_text(json.dumps(changed))
                with self.subTest(case=label), self.assertRaisesRegex(ValueError, 'Invalid DomainOS scrollbar contract'):
                    builder.gtk3_scrollbar_rules(path)
            for label, change in (
                ('missing arrow', lambda g: g.pop('arrow_px')),
                ('inconsistent bar', lambda g: g.update(bar_px=g['bar_px']+1)),
                ('inconsistent thumb', lambda g: g.update(thumb_cross_px=g['thumb_cross_px']+1)),
                ('noninteger shadow', lambda g: g.update(shadow_px=True)),
                ('incompatible inset', lambda g: g.update(view_inset_px=g['view_inset_px']+1)),
            ):
                changed = copy.deepcopy(contract)
                change(changed['geometry'])
                path.write_text(json.dumps(changed))
                with self.subTest(case=label), self.assertRaisesRegex(ValueError, 'Invalid DomainOS scrollbar contract'):
                    builder.gtk3_scrollbar_rules(path)
            # A consistent private contract changes the actual GTK3 masks/CSS;
            # this proves the loader is a drawing input, not just provenance.
            changed = copy.deepcopy(contract)
            geometry = changed['geometry']
            geometry['arrow_px'] += 2
            geometry['thumb_cross_px'] = geometry['arrow_px']
            geometry['bar_px'] = geometry['arrow_px']+2*geometry['shadow_px']
            path.write_text(json.dumps(changed))
            loaded = builder.gtk3_scrollbar_rules(path)['geometry']
            self.assertEqual(len(builder.gtk3_arrow(geometry=loaded)), geometry['arrow_px'])
            manifest = builder.masks(Path(temporary)/'adaptive', geometry=loaded)
            css = builder.gtk3_css(manifest, geometry=loaded)
            self.assertIn('background-size: 13px 13px', css)
            self.assertIn('min-width: 9px; min-height: 18px', css)

    def test_gtk3_direction_keeps_upper_left_light_and_complete_shadowed_tip(self):
        down = builder.gtk3_arrow(direction='down')
        self.assertEqual(down[0][5], 'light')  # top edge of the triangle
        self.assertEqual(down[4][2], 'light')  # left slope
        self.assertEqual(down[4][8], 'dark')  # right slope
        self.assertEqual(down[10][5], 'dark')  # centered lower tip
        right = builder.gtk3_arrow(direction='right')
        self.assertEqual(right[5][0], 'light')  # left base
        self.assertEqual(right[2][4], 'light')  # upper slope
        self.assertEqual(right[8][4], 'dark')  # lower slope
        for direction in ('up', 'down', 'left', 'right'):
            normal = builder.gtk3_arrow(direction=direction)
            pressed = builder.gtk3_arrow('pressed', direction)
            self.assertEqual((len(normal), len(normal[0])), (11, 11))
            for y in range(11):
                for x in range(11):
                    expected = {'light': 'dark', 'dark': 'light'}.get(normal[y][x], normal[y][x])
                    self.assertEqual(pressed[y][x], expected)
        # Measured SR10.4 arrow growth is one pixel on each side every two
        # rows, rather than an even12px silhouette with alternate row widths.
        up = builder.gtk3_arrow(direction='up')
        self.assertEqual([sum(token is not None for token in row) for row in up],
                         [1, 3, 3, 5, 5, 7, 7, 9, 9, 11, 11])

    def test_source_authorization_checks_pixels_across_png_encoders(self):
        from PIL import Image
        pixels, family, _ = art.assets()['stepper-up-normal']
        reference = gtk2.png(pixels, family, art.DEFAULT)
        with Image.open(io.BytesIO(reference)) as source:
            decoded = source.convert('RGBA')
        buffer = io.BytesIO()
        decoded.save(buffer, format='PNG', compress_level=0)
        self.assertNotEqual(reference, buffer.getvalue())
        self.assertTrue(gtk2.same_pixels(buffer.getvalue(), reference))
        decoded.putpixel((5, 5), (0, 0, 0, 255))
        changed = io.BytesIO()
        decoded.save(changed, format='PNG')
        self.assertFalse(gtk2.same_pixels(changed.getvalue(), reference))

    def test_published_packages_have_complete_portable_resource_manifest(self):
        for name in builder.IDENTITIES:
            source = ROOT/'gtk'/name
            manifest = json.loads((source/'MANIFEST.json').read_text())
            actual = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in source.rglob('*') if path.is_file() and path != source/'MANIFEST.json'}
            self.assertEqual(actual, manifest['files'])
            self.assertIn('LICENSE', actual)
            for path in (source/'common/gtk.css', source/'gtk-2.0/gtkrc'):
                self.assertNotIn('/home/', path.read_text())
                self.assertNotIn('IrixClassic', path.read_text())

    def test_gtk2_preparation_is_immutable_and_distinct_by_scheme(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/'generated'
            outputs = [gtk2.prepare_domainos(ROOT/'gtk'/ (art.NAME+'-KDE'), css(exported(kind)), destination) for kind in ('blue', 'dark', 'yellow')]
            self.assertFalse(destination.exists())
            self.assertEqual(len({value.directory for value in outputs}), 3)
            for value in outputs:
                self.assertGreater(value.manifest['asset_count'], 50)
                self.assertNotIn(b'../common/assets/', value.files[value.gtkrc])
                self.assertIn(b'function = STEPPER', value.files[value.gtkrc])

    def test_gtk2_rejects_modified_assets_even_with_modified_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/'theme'
            builder.build(source)
            target = source/'common/assets/stepper-up-normal.png'
            from PIL import Image
            with Image.open(target) as source_image:
                changed = source_image.convert('RGBA')
            changed.putpixel((5, 5), (0, 0, 0, 255))
            changed.save(target)
            manifest = json.loads((source/'MANIFEST.json').read_text())
            manifest['files']['common/assets/stepper-up-normal.png'] = hashlib.sha256(target.read_bytes()).hexdigest()
            (source/'MANIFEST.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(Failure, 'desenho original'):
                gtk2.prepare_domainos(source, css(exported()), Path(folder)/'output')

    def test_gtk2_missing_native_roles_have_a_transaction_diagnostic(self):
        palette = exported()
        del palette['theme_button_decoration_focus_insensitive_breeze']
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/'generated'
            with self.assertRaisesRegex(Failure, 'papéis nativos completos'):
                gtk2.prepare_domainos(ROOT/'gtk'/(art.NAME+'-KDE'), css(palette), destination)
            self.assertFalse(destination.exists())

    def test_gtk3_stepper_geometry_is_explicit_in_all_ambient_states(self):
        contents = (ROOT/'gtk'/ (art.NAME+'-KDE')/'common/gtk-3.0-overrides.css').read_text()
        for state in ('', ':backdrop', ':disabled', ':disabled:backdrop'):
            for selector in ('scrollbar.vertical button.up', 'scrollbar.vertical button.down',
                             'scrollbar.horizontal button.up', 'scrollbar.horizontal button.down'):
                for pressed in ('', ':active'):
                    self.assertIn(selector+pressed+state+' {', contents)
        self.assertIn('-gtk-icon-source: none', contents)
        self.assertIn('background-size: 11px 11px', contents)
        self.assertIn('-GtkScrolledWindow-scrollbar-spacing: 4', contents)
        self.assertIn('scrollbar.vertical button.up { margin-bottom: 1px; }', contents)
        self.assertNotIn('background-size: 100%', contents)


if __name__ == '__main__': unittest.main()
