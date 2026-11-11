# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK2 reload broadcast tests; integration cases use private Xvfb."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from gtk2_reload_notify import reload_open_windows


GTK2_RECEIVER = r'''
import gi, json, pathlib, sys
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk, GLib
ok, _ = Gtk.init_check([])
if not ok: raise SystemExit(3)
w = Gtk.Window(title='Private GTK2 reload receiver')
w.add(Gtk.Button(label='GTK2 event receiver'))
w.show_all()
ready, request, result = map(pathlib.Path, sys.argv[1:4])
settings = Gtk.Settings.get_default()
settings.set_property('gtk-theme-name', 'DomainOS-SR10-4-KDE')
before = settings.get_property('gtk-theme-name')
ready.write_text('ready', encoding='ascii')
def check():
    if request.exists():
        after = settings.get_property('gtk-theme-name')
        result.write_text(json.dumps({'before': before, 'after': after}), encoding='utf-8')
        Gtk.main_quit()
        return False
    return True
GLib.timeout_add(20, check)
Gtk.main()
'''

GTK3_RECEIVER = r'''
import gi, json, pathlib, sys
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
ok, _ = Gtk.init_check([])
if not ok: raise SystemExit(3)
w = Gtk.Window(title='Private GTK3 unaffected client')
b = Gtk.CheckButton(label='GTK3 control sentinel')
w.add(b)
w.show_all()
ready, request, result = map(pathlib.Path, sys.argv[1:4])
ready.write_text('ready', encoding='ascii')
def check():
    if request.exists():
        allocation = b.get_allocation()
        before = b.get_active()
        record = {'visible': w.get_visible(), 'sensitive': b.get_sensitive(),
                  'width': allocation.width, 'height': allocation.height}
        b.set_active(not before)
        record['toggle_works'] = b.get_active() == (not before)
        result.write_text(json.dumps(record), encoding='utf-8')
        Gtk.main_quit()
        return False
    return True
GLib.timeout_add(20, check)
Gtk.main()
'''


class Gtk2ReloadNotifyTests(unittest.TestCase):
    @contextmanager
    def _private_clients(self, *, gtk2=True, gtk3=False):
        temp = tempfile.TemporaryDirectory(prefix='gtk2-reload-', dir='/home/lsi/tempia')
        root = Path(temp.name)
        children = []

        def start(name, source, args):
            script = root / f'{name}.py'
            script.write_text(source, encoding='utf-8')
            children.append(subprocess.Popen([sys.executable, str(script), *map(str, args)],
                                             stdout=subprocess.DEVNULL,
                                             stderr=None))

        try:
            gtk2_ready = root / 'gtk2-ready'
            gtk2_request, gtk2_result = root / 'gtk2-check', root / 'gtk2-result'
            if gtk2:
                start('gtk2', GTK2_RECEIVER, [gtk2_ready, gtk2_request, gtk2_result])
            gtk3_ready, gtk3_request, gtk3_result = (root / 'gtk3-ready',
                root / 'gtk3-check', root / 'gtk3-result')
            if gtk3:
                start('gtk3', GTK3_RECEIVER, [gtk3_ready, gtk3_request, gtk3_result])

            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if any(child.poll() is not None for child in children):
                    self.fail('A native toolkit receiver exited before becoming ready')
                if ((not gtk2 or gtk2_ready.exists()) and
                    (not gtk3 or gtk3_ready.exists())):
                    break
                time.sleep(.01)
            self.assertFalse(gtk2 and not gtk2_ready.exists(), 'GTK2 receiver did not become ready')
            self.assertFalse(gtk3 and not gtk3_ready.exists(), 'GTK3 receiver did not become ready')
            yield {'gtk2_request': gtk2_request, 'gtk2_result': gtk2_result,
                   'gtk3_request': gtk3_request, 'gtk3_result': gtk3_result}
        finally:
            for child in children:
                child.terminate()
            for child in children:
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=2)
            temp.cleanup()

    def test_refuses_to_guess_an_x11_display(self):
        with patch.dict(os.environ, {'DISPLAY': ''}):
            with self.assertRaisesRegex(RuntimeError, 'DISPLAY indisponível'):
                reload_open_windows()

    @unittest.skipUnless(os.environ.get('IRIX_GTK2_RELOAD_TEST') == '1',
                         'requires an explicitly private Xvfb session')
    def test_broadcast_reaches_a_native_gtk2_top_level(self):
        with self._private_clients(gtk2=True) as files:
            result = reload_open_windows()
            self.assertEqual(result['status'], 'sent')
            self.assertGreaterEqual(result['windows_considered'], 1)
            self.assertGreaterEqual(result['events_sent'], 1)
            self.assertEqual(result['racing_x_errors'], 0)
            files['gtk2_request'].write_text('check', encoding='ascii')
            deadline = time.monotonic() + 3
            while not files['gtk2_result'].exists() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(files['gtk2_result'].exists(), 'GTK2 receiver stopped responding')
            state = json.loads(files['gtk2_result'].read_text(encoding='utf-8'))
            self.assertEqual(state['before'], 'DomainOS-SR10-4-KDE')
            self.assertEqual(state['after'], state['before'])

    @unittest.skipUnless(os.environ.get('IRIX_GTK2_RELOAD_TEST') == '1',
                         'requires an explicitly private Xvfb session')
    def test_broadcast_does_not_close_or_disable_gtk3_control(self):
        with self._private_clients(gtk2=True, gtk3=True) as files:
            result = reload_open_windows()
            self.assertEqual(result['status'], 'sent')
            self.assertEqual(result['racing_x_errors'], 0)
            files['gtk2_request'].write_text('check', encoding='ascii')
            deadline = time.monotonic() + 3
            while not files['gtk2_result'].exists() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(files['gtk2_result'].exists(), 'GTK2 receiver stopped responding')
            theme = json.loads(files['gtk2_result'].read_text(encoding='utf-8'))
            self.assertEqual(theme['before'], theme['after'])
            request, result_file = files['gtk3_request'], files['gtk3_result']
            request.write_text('check', encoding='ascii')
            deadline = time.monotonic() + 3
            while not result_file.exists() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue(result_file.exists(), 'GTK3 receiver stopped responding')
            state = json.loads(result_file.read_text(encoding='utf-8'))
            self.assertTrue(state['visible'])
            self.assertTrue(state['sensitive'])
            self.assertTrue(state['toggle_works'])
            self.assertGreater(state['width'], 0)
            self.assertGreater(state['height'], 0)


if __name__ == '__main__':
    unittest.main()
