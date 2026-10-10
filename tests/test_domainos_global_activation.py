# SPDX-License-Identifier: GPL-3.0-or-later
"""A Global choice may never replace or restore an unrelated user's panel."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import activate_domainos as activation
from theme_transaction import Failure


class GlobalActivationTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='domainos-global-activation-',dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.config=self.base/'config';self.config.mkdir()
        self.directory=self.base/'state'

    def test_native_kconfig_global_and_style_must_both_match(self):
        if not shutil.which('kreadconfig6'):self.skipTest('native KConfig CLI unavailable')
        defaults=self.config/'kdedefaults';defaults.mkdir()
        (defaults/'kdeglobals').write_text('[KDE]\nLookAndFeelPackage='+activation.GLOBAL_THEME+'\n')
        (defaults/'plasmarc').write_text('[Theme]\nname=IrixClassicDomainOS\n')
        (self.config/'kdeglobals').write_text('[KDE]\nother=preserved\n')
        protected={path:path.read_bytes() for path in self.config.rglob('*') if path.is_file()}
        activation.require_global_choice(self.config)
        for override in ('org.kde.breeze.desktop',''):
            (self.config/'kdeglobals').write_text('[KDE]\nLookAndFeelPackage='+override+'\n')
            with self.assertRaises(Failure):activation.require_global_choice(self.config)
        (self.config/'kdeglobals').write_bytes(protected[self.config/'kdeglobals'])
        (self.config/'plasmarc').write_text('[Theme]\nname=IrixClassic\n')
        with self.assertRaises(Failure):activation.require_global_choice(self.config)
        for path,contents in protected.items():
            if path.name!='plasmarc':self.assertEqual(path.read_bytes(),contents)

    def test_wrong_global_is_rejected_before_receipt_and_panel_mutation(self):
        with patch.object(activation,'require_global_choice',side_effect=Failure('changed Global')), \
                patch.object(activation,'call',side_effect=AssertionError('native panel mutation')):
            with self.assertRaises(Failure):
                activation.activate({'id':4,'widgets':[]},self.config,self.directory,origin='global')
        self.assertFalse(self.directory.exists())

    def test_changed_global_before_commit_keeps_original_panel(self):
        original={'id':4,'widgets':[]};events=[]
        def dispatch(payload):events.append(payload['action']);return {}
        def rollback(path,record):
            record.update(status='restored',restored=original)
            activation.save(path,record);events.append('rollback');return False
        with patch.object(activation,'require_global_choice',side_effect=[None,None,Failure('changed Global')]), \
                patch.object(activation,'call',side_effect=dispatch), \
                patch.object(activation,'wait_ready',return_value={'id':40,'widgets':[]}), \
                patch.object(activation,'reconcile',side_effect=rollback), \
                patch.object(activation,'seed_preferences',return_value=({},None)):
            with self.assertRaises(Failure):activation.activate(original,self.config,self.directory,origin='global')
        self.assertEqual(events,['create','rollback'])
        _,receipt=activation.latest(self.directory)
        self.assertEqual(receipt['origin'],'global');self.assertEqual(receipt['status'],'restored')
        self.assertEqual(receipt['before'],original)

    def test_global_restore_never_takes_over_a_manual_activation(self):
        with patch.object(activation,'call',side_effect=AssertionError('native panel mutation')):
            with self.assertRaises(Failure):
                activation.restore(self.base/'receipt.json',{'origin':'manual'},
                                   config=self.config,global_request=True)
        self.assertFalse((self.base/'receipt.json').exists())

    def test_multiple_panels_require_an_explicit_id(self):
        panels=[{'id':n,'widgets':[],'geometry':{'screen':n,'location':'bottom'}} for n in (4,5)]
        reply={'state':{'known':[activation.PLUGIN],'panels':panels},
               'screens':[{'id':n,'geometry':{'width':1920,'height':1080}} for n in (4,5)]}
        with self.assertRaisesRegex(Failure,'--painel ID'):activation.choose(reply)
        self.assertEqual(activation.choose(reply,5),panels[1])


if __name__=='__main__':unittest.main()
