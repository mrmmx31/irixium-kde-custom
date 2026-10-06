# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Policy/geometry regression tests. They are not a QML/KWin rendering test."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / 'package/contents/ui'

@unittest.skipUnless(shutil.which('node'), 'Node unavailable: JavaScript checks not executed')
class JavaScriptTests(unittest.TestCase):
    def run_js(self, body):
        payload = {'geometry': (UI/'Geometry.js').read_text(), 'rendering': (UI/'Rendering.js').read_text(), 'body': body}
        js = r'''const vm=require('vm');const fs=require('fs');const p=JSON.parse(fs.readFileSync(0,'utf8'));
const geom={},render={};
vm.runInNewContext(p.geometry.replace(/^\.pragma library\s*$/m,''),geom);
vm.runInNewContext(p.rendering.replace(/^\.pragma library\s*$/m,''),render);
const result=vm.runInNewContext(p.body,{G:geom,R:render});process.stdout.write(JSON.stringify(result));'''
        p = subprocess.run(['node','-e',js],input=json.dumps(payload),text=True,capture_output=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        return json.loads(p.stdout)
    def test_normal_geometry_order(self):
        self.assertTrue(self.run_js('let m=G.metrics(800,false);m.menu.x<m.minimize.x && m.minimize.x<m.maximize.x && m.maximize.x<m.close.x'))
    def test_maximized_geometry_order(self):
        self.assertTrue(self.run_js('let m=G.metrics(800,true);m.menu.x<m.minimize.x && m.minimize.x<m.maximize.x && m.maximize.x<m.close.x'))
    def test_gaps_equal(self):
        self.assertEqual(self.run_js('[false,true].map(max=>{let m=G.metrics(800,max);return [m.maximize.x-m.minimize.x-m.minimize.w,m.close.x-m.maximize.x-m.maximize.w]})'),[[6,6],[6,6]])
    def test_caption_never_over_menu(self):
        self.assertTrue(self.run_js('[false,true].every(max=>{let m=G.metrics(220,max);return m.caption.x>=m.menu.x+m.menu.w+12})'))
    def test_caption_stops_before_actions(self):
        self.assertTrue(self.run_js('[220,500,1920].every(w=>[false,true].every(max=>{let m=G.metrics(w,max);return m.caption.x+m.caption.w<=m.minimize.x-12}))'))
    def test_caption_narrow_clamps_width(self):
        self.assertEqual(self.run_js('G.metrics(120,false).caption.w'),0)
    def test_vertical_center_consistent(self):
        self.assertEqual(self.run_js('[false,true].map(max=>{let m=G.metrics(800,max);return m.menu.y+m.menu.h/2-(m.caption.y+m.caption.h/2)})'),[0,0])
    def test_frame_metrics_preserved(self):
        self.assertEqual(self.run_js('[false,true].map(max=>{let m=G.metrics(800,max);return [m.frame,m.title,m.menu.w,m.menu.h]})'),[[7,34,22,22],[0,34,22,22]])
    def test_normal_state(self):
        self.assertEqual(self.run_js('R.buttonCandidates(true,true,false,false)[0]'),'active-center')
    def test_inactive_state(self):
        self.assertEqual(self.run_js('R.buttonCandidates(false,true,false,false)[0]'),'inactive-center')
    def test_pressed_dominates_hover(self):
        self.assertEqual(self.run_js('R.buttonCandidates(true,true,true,true)[0]'),'pressed-center')
    def test_hover_state(self):
        self.assertEqual(self.run_js('R.buttonCandidates(false,true,false,true)[0]'),'hover-inactive-center')
    def test_unavailable_dominates_press(self):
        self.assertEqual(self.run_js('R.buttonCandidates(false,false,true,true)[0]'),'deactivated-inactive-center')
    def test_missing_element_never_full_atlas(self):
        self.assertEqual(self.run_js('R.pickElement({hasElement:id=>false},["active-center"])'),'irixium-missing-state')
    def test_exact_element_selection(self):
        self.assertEqual(self.run_js('R.pickElement({hasElement:id=>id==="pressed-center"},["pressed-inactive-center","pressed-center"])'),'pressed-center')
    def test_frame_prefix_inactive(self):
        self.assertEqual(self.run_js('R.framePrefix({hasElementPrefix:p=>p==="decoration"||p==="decoration-inactive"},false,false)'),'decoration-inactive')
    def test_frame_max_fallback(self):
        self.assertEqual(self.run_js('R.framePrefix({hasElementPrefix:p=>p==="decoration"||p==="decoration-inactive"},false,true)'),'decoration-inactive')
    def test_frame_missing_never_unprefixed(self):
        self.assertEqual(self.run_js('R.framePrefix({hasElementPrefix:p=>false},true,false)'),'irixium-missing-frame')
    def test_path_spaces_and_unicode(self):
        self.assertEqual(self.run_js('R.localPath("file:///home/teste/tema%20com%20espa%C3%A7o/close.svg")'),'/home/teste/tema com espaço/close.svg')
    def test_file_localhost(self):
        self.assertEqual(self.run_js('R.localPath("file://localhost/tmp/x.svg")'),'/tmp/x.svg')
    def test_raster_detection(self):
        self.assertEqual(self.run_js('[R.isRaster("file:///x/applications.png"),R.isRaster("file:///x/minimize.svg")]'),[True,False])

class SourceContracts(unittest.TestCase):
    def test_menu_state_machine_matches_classic(self):
        classic=ROOT.parent/'classic/package/contents/ui'
        for name in ('ButtonInput.qml','InputState.js'):
            self.assertEqual((UI/name).read_bytes(),(classic/name).read_bytes())
        self.assertIn('onCloseRequested: surface.closeRequested()', (UI/'Surface.qml').read_text())
    def test_frame_actually_uses_asset(self):
        s=(UI/'Surface.qml').read_text();self.assertIn('KSvg.FrameSvgItem',s);self.assertIn('../../assets/decoration.svg',s)
    def test_buttons_select_elements(self):
        s=(UI/'ModernButton.qml').read_text();self.assertIn('KSvg.SvgItem',s);self.assertIn('elementId:',s)
        self.assertNotIn('Image.Stretch',s)
    def test_no_timers_or_opacity_animations(self):
        s=(UI/'ModernButton.qml').read_text();self.assertNotIn('Timer {',s);self.assertNotIn('mouseDoubleClickInterval',s)
        self.assertNotIn('Behavior on',s);self.assertNotIn('onDoubleClicked',s)
    def test_double_click_enabled_only_for_closeable_clients(self):
        s=(UI/'main.qml').read_text();self.assertIn('menuOnPress: false',s);self.assertIn('closeOnDouble: decoration.client.closeable',s)
    def test_no_shared_custom_files(self):
        for f in UI.glob('*'):
            if f.suffix in ('.qml','.js'):
                s=f.read_text();self.assertNotIn('/usr/share',s);self.assertNotIn('/usr/lib',s)
                self.assertNotIn('auroraeTheme.',s);self.assertNotIn('AuroraeButtonGroup',s)
    def test_standalone_surface_has_no_kwin_import(self):
        for name in ('Surface.qml','ModernButton.qml'):
            self.assertNotIn('import org.kde.kwin.decoration',(UI/name).read_text())
    def test_manifest_contains_renderer_hash(self):
        m=json.loads((ROOT/'MANIFEST.json').read_text())['package']
        for name in ('Rendering.js','ModernButton.qml','Surface.qml','Geometry.js','main.qml'):
            self.assertEqual(m['contents/ui/'+name],hashlib.sha256((UI/name).read_bytes()).hexdigest())
    def test_original_assets_unchanged_in_manifest(self):
        m=json.loads((ROOT/'MANIFEST.json').read_text())['package']
        self.assertEqual(m['assets/decoration.svg'],'986fffa5b40e01e531b665df4300d4c1ef63e3d912bcf4de714548efc9244fdc')
        self.assertEqual(m['assets/minimize.svg'],'c3d35495ab25dbae63121f0bbd82da9b443be458499ae411ec95fd7f3a903dbb')
        self.assertEqual(m['assets/close.svg'],m['assets/minimize.svg'])

if __name__=='__main__':unittest.main(verbosity=2)
