# SPDX-License-Identifier: GPL-3.0-or-later
from contextlib import contextmanager, redirect_stdout
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from domainos_color_migration import (JOURNAL_DIRECTORY,
    LEGACY_FILENAME, LEGACY_SHA256, apply_migration, install_with_migration,
    prepare_migration, restore_migration)
from theme_transaction import Failure, snapshot
from user_bundle import Bundle, fingerprint

# Exact 0.2.7 legacy bytes. This fixture remains valid when the source palette's
# internal General/ColorScheme ID changes in the next release.
LEGACY_BYTES = b"""# SPDX-License-Identifier: GPL-3.0-or-later
# Original repository palette; provenance: DomainOS-SR10.4.ORIGEM.json
[ColorEffects:Disabled]
Color=62,83,110
ColorAmount=0
ColorEffect=0
ContrastAmount=0.55
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=false
Color=120,148,167
ColorAmount=0
ColorEffect=0
ContrastAmount=0
ContrastEffect=0
Enable=false
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate=96,127,145
BackgroundNormal=120,148,167
DecorationFocus=197,232,230
DecorationHover=197,232,230
ForegroundActive=16,43,55
ForegroundInactive=62,83,110
ForegroundLink=7,20,27
ForegroundNegative=130,35,35
ForegroundNeutral=110,73,25
ForegroundNormal=16,43,55
ForegroundPositive=49,74,20
ForegroundVisited=70,52,94

[Colors:Complementary]
BackgroundAlternate=25,75,99
BackgroundNormal=62,83,110
DecorationFocus=163,208,230
DecorationHover=163,208,230
ForegroundActive=255,255,255
ForegroundInactive=197,232,230
ForegroundLink=163,208,230
ForegroundNegative=236,173,173
ForegroundNeutral=224,197,152
ForegroundNormal=255,255,255
ForegroundPositive=175,203,126
ForegroundVisited=190,188,213

[Colors:Header]
BackgroundAlternate=96,127,145
BackgroundNormal=120,148,167
DecorationFocus=197,232,230
DecorationHover=197,232,230
ForegroundActive=16,43,55
ForegroundInactive=62,83,110
ForegroundLink=7,20,27
ForegroundNegative=130,35,35
ForegroundNeutral=110,73,25
ForegroundNormal=16,43,55
ForegroundPositive=49,74,20
ForegroundVisited=70,52,94

[Colors:Selection]
BackgroundAlternate=50,151,199
BackgroundNormal=50,151,199
DecorationFocus=255,255,255
DecorationHover=255,255,255
ForegroundActive=255,255,255
ForegroundInactive=197,232,230
ForegroundLink=255,255,255
ForegroundNegative=255,221,221
ForegroundNeutral=255,238,208
ForegroundNormal=255,255,255
ForegroundPositive=226,242,201
ForegroundVisited=226,226,245

[Colors:Tooltip]
BackgroundAlternate=120,148,167
BackgroundNormal=163,208,230
DecorationFocus=25,75,99
DecorationHover=25,75,99
ForegroundActive=16,43,55
ForegroundInactive=62,83,110
ForegroundLink=7,20,27
ForegroundNegative=130,35,35
ForegroundNeutral=110,73,25
ForegroundNormal=16,43,55
ForegroundPositive=49,74,20
ForegroundVisited=70,52,94

[Colors:View]
BackgroundAlternate=103,135,153
BackgroundNormal=96,127,145
DecorationFocus=163,208,230
DecorationHover=163,208,230
ForegroundActive=255,255,255
ForegroundInactive=197,232,230
ForegroundLink=255,255,255
ForegroundNegative=255,207,207
ForegroundNeutral=245,225,190
ForegroundNormal=255,255,255
ForegroundPositive=218,238,190
ForegroundVisited=218,216,242

[Colors:Window]
BackgroundAlternate=96,127,145
BackgroundNormal=120,148,167
DecorationFocus=197,232,230
DecorationHover=197,232,230
ForegroundActive=16,43,55
ForegroundInactive=62,83,110
ForegroundLink=7,20,27
ForegroundNegative=130,35,35
ForegroundNeutral=110,73,25
ForegroundNormal=16,43,55
ForegroundPositive=49,74,20
ForegroundVisited=70,52,94

[General]
ColorScheme=DomainOS-SR10.4
Name=DomainOS SR10.4
shadeSortColumn=true

[KDE]
contrast=9

[WM]
activeBackground=120,148,167
activeBlend=120,148,167
activeForeground=255,255,255
inactiveBackground=96,127,145
inactiveBlend=96,127,145
inactiveForeground=197,232,230
"""


