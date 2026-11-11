#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Diagnostic native GTK2 fixture; invoke with private Xvfb and explicit marker.
import gi,json,os,argparse,sys,subprocess,time
from pathlib import Path
assert os.environ.get('I167_PRIVATE_PROBE')=='1'
parser=argparse.ArgumentParser(description='Native GTK2 properties in a private Xvfb fixture')
parser.add_argument('--recipe',type=Path)
parser.add_argument('--paint-rc',type=Path)
parser.add_argument('--capture',type=Path)
parser.add_argument('--insensitive',action='store_true')
parser.add_argument('--backdrop',action='store_true')
parser.add_argument('--value',type=float,default=25)
parser.add_argument('--cycles',type=Path)
parser.add_argument('--endpoint-cycles',action='store_true')
parser.add_argument('--drag-cycles',type=Path)
args=parser.parse_args()
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gtk2_recipe import scrollbar_properties,scrollbar_rc
gi.require_version('Gtk','2.0')
from gi.repository import Gtk,GObject
Gtk.init([])
proposed=json.loads(args.recipe.read_text()) if args.recipe else None
if proposed: Gtk.rc_parse_string(scrollbar_rc(proposed))
if args.paint_rc: Gtk.rc_parse(str(args.paint_rc))
w=Gtk.Window(); box=Gtk.VBox(spacing=4); w.add(box)
w.set_title('I167 private GTK2 probe '+str(os.getpid()))
adj=Gtk.Adjustment(value=args.value,lower=0,upper=100,step_increment=1,page_increment=10,page_size=20)
bars=[Gtk.HScrollbar(adjustment=adj),Gtk.VScrollbar(adjustment=adj)]
for b in bars:
 if args.drag_cycles:
  b.set_size_request(200,-1) if b.__gtype__.name=='GtkHScrollbar' else b.set_size_request(-1,200)
 if args.insensitive:
  b.set_name('themeLabInsensitiveScroll');b.set_sensitive(False)
 elif args.backdrop:b.set_name('themeLabBackdropScroll')
 alignment=Gtk.Alignment(xalign=0,yalign=0,xscale=0,yscale=0)
 alignment.add(b);box.pack_start(alignment,False,False,0)
w.show_all()
while Gtk.events_pending():Gtk.main_iteration()
props=['slider-width','stepper-size','trough-border','min-slider-length','has-backward-stepper','has-forward-stepper','stepper-spacing','trough-under-steppers']
r={'runtime':f'{Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}','private_display':os.environ['DISPLAY'],'gui_native':True,'recipe_applied':False,'historical_fidelity_claimed':False,'widgets':[]}
def style_value(b,p):
 value=GObject.Value();value.init(b.find_style_property(p).value_type)
 b.style_get_property(p,value);return value.get_value()
for b in bars:
 a=b.get_allocation();req=Gtk.Requisition();b.size_request(req)
 values={p:style_value(b,p) for p in props}
 r['widgets'].append({'type':b.__gtype__.name,'allocation':[a.x,a.y,a.width,a.height],'natural_request':[req.width,req.height],'properties':values})
 if proposed:
  expected=scrollbar_properties(proposed)
  for p in props:
   if p in expected: assert values[p]==expected[p],(p,values[p],expected[p])
  cross=req.height if b.__gtype__.name=='GtkHScrollbar' else req.width
  assert cross==expected['slider-width']+2*expected['trough-border'],cross
  allocated=a.height if b.__gtype__.name=='GtkHScrollbar' else a.width
  assert allocated==cross,(allocated,cross)
if proposed: r.update(geometry_recipe_applied=True,proposal=proposed)
if args.paint_rc: r.update(scrollbar_paint_loaded=True,whole_insensitive=args.insensitive,backdrop_fixture=args.backdrop)
if args.capture:
 subprocess.run(['import','-window','root',str(args.capture)],check=True,timeout=10)
