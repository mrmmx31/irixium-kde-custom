# SPDX-License-Identifier: GPL-3.0-or-later
"""Load only the project's compiled, version-guarded GTK2 push bridge.

Loading verifies the exact supported ABI. Public preflights permit only push
pressure with this bridge; other controls retain their native-input limits.
Presence alone does not prove painting, scene lifecycle or delivery.
"""
import ctypes as C
from pathlib import Path


class BoundPressSetter:
    """Own the GObject reference; invalidate the pointer before native dispose."""
    def __init__(self, button, pointer, setter):
        self.button, self.pointer, self.setter = button, pointer, setter
        self.closed = False
        self.handler = button.connect('destroy', self._destroy)

    def _destroy(self, _button):
        self.close()

    def __call__(self, enabled):
        if self.closed:
            raise ValueError('GTK2: botão da ponte já foi fechado ou destruído.')
        if type(enabled) is not bool:
            raise ValueError('GTK2: estado visual de pressão deve ser booleano.')
        error = self.setter(self.pointer, int(enabled))
        if error:
            raise ValueError('GTK2: pressão visual recusada pela ponte nativa (%d).' % error)

    def close(self):
        if not self.closed:
            self.closed = True
            self.button.disconnect(self.handler)
            self.button, self.pointer = None, None


class Gtk2PressBridge:
    def __init__(self, root):
        path = Path(root) / 'tools/theme-lab/build/libtheme-lab-gtk2-press.so'
        if path.is_symlink() or not path.is_file():
            raise ValueError('GTK2: ponte de pressão ausente; compile gtk2-pressure.')
        self.library = C.CDLL(str(path.absolute()))
        abi = self.library.theme_lab_gtk2_press_abi
        abi.argtypes, abi.restype = [], C.c_int
        if abi() != 1:
            raise ValueError('GTK2: ponte de pressão incompatível com o runtime; versão verificada 2.24.33.')
        self.setter = self.library.theme_lab_gtk2_press_set
        self.setter.argtypes, self.setter.restype = [C.c_void_p, C.c_int], C.c_int
        self.flags = self.library.theme_lab_gtk2_press_input_flags
        self.flags.argtypes, self.flags.restype = [C.c_void_p], C.c_int
        self.capsule = C.pythonapi.PyCapsule_GetPointer
        self.capsule.argtypes, self.capsule.restype = [C.py_object, C.c_char_p], C.c_void_p

    def bind(self, button):
        pointer = self.capsule(button.__gpointer__, None)
        if self.flags(pointer) < 0:
            raise ValueError('GTK2: ponte só aceita GtkButton nativo, vivo e da versão verificada.')
        return BoundPressSetter(button, pointer, self.setter)