class DomainOSColorMigrationTest(unittest.TestCase):
    def setUp(self):
        self.private = tempfile.TemporaryDirectory(prefix='.color-migration-test-', dir=ROOT)
        self.root = Path(self.private.name)
        self.data = self.root / 'data'
        self.state = self.root / 'state'
        self.old = self.data / 'color-schemes' / LEGACY_FILENAME
        self.old.parent.mkdir(parents=True)
        self.old.write_bytes(LEGACY_BYTES)
        self.old.chmod(0o640)
        self.new = self.old.with_name('DomainOS-SR10-4.colors')
        self.new.write_bytes(b'new scheme belongs to independent Bundle\n')
        self.config = self.root / 'config' / 'kdeglobals'
        self.config.parent.mkdir()
        self.config.write_bytes(b'[General]\nColorScheme=Untouched\nwidgetStyle=kvantum\n')
        self.untouched = {self.new: snapshot(self.new), self.config: snapshot(self.config)}
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)
        self.private.cleanup()

    def assertUntouched(self):
        self.assertEqual(self.untouched, {path: snapshot(path) for path in self.untouched})

    def test_dry_preflight_and_apply_create_no_journal_or_config_writes(self):
        before = snapshot(self.old)
        plan = prepare_migration(self.data, self.state)
        self.assertEqual(plan.status, 'canonical_legacy')
        self.assertEqual(plan.change.phase, 0)
        self.assertIsNone(plan.change.data)
        result = apply_migration(plan, dry=True)
        self.assertEqual(result['status'], 'verified')
        self.assertIsNone(result['receipt'])
        self.assertEqual(snapshot(self.old), before)
        self.assertFalse(self.state.exists())
        self.assertUntouched()

    def test_known_legacy_removal_restores_exact_bytes_mode_and_private_receipt(self):
        before = snapshot(self.old)
        result = apply_migration(prepare_migration(self.data, self.state))
        self.assertEqual(result['status'], 'removed')
        self.assertFalse(self.old.exists())
        receipt = Path(result['receipt'])
        record = json.loads(receipt.read_text())
        self.assertEqual(record['entries'][0]['before']['sha256'], LEGACY_SHA256)
        self.assertEqual(record['entries'][0]['before'], before)
        self.assertEqual(record['entries'][0]['after'], {'exists': False})
        self.assertEqual(record['entries'][0]['phase'], 0)
        self.assertEqual(stat.S_IMODE(receipt.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.state / JOURNAL_DIRECTORY).stat().st_mode), 0o700)
        receipt_before = receipt.read_bytes()
        self.assertEqual(restore_migration(self.data, self.state, dry=True)['status'], 'verified_restore')
        self.assertFalse(self.old.exists())
        self.assertEqual(receipt.read_bytes(), receipt_before)
        self.assertEqual(restore_migration(self.data, self.state)['status'], 'restored')
        self.assertEqual(snapshot(self.old), before)
        self.assertUntouched()

    def test_modified_legacy_is_preserved_and_skip_is_explicit(self):
        self.old.write_bytes(LEGACY_BYTES + b'# user customization\n')
        before = snapshot(self.old)
        plan = prepare_migration(self.data, self.state)
        self.assertEqual(plan.status, 'preserved_modified')
        self.assertIsNone(plan.change)
        for dry in (True, False):
            result = apply_migration(plan, dry=dry)
            self.assertEqual(result['status'], 'preserved_modified')
            self.assertIn('modificado preservado', result['reason'])
            self.assertIsNone(result['receipt'])
        self.assertEqual(snapshot(self.old), before)
        self.assertFalse(self.state.exists())
        self.assertEqual(restore_migration(self.data, self.state)['status'], 'not_recorded')
        self.assertFalse(self.state.exists())
        self.assertUntouched()

    def test_symlink_file_or_ancestor_is_rejected_without_touching_referent(self):
        referent = self.root / 'canonical-referent.colors'
        referent.write_bytes(LEGACY_BYTES)
        before = snapshot(referent)
        self.old.unlink()
        self.old.symlink_to(referent)
        with self.assertRaisesRegex(Failure, 'Link simbólico'):
            prepare_migration(self.data, self.state)
        self.assertTrue(self.old.is_symlink())
        self.assertEqual(snapshot(referent), before)
        self.old.unlink()
        self.old.write_bytes(LEGACY_BYTES)
        alias = self.root / 'data-alias'
        alias.symlink_to(self.data, target_is_directory=True)
        with self.assertRaisesRegex(Failure, 'Link simbólico'):
            prepare_migration(alias, self.state)
        self.assertEqual(self.old.read_bytes(), LEGACY_BYTES)
        self.assertFalse(self.state.exists())
        self.assertUntouched()

    def test_repeated_migration_keeps_one_original_backup_and_pointer(self):
        result = apply_migration(prepare_migration(self.data, self.state))
        receipt = Path(result['receipt'])
        journal = self.state / JOURNAL_DIRECTORY
        pointer = (journal / 'latest').read_bytes()
        recorded = receipt.read_bytes()
        directories = list((journal / 'backups').iterdir())
        plan = prepare_migration(self.data, self.state)
        self.assertEqual(plan.status, 'absent')
        self.assertEqual(apply_migration(plan)['status'], 'absent')
        self.assertEqual(apply_migration(plan, dry=True)['status'], 'absent')
        self.assertEqual((journal / 'latest').read_bytes(), pointer)
        self.assertEqual(receipt.read_bytes(), recorded)
        self.assertEqual(list((journal / 'backups').iterdir()), directories)
        restore_migration(self.data, self.state)
        self.assertEqual(restore_migration(self.data, self.state)['status'], 'already_restored')
        self.assertUntouched()

    def test_post_edit_and_tampered_receipt_guards_prevent_any_overwrite(self):
        plan = prepare_migration(self.data, self.state)
        self.old.write_bytes(LEGACY_BYTES + b'# edit after preflight\n')
        edited = snapshot(self.old)
        with self.assertRaisesRegex(Failure, 'mudou após a preparação'):
            apply_migration(plan)
        self.assertEqual(snapshot(self.old), edited)
        self.assertFalse(self.state.exists())
        self.old.write_bytes(LEGACY_BYTES)
        self.old.chmod(0o640)
        result = apply_migration(prepare_migration(self.data, self.state))
        receipt = Path(result['receipt'])
        installed = receipt.read_bytes()
        self.old.write_bytes(b'user replacement after removal\n')
        replaced = snapshot(self.old)
        for dry in (True, False):
            with self.assertRaisesRegex(Failure, 'Edição posterior'):
                restore_migration(self.data, self.state, dry=dry)
            self.assertEqual(snapshot(self.old), replaced)
            self.assertEqual(receipt.read_bytes(), installed)
        self.old.unlink()
        record = json.loads(installed)
        record['entries'][0]['path'] = str(self.new)
        receipt.write_text(json.dumps(record))
        with self.assertRaisesRegex(Failure, 'não pertence'):
            restore_migration(self.data, self.state)
        self.assertFalse(self.old.exists())
        self.assertUntouched()


