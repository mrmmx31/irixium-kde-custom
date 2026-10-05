# SPDX-License-Identifier: GPL-2.0-or-later
"""Upgrade/rollback and actual QML JavaScript expressions; NOT a Qt renderer.

Node.js is optional for developer tests and is not required by the installer.
"""
import contextlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
from irixium_install import Installer, InstallError, digest

V1 = (PACKAGE / 'compatibilidade/v1/AuroraeButtonGroup.qml').read_text()
V2 = (PACKAGE / 'AuroraeButtonGroup.qml').read_text()
NODE = shutil.which('node')


def expression(source, declaration, until='\n'):
    """Extract an expression verbatim, instead of recreating the formula."""
    return source.split(declaration, 1)[1].split(until, 1)[0].strip()


def javascript(program):
    result = subprocess.run([NODE, '-e', program], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.qml = self.root / 'qml/AuroraeButtonGroup.qml'
        self.rc = self.root / 'theme/Irixiumrc'
        self.state = self.root / 'state'
        self.qml.parent.mkdir()
        self.rc.parent.mkdir()
        self.rc.write_bytes((PACKAGE / 'referencia/Irixiumrc-v1').read_bytes())
        self.qml.write_text(V1)
        self.installer = Installer(self.qml, self.rc, self.state,
                                   lambda src, dst: shutil.copyfile(src, dst), PACKAGE)
        self.quiet = contextlib.redirect_stdout(io.StringIO())
        self.quiet.__enter__()

    def tearDown(self):
        self.quiet.__exit__(None, None, None)
        self.tmp.cleanup()

    def test_upgrade_from_v1_and_restore_exact_v1(self):
        old_rc = self.rc.read_bytes()
        backup = self.installer.install()
        self.assertEqual(self.qml.read_text(), V2)
        self.assertEqual(self.rc.read_bytes(), old_rc)
        self.assertEqual((backup / 'AuroraeButtonGroup.qml').read_text(), V1)
        self.installer.restore()
        self.assertEqual(self.qml.read_text(), V1)
        self.assertEqual(self.rc.read_bytes(), old_rc)

    def test_default_preserves_even_custom_title_colors(self):
        custom = self.rc.read_bytes().replace(b'0,0,0,255', b'12,34,56,255')
        self.rc.write_bytes(custom)
        self.installer.install()
        self.assertEqual(self.rc.read_bytes(), custom)

    def test_v1_dry_run_does_not_write(self):
        self.installer.install(dry_run=True)
        self.assertEqual(self.qml.read_text(), V1)
        self.assertFalse(self.state.exists())

    def test_user_modified_v1_is_not_overwritten(self):
        changed = V1.replace('frameBand: 7', 'frameBand: 9')
        self.qml.write_text(changed)
        with self.assertRaises(InstallError):
            self.installer.install()
        self.assertEqual(self.qml.read_text(), changed)
        self.assertFalse(self.state.exists())

    def test_v2_reinstallation_does_not_create_new_backup(self):
        backup = self.installer.install()
        self.assertIsNone(self.installer.install())
        self.assertEqual(list((self.state/'backups').iterdir()), [backup])

    def test_second_restore_can_return_to_before_v1(self):
        # Recreate a v1-format backup, including its original colors.
        original_qml = (PACKAGE / 'upstream/AuroraeButtonGroup.qml').read_bytes()
        original_rc = (PACKAGE / 'upstream/Irixiumrc').read_bytes()
        old = self.state / 'backups/old-v1'
        old.mkdir(parents=True)
        (old / 'AuroraeButtonGroup.qml').write_bytes(original_qml)
        (old / 'Irixiumrc').write_bytes(original_rc)
        old_manifest = {
            'format': 1, 'status': 'installed',
            'qml_path': str(self.qml), 'rc_path': str(self.rc),
            'qml_changed': True, 'rc_changed': True,
            'qml_before': digest(original_qml), 'qml_after': digest(self.qml.read_bytes()),
            'rc_before': digest(original_rc), 'rc_after': digest(self.rc.read_bytes()),
            'rc_mode': 0o644,
        }
        (old / 'manifest.json').write_text(json.dumps(old_manifest))
        (self.state / 'latest').write_text(str(old) + '\n')
        self.installer.install()
        self.installer.restore()
        self.assertEqual(self.qml.read_text(), V1)
        self.assertEqual((self.state/'latest').read_text().strip(), str(old.resolve()))
        self.installer.restore()
        self.assertEqual(self.qml.read_bytes(), original_qml)
        self.assertEqual(self.rc.read_bytes(), original_rc)
        self.assertFalse((self.state/'latest').exists())


@unittest.skipUnless(NODE, 'Node.js unavailable; JavaScript-expression tests not run')
class QmlExpressionRegressionTests(unittest.TestCase):
    def button_result(self, source, button, types, index):
        body = source.split('property var sourceButton: modelData', 1)[1]
        visible = expression(body, 'visible:', '\n                x:')
        type_expression = (expression(body, 'readonly property bool isButtonEntry:', '\n                visible:')
                           if 'readonly property bool isButtonEntry:' in body else 'true')
        return javascript('const sourceButton = ' + json.dumps(button) + ';\n'
                          'const group = {buttons:' + json.dumps(types) + '};\n'
                          'const index = ' + str(index) + ';\n'
                          'const DecorationOptions = {DecorationButtonExplicitSpacer:"_"};\n'
                          'const isButtonEntry = (' + type_expression + ');\n'
                          'console.log(JSON.stringify(Boolean(' + visible + ')));')

    def frame_result(self, left=6, right=6, bottom=6, width=900, height=800, maximized=False):
        body = V2.split('id: irixiumCornerMarks', 1)[1]
        names = ['span', 'topBand', 'leftBand', 'rightBand', 'bottomBand']
        property_program = '\n'.join('irixiumCornerMarks.' + name + ' = (' +
            expression(body, 'readonly property real '+name+':') + ');' for name in names)
        show = expression(body, 'visible:', '\n\n            Repeater')
        model = expression(body, 'model:', '\n                delegate:')
        return javascript('''
const root = {borders:{top:34,left:LEFT,right:RIGHT,bottom:BOTTOM}};
const irixiumOverlay = {artworkBand:7, isLeftGroup:true, isMaximized:MAX};
const width = WIDTH, height = HEIGHT;
const irixiumCornerMarks = {width, height};
'''.replace('LEFT',str(left)).replace('RIGHT',str(right)).replace('BOTTOM',str(bottom))
                .replace('MAX',json.dumps(maximized)).replace('WIDTH',str(width)).replace('HEIGHT',str(height))
                + property_program + '\nconst span=irixiumCornerMarks.span;\n'
                + 'const shown = ('+show+');\nconst markers = ('+model+');\n'
                + 'console.log(JSON.stringify({shown, bands:irixiumCornerMarks, markers}));')

    def test_v1_skips_propertyless_maximize_v2_includes_it(self):
        button = {'visible': True, 'width': 22, 'height': 22, 'x': 26}
        self.assertFalse(self.button_result(V1, button, ['H','X','A'], 2))
        self.assertTrue(self.button_result(V2, button, ['H','X','A'], 2))

    def test_hidden_help_is_still_excluded(self):
        self.assertFalse(self.button_result(V2,
            {'visible':False,'width':22,'height':22,'buttonType':'H'},['H','X','A'],0))

    def test_explicit_spacer_does_not_acquire_separator(self):
        self.assertFalse(self.button_result(V2, {'visible':True,'width':22,'height':22},['X','_','A'],1))

    def test_disabled_but_visible_maximize_keeps_separator(self):
        self.assertTrue(self.button_result(V2, {'visible':True,'width':22,'height':22,'enabled':False},['X','A'],1))

    def test_null_or_zero_sized_item_has_no_separator(self):
        for b in [None, {'visible':True,'width':0,'height':22}, {'visible':True,'width':22,'height':0}]:
            with self.subTest(b=b):
                self.assertFalse(self.button_result(V2,b,['X'],0))

    def test_normal_six_pixel_border_reproduces_v1_failure(self):
        body = V1.split('id: irixiumCornerMarks',1)[1]
        visible = expression(body,'visible:','\n\n            Repeater')
        old_result = javascript('''
const root = {borders:{left:6,right:6,bottom:6}};
const irixiumOverlay = {isLeftGroup:true,isMaximized:false};
const width=900, height=800, span=34, band=7;
console.log(JSON.stringify(Boolean(''' + visible + ')));')
        self.assertFalse(old_result)
        result = self.frame_result()
        self.assertTrue(result['shown'])
        self.assertEqual([m['length'] for m in result['markers']], [5,5,4,4,4,4,4,4])

    def test_each_border_width_is_respected(self):
        for left,right,bottom in [(6,6,6),(4,4,4),(7,7,7),(4,6,7),(0,6,6),(0,0,0),(2,2,2),(12,12,12)]:
            with self.subTest(borders=(left,right,bottom)):
                result=self.frame_result(left,right,bottom)
                self.assertTrue(result['shown'])
                bands=result['bands']
                for n,value in [('leftBand',left),('rightBand',right),('bottomBand',bottom)]:
                    self.assertEqual(bands[n],min(7,value))
                for m in result['markers']:
                    if m['length'] <= 0:
                        continue
                    x,y=m['px'],m['py']
                    w,h=(2,m['length']) if m['vertical'] else (m['length'],2)
                    self.assertGreaterEqual(min(x,y),1)
                    self.assertLessEqual(x+w,899)
                    self.assertLessEqual(y+h,799)
                    self.assertTrue(y+h <= bands['topBand'] or y >= 800-bands['bottomBand'] or
                                    x+w <= bands['leftBand'] or x >= 900-bands['rightBand'])

    def test_maximized_or_tiny_window_hides_frame_marks(self):
        self.assertFalse(self.frame_result(maximized=True)['shown'])
        self.assertFalse(self.frame_result(width=70)['shown'])
        self.assertFalse(self.frame_result(height=70)['shown'])

    def test_small_border_does_not_hide_other_edges(self):
        r=self.frame_result(left=0,right=6,bottom=6)
        self.assertEqual(sum(m['length'] > 0 for m in r['markers']),6)

    def test_overlay_is_raised_only_for_irixium(self):
        self.assertIn('z: irixiumOverlay.isIrixium ? 1 : 0',V2)
        # The zero-size direct child still preserves the parent's childrenRect.
        self.assertRegex(V2,r'id: irixiumOverlay\s+width: 0\s+height: 0')


if __name__ == '__main__':
    unittest.main()
