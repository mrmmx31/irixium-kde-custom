#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Regional configuration preserves choices and supports checked restoration."""
from pathlib import Path
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import configure_domainos_holidays as holidays
from theme_transaction import Failure


class RegionalConfigurationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='domainos-holiday-config-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.data, self.config, self.state = (self.base / name for name in ('data', 'config', 'state'))
        self.config.mkdir()
        self.config_file = self.config / 'plasma_calendar_holiday_regions'
        self.original = b'# preserve\n[General]\nselectedRegions = us_en-us,br_pt-br\nother=unchanged\n[Other]\nvalue=keep\n'
        self.config_file.write_bytes(self.original)
        self.config_file.chmod(0o600)
        self.region_file = self.data / ('kf5/libkholidays/plan2/holiday_' + holidays.REGION)
        self.source = self.base / 'source'
        self.source.write_bytes(b'# isolated transaction fixture, not calendar evidence\n')
        self.patch = patch.object(holidays, 'SOURCE', self.source)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.manager = holidays.transaction(self.data, self.config, self.state)

    def install(self, dry=False):
        with self.manager.locked():
            return self.manager.install(holidays.changes(self.data, self.config), dry=dry)

    def test_dry_run_does_not_change_region_or_selection(self):
        self.install(dry=True)
        self.assertFalse(self.region_file.exists())
        self.assertEqual(self.config_file.read_bytes(), self.original)
        self.assertEqual(stat.S_IMODE(self.config_file.stat().st_mode), 0o600)

    def test_cli_check_does_not_create_a_state_journal(self):
        environment = dict(os.environ, HOME=str(self.base), XDG_DATA_HOME=str(self.data),
            XDG_CONFIG_HOME=str(self.config), XDG_STATE_HOME=str(self.state),
            PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([sys.executable, '-B',
            str(Path(holidays.__file__)), '--manaus-2026', '--verificar'],
            env=environment, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.state.exists())
        self.assertFalse(self.region_file.exists())
        self.assertEqual(self.config_file.read_bytes(), self.original)

    def test_addition_preserves_prior_choice_and_other_keys_then_restores_bytes_and_mode(self):
        receipt = self.install()
        self.assertIsNotNone(receipt)
        self.assertEqual(self.region_file.read_bytes(), self.source.read_bytes())
        self.assertEqual(holidays.selected_regions(self.config_file.read_bytes()),
            ['us_en-us', *holidays.REGIONS])
        self.assertIn(b'other=unchanged\n[Other]\nvalue=keep\n', self.config_file.read_bytes())
        self.assertEqual(stat.S_IMODE(self.config_file.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.region_file.stat().st_mode), 0o644)
        with self.manager.locked():
            self.manager.restore()
        self.assertFalse(self.region_file.exists())
        self.assertEqual(self.config_file.read_bytes(), self.original)
        self.assertEqual(stat.S_IMODE(self.config_file.stat().st_mode), 0o600)

    def test_identical_reinstall_keeps_original_restore_receipt(self):
        first = self.install()
        self.assertIsNone(self.install())
        self.assertEqual(self.manager.latest()[0], first)
        with self.manager.locked():
            self.manager.restore()
        self.assertEqual(self.config_file.read_bytes(), self.original)

    def test_later_user_edit_blocks_restore_before_removing_any_region(self):
        self.install()
        modified = self.config_file.read_bytes() + b'# later user choice\n'
        self.config_file.write_bytes(modified)
        with self.manager.locked(), self.assertRaisesRegex(Failure, 'Edição posterior'):
            self.manager.restore()
        self.assertEqual(self.config_file.read_bytes(), modified)
        self.assertEqual(self.region_file.read_bytes(), self.source.read_bytes())

    def test_duplicate_or_immutable_configuration_is_rejected_without_changes(self):
        for content in (b'[General]\nselectedRegions=br_pt-br\nselectedRegions=us_en-us\n',
                        b'[General][$i]\nselectedRegions=br_pt-br\n',
                        b'[General]\nselectedRegions[$i]=br_pt-br\n'):
            with self.subTest(content=content):
                self.config_file.write_bytes(content)
                with self.assertRaises(Failure):
                    self.install()
                self.assertFalse(self.region_file.exists())
                self.assertEqual(self.config_file.read_bytes(), content)


if __name__ == '__main__':
    unittest.main()
