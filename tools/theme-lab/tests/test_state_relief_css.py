#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK3 native CSS parsing only; does not prove painted pixels or fidelity."""
import importlib.util
from pathlib import Path
import re
import tempfile
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
ROOT=Path(__file__).resolve().parents[3]
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
backend=module(ROOT/'tools/theme-lab/backend.py','state_backend')
fixtures=module(ROOT/'tools/theme-lab/tests/test_backend.py','state_fixtures')
assert Gtk.init_check(None)[0]
builder=backend.load_builder(ROOT)
with tempfile.TemporaryDirectory(prefix='i118-native-css-') as directory:
    folder=Path(directory)
    cases=[(piece,state,relief) for piece,states in (
        ('arrow',('normal','pressed','disabled','backdrop','hover')),
        ('arrow_button',backend.PART_STATE_IDS),
        ('trough',('normal','disabled','backdrop')),
        ('thumb',('normal','pressed','disabled','backdrop','hover')),
        ('fitting',('normal','disabled','backdrop')))
        for state in states for relief in ('flat','raised','sunken')]
    for piece,state,relief in cases:
        recipe=fixtures.model()['recipes']['gtk3']
        recipe['scrollbar_parts']={piece:{'state_relief':{state:relief}}}
        with backend.piece_assets(builder,recipe,recipe['geometry']):
            manifest=builder.masks(folder/'adaptive',geometry=recipe['geometry'])
        common,css=backend.gtk3_sources(builder,manifest,recipe,recipe['geometry'])
        css=common+css
        # Artificial parser fixture; products still reference KDE roles.
        names=sorted(set(re.findall(r'@([A-Za-z_][A-Za-z_0-9]*)',css)))
        css=''.join('@define-color '+name+' #808080;\n' for name in names)+css
        path=folder/'gtk.css';path.write_text(css)
        provider=Gtk.CssProvider();errors=[]
        provider.connect('parsing-error',lambda p,section,error: errors.append(str(error)))
        provider.load_from_path(str(path))
        assert not errors,(state,relief,errors)
        print(piece,state,relief,'native CSS parse passed')
