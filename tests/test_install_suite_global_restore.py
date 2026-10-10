# SPDX-License-Identifier: GPL-3.0-or-later
"""Suite restoration validates/stops its Global worker before theme removal.

No native session or theme destination is mutated. Separate Style opt-in is
kept; recovery helper files and their backups are deliberately retained.
"""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import install_suite as suite
import domainos_style_bridge as bridge
import domainos_color_migration as migration
import theme_companion_bridge as companion
from theme_transaction import Failure


class SuiteGlobalRestoreTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.suite-global-restore-',dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.roots=tuple(self.base/name for name in ('data','config','state'))
        self.events=[]

    def run_restore(self,*,dry=False,style=False,edited=False):
        events=self.events
        class Bundle:
            def __init__(self,*_):pass
            def locked(self):return contextlib.nullcontext()
            def restore(self,*,dry=False,**_):events.append('bundle-dry' if dry else 'bundle-restore')
        def detach(*_,dry=False):
            events.append('global-dry' if dry else 'global-detach')
            if edited:raise Failure('Edição posterior detectada na ponte')
            return {'status':'ready' if dry else 'detached','style_enabled':style,'enabled':style}
        def service(args):events.append(('service',args))
        args=['install_suite.py','--restaurar']+(['--verificar'] if dry else [])
        with contextlib.redirect_stdout(io.StringIO()), \
                patch.object(sys,'argv',args),patch.object(suite,'roots',return_value=self.roots), \
                patch.object(suite,'Bundle',Bundle),patch.object(suite,'refresh_icons'), \
                patch.object(companion,'uninstall'),patch.object(companion,'stop_if_installed'), \
                patch.object(companion,'restore_palette_resources',return_value=[]), \
                patch.object(migration,'restore_migration'), \
                patch.object(bridge,'detach_global_choices',side_effect=detach), \
                patch.object(bridge,'service_command',side_effect=service):
            suite.main()

    def test_global_worker_stops_before_removal_and_is_disabled_without_style_opt_in(self):
        self.run_restore()
        stop=('service',['stop',bridge.UNIT])
        disable=('service',['disable',bridge.UNIT])
        self.assertLess(self.events.index(stop),self.events.index('bundle-restore'))
        self.assertLess(self.events.index('bundle-restore'),self.events.index('global-detach'))
        self.assertIn(disable,self.events)
        self.assertNotIn(('service',['start',bridge.UNIT]),self.events)

    def test_prior_style_worker_resumes_after_complete_restore(self):
        self.run_restore(style=True)
        self.assertNotIn(('service',['disable',bridge.UNIT]),self.events)
        self.assertGreater(self.events.index(('service',['start',bridge.UNIT])),
                           self.events.index('bundle-restore'))

    def test_dry_restore_does_not_change_flags_or_manage_any_service(self):
        self.run_restore(dry=True)
        self.assertNotIn('global-detach',self.events)
        self.assertNotIn('bundle-restore',self.events)
        self.assertTrue(all(not isinstance(event,tuple) for event in self.events))

    def test_edited_worker_blocks_before_component_removal_or_service_change(self):
        with self.assertRaisesRegex(Failure,'Edição posterior'):self.run_restore(edited=True)
        self.assertEqual(self.events,['global-dry'])


if __name__=='__main__':unittest.main()
