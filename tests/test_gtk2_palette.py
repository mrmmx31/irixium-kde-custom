# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure GTK2 palette generation; no native sessions or personal RC files."""
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import gtk2_palette as gtk2
from theme_transaction import Failure


def native_export(overrides=None):
    # Literal syntax of KDE GTK Config, with deliberately distinct role colors.
    roles = {name:'#616263' for name in gtk2.REQUIRED}
    roles.update({
        'theme_bg_color_breeze':'#304050', 'theme_fg_color_breeze':'#ededed',
        'theme_base_color_breeze':'#102030', 'theme_text_color_breeze':'#e1e2e3',
        'theme_selected_bg_color_breeze':'#d5b420', 'theme_selected_fg_color_breeze':'#182128',
        'theme_button_background_normal_breeze':'#456789',
        'theme_button_foreground_normal_breeze':'#f2f3f4',
        'theme_button_background_insensitive_breeze':'#708090',
        'theme_button_foreground_insensitive_breeze':'#a0b0c0',
        'insensitive_bg_color_breeze':'#344454', 'insensitive_fg_color_breeze':'#647484',
        'insensitive_base_color_breeze':'#203040', 'insensitive_base_fg_color_breeze':'#8090a0',
        'insensitive_selected_bg_color_breeze':'#a59470',
        'tooltip_background_breeze':'#f3d4a5', 'tooltip_text_breeze':'#132435',
        'error_color_breeze':'#db3659', 'link_color_breeze':'#45b8e2',
        'link_visited_color_breeze':'#8a65b5',
        'theme_header_background_breeze':'#224466', 'theme_header_foreground_breeze':'#f1d3b5',
        'theme_button_decoration_focus_breeze':'#a3b4c5',
    })
    roles.update(overrides or {})
    return ''.join('@define-color '+key+' '+value+';\n' for key,value in sorted(roles.items())).encode()


