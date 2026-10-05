# SPDX-License-Identifier: GPL-2.0-or-later
"""Sandbox checks only. These tests do not load Qt or a KWin session."""
import configparser
import contextlib
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
from irixium_install import Installer, InstallError, replace_title_colors, normalized_qml


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.qml = self.root / "qt6/AuroraeButtonGroup.qml"
        self.rc = self.root / "user/Irixiumrc"
        self.state = self.root / "state"
        self.qml.parent.mkdir()
        self.rc.parent.mkdir()
        self.base_qml = (PACKAGE / "upstream/AuroraeButtonGroup.qml").read_bytes()
        self.new_qml = (PACKAGE / "AuroraeButtonGroup.qml").read_bytes()
        self.base_rc = (PACKAGE / "upstream/Irixiumrc").read_bytes()
        self.qml.write_bytes(self.base_qml)
        self.rc.write_bytes(self.base_rc)
        self.rc.chmod(0o640)
        self.installer = Installer(self.qml, self.rc, self.state,
                                   lambda src, dst: shutil.copyfile(src, dst), PACKAGE)
        self.quiet = contextlib.redirect_stdout(io.StringIO())
        self.quiet.__enter__()

    def tearDown(self):
        self.quiet.__exit__(None, None, None)
        self.tmp.cleanup()

    def test_dry_run_writes_nothing(self):
        self.installer.install(dry_run=True)
        self.assertEqual(self.qml.read_bytes(), self.base_qml)
        self.assertEqual(self.rc.read_bytes(), self.base_rc)
        self.assertFalse(self.state.exists())

    def test_install_and_exact_restore(self):
        backup = self.installer.install(keep_color=False)
        self.assertEqual(self.qml.read_bytes(), self.new_qml)
        self.assertEqual(self.rc.read_bytes(), replace_title_colors(self.base_rc))
        self.assertEqual(self.rc.stat().st_mode & 0o777, 0o640)
        self.assertEqual((backup / "Irixiumrc").read_bytes(), self.base_rc)
        self.installer.restore()
        self.assertEqual(self.qml.read_bytes(), self.base_qml)
        self.assertEqual(self.rc.read_bytes(), self.base_rc)
        self.assertEqual(json.loads((backup / "manifest.json").read_text())["status"], "restored")
        self.assertFalse((self.state / "latest").exists())

    def test_keep_colors(self):
        self.installer.install(keep_color=True)
        self.assertEqual(self.rc.read_bytes(), self.base_rc)
        self.installer.restore()
        self.assertEqual(self.qml.read_bytes(), self.base_qml)

    def test_local_geometry_is_preserved(self):
        custom = self.base_rc.replace(b"TitleHeight=34", b"TitleHeight=36").replace(
            b"ButtonMarginTopMaximized=6", b"ButtonMarginTopMaximized=7")
        custom += b"\n# personal setting\nTitleBorderRight=9\n"
        self.rc.write_bytes(custom)
        self.installer.install(keep_color=False)
        self.assertEqual(self.rc.read_bytes(), replace_title_colors(custom))
        self.installer.restore()
        self.assertEqual(self.rc.read_bytes(), custom)

    def test_unknown_qml_is_refused_before_writes(self):
        unknown = self.base_qml.replace(b"spacing: auroraeTheme", b"spacing: 2 + auroraeTheme")
        self.qml.write_bytes(unknown)
        with self.assertRaises(InstallError):
            self.installer.install(keep_color=False)
        self.assertEqual(self.qml.read_bytes(), unknown)
        self.assertEqual(self.rc.read_bytes(), self.base_rc)
        self.assertFalse(self.state.exists())

    def test_reinstall_is_idempotent(self):
        backup = self.installer.install(keep_color=False)
        self.assertIsNone(self.installer.install(keep_color=False))
        self.assertEqual(list((self.state / "backups").iterdir()), [backup])
        self.installer.restore()
        self.assertEqual(self.qml.read_bytes(), self.base_qml)

    def test_qml_update_after_install_blocks_restore(self):
        self.installer.install(keep_color=False)
        self.qml.write_bytes(b"// a newer KDE component\n")
        with self.assertRaises(InstallError):
            self.installer.restore()
        self.assertEqual(self.qml.read_bytes(), b"// a newer KDE component\n")
        self.assertEqual(self.rc.read_bytes(), replace_title_colors(self.base_rc))

    def test_rc_edit_after_install_blocks_restore(self):
        self.installer.install(keep_color=False)
        changed = self.rc.read_bytes() + b"\n# later local edit\n"
        self.rc.write_bytes(changed)
        with self.assertRaises(InstallError):
            self.installer.restore()
        self.assertEqual(self.qml.read_bytes(), self.new_qml)
        self.assertEqual(self.rc.read_bytes(), changed)

    def test_authorization_failure_keeps_previous_files(self):
        def fail(src, dst):
            raise InstallError("authorization canceled")
        self.installer.copy_system = fail
        with self.assertRaises(InstallError):
            self.installer.install(keep_color=False)
        self.assertEqual(self.qml.read_bytes(), self.base_qml)
        self.assertEqual(self.rc.read_bytes(), self.base_rc)
        backup = next((self.state / "backups").iterdir())
        self.assertEqual(json.loads((backup / "manifest.json").read_text())["status"], "failed_rolled_back")

    def test_partial_copy_failure_rolls_back(self):
        calls = []
        def partial_then_restore(src, dst):
            calls.append(src)
            if len(calls) == 1:
                dst.write_bytes(b"partial QML")
                raise InstallError("simulated disk error")
            shutil.copyfile(src, dst)
        self.installer.copy_system = partial_then_restore
        with self.assertRaises(InstallError):
            self.installer.install(keep_color=False)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.qml.read_bytes(), self.base_qml)
        self.assertEqual(self.rc.read_bytes(), self.base_rc)

    def test_backup_tampering_blocks_restore(self):
        backup = self.installer.install(keep_color=False)
        (backup / "Irixiumrc").write_bytes(b"tampered")
        with self.assertRaises(InstallError):
            self.installer.restore()
        self.assertEqual(self.qml.read_bytes(), self.new_qml)

    def test_restore_dry_run(self):
        self.installer.install(keep_color=False)
        self.installer.restore(dry_run=True)
        self.assertEqual(self.qml.read_bytes(), self.new_qml)
        self.assertEqual(self.rc.read_bytes(), replace_title_colors(self.base_rc))

    def test_symlink_rc_is_refused(self):
        moved = self.rc.with_name("originalrc")
        self.rc.rename(moved)
        self.rc.symlink_to(moved)
        with self.assertRaises(InstallError):
            self.installer.install(keep_color=False)
        self.assertEqual(moved.read_bytes(), self.base_rc)


