# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import manage
from layout import VALUES, update_layout
spec = importlib.util.spec_from_file_location('integrate', ROOT / 'integrar-repositorio.py')
integrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrate)
BASE = (ROOT / 'referencia/Irixiumrc').read_bytes()
QML = (ROOT / 'compatibilidade/AuroraeButtonGroup-plasma63.qml').read_bytes()


class LayoutTests(unittest.TestCase):
    def test_layout_only(self):
        new = update_layout(BASE)
        self.assertEqual(BASE.split(b'[Layout]')[0], new.split(b'[Layout]')[0])
        old = dict(line.split('=', 1) for line in BASE.decode().splitlines() if '=' in line)
        now = dict(line.split('=', 1) for line in new.decode().splitlines() if '=' in line)
        for k in old:
            if k not in VALUES:
                self.assertEqual(old[k], now[k], k)
        self.assertEqual({k: now[k] for k in VALUES}, VALUES)

    def test_custom_colors_and_extra_groups_preserved(self):
        old = BASE.replace(b'255,255,255,255', b'0,0,0,255') + b'\n[Other]\nKeep=123\n'
        new = update_layout(old)
        self.assertIn(b'ActiveTextColor=0,0,0,255', new)
        self.assertTrue(new.endswith(b'\n[Other]\nKeep=123\n'))

    def test_idempotent(self):
        self.assertEqual(update_layout(update_layout(BASE)), update_layout(BASE))

    def test_crlf_preserved(self):
        new = update_layout(BASE.replace(b'\n', b'\r\n'))
        self.assertNotIn(b'\n', new.replace(b'\r\n', b''))

    def test_missing_final_newline(self):
        new = update_layout(BASE.rstrip(b'\n'))
        self.assertIn(b'\nTitleBorderLeft=12\n', new)

    def test_refuse_duplicate_layout(self):
        with self.assertRaises(ValueError): update_layout(BASE + b'\n[Layout]\n')

    def test_refuse_duplicate_key(self):
        with self.assertRaises(ValueError): update_layout(BASE + b'\nButtonSpacing=2\n')

    def test_refuse_other_face_size(self):
        with self.assertRaises(ValueError): update_layout(BASE.replace(b'ButtonWidth=22', b'ButtonWidth=28'))

    def test_refuse_specific_width_and_custom_title(self):
        with self.assertRaises(ValueError): update_layout(BASE + b'\nButtonWidthMenu=30\n')
        with self.assertRaises(ValueError): update_layout(BASE.replace(b'TitleHeight=34', b'TitleHeight=40'))

    def test_no_negative_title_margins(self):
        for key, value in VALUES.items(): self.assertGreaterEqual(int(value), 0, key)

    def test_preview_rc_matches_transform(self):
        self.assertEqual((ROOT / 'aurorae/Irixium/Irixiumrc').read_bytes(), update_layout(BASE))

    def test_total_height_and_centers_preserved(self):
        # Same C++ formula as the default Aurorae button-size factor 1.
        self.assertEqual(26 + 7 + 1, 34)
        self.assertEqual(26 + 4 + 4, 34)
        self.assertEqual(7 + 26/2, 3 + 34/2)
        self.assertEqual(4 + 26/2, 0 + 34/2)
        self.assertEqual(7 + 2, 3 + 6)
        self.assertEqual(4 + 2, 0 + 6)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        p = Path(self.temp.name)
        self.qml = p / 'qt6/qml/org/kde/kwin/decoration/AuroraeButtonGroup.qml'
        self.rc = p / 'share/aurorae/themes/Irixium/Irixiumrc'
        self.state = p / 'state/irixium-moderno-geometria'
        self.qml.parent.mkdir(parents=True); self.rc.parent.mkdir(parents=True)
        self.qml.write_bytes(QML); self.rc.write_bytes(BASE)
        self.calls = []
        def copy(data, target, expected):
            self.assertEqual(target.read_bytes(), expected)
            self.calls.append(target)
            manage.atomic(target, data, 0o644)
        self.copy = copy
        self.installer = manage.Installer(self.qml, self.rc, self.state, ROOT, copy)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__(); self.addCleanup(self.output.__exit__, None, None, None)

    def test_dry_run_no_writes(self):
        self.installer.install(True)
        self.assertEqual(self.qml.read_bytes(), QML)
        self.assertEqual(self.rc.read_bytes(), BASE)
        self.assertFalse(self.state.exists()); self.assertEqual(self.calls, [])

    def test_install_and_restore_exact(self):
        self.installer.install()
        self.assertEqual(self.rc.read_bytes(), update_layout(BASE))
        self.assertEqual(self.qml.read_bytes(), (ROOT/'AuroraeButtonGroup.qml').read_bytes())
        self.installer.restore()
        self.assertEqual(self.rc.read_bytes(), BASE)
        self.assertEqual(self.qml.read_bytes(), QML)

    def test_install_v1_and_v2(self):
        for version in ('v1','v2'):
            with self.subTest(version=version):
                original = (ROOT/f'compatibilidade/AuroraeButtonGroup-{version}.qml').read_bytes()
                self.qml.write_bytes(original)
                self.installer.install(); self.installer.restore()
                self.assertEqual(self.qml.read_bytes(), original)

    def test_no_new_backup_if_already_applied(self):
        self.installer.install()
        latest = self.installer.latest()
        self.assertIsNone(self.installer.install())
        self.assertEqual(self.installer.latest(), latest)

    def test_unknown_qml_is_refused(self):
        self.qml.write_bytes(QML + b'\n// unreviewed modification\n')
        with self.assertRaises(manage.Failure): self.installer.install()
        self.assertFalse(self.state.exists()); self.assertEqual(self.rc.read_bytes(), BASE)

    def test_refuse_local_rc_custom_dimensions(self):
        self.rc.write_bytes(BASE.replace(b'ButtonHeight=22',b'ButtonHeight=24'))
        with self.assertRaises(ValueError): self.installer.install()
        self.assertFalse(self.state.exists())

    def test_crlf_original_qml_accepted(self):
        original = QML.replace(b'\n',b'\r\n')
        self.qml.write_bytes(original)
        self.installer.install(); self.installer.restore()
        self.assertEqual(self.qml.read_bytes(), original)

    def test_restore_dry_run(self):
        self.installer.install()
        after = self.qml.read_bytes()
        self.installer.restore(dry_run=True)
        self.assertEqual(self.qml.read_bytes(),after)
        self.assertEqual(json.loads((self.installer.latest()/'receipt.json').read_text())['status'],'installed')

    def test_custom_color_is_not_reset(self):
        custom = BASE.replace(b'255,255,255,255',b'0,0,0,255')
        self.rc.write_bytes(custom)
        self.installer.install()
        self.assertIn(b'ActiveTextColor=0,0,0,255', self.rc.read_bytes())
        self.installer.restore(); self.assertEqual(self.rc.read_bytes(), custom)

    def test_unrelated_classic_and_modern_assets_untouched(self):
        sentinels = [self.rc.parent / x for x in ('MenuButton.qml','minimize.svg','maximize.svg','decoration.svg')]
        classic = Path(self.temp.name)/'share/kwin/decorations/irix_classic/main.qml'
        classic.parent.mkdir(parents=True); sentinels += [classic]
        for p in sentinels: p.write_bytes(b'keep exactly')
        self.installer.install()
        for p in sentinels: self.assertEqual(p.read_bytes(), b'keep exactly')

    def test_restore_refuses_later_edits(self):
        self.installer.install()
        self.rc.write_bytes(self.rc.read_bytes()+b'\n# local edit\n')
        qml = self.qml.read_bytes()
        with self.assertRaises(manage.Failure): self.installer.restore()
        self.assertEqual(self.qml.read_bytes(), qml)

    def test_restore_refuses_kde_update(self):
        self.installer.install()
        self.qml.write_bytes(b'new KDE version')
        with self.assertRaises(manage.Failure): self.installer.restore()
        self.assertEqual(self.qml.read_bytes(),b'new KDE version')

    def test_auth_cancel_rolls_back(self):
        def cancel(*args): raise manage.Failure('cancelled')
        self.installer.copy_system = cancel
        with self.assertRaises(manage.Failure): self.installer.install()
        self.assertEqual(self.rc.read_bytes(), BASE); self.assertEqual(self.qml.read_bytes(), QML)
        self.assertIsNone(self.installer.latest())

    def test_user_write_failure_rolls_back_system(self):
        original = manage.atomic
        failed = False
        def write(path,data,*args):
            nonlocal failed
            if path == self.rc and not failed:
                failed = True
                raise OSError('simulated disk write failure')
            return original(path,data,*args)
        with patch.object(manage,'atomic',side_effect=write):
            with self.assertRaises(manage.Failure): self.installer.install()
        self.assertEqual(self.qml.read_bytes(),QML); self.assertEqual(self.rc.read_bytes(),BASE)

    def test_pending_receipt_recovery(self):
        self.installer.install()
        backup = self.installer.latest()
        receipt = json.loads((backup/'receipt.json').read_text())
        receipt['status']='prepared'; self.installer.save_receipt(backup,receipt)
        self.rc.write_bytes(BASE)  # model interruption after only the QML write
        with self.assertRaises(manage.Failure): self.installer.install()
        self.installer.restore(recovery=True)
        self.assertEqual(self.qml.read_bytes(),QML); self.assertEqual(self.rc.read_bytes(),BASE)

    def test_corrupt_backup_refused(self):
        self.installer.install()
        (self.installer.latest()/'qml.before').write_bytes(b'corrupt')
        with self.assertRaises(manage.Failure): self.installer.restore()

    def test_wrong_receipt_destination_refused(self):
        self.installer.install()
        backup=self.installer.latest(); r=json.loads((backup/'receipt.json').read_text())
        r['rc_path']='/other/Irixiumrc'; self.installer.save_receipt(backup,r)
        with self.assertRaises(manage.Failure): self.installer.restore()

    def test_symlink_refused(self):
        other=self.rc.with_name('other'); self.rc.rename(other); self.rc.symlink_to(other)
        with self.assertRaises(manage.Failure): self.installer.install()

    def test_latest_traversal_refused(self):
        self.state.mkdir(parents=True); (self.state/'latest').write_text('../../elsewhere')
        with self.assertRaises(manage.Failure): self.installer.latest()


