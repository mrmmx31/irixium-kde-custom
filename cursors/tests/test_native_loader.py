# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify actual libXcursor lookup, aliases and animation frames without an X server."""
import ctypes as C
import ctypes.util
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from cursor_audit import REQUIRED
from xcursor import read


class Image(C.Structure):
    _fields_=[(name,C.c_uint32) for name in ('version','size','width','height','xhot','yhot','delay')]+[('pixels',C.POINTER(C.c_uint32))]


class Images(C.Structure):
    _fields_=[('nimage',C.c_int),('images',C.POINTER(C.POINTER(Image))),('name',C.c_char_p)]


@unittest.skipUnless(ctypes.util.find_library('Xcursor'),'libXcursor indisponível')
class NativeLoader(unittest.TestCase):
    def test_every_standard_role_loads_correct_artwork_size_hotspot_and_frames(self):
        # Run in a child process so libXcursor's cached search path cannot affect
        # another test or be affected by it. No session settings are touched.
        import subprocess
        env=os.environ.copy();env['XCURSOR_PATH']=str(ROOT)
        subprocess.run([sys.executable,str(Path(__file__)),'--probe'],env=env,check=True)


def probe():
    lib=C.CDLL(ctypes.util.find_library('Xcursor'))
    lib.XcursorLibraryLoadImages.argtypes=[C.c_char_p,C.c_char_p,C.c_int]
    lib.XcursorLibraryLoadImages.restype=C.POINTER(Images)
    lib.XcursorImagesDestroy.argtypes=[C.POINTER(Images)]
    cases=0
    for theme in ('sgi','SGI-Classic','SGI-Irixium'):
        for role in REQUIRED:
            for size in (24,32,48,64,96):
                expected=[f for f in read(ROOT/theme/'cursors'/role) if f['size']==size]
                result=lib.XcursorLibraryLoadImages(role.encode(),theme.encode(),size)
                assert result, (theme,role,size)
                try:
                    assert result.contents.nimage==len(expected),(theme,role,size,'frames')
                    for i,e in enumerate(expected):
                        f=result.contents.images[i].contents
                        assert (f.size,f.width,f.height,f.xhot,f.yhot,f.delay)==(size,e['width'],e['height'],*e['hotspot'],e['delay'])
                        assert C.string_at(f.pixels,f.width*f.height*4)==e['pixels'],(theme,role,size,'pixels')
                    cases+=1
                finally: lib.XcursorImagesDestroy(result)
    print('libXcursor:',cases,'consultas exatas passaram; nenhum fallback ou alteração na sessão.')


if __name__=='__main__':
    if '--probe' in sys.argv:probe()
    else:unittest.main()
