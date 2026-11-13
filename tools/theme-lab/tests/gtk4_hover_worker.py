# SPDX-License-Identifier: GPL-3.0-or-later
"""Observe production GTK4 tooltip windows in its real native event loop."""
import ctypes as C
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

assert os.environ.get('T07_PRIVATE_PROBE')=='1'
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'plasma/tests/galerias-nativas'))
spec=importlib.util.spec_from_file_location('gtk4_gallery',root/'plasma/tests/galerias-nativas/gtk4_demo.py')
gallery=importlib.util.module_from_spec(spec);spec.loader.exec_module(gallery)
g=gallery;P,I=g.P,g.I
active=g.api('gtk_application_get_active_window',P,P)
tops=g.api('gtk_window_get_toplevels',P)
length=g.bind(g.gio,'g_list_model_get_n_items',g.U,P)
item=g.bind(g.gio,'g_list_model_get_item',P,P,g.U)
visible=g.api('gtk_widget_get_mapped',I,P)
css_name=g.api('gtk_widget_get_css_name',g.S,P)
native_widget=g.api('gtk_widget_get_native',P,P)
surface=g.api('gtk_native_get_surface',P,P)
xid=g.api('gdk_x11_surface_get_xid',C.c_ulong,P)
button_label=g.api('gtk_button_get_label',g.S,P)
menu_button_label=g.api('gtk_menu_button_get_label',g.S,P)
tooltip_text=g.api('gtk_widget_get_tooltip_text',g.S,P)
class Rect(C.Structure):
    _fields_=[('x',C.c_float),('y',C.c_float),('width',C.c_float),('height',C.c_float)]
# gtk4_demo.py binds this shared ctypes function with a void pointer because
# its own Bounds type is private to that module. Rebinding the same ctypes
# symbol here with POINTER(Rect) mutates the gallery's function signature and
# makes the gallery callback reject its structurally identical Bounds object.
bounds=g.api('gtk_widget_compute_bounds',I,P,P,C.c_void_p)
timer=g.bind(g.glib,'g_timeout_add',g.U,g.U,P,P)
TICK=C.CFUNCTYPE(I,P)
state={'phase':'wait','start':time.monotonic()};errors=[];proof={}

def widgets(node):
    yield node
    child=g.first_child(node)
    while child:
        yield from widgets(child);child=g.next_sibling(child)

def geometry(widget):
    native=surface(widget);assert native
    # xdotool promotes a reparented client to the Openbox frame when querying
    # geometry, adding the decoration offset to GTK child coordinates. Read
    # the exact GDK client XID so screen positions share GtkWindow's origin.
    data=subprocess.check_output(['xwininfo','-id',str(xid(native))],text=True,timeout=2)
    values={}
    for line in data.splitlines():
        if ':' not in line:
            continue
        key,value=line.split(':',1)
        if key.strip() in ('Absolute upper-left X','Absolute upper-left Y','Width','Height'):
            values[key.strip()]=int(value.strip())
    if len(values)!=4:
        raise RuntimeError('xwininfo did not report client geometry: '+data)
    return (values['Absolute upper-left X'],values['Absolute upper-left Y'],
            values['Width'],values['Height'])

def tips():
    found=[];model=tops()
    for n in range(length(model)):
        widget=item(model,n)
        try:
            for node in widgets(widget):
                if css_name(node)==b'tooltip' and visible(node):
                    found.append(geometry(native_widget(node)))
        finally:g.unref(widget)
    window=state.get('window')
    if window:
        x,y,_,_=geometry(window)
        for delayed in g.hint_popovers:
            if not delayed.visible or not delayed.popover:
                continue
            rect=Rect()
            if bounds(delayed.popover,window,C.byref(rect)):
                found.append((x+int(rect.x),y+int(rect.y),
                              int(rect.width),int(rect.height)))
    return found

def popover_diagnostics(window):
    result=[]
    for delayed in g.hint_popovers:
        rect=Rect()
        measured=bool(delayed.popover and bounds(delayed.popover,window,C.byref(rect)))
        result.append({'visible':delayed.visible,'position':delayed.position_strategy,
                       'bounds':((int(rect.x),int(rect.y),int(rect.width),int(rect.height))
                                 if measured else None)})
    return result