class DomainOSColorInstallCoordinationTest(unittest.TestCase):
    """Real Bundle/Transaction IO in an inert private four-component package."""

    def setUp(self):
        self.private = tempfile.TemporaryDirectory(prefix='.color-coordination-test-', dir=ROOT)
        self.root = Path(self.private.name)
        self.data, self.state = self.root / 'data', self.root / 'state'
        self.old = self.data / 'color-schemes' / LEGACY_FILENAME
        self.new = self.old.with_name('DomainOS-SR10-4.colors')
        destinations = [self.data / name for name in ('panel', 'grosview', 'style')]
        self.targets = destinations + [self.new]
        self.sources = self.root / 'sources'
        self.sources.mkdir()
        self.pairs = []
        for index, target in enumerate(self.targets):
            source = self.sources / str(index)
            if index == 3:
                source.write_bytes(b'[General]\nColorScheme=DomainOS-SR10-4\nName=DomainOS SR10.4\n')
            else:
                source.mkdir()
                (source / 'payload').write_bytes(b'new inert component ' + str(index).encode())
            self.pairs.append((source, target))
        # A genuine pre-008 four-target receipt whose old color name must remain
        # allowed by the new Bundle. These inert trees contain no executable code.
        self.original_sources = self.root / 'old-sources'
        self.original_sources.mkdir()
        old_pairs = []
        for index, target in enumerate(destinations + [self.old]):
            source = self.original_sources / str(index)
            if index == 3:
                source.write_bytes(LEGACY_BYTES)
                source.chmod(0o640)
            else:
                source.mkdir()
                (source / 'payload').write_bytes(b'old inert component ' + str(index).encode())
            old_pairs.append((source, target))
        self.bundle = Bundle(self.state / 'irixium-domainos', self.targets + [self.old])
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        with self.bundle.locked():
            self.bundle.install(old_pairs)
        self.before = self.current_components()
        self.config = self.root / 'config' / 'kdeglobals'
        self.config.parent.mkdir()
        self.config.write_bytes(b'[General]\nColorScheme=DomainOS-SR10.4\nwidgetStyle=kvantum\n')
        self.sibling = self.old.with_name('Unrelated.colors')
        self.sibling.write_bytes(b'user-owned unrelated scheme\n')
        self.canaries = {path: snapshot(path) for path in (self.config, self.sibling)}

    def tearDown(self):
        self.output.__exit__(None, None, None)
        self.private.cleanup()

    def current_components(self):
        return {str(path): fingerprint(path) for path in self.targets + [self.old]}

    def assertCanaries(self):
        self.assertEqual(self.canaries, {path: snapshot(path) for path in self.canaries})

    def install(self, dry=False):
        return install_with_migration(self.bundle, self.pairs,
                                      prepare_migration(self.data, self.state), dry=dry)

    def test_old_to_new_dry_install_and_restore_preserve_exact_four_components(self):
        journal = self.state / JOURNAL_DIRECTORY
        main_receipt, _ = self.bundle.latest()
        old_record = main_receipt.read_bytes()
        old_mode = snapshot(self.old)
        self.install(dry=True)
        self.assertEqual(self.current_components(), self.before)
        self.assertEqual(main_receipt.read_bytes(), old_record)
        self.assertFalse(journal.exists())
        result = self.install()
        self.assertEqual(result['migration']['status'], 'removed')
        self.assertFalse(self.old.exists())
        self.assertEqual(fingerprint(self.new), fingerprint(self.pairs[-1][0]))
        for source, target in self.pairs:
            self.assertEqual(fingerprint(source), fingerprint(target))
        installed = self.current_components()
        restore_migration(self.data, self.state, dry=True)
        self.bundle.restore(dry=True)
        self.assertEqual(self.current_components(), installed)
        # Both preflights precede either write, as required by the CLI contract.
        restore_migration(self.data, self.state)
        with self.bundle.locked():
            self.bundle.restore()
        self.assertEqual(self.current_components(), self.before)
        self.assertEqual(snapshot(self.old), old_mode)
        self.assertCanaries()

    def test_new_allowlist_restores_a_pre_008_receipt_without_migration(self):
        self.bundle.restore(dry=True)
        self.assertEqual(self.current_components(), self.before)
        with self.bundle.locked():
            self.bundle.restore()
        for target in self.targets + [self.old]:
            self.assertFalse(target.exists())
        self.assertFalse((self.state / JOURNAL_DIRECTORY).exists())
        self.assertCanaries()

    def test_modified_legacy_survives_install_and_main_restore(self):
        self.old.write_bytes(LEGACY_BYTES + b'# customization\n')
        preserved = snapshot(self.old)
        result = self.install()
        self.assertEqual(result['migration']['status'], 'preserved_modified')
        self.assertIsNone(result['migration']['receipt'])
        self.assertFalse((self.state / JOURNAL_DIRECTORY).exists())
        self.assertEqual(snapshot(self.old), preserved)
        with self.bundle.locked():
            self.bundle.restore()
        self.assertEqual(snapshot(self.old), preserved)
        self.assertFalse(self.new.exists())
        self.assertCanaries()

    def test_failure_before_legacy_commit_restores_new_bundle_only(self):
        plan = prepare_migration(self.data, self.state)

        def edit_then_fail(prepared):
            self.old.write_bytes(LEGACY_BYTES + b'# concurrent user edit\n')
            return apply_migration(prepared)

        with patch('domainos_color_migration.apply_migration', side_effect=edit_then_fail):
            with self.assertRaisesRegex(Failure, 'mudou após a preparação'):
                install_with_migration(self.bundle, self.pairs, plan)
        self.assertEqual(self.old.read_bytes(), LEGACY_BYTES + b'# concurrent user edit\n')
        self.assertFalse(self.new.exists())
        for target in self.targets[:-1]:
            self.assertEqual(fingerprint(target), self.before[str(target)])
        self.assertFalse((self.state / JOURNAL_DIRECTORY).exists())
        self.assertCanaries()

    def test_failure_after_legacy_commit_rolls_back_both_new_receipts(self):
        before = snapshot(self.old)

        def committed_then_fail(plan):
            apply_migration(plan)
            raise OSError('injected result delivery failure after migration commit')

        with patch('domainos_color_migration.apply_migration', side_effect=committed_then_fail):
            with self.assertRaisesRegex(OSError, 'after migration commit'):
                self.install()
        self.assertEqual(self.current_components(), self.before)
        self.assertEqual(snapshot(self.old), before)
        self.assertEqual(self.bundle.latest()[1]['status'], 'restored')
        journal = self.state / JOURNAL_DIRECTORY
        token = (journal / 'latest').read_text().strip()
        record = json.loads((journal / 'backups' / token / 'receipt.json').read_text())
        self.assertEqual(record['status'], 'restored')
        self.assertRegex(record['operationToken'], r'^[0-9a-f]{32}$')
        self.assertCanaries()

    def test_failed_noop_install_never_rewinds_a_previous_migration(self):
        result = self.install()
        main_receipt, _ = self.bundle.latest()
        migration_receipt = Path(result['migration']['receipt'])
        original_records = [path.read_bytes() for path in (main_receipt, migration_receipt)]
        components = self.current_components()
        with patch('domainos_color_migration.apply_migration', side_effect=OSError('injected no-op failure')):
            with self.assertRaisesRegex(OSError, 'no-op failure'):
                self.install()
        self.assertEqual(self.current_components(), components)
        self.assertEqual([path.read_bytes() for path in (main_receipt, migration_receipt)], original_records)
        self.assertFalse(self.old.exists())
        self.assertCanaries()

    def test_post_commit_edit_blocks_both_rollbacks_before_any_restore_write(self):
        def committed_then_edit_and_fail(plan):
            apply_migration(plan)
            self.old.write_bytes(b'user replacement after commit\n')
            raise OSError('injected after user replacement')

        with patch('domainos_color_migration.apply_migration', side_effect=committed_then_edit_and_fail):
            with self.assertRaisesRegex(Failure, 'preserve os dois journals'):
                self.install()
        self.assertEqual(self.old.read_bytes(), b'user replacement after commit\n')
        for source, target in self.pairs:
            self.assertEqual(fingerprint(source), fingerprint(target))
        self.assertEqual(self.bundle.latest()[1]['status'], 'installed')
        self.assertCanaries()

    def test_interrupted_journal_requires_explicit_recovery_and_restores_legacy(self):
        result = self.install()
        receipt = Path(result['migration']['receipt'])
        record = json.loads(receipt.read_text())
        record['status'] = 'recovery_needed'
        receipt.write_text(json.dumps(record))
        installed = self.current_components()
        with self.assertRaisesRegex(Failure, 'Use --recuperar'):
            restore_migration(self.data, self.state, dry=True)
        self.assertEqual(self.current_components(), installed)
        restore_migration(self.data, self.state, recovery=True, dry=True)
        self.assertFalse(self.old.exists())
        restore_migration(self.data, self.state, recovery=True)
        with self.bundle.locked():
            self.bundle.restore()
        self.assertEqual(self.current_components(), self.before)
        self.assertCanaries()


