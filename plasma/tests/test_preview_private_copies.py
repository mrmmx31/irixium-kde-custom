#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression for the actual readonly-export failures before preview startup."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parents[1] / "tools/prever-tema-completo.py"
spec = importlib.util.spec_from_file_location("preview_private_copies", SOURCE)
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class PrivateCopyTests(unittest.TestCase):
    def test_readonly_export_can_normalize_metadata_and_regenerate_private_css(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "readonly"
            (source / "common").mkdir(parents=True)
            (source / "metadata.json").write_text('{"KPlugin":{"Id":"source"}}\n')
            (source / "common/gtk.css").write_text("button { color: white; }\n")
            (source / "run").write_text("#!/bin/sh\nexit 0\n")
            for path in (source, *source.rglob("*")):
                path.chmod(0o555 if path.is_dir() or path.name == "run" else 0o444)
            before = {str(path.relative_to(source)): (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
                      for path in source.rglob("*") if path.is_file()}
            try:
                target = root / "private"
                preview.copy_private_tree(source, target)
                preview.write_json(target / "metadata.json", {"KPlugin": {"Id": "normalized"}})
                (target / "common/gtk.css.tmp").write_text("button { color: black; }\n")
                (target / "common/gtk.css.tmp").replace(target / "common/gtk.css")
                self.assertEqual(json.loads((target / "metadata.json").read_text())["KPlugin"]["Id"],
                                 "normalized")
                self.assertIn("black", (target / "common/gtk.css").read_text())
                self.assertTrue(os.access(target / "run", os.X_OK))
                after = {str(path.relative_to(source)): (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
                         for path in source.rglob("*") if path.is_file()}
                self.assertEqual(before, after)
                self.assertEqual(stat.S_IMODE(source.stat().st_mode), 0o555)
                self.assertEqual(stat.S_IMODE((source / "common").stat().st_mode), 0o555)
                self.assertTrue(all(path.stat().st_uid == os.getuid()
                                    for path in (target, *target.rglob("*"))))
            finally:
                for path in (source, *source.rglob("*")):
                    path.chmod(stat.S_IMODE(path.stat().st_mode) | stat.S_IWUSR)

    def test_default_launch_creates_private_owned_parent_before_destination_guard(self):
        with patch.object(sys, "argv", [str(SOURCE), "--pacote", "/tmp/unused-test.zip"]), \
                patch.object(preview, "prepare") as prepare:
            preview.main()
        output = prepare.call_args.args[0].saida
        try:
            self.assertFalse(output.exists())
            self.assertFalse(output.parent.is_symlink())
            self.assertEqual(output.parent.stat().st_uid, os.getuid())
            self.assertEqual(stat.S_IMODE(output.parent.stat().st_mode), 0o700)
        finally:
            output.parent.rmdir()

    def test_explicit_output_is_kept_for_existing_destination_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "chosen"
            with patch.object(sys, "argv", [str(SOURCE), "--pacote", "/tmp/unused-test.zip",
                                             "--saida", str(output)]), \
                    patch.object(preview, "prepare") as prepare, \
                    patch.object(preview.tempfile, "mkdtemp") as mkdtemp:
                preview.main()
            self.assertEqual(prepare.call_args.args[0].saida, output)
            mkdtemp.assert_not_called()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