def tooltip_diagnostics():
    result=[];model=tops()
    for n in range(length(model)):
        widget=item(model,n)
        try:
            for node in widgets(widget):
                if css_name(node)!=b'tooltip' or not visible(node):
                    continue
                labels=[g.label_text(child).decode('utf-8','replace')
                        for child in widgets(node) if g.type_name(child)==b'GtkLabel'
                        and g.label_text(child)]
                result.append({'geometry':geometry(native_widget(node)),'labels':labels,
                               'type':g.type_name(node).decode(),
                               'top_type':g.type_name(widget).decode()})
        finally:g.unref(widget)
    return result

def move(x,y):subprocess.run(['xdotool','mousemove',str(x),str(y)],check=True,timeout=2)

def click_widget(widget):
    native=native_widget(widget);rect=Rect()
    assert bounds(widget,native,C.byref(rect))
    x,y,_,_=geometry(native)
    move(x+int(rect.x+rect.width/2),y+int(rect.y+rect.height/2))
    subprocess.run(['xdotool','click','1'],check=True,timeout=2)

def widget_bounds(widget):
    native=native_widget(widget);rect=Rect()
    assert bounds(widget,native,C.byref(rect))
    x,y,_,_=geometry(native)
    return (x+int(rect.x),y+int(rect.y),int(rect.width),int(rect.height))

def menu_rows():
    return [w for w in widgets(state['window'])
            if g.type_name(w)==b'GtkModelButton' and visible(w)]

