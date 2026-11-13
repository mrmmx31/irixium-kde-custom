# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from xcursor import read, write
from cursor_audit import audit_theme, REQUIRED


class CursorThemes(unittest.TestCase):
    def test_all_themes_cover_kde_and_wayland_at_all_sizes(self):
        for name in ('sgi', 'SGI-Classic', 'SGI-Irixium'):
            with self.subTest(theme=name):
                self.assertEqual(audit_theme(ROOT/name)['errors'], [])

    def test_original_sources_preserved(self):
        for name, digest in json.loads((ROOT/'sources/manifest.json').read_text()).items():
            self.assertEqual(hashlib.sha256((ROOT/'sources/sgi-enhanced'/name).read_bytes()).hexdigest(), digest)

    def test_classic_native_arrow_preserves_reference_pixels(self):
        original = read(ROOT/'sources/sgi-enhanced/left_ptr')[0]
        current = next(f for f in read(ROOT/'SGI-Classic/cursors/left_ptr') if f['size']==32)
        self.assertEqual(current,original)

    def test_modern_edges_use_valid_premultiplied_alpha(self):
        for path in (ROOT/'SGI-Irixium/cursors').iterdir():
            if path.is_symlink():
                continue
            for f in read(path):
                pixels = list(zip(*[iter(f['pixels'])]*4))
                self.assertTrue(all(max(b,g,r)<=a for b,g,r,a in pixels), path.name)
        for role in ('default','wait','progress','grab','text'):
            for f in read(ROOT/'SGI-Irixium/cursors'/role):
                self.assertTrue(any(0<a<255 for a in f['pixels'][3::4]),(role,f['size']))

    def test_large_classic_edges_are_crisp_and_not_nearest_neighbour_blocks(self):
        from PIL import Image
        source = read(ROOT/'sources/sgi-enhanced/left_ptr')[0]
        im = Image.frombytes('RGBA',(source['width'],source['height']),source['pixels'],'raw','BGRA')
        for f in read(ROOT/'SGI-Classic/cursors/default'):
            if f['size']==32:
                continue
            old = im.resize((f['width'],f['height']),Image.Resampling.NEAREST).tobytes('raw','BGRA')
            self.assertNotEqual(f['pixels'],old)
            self.assertTrue(set(f['pixels'][3::4]) <= {0,255})

    def test_wait_progress_and_move_keep_distinct_meanings(self):
        for theme in ('sgi', 'SGI-Classic', 'SGI-Irixium'):
            payload = ROOT/theme/'cursors'
            self.assertEqual((payload/'wait').resolve(), payload/'watch')
            self.assertEqual((payload/'progress').resolve(), payload/'left_ptr_watch')
            self.assertNotEqual((payload/'wait').read_bytes(), (payload/'progress').read_bytes())
            self.assertNotEqual((payload/'grab').read_bytes(), (payload/'grabbing').read_bytes())
            self.assertEqual((payload/'col-resize').read_bytes(), (payload/'ew-resize').read_bytes())
            self.assertEqual((payload/'row-resize').read_bytes(), (payload/'ns-resize').read_bytes())

    def test_native_busy_animation_has_stable_hotspot_and_visible_frames(self):
        for theme in ('SGI-Classic', 'SGI-Irixium'):
            for name in ('wait', 'progress'):
                frames = read(ROOT/theme/'cursors'/name)
                for size in (24, 32, 48, 64, 96):
                    group = [f for f in frames if f['size']==size]
                    self.assertEqual(len(group), 8)
                    self.assertEqual(len({f['hotspot'] for f in group}), 1)
                    self.assertEqual({f['delay'] for f in group}, {125})
                    self.assertGreater(len({f['pixels'] for f in group}), 1)
                    self.assertTrue(all(any(f['pixels']) for f in group))

    def test_reader_rejects_truncation_and_bad_hotspot(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad';p.write_bytes(b'Xcur')
            with self.assertRaises(ValueError): read(p)
            with self.assertRaises(ValueError):
                write(p,[{'size':32,'width':1,'height':1,'hotspot':(1,0),'delay':1,'pixels':b'\0'*4}])

    def test_roundtrip_preserves_pixels_delays_and_hotspots(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=read(ROOT/'SGI-Classic/cursors/watch')
            p=Path(tmp)/'cursor';write(p, source)
            self.assertEqual(read(p),source)