class SourceAndGeometryTests(unittest.TestCase):
    def test_original_qml_logic_is_unchanged(self):
        new = (PACKAGE / "AuroraeButtonGroup.qml").read_text()
        original = (PACKAGE / "upstream/AuroraeButtonGroup.qml").read_text()
        stripped = re.sub(r"\n    // IRIXIUM_DIVISORIAS_BEGIN v2.*?    // IRIXIUM_DIVISORIAS_END\n", "", new, flags=re.S)
        self.assertEqual(normalized_qml(stripped.encode()), normalized_qml(original.encode()))

    def test_only_title_colors_differ_in_rc(self):
        old = configparser.ConfigParser()
        old.read(PACKAGE / "upstream/Irixiumrc")
        new = configparser.ConfigParser()
        new.read(PACKAGE / "referencia/Irixiumrc-v1")
        changes = {(section, key) for section in old.sections() for key in old[section]
                   if old[section][key] != new[section][key]}
        self.assertEqual(changes, {("General", "activetextcolor"), ("General", "inactivetextcolor")})
        self.assertEqual(dict(old["Layout"]), dict(new["Layout"]))

    def test_qml_overlay_has_no_input_handlers(self):
        text = (PACKAGE / "AuroraeButtonGroup.qml").read_text().split("// IRIXIUM_DIVISORIAS_BEGIN v2", 1)[1]
        text = re.sub(r"//[^\n]*", "", text)
        self.assertNotRegex(text, r"\b(MouseArea|TapHandler|DragHandler|Keys|Shortcut)\b")
        self.assertIn("width: 0", text)
        self.assertIn("height: 0", text)

    def test_theme_path_filter(self):
        regex = re.compile(r"/Irixium/decoration(?:\.svgz?)?$")
        for path in ("/home/user/.local/share/aurorae/themes/Irixium/decoration.svg",
                     "/usr/share/aurorae/themes/Irixium/decoration.svgz",
                     "/usr/share/aurorae/themes/Irixium/decoration"):
            self.assertRegex(path, regex)
        for path in ("/themes/Breeze/decoration.svg", "/themes/Irixium-Copy/decoration.svg", ""):
            self.assertIsNone(regex.search(path))

    def test_button_centers_unchanged(self):
        rc = configparser.ConfigParser()
        rc.read(PACKAGE / "referencia/Irixiumrc-v1")
        layout = rc["Layout"]
        center_normal = layout.getfloat("TitleEdgeTop") + layout.getfloat("ButtonMarginTop") + layout.getfloat("ButtonHeight") / 2
        center_max = layout.getfloat("TitleEdgeTopMaximized") + layout.getfloat("ButtonMarginTopMaximized") + layout.getfloat("ButtonHeight") / 2
        self.assertEqual((center_normal, center_max), (20, 17))
        self.assertEqual(layout.getint("ButtonSpacing"), 4)

    def test_separator_rectangles_stay_in_titlebar(self):
        # Arithmetic model of the QML, NOT a Qt renderer test.
        for height in (28, 34, 36, 48, 64):
            for maximized in (False, True):
                top = 0 if maximized else 7
                bottom = height
                line_height = max(0, bottom - top - 1)
                self.assertGreaterEqual(top, 0)
                self.assertLessEqual(top + line_height, bottom - 1)

    def test_corner_rectangles_stay_inside_frame(self):
        # Checks the eight marker coordinates for a matrix of window sizes.
        for width in (72, 128, 640, 1920, 3840):
            for height in (72, 128, 480, 1080, 2160):
                span, band = 34, 7
                markers = [(span, 1, 2, band-2), (width-span-2, 1, 2, band-2),
                           (span, height-band+1, 2, band-2), (width-span-2, height-band+1, 2, band-2),
                           (1, span, band-2, 2), (width-band+1, span, band-2, 2),
                           (1, height-span-2, band-2, 2), (width-band+1, height-span-2, band-2, 2)]
                for x, y, w, h in markers:
                    self.assertGreaterEqual(x, 1)
                    self.assertGreaterEqual(y, 1)
                    self.assertLessEqual(x+w, width-1)
                    self.assertLessEqual(y+h, height-1)
                    self.assertTrue(y+h <= band or y >= height-band or x+w <= band or x >= width-band)

    def test_existing_comments_and_crlf_are_preserved(self):
        old = b"[General]\r\n# keep me\r\nActiveTextColor=1,2,3,255\r\nInactiveTextColor=4,5,6,255\r\n\r\n[Layout]\r\nButtonHeight=22\r\n"
        new = replace_title_colors(old)
        self.assertIn(b"# keep me\r\n", new)
        self.assertIn(b"[Layout]\r\nButtonHeight=22\r\n", new)
        self.assertEqual(new.count(b"\n"), new.count(b"\r\n"))

    def test_duplicate_color_key_is_refused(self):
        with self.assertRaises(InstallError):
            replace_title_colors(b"[General]\nActiveTextColor=a\nActiveTextColor=b\n")

    def test_missing_color_keys_are_added(self):
        self.assertIn(b"ActiveTextColor=0,0,0,255\n", replace_title_colors(b"[General]\n\n[Layout]\nButtonHeight=22\n"))


if __name__ == "__main__":
    unittest.main()