class IntegrationTests(unittest.TestCase):
    # Contains both top-level and nested set -eu, as in the repository installer.
    SCRIPT = b'''#!/bin/sh
set -eu
bundle_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
pkexec sh -c '\n        set -eu\n        :\n'
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight HXA
printf '%s\\n' "Irixium customiza\xc3\xa7\xc3\xa3o reaplicada."
'''
    def test_hook_and_early_normal_user_guard(self):
        out = integrate.patch_installer(self.SCRIPT).decode()
        self.assertIn(integrate.HOOK,out); self.assertIn(integrate.GUARD,out)
        self.assertLess(out.index(integrate.GUARD),out.index('pkexec'))
        self.assertIn('ButtonsOnRight HXA',out)

    def test_hook_idempotent(self):
        out = integrate.patch_installer(self.SCRIPT)
        self.assertEqual(integrate.patch_installer(out),out)

    def test_installer_other_actions_preserved(self):
        new = integrate.patch_installer(self.SCRIPT).decode()
        self.assertEqual(new.replace('\n'+integrate.GUARD,'').replace(integrate.HOOK+'\n',''),self.SCRIPT.decode())

    def test_unknown_installer_refused(self):
        with self.assertRaises(manage.Failure): integrate.patch_installer(b'#!/bin/sh\nexit 0\n')

    def test_existing_changed_hook_refused(self):
        new=integrate.patch_installer(self.SCRIPT).replace(b'geometria/instalar.sh',b'geometria/outro.sh')
        with self.assertRaises(manage.Failure): integrate.patch_installer(new)

    def test_plan_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); (repo/'aurorae/Irixium').mkdir(parents=True)
            (repo/'aurorae/Irixium/Irixiumrc').write_bytes(BASE)
            (repo/'update-irixium.sh').write_bytes(self.SCRIPT)
            old,new,dest=integrate.plan(repo)
            self.assertFalse(dest.exists())
            self.assertEqual((repo/'aurorae/Irixium/Irixiumrc').read_bytes(),BASE)
            self.assertNotEqual(old,new)

    def test_refuse_existing_unrelated_package(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); (repo/'aurorae/Irixium').mkdir(parents=True)
            (repo/'aurorae/Irixium/Irixiumrc').write_bytes(BASE)
            (repo/'update-irixium.sh').write_bytes(self.SCRIPT)
            (repo/'moderno/geometria').mkdir(parents=True)
            (repo/'moderno/geometria/keep.txt').write_bytes(b'keep')
            with self.assertRaises(manage.Failure): integrate.plan(repo)
            self.assertEqual((repo/'moderno/geometria/keep.txt').read_bytes(),b'keep')


if __name__ == '__main__': unittest.main()