if args.cycles or args.drag_cycles:
 if args.cycles:args.cycles.mkdir(parents=True,exist_ok=True)
 def drain_for(seconds=.06):
  deadline=time.monotonic()+seconds
  while time.monotonic()<deadline:
   while Gtk.events_pending():Gtk.main_iteration()
   time.sleep(.001)
 def x(*values):
  return subprocess.run(['xdotool',*map(str,values)],check=True,capture_output=True,text=True,timeout=5).stdout
 windows=x('search','--onlyvisible','--pid',os.getpid()).split()
 assert len(windows)==1,windows
 origin=dict(line.split('=',1) for line in x('getwindowgeometry','--shell',windows[0]).splitlines() if '=' in line)
 ox,oy=int(origin['X']),int(origin['Y'])
 properties=scrollbar_properties(proposed)
 border,cross,longitudinal=(properties[k] for k in ('trough-border','slider-width','stepper-size'))
 cycles=[]
 for direction in (('left','right','up','down') if args.cycles else ()):
  horizontal=direction in ('left','right');b=bars[0 if horizontal else 1];a=b.get_allocation()
  decreasing=direction in ('left','up')
  start=(0 if decreasing else 80) if args.endpoint_cycles else 25
  adj.set_value(start);drain_for()
  px=ox+a.x+(border+longitudinal//2 if decreasing else a.width-border-longitudinal//2-1) if horizontal else ox+a.x+border+cross//2
  py=oy+a.y+border+cross//2 if horizontal else oy+a.y+(border+longitudinal//2 if decreasing else a.height-border-longitudinal//2-1)
  held=False
  try:
   x('mousemove','--sync',px,py);drain_for()
   x('mousedown',1);held=True;drain_for()
   after_press=adj.get_value()
   expected=start if args.insensitive or args.endpoint_cycles else start+(-1 if decreasing else 1)
   assert after_press==expected,(direction,start,after_press,expected)
   pressed=args.cycles/(direction+'-held.png')
   subprocess.run(['import','-window','root',str(pressed)],check=True,timeout=10)
  finally:
   if held:x('mouseup',1)
  x('mousemove','--sync',100,100);drain_for()
  released=args.cycles/(direction+'-released.png')
  subprocess.run(['import','-window','root',str(released)],check=True,timeout=10)
  assert adj.get_value()==after_press,(direction,'unexpected change after release')
  cycles.append({'direction':direction,'start':start,'held_value':after_press,'released_value':adj.get_value(),
                 'blocked':args.insensitive or args.endpoint_cycles,'held_capture':str(pressed),'released_capture':str(released)})
 r['cycles']=cycles
 if args.drag_cycles:
  args.drag_cycles.mkdir(parents=True,exist_ok=True)
  drags=[]
  for b in bars:
   horizontal=b.__gtype__.name=='GtkHScrollbar';a=b.get_allocation()
   adj.set_value(25);drain_for()
   slider_start,slider_end=b.get_slider_range()
   center=(slider_start+slider_end)//2
   px=ox+a.x+(center if horizontal else border+cross//2)
   py=oy+a.y+(border+cross//2 if horizontal else center)
   held=False
   label='horizontal' if horizontal else 'vertical'
   try:
    x('mousemove','--sync',px,py);drain_for()
    x('mousedown',1);held=True;drain_for()
    assert adj.get_value()==25,(label,'press moved the cursor')
    x('mousemove','--sync',px+(24 if horizontal else 0),py+(0 if horizontal else 24));drain_for()
    value=adj.get_value()
    assert 25<value<=80,(label,'drag did not increase adjustment',value)
    held_capture=args.drag_cycles/(label+'-held.png')
    subprocess.run(['import','-window','root',str(held_capture)],check=True,timeout=10)
    held_range=list(b.get_slider_range())
   finally:
    if held:x('mouseup',1)
   x('mousemove','--sync',300,300);drain_for()
   released_capture=args.drag_cycles/(label+'-released.png')
   subprocess.run(['import','-window','root',str(released_capture)],check=True,timeout=10)
   assert adj.get_value()==value,(label,'release moved adjustment')
   drags.append({'orientation':label,'start':25,'held_value':value,'released_value':adj.get_value(),
                 'held_range':held_range,'released_range':list(b.get_slider_range()),
                 'held_capture':str(held_capture),'released_capture':str(released_capture)})
  r['drags']=drags
w.destroy()
print(json.dumps(r,indent=2))
