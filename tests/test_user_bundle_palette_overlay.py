# SPDX-License-Identifier: GPL-3.0-or-later
"""Whole-tree restore checks project only journal-validated owned files."""
from contextlib import redirect_stdout
import hashlib
import io
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from theme_transaction import Failure, image, snapshot
from user_bundle import Bundle
import gtk2_palette_runtime as gtk2
from test_gtk2_palette import native_export


def whole_files(root):
    return {str(path.relative_to(root)): (hashlib.sha256(path.read_bytes()).hexdigest(),
            stat.S_IMODE(path.stat().st_mode), path.stat().st_mtime_ns)
            for path in root.rglob('*') if path.is_file() and not path.is_symlink()}


class PaletteOverlayRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.bundle-overlay-', dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source, self.dest = [self.base/name for name in ('source', 'data with spaces/theme')]
        self.source.mkdir(); (self.source/'gtk-4.0').mkdir()
        (self.source/'gtk-4.0/gtk.css').write_bytes(b'@import "common.css";\n')
        (self.source/'common.css').write_bytes(b'button {color:black;}\n')
        self.dest.mkdir(parents=True); (self.dest/'previous.txt').write_bytes(b'original before suite\n')
        self.bundle = Bundle(self.base/'state/suite', [self.dest])
        with redirect_stdout(io.StringIO()): self.bundle.install([(self.source, self.dest)])
        self.entry = self.dest/'gtk-4.0/gtk.css'
        self.generated = self.dest/'gtk-4.0/gtk.kde-live.css'
        original = snapshot(self.entry)
        self.entry.write_bytes(b'/* own current palette entry */\n'); self.entry.chmod(0o640)
        self.generated.write_bytes(b'button {color:yellow;}\n')
        self.overlays = [{'path': str(self.entry), 'before': snapshot(self.entry), 'after': original},
            {'path': str(self.generated), 'before': snapshot(self.generated), 'after': image(None)}]

    def dry(self, overlays=None):
        with redirect_stdout(io.StringIO()): self.bundle.restore(dry=True, overlays=overlays)

    def test_valid_projection_restores_exact_files_in_memory_without_writing(self):
        before = whole_files(self.base)
        self.dry(self.overlays)
        self.assertEqual(whole_files(self.base), before)

    def test_original_whole_tree_guard_rejects_active_overlay(self):
        before = whole_files(self.base)
        with self.assertRaisesRegex(Failure, 'Edição posterior'): self.dry()
        self.assertEqual(whole_files(self.base), before)

    def test_unrelated_edit_and_extra_file_are_not_hidden_by_projection(self):
        path = self.dest/'common.css'; path.write_bytes(b'personal modification\n')
        with self.assertRaisesRegex(Failure, 'Edição posterior'): self.dry(self.overlays)
        path.write_bytes((self.source/'common.css').read_bytes())
        (self.dest/'my-custom-file.css').write_bytes(b'personal new file\n')
        with self.assertRaisesRegex(Failure, 'Edição posterior'): self.dry(self.overlays)

    def test_edited_overlay_bytes_or_mode_refused_before_projection(self):
        original = self.entry.read_bytes()
        self.entry.write_bytes(original+b'# personal\n')
        with self.assertRaisesRegex(Failure, 'Overlay mudou'): self.dry(self.overlays)
        self.entry.write_bytes(original); self.entry.chmod(0o644)
        with self.assertRaisesRegex(Failure, 'Overlay mudou'): self.dry(self.overlays)

    def test_duplicate_foreign_or_malformed_projection_refused(self):
        with self.assertRaises(Failure): self.dry(self.overlays+[self.overlays[0]])
        foreign = self.base/'foreign'; foreign.write_bytes(b'outside\n')
        with self.assertRaises(Failure):
            self.dry([{'path': str(foreign), 'before': snapshot(foreign), 'after': image(None)}])
        with self.assertRaises(Failure): self.dry([{'path': str(self.entry)}])
        with self.assertRaises(Failure):
            self.dry([dict(self.overlays[0], after={'exists': True, 'sha256': 'bad'})])

    def test_real_restore_cannot_use_a_virtual_projection(self):
        before = whole_files(self.base)
        with self.assertRaisesRegex(Failure, 'somente'): self.bundle.restore(overlays=self.overlays)
        self.assertEqual(whole_files(self.base), before)

    def test_symbolic_overlay_and_changed_backup_still_refused(self):
        self.entry.unlink(); self.entry.symlink_to(self.source/'gtk-4.0/gtk.css')
        with self.assertRaises(Failure): self.dry(self.overlays)
        self.entry.unlink(); self.entry.write_bytes(b'/* own current palette entry */\n'); self.entry.chmod(0o640)
        receipt, record = self.bundle.latest()
        (receipt.parent/record['entries'][0]['saved']/'previous.txt').write_bytes(b'backup tampered\n')
        with self.assertRaisesRegex(Failure, 'Backup alterado'): self.dry(self.overlays)

    def test_native_gtk2_runtime_dry_plan_projects_setup_baseline_and_real_restore(self):
        data, config, state, home = [self.base/name for name in ('gtk2data', 'gtk2config', 'gtk2state', 'gtk2home')]
        for path in (data, config, state, home): path.mkdir()
        original = data/'themes/Irixium/gtk-2.0/gtkrc'; original.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/'gtk/Irixium/gtk-2.0/gtkrc', original)
        css = config/'gtk-3.0/colors.css'; css.parent.mkdir(); css.write_bytes(native_export())
        sources = []
        for index, root in enumerate((data/'themes/Irixium-KDE', home/'.themes/Irixium-KDE')):
            root.mkdir(parents=True); (root/'previous.txt').write_bytes(b'pre-suite\n')
            source = self.base/f'gtk2source{index}'; (source/'gtk-2.0').mkdir(parents=True)
            shutil.copyfile(ROOT/'gtk/Irixium-KDE/gtk-2.0/gtkrc', source/'gtk-2.0/gtkrc')
            sources.append((source, root))
        bundle = Bundle(state/'suite', [root for _, root in sources])
        with redirect_stdout(io.StringIO()):
            bundle.install(sources); gtk2.setup(data, config, state, home)
            with self.assertRaises(Failure): bundle.restore(dry=True)
            before = whole_files(self.base)
            result = gtk2.restore(data, config, state, home, dry=True)
            self.assertEqual(len(result['overlays']), 2)
            bundle.restore(dry=True, overlays=result['overlays'])
            self.assertEqual(whole_files(self.base), before)
            gtk2.restore(data, config, state, home)
            bundle.restore()
        for _, root in sources:
            self.assertEqual({path.name for path in root.iterdir()}, {'previous.txt'})
            self.assertEqual((root/'previous.txt').read_bytes(), b'pre-suite\n')


if __name__ == '__main__': unittest.main()