@TICK
def tick(_):
    try:
        now=time.monotonic();phase=state['phase'];elapsed=now-state['start']
        if phase=='wait':
            window=active(g.application)
            if not window or elapsed<.7:return 1
            assert g.display_name(g.widget_display(window)).decode()==os.environ['DISPLAY']
            subprocess.run(['xdotool','windowfocus',str(xid(surface(window)))],check=True,timeout=2)
            button=next(w for w in widgets(window) if g.type_name(w)==b'GtkButton'
                        and button_label(w)==b'Press and release')
            rect=Rect();assert bounds(button,window,C.byref(rect))
            if not visible(button) or rect.width<80 or rect.height<20:
                assert elapsed<5,'production button never finished native allocation'
                return 1
            x,y,_,_=geometry(window)
            control=(x+int(rect.x),y+int(rect.y),int(rect.width),int(rect.height))
            state['control']=control;state['window']=window
            move(0,0);state.update(phase='cold',start=now)
        elif phase=='cold' and elapsed>.7:
            x,y,w,h=state['control'];move(x+w//2,y+h//2)
            state.update(phase='hover',start=now)
        elif phase=='hover':
            shown=tips()
            if elapsed<.2:assert not shown,'tooltip appeared without cold delay'
            if shown:
                assert len(shown)==1
                x,y,w,h=shown[0];a,b,c,d=state['control']
                assert not (x<a+c and a<x+w and y<b+d and b<y+h),(
                    'tooltip covers button: tooltip=%r control=%r popovers=%r' %
                    (shown[0],state['control'],{'popovers':popover_diagnostics(state['window']),
                                                 'native_windows':tooltip_diagnostics()}))
                display=subprocess.check_output(['xdotool','getdisplaygeometry'],text=True,timeout=2)
                width,height=map(int,display.split())
                assert x>=0 and y>=0 and x+w<=width and y+h<=height
                state['tip']=shown[0];state.update(phase='stable',start=now)
            elif elapsed>3:
                model=tops();observed=[]
                for n in range(length(model)):
                    widget=item(model,n)
                    observed.append({'type':g.type_name(widget).decode(),'visible':bool(visible(widget)),
                                     'tooltip_children':[(g.type_name(w).decode(),bool(visible(w))) for w in widgets(widget)
                                                         if b'Tooltip' in g.type_name(w) or b'Popover' in g.type_name(w)]})
                    g.unref(widget)
                raise AssertionError('native tooltip never appeared: '+json.dumps({'control':state['control'],'windows':observed}))
        elif phase=='stable':
            observed=tips()
            assert observed==[state['tip']],('tooltip oscillation: expected '
                +repr(state['tip'])+' observed '+repr(observed))
            if elapsed>.4:
                move(0,0);state.update(phase='leave',start=now)
        elif phase=='leave' and elapsed>.7:
            assert not tips(),'tooltip remained after leaving'
            x,y,w,h=state['control'];move(x+w//2,y+h//2)
            subprocess.run(['xdotool','click','1'],check=True,timeout=2)
            state.update(phase='click',start=now)
        elif phase=='click' and elapsed>.3:
            assert g.clicks==1,'native click lost after hover'
            proof.update(status='passed',control=state['control'],tooltip=state['tip'],
                         stable_ms=400,delay_checked_ms=200,closed_after_leave=True,
                         native_clicks=g.clicks,scope='one real GTK4 production push, default native style')
            menu=next(w for w in widgets(state['window']) if g.type_name(w)==b'GtkMenuButton'
                      and menu_button_label(w)==b'Native MenuButton')
            state['menu']=menu;click_widget(menu)
            state.update(phase='menu',start=now)
        elif phase=='menu' and elapsed>.3:
            rows=menu_rows();assert len(rows)>=4,'native menu did not open'
            assert all(g.tooltip_get(w) for w in rows),'opened menu row missing hint'
            target=next(w for w in rows if any(g.type_name(n)==b'GtkLabel'
                        and g.label_text(n)==b'Record native menu activation' for n in widgets(w)))
            state['opened_rows']=len(rows);state['menu_target']=target
            move(0,0);state.update(phase='menu_cold',start=now)
        elif phase=='menu_cold' and elapsed>.7:
            x,y,w,h=widget_bounds(state['menu_target'])
            state['menu_row_bounds']=(x,y,w,h)
            move(x+w//2,y+h//2);state.update(phase='menu_hover',start=now)
        elif phase=='menu_hover':
            shown=tips();expected=tooltip_text(state['menu_target'])
            if elapsed<.2:assert not shown,'menu-row tooltip appeared without cold delay'
            if shown:
                assert len(shown)==1,('multiple tooltips while hovering one menu row: '
                                      +repr(shown))
                x,y,w,h=shown[0];a,b,c,d=state['menu_row_bounds']
                assert (not (x<a+c and a<x+w and y<b+d and b<y+h)), \
                    'menu-row tooltip covers the hovered row'
                display=subprocess.check_output(['xdotool','getdisplaygeometry'],text=True,timeout=2)
                width,height=map(int,display.split())
                assert (x>=0 and y>=0 and x+w<=width and y+h<=height), \
                    'menu-row tooltip extends beyond the screen'
                state['menu_tip']=shown[0]
                state['menu_tip_text']=expected.decode() if expected else None
                state.update(phase='menu_stable',start=now)
            elif elapsed>3:
                raise AssertionError('native tooltip did not appear over a mapped GtkModelButton')
        elif phase=='menu_stable':
            assert tips()==[state['menu_tip']],('menu-row tooltip moved or oscillated: '
                                                +repr(tips()))
            assert (state['menu_tip_text']=='Registra a ativação deste item na amostra, sem iniciar aplicações.'), \
                'visible menu-row tooltip did not match its configured UTF-8 text'
            if elapsed>.4:
                move(0,0);state.update(phase='menu_leave',start=now)
        elif phase=='menu_leave' and elapsed>.7:
            assert not tips(),'menu-row tooltip remained after pointer left the row'
            assert menu_rows(),'native menu closed while pointer left its row'
            click_widget(state['menu_target'])
            state.update(phase='menu_action',start=now)
        elif phase=='menu_action' and elapsed>.4:
            assert g.label_text(g.status)==b'Native GAction activation received','menu action lost'
            assert not menu_rows(),'menu stayed open after activation'
            click_widget(state['menu']);state.update(phase='reopen',start=now)
        elif phase=='reopen' and elapsed>.3:
            rows=menu_rows();assert rows and all(g.tooltip_get(w) for w in rows)
            subprocess.run(['xdotool','key','Escape'],check=True,timeout=2)
            state.update(phase='cancel',start=now)
        elif phase=='cancel' and elapsed>.4:
            assert not menu_rows(),'Escape did not dismiss native menu'
            proof['menu']={'opened_rows':state['opened_rows'],'hints_present_on_reopen':True,
                           'row_hover_tooltip':state['menu_tip_text'],
                           'row_bounds':state['menu_row_bounds'],
                           'row_tooltip_bounds':state['menu_tip'],
                           'row_tooltip_stable_ms':400,'row_tooltip_closed_after_leave':True,
                           'native_action_received':True,'escape_closed':True}
            g.app_quit(g.application);return 0
        return 1
    except Exception as error:
        errors.append(str(error));g.app_quit(g.application);return 0

@g.CALLBACK
def start_probe(_application,_data):
    timer(100,C.cast(tick,P),None)

g.signal(g.application,'activate',start_probe)
g.app_run(g.application,0,None)
assert not errors,errors
assert proof.get('status')=='passed'
print(json.dumps({'hover_proof':proof}),flush=True)
