#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native X keyboard and clipboard against disposable GTK text controls."""
import json
import os
from pathlib import Path
import subprocess
import sys
assert os.environ.get('T04_PRIVATE_TEXT_EDITING') == '1'
import gi
gi.require_version('Gtk', sys.argv[1])
gi.require_version('Gdk', sys.argv[1])
from gi.repository import Gtk, Gdk, GLib
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preview_text_editing import bind
baseline = '--baseline' in sys.argv
Gtk.init([])
window = Gtk.Window(); window.set_title('T04 private editing probe'); box = Gtk.VBox(); window.add(box)
entry = Gtk.Entry(); entry.set_text('Initial entry')
text = Gtk.TextView(); text.get_buffer().set_text('Initial text')
spin = Gtk.SpinButton.new_with_range(0, 100, 1); spin.set_value(42)
for widget in (entry, text, spin):box.pack_start(widget, True, True, 0)
scene_mode = '--scene-fixture' in sys.argv
native_scene = None
if scene_mode:
 assert sys.argv[1] == '3.0'
 from types import SimpleNamespace
 import tempfile, hashlib
 import preview_gtk as preview
 model=json.loads(Path(sys.argv[sys.argv.index('--scene-fixture')+1]).read_text())
 recipe=model['recipes']['gtk3'];recipe['visible_controls']=(1<<4)|(1<<6)|(1<<7)
 recipe['selected_control']=4
 for i,y in ((4,16),(6,70),(7,130)):recipe['positions'][i]=[16,y]
 private=Path(tempfile.mkdtemp(prefix='editing-scene-'));project=private/'PROJECT.json';project.write_text(json.dumps(model))
 window.destroy()
 native_scene=preview.NativeScene(Gtk,Gdk,GLib,SimpleNamespace(embed_window=None,family='gtk3',project=project),model,hashlib.sha256(project.read_bytes()).hexdigest(),SimpleNamespace(emit=lambda *a,**k:None))
 window=native_scene.window;window.set_title('T04 private editing probe')
 entry=native_scene.widgets[4];spin=native_scene.widgets[6];text=native_scene.widgets[7].get_child()
window.set_default_size(500, 450);window.show_all()
Gdk.flush()
subprocess.run(['xdotool','search','--onlyvisible','--name','^T04 private editing probe$','windowfocus'],check=True,timeout=5)
if sys.argv[1] == '2.0':
 # Gdk2 typelib omits atom_intern; fixture uses the installed public C API.
 import ctypes
 gtk = ctypes.CDLL('libgtk-x11-2.0.so.0')
 gdk = ctypes.CDLL('libgdk-x11-2.0.so.0')
 glib = ctypes.CDLL('libglib-2.0.so.0')
 gdk.gdk_atom_intern.argtypes=[ctypes.c_char_p,ctypes.c_int];gdk.gdk_atom_intern.restype=ctypes.c_void_p
 gtk.gtk_clipboard_get.argtypes=[ctypes.c_void_p];gtk.gtk_clipboard_get.restype=ctypes.c_void_p
 gtk.gtk_clipboard_set_text.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int]
 gtk.gtk_clipboard_store.argtypes=[ctypes.c_void_p]
 gtk.gtk_clipboard_wait_for_text.argtypes=[ctypes.c_void_p];gtk.gtk_clipboard_wait_for_text.restype=ctypes.c_void_p
 glib.g_free.argtypes=[ctypes.c_void_p]
 class ClipboardFixture:
  def __init__(self):self.pointer=gtk.gtk_clipboard_get(gdk.gdk_atom_intern(b'CLIPBOARD',0))
  def set_text(self,text,length):gtk.gtk_clipboard_set_text(self.pointer,text.encode('utf-8'),length)
  def store(self):gtk.gtk_clipboard_store(self.pointer)
  def wait_for_text(self):
   pointer=gtk.gtk_clipboard_wait_for_text(self.pointer)
   if not pointer:return None
   try:return ctypes.string_at(pointer).decode('utf-8')
   finally:glib.g_free(pointer)
 clipboard=ClipboardFixture()