class DomainOSColorInstallerTransitionTest(unittest.TestCase):
    """Real CLI/migration/Bundle IO, with native preparation isolated explicitly.

    Inert four-component payloads exercise migration, restoration and modes.
    Native compilation/preflight has its own test_domainos_native_menu.py;
    these fixtures must not silently compile source from the live checkout.
    """

    def setUp(self):
        import install_domainos
        self.installer = install_domainos
        self.private = tempfile.TemporaryDirectory(prefix='.color-installer-test-', dir=ROOT)
        self.root = Path(self.private.name)
        self.source = self.root / 'source'
        self.data, self.config, self.state = (self.root / name for name in ('data', 'config', 'state'))
        self.targets = [self.data / dest for dest in self.installer.TARGETS]
        self.old = self.data / 'color-schemes' / LEGACY_FILENAME
        self.new = self.data / 'color-schemes' / 'DomainOS-SR10-4.colors'
        self.original = self.root / 'original'
        self.original.mkdir()
        initial_pairs = []
        for index, (dest, source) in enumerate(self.installer.TARGETS.items()):
            current_source = self.source / source
            current_source.parent.mkdir(parents=True, exist_ok=True)
            old_source = self.original / str(index)
            if index == 3:
                current_source.write_bytes(b'[General]\nColorScheme=DomainOS-SR10-4\nName=DomainOS SR10.4\n')
                old_source.write_bytes(LEGACY_BYTES)
                old_source.chmod(0o640)
                initial_pairs.append((old_source, self.old))
            else:
                current_source.mkdir()
                (current_source / 'payload').write_bytes(b'new component ' + str(index).encode())
                old_source.mkdir()
                (old_source / 'payload').write_bytes(b'old component ' + str(index).encode())
                initial_pairs.append((old_source, self.data / dest))
        self.bundle = Bundle(self.state / 'irixium-domainos', self.targets + [self.old])
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        with self.bundle.locked():
            self.bundle.install(initial_pairs)
        self.before = self.current_components()
        self.old_snapshot = snapshot(self.old)
        self.config.mkdir()
        self.preferences = self.config / 'kdeglobals'
        self.preferences.write_bytes(b'[General]\nColorScheme=DomainOS-SR10.4\nwidgetStyle=kvantum\n')
        self.preferences_before = snapshot(self.preferences)
        self.inventory = {'components': [dict(destination=dest, source=source, root='data')
                                         for dest, source in self.installer.TARGETS.items()]}
        self.prepared_calls = []

    def tearDown(self):
        self.output.__exit__(None, None, None)
        self.private.cleanup()

    def current_components(self):
        return {str(path): fingerprint(path) for path in self.targets + [self.old]}

    @contextmanager
    def fixture_prepared_source_pairs(self, source_root, pairs, *, dry=False):
        """Bypass only the SDK boundary after asserting the inert test scope."""
        self.assertEqual(source_root, self.source)
        expected = [(self.source/source, self.data/dest)
                    for dest, source in self.installer.TARGETS.items()]
        self.assertEqual(pairs, expected)
        for index, (source, _destination) in enumerate(pairs):
            self.assertFalse(source.is_symlink())
            if index == 3:
                self.assertEqual(source.read_bytes(),
                    b'[General]\nColorScheme=DomainOS-SR10-4\nName=DomainOS SR10.4\n')
            else:
                self.assertEqual(list(source.iterdir()), [source/'payload'])
                self.assertEqual((source/'payload').read_bytes(),
                    b'new component '+str(index).encode())
        self.prepared_calls.append(dry)
        yield pairs

    def run_cli(self, *args):
        with patch.object(self.installer, 'ROOT', self.source), \
                patch.object(self.installer, 'catalog', return_value=self.inventory), \
                patch.object(self.installer, 'roots', return_value=(self.data, self.config, self.state)), \
                patch.object(self.installer, 'check_runtime'), \
                patch.object(self.installer, 'prepared_source_pairs',
                             side_effect=self.fixture_prepared_source_pairs), \
                patch.object(sys, 'argv', ['install_domainos.py', *args]):
            self.installer.main()

    def test_real_cli_transitions_old_receipt_to_alias_and_restores_exactly(self):
        self.run_cli('--verificar')
        self.assertEqual(self.current_components(), self.before)
        self.assertFalse((self.state / JOURNAL_DIRECTORY).exists())
        self.run_cli()
        self.assertFalse(self.old.exists())
        self.assertTrue(self.new.exists())
        installed = self.current_components()
        self.run_cli('--restaurar', '--verificar')
        self.assertEqual(self.current_components(), installed)
        self.run_cli('--restaurar')
        self.assertEqual(self.current_components(), self.before)
        self.assertEqual(snapshot(self.old), self.old_snapshot)
        self.assertEqual(snapshot(self.preferences), self.preferences_before)
        self.assertEqual(self.prepared_calls, [True, False])

    def test_real_cli_accepts_a_pre_008_receipt_without_migration(self):
        self.run_cli('--restaurar', '--verificar')
        self.assertEqual(self.current_components(), self.before)
        self.run_cli('--restaurar')
        self.assertTrue(all(not path.exists() for path in self.targets + [self.old]))
        self.assertFalse((self.state / JOURNAL_DIRECTORY).exists())
        self.assertEqual(snapshot(self.preferences), self.preferences_before)
        self.assertEqual(self.prepared_calls, [])

    def test_real_cli_explicit_recovery_handles_interrupted_migration(self):
        self.run_cli()
        journal = self.state / JOURNAL_DIRECTORY
        token = (journal / 'latest').read_text().strip()
        receipt = journal / 'backups' / token / 'receipt.json'
        record = json.loads(receipt.read_text())
        record['status'] = 'recovery_needed'
        receipt.write_text(json.dumps(record))
        installed = self.current_components()
        with self.assertRaisesRegex(Failure, 'Use --recuperar'):
            self.run_cli('--restaurar', '--verificar')
        self.assertEqual(self.current_components(), installed)
        self.run_cli('--restaurar', '--recuperar', '--verificar')
        self.assertEqual(self.current_components(), installed)
        self.run_cli('--restaurar', '--recuperar')
        self.assertEqual(self.current_components(), self.before)
        self.assertEqual(snapshot(self.preferences), self.preferences_before)
        self.assertEqual(self.prepared_calls, [False])

    def test_real_cli_rejects_recovery_flag_without_restore_before_any_write(self):
        with self.assertRaises(SystemExit) as error:
            self.run_cli('--recuperar')
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.current_components(), self.before)
        self.assertFalse((self.state / JOURNAL_DIRECTORY).exists())
        self.assertEqual(snapshot(self.preferences), self.preferences_before)


if __name__ == '__main__':
    unittest.main()
