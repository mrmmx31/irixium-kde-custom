#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Interactive native Gtk4 C-ABI widgets, without the absent Gtk4 GIR package.
No CSS provider, custom painting, theme override or font assignment.
"""
import argparse
import ctypes as C
import json
import os
from demo_env import require_private_session

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--verificar",action="store_true",help="Resolve C ABI symbols only; never initialize GTK or connect to a display")
args=parser.parse_args()
gtk=C.CDLL("libgtk-4.so.1")
gio=C.CDLL("libgio-2.0.so.0")
obj=C.CDLL("libgobject-2.0.so.0")
glib=C.CDLL("libglib-2.0.so.0")
P,I,U,S,D=C.c_void_p,C.c_int,C.c_uint,C.c_char_p,C.c_double

def bind(library,name,result,*parameters):
    function=getattr(library,name)
    function.restype=result
    function.argtypes=list(parameters)
    return function

def api(name,result=P,*parameters): return bind(gtk,name,result,*parameters)

version=[api("gtk_get_"+kind+"_version",U)() for kind in ("major","minor","micro")]
app_new=api("gtk_application_new",P,S,I)
app_window=api("gtk_application_window_new",P,P)
app_run=bind(gio,"g_application_run",I,P,I,C.POINTER(S))
app_quit=bind(gio,"g_application_quit",None,P)
window_title=api("gtk_window_set_title",None,P,S)
window_size=api("gtk_window_set_default_size",None,P,I,I)
window_child=api("gtk_window_set_child",None,P,P)
window_present=api("gtk_window_present",None,P)
box_new=api("gtk_box_new",P,I,I)
append=api("gtk_box_append",None,P,P)
label_new=api("gtk_label_new",P,S)
label_set=api("gtk_label_set_text",None,P,S)
label_xalign=api("gtk_label_set_xalign",None,P,C.c_float)
button_new=api("gtk_button_new_with_label",P,S)
toggle_new=api("gtk_toggle_button_new_with_label",P,S)
toggle_active=api("gtk_toggle_button_set_active",None,P,I)
sensitive=api("gtk_widget_set_sensitive",None,P,I)
hexpand=api("gtk_widget_set_hexpand",None,P,I)
vexpand=api("gtk_widget_set_vexpand",None,P,I)
margin=[api("gtk_widget_set_margin_"+side,None,P,I) for side in ("top","bottom","start","end")]
tooltip=api("gtk_widget_set_tooltip_text",None,P,S)
entry_new=api("gtk_entry_new")
entry_set=api("gtk_editable_set_text",None,P,S)
entry_editable=api("gtk_editable_set_editable",None,P,I)
check_new=api("gtk_check_button_new_with_label",P,S)
check_active=api("gtk_check_button_set_active",None,P,I)
check_mixed=api("gtk_check_button_set_inconsistent",None,P,I)
check_group=api("gtk_check_button_set_group",None,P,P)
switch_new=api("gtk_switch_new")
switch_set=api("gtk_switch_set_active",None,P,I)
switch_get=api("gtk_switch_get_active",I,P)
dropdown_new=api("gtk_drop_down_new_from_strings",P,C.POINTER(S))
spin_new=api("gtk_spin_button_new_with_range",P,D,D,D)
spin_set=api("gtk_spin_button_set_value",None,P,D)
scale_new=api("gtk_scale_new_with_range",P,I,D,D,D)
range_set=api("gtk_range_set_value",None,P,D)
progress_new=api("gtk_progress_bar_new")
progress_set=api("gtk_progress_bar_set_fraction",None,P,D)
progress_text=api("gtk_progress_bar_set_text",None,P,S)
progress_show=api("gtk_progress_bar_set_show_text",None,P,I)
book_new=api("gtk_notebook_new")
book_add=api("gtk_notebook_append_page",I,P,P,P)
list_new=api("gtk_list_box_new")
list_add=api("gtk_list_box_append",None,P,P)
list_row=api("gtk_list_box_get_row_at_index",P,P,I)
list_select=api("gtk_list_box_select_row",None,P,P)
scroll_new=api("gtk_scrolled_window_new")
scroll_child=api("gtk_scrolled_window_set_child",None,P,P)
scroll_policy=api("gtk_scrolled_window_set_policy",None,P,I,I)
scroll_overlay=api("gtk_scrolled_window_set_overlay_scrolling",None,P,I)
text_new=api("gtk_text_view_new")
text_buffer=api("gtk_text_view_get_buffer",P,P)
text_set=api("gtk_text_buffer_set_text",None,P,S,I)
settings_get=api("gtk_settings_get_default")
object_get=bind(obj,"g_object_get",None,P,S,P,P)
free=bind(glib,"g_free",None,P)
connect=bind(obj,"g_signal_connect_data",C.c_ulong,P,S,P,P,P,U)
unref=bind(obj,"g_object_unref",None,P)
menu_new=bind(gio,"g_menu_new",P)
menu_append=bind(gio,"g_menu_append",None,P,S,S)
menu_sub=bind(gio,"g_menu_append_submenu",None,P,S,P)
menu_section=bind(gio,"g_menu_append_section",None,P,S,P)
action_new=bind(gio,"g_simple_action_new",P,S,P)
action_stateful=bind(gio,"g_simple_action_new_stateful",P,S,P,P)
action_enabled=bind(gio,"g_simple_action_set_enabled",None,P,I)
action_add=bind(gio,"g_action_map_add_action",None,P,P)
action_get_state=bind(gio,"g_action_get_state",P,P)
action_set_state=bind(gio,"g_simple_action_set_state",None,P,P)
variant_bool=bind(glib,"g_variant_new_boolean",P,I)
variant_get_bool=bind(glib,"g_variant_get_boolean",I,P)
variant_unref=bind(glib,"g_variant_unref",None,P)
menubar_new=api("gtk_popover_menu_bar_new_from_model",P,P)
menu_button_new=api("gtk_menu_button_new")
menu_button_label=api("gtk_menu_button_set_label",None,P,S)
menu_button_model=api("gtk_menu_button_set_menu_model",None,P,P)
if args.verificar:
    print(json.dumps({"status":"ready","toolkit":"GTK4 C ABI","version":".".join(map(str,version)),"gui_started":False,"gtk_initialized":False,"gir_required":False}))
    raise SystemExit(0)
require_private_session()

CALLBACK=C.CFUNCTYPE(None,P,P)
ACTION=C.CFUNCTYPE(None,P,P,P)
NOTIFY=C.CFUNCTYPE(None,P,P,P)
callbacks=[]
status=None
clicks=0
application=app_new(b"org.irixclassic.NativeGTK4Demo",1<<5)

def signal(widget,name,callback):
    callbacks.append(callback)
    connect(widget,name.encode(),C.cast(callback,P),None,None,0)

def label(caption):
    widget=label_new(caption.encode())
    label_xalign(widget,0)
    return widget

def row(): return box_new(0,8)
def note(caption):
    if status: label_set(status,caption.encode())
def setting(name):
    value=S()
    object_get(settings_get(),name.encode(),C.byref(value),None)
    result=value.value.decode() if value.value else None
    if value: free(C.cast(value,P))
    return result

@CALLBACK
def clicked(_button,_data):
    global clicks
    clicks+=1
    note("Native Gtk4 clicked signal received %d time(s)" % clicks)

@ACTION
def menu_record(_action,_parameter,_data): note("Native GAction activation received")
@ACTION
def menu_quit(_action,_parameter,_data): app_quit(application)
@ACTION
def menu_toggle(action,_parameter,_data):
    old=action_get_state(action)
    value=not variant_get_bool(old)
    variant_unref(old)
    action_set_state(action,variant_bool(value))
    note("Native checkable GAction toggled to " + str(value))
@NOTIFY
def switch_changed(widget,_property,_data): note("Native Gtk.Switch is " + ("on" if switch_get(widget) else "off"))

@CALLBACK
def activate(app,_data):
    global status
    window=app_window(app)
    theme,font=setting("gtk-theme-name"),setting("gtk-font-name")
    theme_title="DomainOS SR10.4" if theme.startswith("DomainOS-SR10-4") else "integrated theme demo"
    window_title(window,("NATIVEAPP GTK4 — %s PID %d" % (theme_title,os.getpid())).encode())
    window_size(window,850,620)
    outer=box_new(1,6)
    for fn in margin: fn(outer,6)
    window_child(window,outer)
    append(outer,label("REAL Gtk4 C-ABI widgets | theme: %s | font: %s" % (theme,font)))
    status=label("Only artificial controls/data; no files or personal applications are opened")
    for name,callback in (("record",menu_record),("quit",menu_quit)):
        action=action_new(name.encode(),None)
        signal(action,"activate",callback)
        action_add(app,action)
        unref(action)
    disabled=action_new(b"disabled",None)
    action_enabled(disabled,0)
    action_add(app,disabled)
    unref(disabled)
    checked=action_stateful(b"checked",None,variant_bool(1))
    signal(checked,"activate",menu_toggle)
    action_add(app,checked)
    unref(checked)
    model=menu_new()
    filemenu=menu_new()
    menu_append(filemenu,b"Record native menu activation",b"app.record")
    menu_append(filemenu,b"Unavailable menu action",b"app.disabled")
    section=menu_new()
    menu_append(section,b"Checkable menu item",b"app.checked")
    options=menu_new()
    menu_append(options,b"Submenu A",b"app.record")
    menu_append(options,b"Submenu B",b"app.record")
    menu_sub(section,b"Native submenu",options)
    menu_section(filemenu,None,section)
    menu_append(filemenu,b"Close only this demo",b"app.quit")
    menu_sub(model,b"Native Menu",filemenu)
    append(outer,menubar_new(model))
    book=book_new()
    vexpand(book,1)
    append(outer,book)
    controls=box_new(1,8)
    for fn in margin: fn(controls,8)
    book_add(book,controls,label("Native controls"))
    buttons=row()
    button=button_new(b"Press and release")
    signal(button,"clicked",clicked)
    tooltip(button,b"Native GTK4 button: hold the pointer button to inspect its pressed relief")
    toggle=toggle_new(b"Latched toggle")
    toggle_active(toggle,1)
    unavailable=button_new(b"Disabled button")
    sensitive(unavailable,0)
    menu_button=menu_button_new()
    menu_button_label(menu_button,b"Native MenuButton")
    menu_button_model(menu_button,filemenu)
    for item in (button,toggle,unavailable,menu_button): append(buttons,item)
    append(controls,buttons)
    fields=row()
    for caption,editable,enabled in (("Editable native Gtk.Entry",True,True),("Read only",False,True),("Disabled field",True,False)):
        entry=entry_new()
        entry_set(entry,caption.encode())
        entry_editable(entry,editable)
        sensitive(entry,enabled)
        hexpand(entry,1)
        append(fields,entry)
    append(controls,fields)
    checks=row()
    for caption,active,mixed,enabled in (("Off",False,False,True),("Checked",True,False,True),("Mixed",True,True,True),("Disabled",True,False,False)):
        check=check_new(caption.encode())
        check_active(check,active)
        check_mixed(check,mixed)
        sensitive(check,enabled)
        append(checks,check)
    radio1=check_new(b"Radio A")
    radio2=check_new(b"Radio B")
    check_group(radio2,radio1)
    for radio in (radio1,radio2): append(checks,radio)
    append(controls,checks)
    switches=row()
    append(switches,label("Native Gtk.Switch controls:"))
    for active,enabled in ((False,True),(True,True),(True,False)):
        switch=switch_new()
        switch_set(switch,active)
        sensitive(switch,enabled)
        signal(switch,"notify::active",switch_changed)
        append(switches,switch)
    append(controls,switches)
    values=row()
    strings=(S*4)(b"First option",b"Second option",b"Third option",None)
    dropdown=dropdown_new(strings)
    spin=spin_new(0,100,1)
    spin_set(spin,42)
    scale=scale_new(0,0,100,1)
    range_set(scale,38)
    hexpand(scale,1)
    for item in (dropdown,spin,scale): append(values,item)
    append(controls,values)
    progress=progress_new()
    progress_set(progress,.57)
    progress_show(progress,1)
    progress_text(progress,b"Native progress 57% (static test data)")
    append(controls,progress)
    listing=list_new()
    for index in range(1,41): list_add(listing,label("Item %02d — Artificial row for native scrolling — " % index + "long text "*20))
    list_select(listing,list_row(listing,1))
    scroll=scroll_new()
    scroll_overlay(scroll,0)
    scroll_policy(scroll,0,0)
    scroll_child(scroll,listing)
    vexpand(scroll,1)
    append(controls,scroll)
    text=text_new()
    content=("Native Gtk.TextView\nSelect/edit text here.\n" + "Sample paragraph for native vertical scrolling.\n"*50).encode()
    text_set(text_buffer(text),content,-1)
    text_scroll=scroll_new()
    scroll_overlay(text_scroll,0)
    scroll_child(text_scroll,text)
    book_add(book,text_scroll,label("Text and scrolling"))
    append(outer,status)
    window_present(window)
    print(json.dumps({"status":"opened","toolkit":"GTK4 C ABI","version":".".join(map(str,version)),"pid":os.getpid(),"theme":theme,"font":font,"custom_css":False}),flush=True)
    for menu in (model,filemenu,section,options): unref(menu)

signal(application,"activate",activate)
try:
    raise SystemExit(app_run(application,0,None))
finally:
    unref(application)