else:clipboard = Gtk.Clipboard.get(Gdk.atom_intern('CLIPBOARD',False))
if not baseline and not scene_mode:
 for w in (entry, text, spin):bind(w, Gtk, Gdk, GLib)
failures, results = [], []
widgets = [spin] if '--spin-only' in sys.argv else [entry] if baseline else [entry, text, spin]
state = {'widget': 0, 'stage': 0}

def get(w):
 if isinstance(w, Gtk.TextView):
  b=w.get_buffer();return b.get_text(b.get_start_iter(),b.get_end_iter(),True)
 return w.get_text()

def key(k):
 subprocess.run(['xdotool','key','--clearmodifiers',k],check=True,timeout=5)

def replace(value):
 clipboard.set_text(value,-1);clipboard.store();key('ctrl+a');key('ctrl+v')

def step():
 try:
  w=widgets[state['widget']];stage=state['stage']
  initial=initial_texts[state['widget']]
  sample='63' if isinstance(w,Gtk.SpinButton) else 'ação — São Paulo\nsegunda linha\nterceira' if isinstance(w,Gtk.TextView) else 'ação — São Paulo'
  other='17' if isinstance(w,Gtk.SpinButton) else 'substituição'
  if stage==0:w.grab_focus();replace(sample)
  elif stage==1:
   assert get(w)==sample,(stage,get(w));key('ctrl+z')
  elif stage==2:
   if baseline:
    assert get(w)==sample,'Unexpected native undo; baseline assumption invalid'
    results.append({'baseline':'Ctrl+Z did not restore GtkEntry text'});Gtk.main_quit();return False
   assert get(w)==initial,(stage,get(w));key('ctrl+shift+z')
  elif stage==3:
   assert get(w)==sample,(stage,get(w));key('ctrl+a');key('ctrl+c')
   assert clipboard.wait_for_text()==sample
   key('ctrl+x')
  elif stage==4:assert get(w)=='',(stage,get(w));key('ctrl+z')
  elif stage==5:assert get(w)==sample,(stage,get(w));key('ctrl+y')
  elif stage==6:assert get(w)=='',(stage,get(w));key('ctrl+v')
  elif stage==7:assert get(w)==sample,(stage,get(w));replace(other)
  elif stage==8:assert get(w)==other,(stage,get(w));key('ctrl+z')
  elif stage==9:
   assert get(w)==sample,(stage,get(w))
   menu=Gtk.Menu();w.emit('populate-popup',menu)
   labels=[item.get_label() for item in menu.get_children() if isinstance(item,Gtk.MenuItem)]
   assert labels[:2]==['Undo','Redo'],labels
   menu.get_children()[1].activate()
  elif stage==10:
   assert get(w)==other,(stage,get(w))
   if scene_mode:
    native_scene.build(model)
    widgets[:]=[native_scene.widgets[4],native_scene.widgets[7].get_child(),native_scene.widgets[6]]
    assert get(widgets[state['widget']])==other, ('rebuild',get(widgets[state['widget']]),other)
    widgets[state['widget']].grab_focus();key('ctrl+z')
    state['stage']=11;return True
  elif stage==11:
   assert get(w)==sample,(stage,get(w))
  if stage==10 or stage==11:
   results.append({'widget':w.__class__.__name__,'unicode':not isinstance(w,Gtk.SpinButton),'shortcuts':'Ctrl+A/C/X/V/Z/Y/Shift+Z','menu':'Undo/Redo activation'})
   state['widget']+=1;state['stage']=0
   if state['widget']==len(widgets):Gtk.main_quit();return False
   return True
  state['stage']+=1
 except Exception as e:
  failures.append({'widget':state['widget'],'stage':state['stage'],'error':repr(e)});Gtk.main_quit();return False
 return True
initial_texts=[get(w) for w in widgets]
GLib.timeout_add(300,step)
GLib.timeout_add_seconds(35,lambda:(failures.append('timeout'),Gtk.main_quit(),False)[-1])
Gtk.main();window.destroy()
assert not failures,failures
print(json.dumps({'status':'passed','gtk':sys.argv[1],'baseline':baseline,'real_scene_rebuilt':scene_mode,'results':results},ensure_ascii=False))
