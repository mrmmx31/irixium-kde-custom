# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import classic_desktop
from theme_transaction import snapshot


@unittest.skipUnless(shutil.which('node'), 'Node is needed for the isolated Plasma scripting fixture')
class DesktopScriptTest(unittest.TestCase):
    def run_script(self, fixture, actions):
        # Only the Plasma scripting API is substituted. The production SCRIPT runs unchanged.
        api = r'''
const fixture = FIXTURE;
const calls = [];
let nextId = 10000;
function containment(value) {
    value._widgets = (value.widgets || []).map(w => Object.assign({}, w));
    value.widgets = () => value._widgets;
    value.widgetById = id => value._widgets.find(w => w.id === id) || null;
    value._widgets.forEach(w => {w.remove = () => {
        calls.push({action: 'remove', containment: value.id, id: w.id});
        value._widgets = value._widgets.filter(other => other.id !== w.id);
    };});
    value.addWidget = (type, x, y, width, height) => {
        calls.push({action: 'add', containment: value.id, type, geometry: {x,y,width,height}});
        const w = {id: nextId++, type, geometry: {x,y,width,height}};
        w.remove = () => {
            calls.push({action: 'remove', containment: value.id, id: w.id});
            value._widgets = value._widgets.filter(other => other.id !== w.id);
        };
        value._widgets.push(w);
        return w;
    };
    return value;
}
const ds = (fixture.desktops || []).map(containment);
const ps = (fixture.panels || []).map(containment);
const knownWidgetTypes = fixture.known || ['org.kde.plasma.pager','org.irixclassic.grosview'];
function desktops() {return ds;}
function panels() {return ps;}
function desktopById(id) {return ds.find(d => d.id === id) || null;}
function panelById(id) {return ps.find(p => p.id === id) || null;}
function desktopForScreen(screen) {return ds.find(d => d.screen === screen) || null;}
function screenGeometry(screen) {return fixture.screens[screen];}
'''.replace('FIXTURE', json.dumps(fixture))
        code = api + classic_desktop.SCRIPT + '\nconsole.log(JSON.stringify({results: '+json.dumps(actions)+'.map(run), calls: calls}));'
        completed = subprocess.run(['node'], input=code, text=True, capture_output=True, check=True, timeout=10)
        return json.loads(completed.stdout)

    def test_grosview_uses_local_upper_right_coordinates_on_offset_screen(self):
        result = self.run_script({'desktops': [{'id': 2, 'screen': 1}],
                                  'screens': {'1': {'x': 1920, 'y': 120, 'width': 1920, 'height': 1080}}},
                                 [{'action': 'add', 'screen': 1, 'grosview': True}])
        self.assertTrue(result['results'][0]['ok'])
        self.assertEqual(result['calls'], [{'action': 'add', 'containment': 2, 'type': classic_desktop.GROSVIEW,
                                           'geometry': {'x': 1624, 'y': 16, 'width': 280, 'height': 220}}])

    def test_existing_grosview_is_never_moved_or_duplicated(self):
        geometry = {'x': 40, 'y': 70, 'width': 320, 'height': 260}
        result = self.run_script({'desktops': [{'id': 2, 'screen': 0, 'widgets': [
            {'id': 11, 'type': classic_desktop.GROSVIEW, 'geometry': geometry}]}]},
            [{'action': 'add', 'screen': 0, 'grosview': True}]*2)
        self.assertEqual(result['calls'], [])
        self.assertTrue(all(r['ok'] and r['created'] == [] for r in result['results']))
        self.assertEqual(result['results'][-1]['state']['desktops'][0]['widgets'][0]['geometry'], geometry)

    def test_new_grosview_addition_is_idempotent(self):
        result = self.run_script({'desktops': [{'id': 2, 'screen': 0}],
                                  'screens': {'0': {'width': 640, 'height': 480}}},
                                 [{'action': 'add', 'screen': 0, 'grosview': True}]*2)
        self.assertEqual(len(result['calls']), 1)
        self.assertEqual(result['results'][1]['created'], [])

    def test_pager_is_added_at_tray_geometry_without_rewriting_existing_widgets(self):
        result = self.run_script({'panels': [{'id': 5, 'screen': 0, 'widgets': [
            {'id': 9, 'type': 'org.kde.plasma.systemtray', 'geometry': {'x': 920, 'y': 0, 'width': 80, 'height': 64}}]}]},
            [{'action': 'add', 'screen': 0, 'pager': True}])
        self.assertEqual(result['calls'][0]['geometry'], {'x': 920, 'y': 0, 'width': 112, 'height': 64})
        self.assertEqual(result['results'][0]['state']['panels'][0]['widgets'][0]['id'], 9)

    def test_failure_in_second_widget_rolls_back_only_the_first_new_widget(self):
        result = self.run_script({'panels': [{'id': 5, 'screen': 0, 'widgets': [
            {'id': 9, 'type': 'org.kde.plasma.systemtray', 'geometry': {'x': 920, 'y': 0, 'height': 64}}]}],
            'desktops': [{'id': 2, 'screen': 0}], 'screens': {'0': {'width': 180, 'height': 150}}},
            [{'action': 'add', 'screen': 0, 'pager': True, 'grosview': True}])
        self.assertFalse(result['results'][0]['ok'])
        self.assertEqual(result['results'][0]['rollback_errors'], [])
        self.assertEqual([w['id'] for w in result['results'][0]['state']['panels'][0]['widgets']], [9])
        self.assertEqual(result['calls'][-1], {'action': 'remove', 'containment': 5, 'id': 10000})

    def test_rollback_preserves_existing_widget_and_refuses_changed_type(self):
        result = self.run_script({'desktops': [{'id': 2, 'screen': 0, 'widgets': [
            {'id': 11, 'type': classic_desktop.GROSVIEW, 'geometry': {'x': 40, 'y': 70}},
            {'id': 12, 'type': 'org.kde.plasma.notes', 'geometry': {'x': 10, 'y': 10}}]}]},
            [{'action': 'rollback', 'created': [{'containment': 2, 'id': 12, 'type': classic_desktop.GROSVIEW}]}])
        self.assertFalse(result['results'][0]['ok'])
        self.assertEqual(result['calls'], [])
        self.assertEqual([w['id'] for w in result['results'][0]['state']['desktops'][0]['widgets']], [11, 12])


class DesktopTransactionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data, self.config, self.state = [self.root/name for name in ('data', 'config', 'state')]
        self.config.mkdir(); (self.config/'kwinrc').write_bytes(b'[Desktops]\nNumber=1\nPrivatePreference=retain\n')
        self.old = snapshot(self.config/'kwinrc')
        self.before = {'known': [classic_desktop.PAGER, classic_desktop.GROSVIEW], 'desktops': [], 'panels': []}
        self.created = [{'containment': 5, 'id': 20, 'type': classic_desktop.PAGER}]
        self.desktops = [[0, 'one', 'Existing user name']]

    def run_main(self, args, plasma, native, ensure=None):
        with patch.object(sys, 'argv', ['classic_desktop', *args]), \
             patch('reload_decoration.check_session'), \
             patch('install_suite.roots', return_value=(self.data, self.config, self.state)), \
             patch.object(classic_desktop, 'plasma', side_effect=plasma) as calls, \
             patch.object(classic_desktop, 'desktop_state', side_effect=native), \
             patch.object(classic_desktop, 'ensure_desktops', side_effect=ensure) as desktop_calls, \
             redirect_stdout(io.StringIO()):
            classic_desktop.main()
            return calls, desktop_calls

    def receipt(self):
        paths = list(self.state.glob('irixclassic-desktop/*/receipt.json'))
        self.assertEqual(len(paths), 1)
        return json.loads(paths[0].read_text())

    def test_dry_run_writes_neither_receipt_nor_public_file(self):
        public = self.root/'result.json'
        self.run_main(['--pager', '--verificar'], [{'ok': True, 'state': self.before}], [self.desktops])
        self.assertFalse(self.state.exists()); self.assertFalse(public.exists())
        self.assertEqual(snapshot(self.config/'kwinrc'), self.old)

    def test_create_desktop_failure_removes_only_new_widget_and_marks_failed_receipt(self):
        calls = []
        def plasma(payload):
            calls.append(payload)
            if payload['action'] == 'add': return {'ok': True, 'created': self.created, 'state': self.before}
            return {'ok': True, 'state': self.before}
        with self.assertRaisesRegex(classic_desktop.Failure, 'createDesktop failure'):
            self.run_main(['--pager'], plasma, [self.desktops, self.desktops],
                          lambda _: (_ for _ in ()).throw(OSError('createDesktop failure')))
        self.assertEqual(calls[-1], {'action': 'rollback', 'created': self.created})
        record = self.receipt()
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(record['before']['status'], 'planned')
        self.assertNotIn('created_widgets', record['before'])
        self.assertIn('createDesktop failure', record['error'])
        self.assertEqual(record['result']['virtual_desktops_after_failure'], self.desktops)
        self.assertEqual(snapshot(self.config/'kwinrc'), self.old)

    def test_post_creation_query_failure_retains_new_desktop_and_records_its_state(self):
        two = self.desktops + [[1, 'two', 'Desktop 2']]
        with self.assertRaisesRegex(classic_desktop.Failure, 'query failed'):
            self.run_main(['--pager'], [
                {'ok': True, 'state': self.before}, {'ok': True, 'created': self.created},
                {'ok': True, 'state': self.before}],
                [self.desktops, OSError('query failed'), two], lambda _: 'Desktop 2')
        record = self.receipt()
        self.assertTrue(record['result']['desktop_creation_attempted'])
        self.assertEqual(record['result']['virtual_desktops_after_failure'], two)
        self.assertIn('Nenhuma área removida', record['result']['virtual_desktop_recovery'])

    def test_widget_rollback_error_preserves_original_error_in_recovery_receipt(self):
        with self.assertRaisesRegex(classic_desktop.Failure, 'original failure.*remove failed'):
            self.run_main(['--pager'], [
                {'ok': True, 'state': self.before}, {'ok': True, 'created': self.created},
                OSError('remove failed')], [self.desktops, self.desktops],
                lambda _: (_ for _ in ()).throw(OSError('original failure')))
        record = self.receipt()
        self.assertEqual(record['status'], 'recovery_needed')
        self.assertIn('original failure', record['error'])
        self.assertIn('remove failed', record['recovery_errors'][0])

    def test_missing_add_response_never_guesses_widget_ids_for_removal(self):
        with self.assertRaisesRegex(classic_desktop.Failure, 'IDs; confira'):
            self.run_main(['--grosview'], [
                {'ok': True, 'state': self.before}, OSError('Plasma reply timed out')], [])
        record = self.receipt()
        self.assertEqual(record['status'], 'recovery_needed')
        self.assertEqual(record['result']['created_widgets'], [])
        self.assertIn('Plasma reply timed out', record['error'])

    def test_applied_public_report_excludes_private_kwinrc_backup(self):
        public = self.root/'public.json'; two = self.desktops + [[1, 'two', 'Desktop 2']]
        self.run_main(['--pager', '--saida', str(public)], [
            {'ok': True, 'state': self.before}, {'ok': True, 'created': []},
            {'ok': True, 'state': self.before}], [self.desktops, two], lambda _: 'Desktop 2')
        self.assertNotIn('base64', public.read_text())
        self.assertNotIn('PrivatePreference', public.read_text())
        self.assertEqual(self.receipt()['kwinrc_before'], self.old)

    def test_existing_virtual_desktops_are_never_renamed_or_replaced(self):
        from unittest.mock import Mock
        call = Mock()
        before = [[0, 'one', 'User desk'], [1, 'two', 'Work']]
        self.assertIsNone(classic_desktop.ensure_desktops(before, call=call)); call.assert_not_called()
        self.assertEqual(classic_desktop.ensure_desktops(before[:1], call=call), 'Desktop 2')
        call.assert_called_once_with(1, 'Desktop 2')