class Gtk2PaletteTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='.gtk2-palette-test-',dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.theme = ROOT/'gtk/IrixClassic'
        self.destination = self.root/'XDG data with spaces'/'generated GTK2'
        self.palette = gtk2.exported_palette(native_export())

    def prepared(self, overrides=None):
        return gtk2.prepare(self.theme,native_export(overrides),self.destination)

    def test_export_requires_actual_roles_instead_of_guessing_disabled_effects(self):
        with self.assertRaisesRegex(Failure,'Papéis KDE ausentes'):
            gtk2.exported_palette(b'@define-color theme_bg_color_breeze #123456;\n')
        with self.assertRaisesRegex(Failure,'UTF-8'):
            gtk2.exported_palette(b'\xff')
        with self.assertRaisesRegex(Failure,'grande'):
            gtk2.exported_palette(b'x'*(256*1024+1))
        bad = native_export().replace(b'#456789',b'rgb(1, 2, 3)')
        with self.assertRaisesRegex(Failure,'theme_button_background_normal_breeze'):
            gtk2.exported_palette(bad)

    def test_family_roles_are_distinct_and_marks_use_effective_native_colors(self):
        cases = [('command-normal.png','#999999','theme_button_background_normal_breeze'),
                 ('menupanel-normal.png','#c1c1c1','theme_bg_color_breeze'),
                 ('menustrip-normal.png','#c1c1c1','theme_header_background_breeze'),
                 ('input-normal.png','#b6b6aa','theme_base_color_breeze'),
                 ('input-disabled.png','#b6b6aa','insensitive_base_color_breeze'),
                 ('command-disabled.png','#999999','theme_button_background_insensitive_breeze'),
                 ('arrow-up-normal.png','#4c4c4c','theme_button_foreground_normal_breeze'),
                 ('arrow-up-disabled.png','#858585','theme_button_foreground_insensitive_breeze'),
                 ('menurow-focused.png','#dfdfdf','theme_selected_bg_color_breeze'),
                 ('meter-fill-normal.png','#719e9e','theme_selected_bg_color_breeze'),
                 ('meter-fill-disabled.png','#8eaaaa','insensitive_selected_bg_color_breeze'),
                 ('check-on.png','#cc0000','error_color_breeze'),
                 ('radio-on.png','#0000cc','link_color_breeze'),
                 ('check-on-disabled.png','#858585','theme_button_foreground_insensitive_breeze'),
                 ('radio-on-disabled.png','#858585','theme_button_foreground_insensitive_breeze')]
        for name,color,role in cases:
            with self.subTest(asset=name):
                self.assertEqual(gtk2.asset_color(name,color,self.palette),self.palette[role])
        self.assertEqual(gtk2.asset_color('check-on.png','#660000',self.palette),'#6e1b2c')
        self.assertEqual(gtk2.asset_css_expression('command-normal.png','#999999'),
                         '@theme_button_background_normal_breeze')
        self.assertIn('mix(@theme_button_background_normal_breeze, #ffffff,',
                      gtk2.asset_css_expression('command-normal.png','#e1e1e1'))

    def test_shared_plan_covers_all_54_gtk3_gtk4_referenced_maps_without_global_rgb_mapping(self):
        css=[self.theme/'common/gtk.css',self.theme/'gtk-3.0/gtk.css',self.theme/'gtk-4.0/gtk.css']
        names=set()
        for source in css:names.update(re.findall(r'assets/([^"\)]+\.png)',source.read_text()))
        self.assertEqual(len(names),54)
        for name in sorted(names):
            image=Image.open(self.theme/'common/assets'/name).convert('RGBA')
            for r,g,b,a in set(image.getdata()):
                if a:
                    with self.subTest(asset=name,color=(r,g,b)):
                        expression=gtk2.asset_css_expression(name,gtk2._hex((r,g,b)))
                        self.assertTrue(expression.startswith(('@','mix(@')))
        self.assertEqual(gtk2.asset_color('spin-normal.png','#999999',self.palette),self.palette['theme_button_background_normal_breeze'])
        self.assertEqual(gtk2.asset_color('stepper-up-normal.png','#000000',self.palette),self.palette['theme_button_foreground_normal_breeze'])
        self.assertEqual(gtk2.asset_color('stipple.png','#c1c1c1',self.palette),self.palette['theme_bg_color_breeze'])
        self.assertNotEqual(gtk2.asset_color('command-normal.png','#999999',self.palette),
                            gtk2.asset_color('stipple.png','#999999',self.palette))

    def test_shadows_keep_band_order_and_pressure_swaps_native_bevel(self):
        result = self.prepared()
        def pixels(name):
            return Image.open(io.BytesIO(result.files[result.directory/'assets'/name])).convert('RGBA')
        normal, pressed = pixels('command-normal.png'), pixels('command-pressed.png')
        self.assertEqual(normal.getpixel((12,12))[:3],(69,103,137))
        self.assertEqual(normal.getpixel((12,0)),pressed.getpixel((12,0)))
        self.assertNotEqual(normal.getpixel((12,1)),pressed.getpixel((12,1)))
        luminosity=lambda rgb:sum(rgb[:3])
        self.assertGreater(luminosity(normal.getpixel((12,1))),luminosity(normal.getpixel((12,12))))
        self.assertLess(luminosity(pressed.getpixel((12,1))),luminosity(pressed.getpixel((12,12))))

    def test_all_referenced_assets_preserve_size_alpha_masks_and_rc_engine_geometry(self):
        original=(self.theme/'gtk-2.0/gtkrc').read_text()
        expected_names=set(gtk2._ASSET.findall(original))
        self.assertEqual(len(expected_names),87)
        expected_names.update(f'stepper-{direction}-{state}.png'
                              for direction in ('up','down','left','right')
                              for state in ('normal','pressed','toggled','disabled'))
        for variant in ({}, {'theme_bg_color_breeze':'#f4e390','theme_button_background_normal_breeze':'#dbce70'},
                        {'theme_bg_color_breeze':'#101820','theme_button_background_normal_breeze':'#28313a'}):
            result=self.prepared(variant)
            self.assertEqual(result.manifest['asset_count'],103)
            self.assertEqual(set(result.manifest['source_assets']),expected_names)
            self.assertEqual(result.manifest['scrollbars']['native_recipe'],'pixmap-STEPPER')
            for name in sorted(expected_names):
                source=Image.open(self.theme/'common/assets'/name).convert('RGBA')
                generated=Image.open(io.BytesIO(result.files[result.directory/'assets'/name])).convert('RGBA')
                with self.subTest(asset=name,variant=variant):
                    self.assertEqual(source.size,generated.size)
                    self.assertEqual(source.getchannel('A').tobytes(),generated.getchannel('A').tobytes())
            generated_rc=result.files[result.gtkrc].decode()
            old_geometry=re.findall(r'(?:border\s*=\s*\{[^}]+\}|(?:overlay_)?stretch\s*=\s*\w+|[xy]thickness\s*=\s*\d+|Gtk\w+::[\w-]+\s*=\s*[^\n]+)',original)
            unchanged_rc='\n'.join(line for line in generated_rc.splitlines()
                                   if 'function = STEPPER' not in line)
            new_geometry=re.findall(r'(?:border\s*=\s*\{[^}]+\}|(?:overlay_)?stretch\s*=\s*\w+|[xy]thickness\s*=\s*\d+|Gtk\w+::[\w-]+\s*=\s*[^\n]+)',unchanged_rc)
            # Color roles change; every GTK2 native geometry/input directive remains.
            without_colors=lambda items:[x for x in items if 'link-color' not in x]
            self.assertEqual(without_colors(old_geometry),without_colors(new_geometry))
            self.assertEqual(original.count('image {')+20,generated_rc.count('image {'))
            self.assertEqual(unchanged_rc.count('function = ARROW'),original.count('function = ARROW'))
            self.assertIn('engine "pixmap"',generated_rc)
            self.assertNotIn('../common/assets/',generated_rc)

    def test_rc_roles_buttons_selected_text_tooltips_and_user_font_are_not_fixed(self):
        result=self.prepared(); text=result.files[result.gtkrc].decode()
        self.assertIn('base[NORMAL] = "#102030"',text)
        self.assertIn('fg[INSENSITIVE] = "#647484"',text)
        self.assertIn('fg[PRELIGHT] = "#182128"',text)
        self.assertIn('fg[NORMAL] = "#f2f3f4"',text)
        self.assertIn('fg[NORMAL] = "#f1d3b5"',text)
        self.assertIn('bg[NORMAL] = "#f3d4a5"',text)
        self.assertNotIn('gtk-font-name',text)
        self.assertNotIn('gtk-theme-name',text)
        self.assertIn('style : rc "irixclassic-kde-default"',text)
        self.assertIn('selected_bg_color:#d5b420\\nselected_fg_color:#182128',text)

    def test_preparation_is_deterministic_and_never_writes_source_or_destination(self):
        relevant=[self.theme/'gtk-2.0/gtkrc',*sorted((self.theme/'common/assets').glob('*.png'))]
        hashes=lambda:{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in relevant}
        before=hashes(); first,second=self.prepared(),self.prepared()
        self.assertEqual(first.directory,second.directory)
        self.assertEqual(first.files,second.files)
        self.assertFalse(self.destination.exists())
        self.assertEqual(before,hashes())
        different=self.prepared({'theme_button_background_normal_breeze':'#c0a038'})
        self.assertNotEqual(first.directory,different.directory)
        manifest=json.loads(first.files[first.directory/'manifest.json'])
        self.assertEqual(manifest['id'],first.directory.name)
        for relative,digest in manifest['generated'].items():
            self.assertEqual(hashlib.sha256(first.files[first.directory/relative]).hexdigest(),digest)

    def test_rc_paths_are_relocated_and_quoted_without_checkout_or_cwd_dependencies(self):
        result=self.prepared()
        assets=re.findall(r'(?:overlay_)?file\s*=\s*("(?:[^"\\]|\\.)*")',result.files[result.gtkrc].decode())
        self.assertTrue(assets)
        for literal in assets:
            relative=Path(json.loads(literal))
            self.assertFalse(relative.is_absolute())
            path=result.directory/relative
            self.assertTrue(path.is_relative_to(result.directory/'assets'))
            self.assertIn(path,result.files)
        other=gtk2.prepare(self.theme,native_export(),self.root/'Other XDG path')
        self.assertEqual(result.directory.name,other.directory.name)
        self.assertNotIn(str(result.directory),other.files[other.gtkrc].decode())

    def test_include_preserves_all_user_directives_replaces_only_owned_block_and_removes_exactly(self):
        original=b'include "/personal/other.rc"\n# private comments\ngtk-font-name="User font 13"'
        a,b=self.root/'generated A'/ 'gtkrc',self.root/'generated B'/'gtkrc'
        first=gtk2.include_palette(original,a)
        self.assertEqual(first.count(gtk2.BEGIN.encode()),1)
        self.assertEqual(gtk2.include_palette(first,a),first)
        second=gtk2.include_palette(first,b)
        self.assertNotIn(str(a).encode(),second)
        self.assertIn(str(b).encode(),second)
        self.assertTrue(second.startswith(original))
        self.assertEqual(gtk2.include_palette(second,None),original)
        self.assertIn(b'include "/personal/other.rc"',second)

    def test_refuse_ambiguous_owned_blocks_links_external_assets_and_unknown_families(self):
        for broken in (gtk2.BEGIN,gtk2.END,gtk2.BEGIN+gtk2.END+gtk2.BEGIN+gtk2.END,
                       gtk2.END+gtk2.BEGIN):
            with self.assertRaises(Failure):gtk2.include_palette(broken.encode(),self.root/'gtkrc')
        with self.assertRaises(Failure):gtk2.include_palette(b'',self.root/'bad\npath')
        link=self.root/'linked';link.symlink_to(self.destination)
        with self.assertRaises(Failure):gtk2.prepare(self.theme,native_export(),link)
        theme=self.root/'Changed theme';(theme/'gtk-2.0').mkdir(parents=True)
        original=(self.theme/'gtk-2.0/gtkrc').read_text()
        (theme/'gtk-2.0/gtkrc').write_text(original.replace('../common/assets/command-normal.png','/outside.png'))
        with self.assertRaisesRegex(Failure,'dependência externa'):
            gtk2.prepare(theme,native_export(),self.destination)
        with self.assertRaisesRegex(Failure,'Família'):
            gtk2.asset_color('unknown-normal.png','#999999',self.palette)
        with self.assertRaisesRegex(Failure,'sem papel'):
            gtk2.asset_color('command-normal.png','#123456',self.palette)


if __name__=='__main__':unittest.main()
