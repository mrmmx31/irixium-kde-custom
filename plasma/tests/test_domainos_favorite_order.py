#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only order selection: native client/activity, legacy and ambiguity."""
import importlib.util
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
CODE=ROOT/'plasma/applets/org.irixclassic.domainos.panel/contents/code'
sys.path.insert(0,str(CODE))
spec=importlib.util.spec_from_file_location('domainos_favorite_order',CODE/'favorite_order.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)


class OrderTest(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory(prefix='.qa-favorite-order-',dir=ROOT)
        self.addCleanup(self.work.cleanup);self.root=Path(self.work.name)
        self.applets=self.root/'plasma-org.kde.plasma.desktop-appletsrc'
        self.stats=self.root/'kactivitymanagerd-statsrc'
        self.request={'activity':'activity-one','members':['alpha.desktop','beta.desktop','preferred://browser','file:///tmp/document']}
    def existing(self,*ids):
        self.applets.write_text(''.join(f'[Containments][7][Applets][{id}]\nplugin=org.kde.plasma.kicker\n' for id in ids))
    def order(self,id,order,scope='global'):
        with self.stats.open('a') as stream:
            stream.write(f'[Favorites-org.kde.plasma.kicker.favorites.instance-{id}-{scope}]\nordering={order}\n')
    def read(self):
        before={p.name:p.read_bytes() for p in (self.applets,self.stats) if p.is_file()}
        request={key:value for key,value in self.request.items() if key!='members'}
        request['memberHashes']=[hashlib.md5(helper.key(item).encode('utf-8'),usedforsecurity=False).hexdigest() for item in self.request['members']]
        result=helper.observe(request,self.root)
        self.assertEqual(before,{p.name:p.read_bytes() for p in (self.applets,self.stats) if p.is_file()})
        return result
    def test_existing_wins_over_newer_removed_menu(self):
        self.existing(4);self.order(4,'applications:beta.desktop,applications:alpha.desktop')
        self.order(90,'applications:alpha.desktop,applications:beta.desktop')
        result=self.read();self.assertEqual(result['kind'],'existing');self.assertEqual(result['order'],['beta.desktop','alpha.desktop'])
    def test_activity_precedes_global_and_preserves_other_provider_ids(self):
        self.existing(4);self.order(4,'file:///tmp/document,applications:beta.desktop','activity-one')
        self.order(4,'applications:alpha.desktop,preferred://browser,applications:beta.desktop')
        self.assertEqual(self.read()['order'],['file:///tmp/document','beta.desktop','alpha.desktop','preferred://browser'])
    def test_conflicting_existing_menus_are_explicitly_ambiguous(self):
        self.existing(4,5);self.order(4,'alpha.desktop,beta.desktop');self.order(5,'beta.desktop,alpha.desktop')
        self.assertEqual(self.read()['outcome'],'ambiguous')
    def test_equivalent_existing_orders_do_not_conflict_over_stale_members(self):
        self.existing(4,5);self.order(4,'alpha.desktop,old.desktop,beta.desktop');self.order(5,'applications:alpha.desktop,beta.desktop')
        self.assertEqual(self.read()['order'],['alpha.desktop','beta.desktop'])
    def test_legacy_compatible_highest_instance_and_no_file_creation(self):
        self.order(2,'alpha.desktop,beta.desktop');self.order(7,'beta.desktop,alpha.desktop');self.order(90,'unrelated.desktop')
        result=self.read();self.assertFalse(self.applets.exists());self.assertEqual(result['kind'],'legacy');self.assertEqual(result['location'],'7');self.assertEqual(result['order'],['beta.desktop','alpha.desktop'])
    def test_missing_configuration_retains_native_provider_order(self):
        result=self.read();self.assertTrue(result['ok']);self.assertEqual(result['kind'],'provider');self.assertEqual(result['order'],[])
    def test_reopening_reads_updated_peer_order_without_any_write(self):
        self.existing(4);self.order(4,'alpha.desktop,beta.desktop');self.assertEqual(self.read()['order'][0],'alpha.desktop')
        self.stats.write_text('[Favorites-org.kde.plasma.kicker.favorites.instance-4-global]\nordering=beta.desktop,alpha.desktop\n')
        self.assertEqual(self.read()['order'][0],'beta.desktop')
    def test_escaped_comma_and_encoded_application_identity(self):
        self.request['members']=['a,b.desktop','alpha.desktop'];self.existing(4)
        self.order(4,r'applications:a\,b.desktop,applications:alpha.desktop')
        self.assertEqual(self.read()['order'],['a,b.desktop','alpha.desktop'])
    def test_malformed_configuration_fails_without_changes(self):
        self.existing(4);self.stats.write_text('malformed configuration')
        before=self.stats.read_bytes()
        with self.assertRaises(Exception):self.read()
        self.assertEqual(before,self.stats.read_bytes())


if __name__=='__main__':unittest.main()
