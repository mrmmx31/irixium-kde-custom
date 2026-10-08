# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from user_bundle import Bundle, fingerprint
from theme_transaction import Failure
from install_suite import sources


class UserBundleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root/'source'; self.source.mkdir()
        (self.source/'icon.svg').write_text('new')
        self.dest = self.root/'data/icons/Theme'
        self.state = self.root/'state'
        self.bundle = Bundle(self.state, [self.dest])
        self.output = redirect_stdout(io.StringIO()); self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def install(self, dry=False):
        self.bundle.install([(self.source, self.dest)], dry)

    def test_dry_run_writes_nothing(self):
        self.install(True)
        self.assertFalse(self.dest.exists()); self.assertFalse(self.state.exists())

    def test_update_removes_stale_icons_and_restores_exact_previous_tree(self):
        self.dest.mkdir(parents=True)
        (self.dest/'obsolete.svg').write_text('old')
        (self.dest/'alias.svg').symlink_to('obsolete.svg')
        before = fingerprint(self.dest)
        self.install()
        self.assertFalse((self.dest/'obsolete.svg').exists())
        self.assertEqual((self.dest/'icon.svg').read_text(), 'new')
        self.bundle.restore()
        self.assertEqual(fingerprint(self.dest), before)
        self.assertTrue((self.dest/'alias.svg').is_symlink())

    def test_idempotent_preserves_last_useful_backup(self):
        self.install()
        pointer = (self.state/'latest').read_text()
        (self.dest/'icon-theme.cache').write_bytes(b'generated')
        self.install()
        self.assertEqual((self.state/'latest').read_text(), pointer)
        self.bundle.restore()
        self.assertFalse(self.dest.exists())

    def test_local_post_install_edit_prevents_restore(self):
        self.install(); (self.dest/'icon.svg').write_text('user edit')
        with self.assertRaises(Failure): self.bundle.restore()
        self.assertEqual((self.dest/'icon.svg').read_text(), 'user edit')

    def test_failure_rolls_back_previous_components(self):
        other = self.root/'data/other'; other.mkdir(parents=True)
        (other/'keep').write_text('other before')
        self.dest.mkdir(parents=True); (self.dest/'keep').write_text('before')
        before = [fingerprint(self.dest), fingerprint(other)]
        bundle = Bundle(self.state, [self.dest,other])
        replace = os.replace
        def fail(source, dest):
            if dest == other and '.stage-' in str(source):
                raise OSError('injected failure')
            return replace(source,dest)
        with patch('user_bundle.os.replace', side_effect=fail):
            with self.assertRaises(OSError):
                bundle.install([(self.source,self.dest),(self.source,other)])
        self.assertEqual([fingerprint(self.dest),fingerprint(other)],before)

    def test_external_link_rejected_before_writes(self):
        (self.source/'external').symlink_to('/etc/passwd')
        with self.assertRaises(Failure): self.install()
        self.assertFalse(self.dest.exists())

    def test_internal_links_are_self_contained_after_install(self):
        (self.source/'alias.svg').symlink_to('icon.svg'); self.install()
        self.assertFalse((self.dest/'alias.svg').is_symlink())
        self.assertEqual((self.dest/'alias.svg').read_text(),'new')

    def test_all_theme_dependencies_present_and_user_scoped(self):
        data,config = self.root/'data',self.root/'config'
        pairs = sources(data,config)
        self.assertEqual(len(pairs),27)
        for source,dest in pairs:
            self.assertTrue(source.exists(),source)
            self.assertTrue(dest.is_relative_to(data) or dest.is_relative_to(config))
        targets = {str(d.relative_to(data)) for _,d in pairs if d.is_relative_to(data)}
        self.assertIn('color-schemes/Irixium.colors',targets)
        self.assertTrue({'icons/Irixium','icons/IrixClassic-SGI','icons/sgi'}.issubset(targets))

    def test_single_file_does_not_replace_sibling_color_schemes(self):
        sibling = self.root/'data/color-schemes/Other.colors'
        sibling.parent.mkdir(parents=True); sibling.write_text('keep')
        dest = sibling.with_name('Irixium.colors')
        bundle = Bundle(self.state,[dest]);bundle.install([(self.source/'icon.svg',dest)])
        self.assertEqual(sibling.read_text(),'keep')
        bundle.restore(); self.assertFalse(dest.exists()); self.assertEqual(sibling.read_text(),'keep')
