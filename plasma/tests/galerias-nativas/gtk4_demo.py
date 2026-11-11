#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Interactive native Gtk4 C-ABI widgets, without the absent Gtk4 GIR package.
No CSS provider, custom painting, theme override or font assignment.
"""
import argparse
import ctypes as C
import json
import os
import sys
import time
from pathlib import Path
from demo_env import require_private_session

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--verificar",action="store_true",help="Resolve C ABI symbols only; never initialize GTK or connect to a display")
parser.add_argument("--theme-lab-scrollbar-css",type=Path)
parser.add_argument("--theme-lab-scrollbar-class")
args=parser.parse_args()
if bool(args.theme_lab_scrollbar_css) != bool(args.theme_lab_scrollbar_class):
    parser.error('--theme-lab-scrollbar-css and --theme-lab-scrollbar-class must be supplied together')
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
overlay_new=api("gtk_overlay_new")
overlay_child=api("gtk_overlay_set_child",None,P,P)
overlay_add=api("gtk_overlay_add_overlay",None,P,P)
fixed_new=api("gtk_fixed_new")
fixed_put=api("gtk_fixed_put",None,P,P,D,D)
compute_bounds=api("gtk_widget_compute_bounds",I,P,P,C.c_void_p)
box_new=api("gtk_box_new",P,I,I)
append=api("gtk_box_append",None,P,P)
label_new=api("gtk_label_new",P,S)
label_set=api("gtk_label_set_text",None,P,S)
label_xalign=api("gtk_label_set_xalign",None,P,C.c_float)
button_new=api("gtk_button_new_with_label",P,S)
button_label=api("gtk_button_get_label",S,P)
toggle_new=api("gtk_toggle_button_new_with_label",P,S)
toggle_active=api("gtk_toggle_button_set_active",None,P,I)
sensitive=api("gtk_widget_set_sensitive",None,P,I)
hexpand=api("gtk_widget_set_hexpand",None,P,I)
vexpand=api("gtk_widget_set_vexpand",None,P,I)
margin=[api("gtk_widget_set_margin_"+side,None,P,I) for side in ("top","bottom","start","end")]
tooltip=api("gtk_widget_set_tooltip_text",None,P,S)
tooltip_get=api("gtk_widget_get_tooltip_text",S,P)
widget_has_tooltip=api("gtk_widget_get_has_tooltip",I,P)
widget_display=api("gtk_widget_get_display",P,P)
display_name=api("gdk_display_get_name",S,P)
first_child=api("gtk_widget_get_first_child",P,P)
next_sibling=api("gtk_widget_get_next_sibling",P,P)
type_name=bind(obj,"g_type_name_from_instance",S,P)
widget_parent=api("gtk_widget_get_parent",P,P)
object_data=bind(obj,"g_object_get_data",P,P,S)
object_set_data=bind(obj,"g_object_set_data",None,P,S,P)
orientation=api("gtk_orientable_get_orientation",I,P)
css_name=api("gtk_widget_get_css_name",S,P)
css_class_add=api("gtk_widget_add_css_class",None,P,S)
css_class_has=api("gtk_widget_has_css_class",I,P,S)
widget_width=api("gtk_widget_get_width",I,P)
widget_height=api("gtk_widget_get_height",I,P)
widget_mapped=api("gtk_widget_get_mapped",I,P)
widget_native=api("gtk_widget_get_native",P,P)
widget_can_target=api("gtk_widget_set_can_target",None,P,I)
timeout_add=bind(glib,"g_timeout_add",U,U,P,P)
display_monitors=api("gdk_display_get_monitors",P,P)
monitor_geometry=api("gdk_monitor_get_geometry",None,P,C.c_void_p)
list_length=bind(gio,"g_list_model_get_n_items",U,P)
list_item=bind(gio,"g_list_model_get_item",P,P,U)

class GdkRectangle(C.Structure):
    _fields_=[('x',I),('y',I),('width',I),('height',I)]

def fitted_window_size(window):
    """Keep the private gallery's default client size inside the first monitor."""
    monitors=display_monitors(widget_display(window))
    if not monitors or not list_length(monitors):
        return 850,620
    monitor=list_item(monitors,0)
    if not monitor:
        return 850,620
    try:
        geometry=GdkRectangle()
        monitor_geometry(monitor,C.byref(geometry))
    finally:
        unref(monitor)
    return min(850,max(480,geometry.width-40)),min(620,max(360,geometry.height-80))
object_ref=bind(obj,"g_object_ref",P,P)
object_unref=bind(obj,"g_object_unref",None,P)
provider_new=api("gtk_css_provider_new")
provider_load=api("gtk_css_provider_load_from_path",None,P,S)
provider_add=bind(gtk,"gtk_style_context_add_provider_for_display",None,P,P,U)
context_iteration=bind(glib,"g_main_context_iteration",I,P,I)
open_status_callbacks=[]

scrollbar_get_type=api("gtk_scrollbar_get_type",C.c_size_t)
type_class_ref=bind(obj,"g_type_class_ref",P,C.c_size_t)
type_class_unref=bind(obj,"g_type_class_unref",None,P)
find_property=bind(obj,"g_object_class_find_property",P,P,S)
label_text=api("gtk_label_get_text",S,P)
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
try:
    from gtk4_hint_popover import DelayedPopoverHint
except ModuleNotFoundError as error:
    if error.name != 'gtk4_hint_popover':
        raise
    for parent in Path(__file__).resolve().parents:
        module_dir = parent / 'tools/theme-lab'
        if (module_dir / 'gtk4_hint_popover.py').is_file():
            sys.path.insert(0, str(module_dir))
            break
    from gtk4_hint_popover import DelayedPopoverHint

CALLBACK=C.CFUNCTYPE(None,P,P)
ACTION=C.CFUNCTYPE(None,P,P,P)
NOTIFY=C.CFUNCTYPE(None,P,P,P)
callbacks=[]
status=None
clicks=0
hint_widgets=[]
hint_popovers=[]
hint_retry_callbacks=[]
hint_retry_pending=set()
hint_retry_failures=[]
hint_layer=None
root_overlay=None
scrollbar_style_class=args.theme_lab_scrollbar_class
scrollbar_css_errors=[]
styled_scrollbars=[]

def hint(widget,text):
    tooltip(widget,text.encode('utf-8'))
    hint_widgets.append((widget,text))

class Bounds(C.Structure):
    _fields_=[('x',C.c_float),('y',C.c_float),('width',C.c_float),('height',C.c_float)]

def attach_vertical_scrollbar_hint(widget):
    return attach_delayed_hint(widget)

def attach_delayed_hint(widget):
    if not hint_layer or object_data(widget,b'gallery-hint-popover-bound'):
        return False
    # Compute both rectangles relative to the same GtkNative, then translate
    # into the GtkFixed overlay's coordinates. Some GTK4 composite widgets
    # report inflated bounds when GtkWidgetComputeBounds targets the overlay
    # child directly; that can put the anchor beyond the viewport edge.
    native=widget_native(widget)
    if not native:
        return False
    area,layer_area=Bounds(),Bounds()
    if (not compute_bounds(widget,native,C.byref(area)) or
            not compute_bounds(hint_layer,native,C.byref(layer_area))):
        return False
    # Large GtkListBox allocations can extend beyond their visible
    # GtkScrolledWindow viewport; anchor from the visible intersection.
    ancestor=widget_parent(widget)
    while ancestor:
        if type_name(ancestor)==b'GtkScrolledWindow':
            clip=Bounds()
            if compute_bounds(ancestor,native,C.byref(clip)):
                left=max(area.x,clip.x)
                top=max(area.y,clip.y)
                right=min(area.x+area.width,clip.x+clip.width)
                bottom=min(area.y+area.height,clip.y+clip.height)
                area.x,area.y=left,top
                area.width,area.height=max(0,right-left),max(0,bottom-top)
            break
        ancestor=widget_parent(ancestor)
    area.x-=layer_area.x
    area.y-=layer_area.y
    width,height=round(area.width),round(area.height)
    if width<=0 or height<=0:
        return False
    text_ptr=tooltip_get(widget)
    if not text_ptr:
        return False
    text=C.string_at(text_ptr).decode('utf-8')
    hint_popovers.append(DelayedPopoverHint(
        widget,hint_layer,round(area.x),round(area.y),width,height,text))
    object_set_data(widget,b'gallery-hint-popover-bound',P(1))
    return True

@CALLBACK
def attach_vertical_hint_on_map(widget,_data):
    schedule_delayed_hint_retry(widget)

def schedule_delayed_hint_retry(widget):
    key=int(widget)
    if key in hint_retry_pending:
        return
    held_widget=object_ref(widget)
    attempts={'count':0}

    @C.CFUNCTYPE(I,P)
    def retry(_data):
        attempts['count']+=1
        try:
            if attach_delayed_hint(held_widget):
                hint_retry_pending.discard(key)
                object_unref(held_widget)
                return 0
        except Exception as error:
            hint_retry_failures.append(str(error))
            hint_retry_pending.discard(key)
            object_unref(held_widget)
            return 0
        if attempts['count']>=40:
            hint_retry_failures.append('GTK4 hint bounds unavailable after 1 second')
            hint_retry_pending.discard(key)
            object_unref(held_widget)
            return 0
        return 1

    hint_retry_callbacks.append(retry)
    hint_retry_pending.add(key)
    if not timeout_add(25,C.cast(retry,P),None):
        hint_retry_pending.discard(key)
        object_unref(held_widget)
        hint_retry_failures.append('GLib refused the GTK4 hint attachment timer')

def internal_hints(widget):
    """Inspect native child widgets without replacing their painting or signals."""
    counts={'scrollbars':0,'menu_rows':0,'scrollbar_contract':None}
    menu_text={
        'Record native menu activation':'Registra a ativação deste item na amostra, sem iniciar aplicações.',
        'Unavailable menu action':'Ação indisponível da amostra: não pode ser executada.',
        'Checkable menu item':'Marca ou desmarca esta opção do menu nativo da amostra.',
        'Native submenu':'Abre o submenu com duas ações de exemplo.',
        'Submenu A':'Registra a ativação da primeira ação de exemplo.',
        'Submenu B':'Registra a ativação da segunda ação de exemplo.',
        'Close only this demo':'Fecha somente esta galeria privada; não encerra a sessão pessoal.',
    }
    def descendants(node):
        yield node
        child=first_child(node)
        while child:
            yield from descendants(child)
            child=next_sibling(child)
    # Snapshot the tree before inserting transparent popover anchors into its overlay.
    for child in list(descendants(widget)):
        kind=type_name(child).decode()
        if kind.startswith('GtkPopover') and not object_data(child,b'gallery-hint-map-bound'):
            object_set_data(child,b'gallery-hint-map-bound',P(1))
            signal(child,'map',refresh_internal_hints)
        if kind=='GtkScrollbar':
            axis='horizontal' if orientation(child)==0 else 'vertical'
            if scrollbar_style_class:
                css_class_add(child,scrollbar_style_class.encode('ascii'))
                styled_scrollbars.append(child)
            text='Barra %s: arraste o cursor ou acione o trilho para percorrer o conteúdo nativo.' % axis
            if not tooltip_get(child):hint(child,text)
            if axis=='vertical' and not attach_vertical_scrollbar_hint(child):
                if widget_mapped(child):
                    schedule_delayed_hint_retry(child)
                elif not object_data(child,b'gallery-hint-map-bound'):
                    object_set_data(child,b'gallery-hint-map-bound',P(1))
                    signal(child,'map',attach_vertical_hint_on_map)
            counts['scrollbars']+=1
            if counts['scrollbar_contract'] is None:
                klass=type_class_ref(scrollbar_get_type())
                try:
                    properties=('has-backward-stepper','has-forward-stepper',
                                'has-secondary-backward-stepper','has-secondary-forward-stepper')
                    counts['scrollbar_contract']={
                        'gtk_version':'.'.join(map(str,version)),
                        'widget_css_name':css_name(child).decode('ascii'),
                        'arrow_stepper_properties':{name:bool(find_property(klass,name.encode()))
                                                    for name in properties},
                        'observed_widget_type':kind,
                        'orientation':axis,
                    }
                finally:
                    type_class_unref(klass)
        elif kind in ('GtkListBox','GtkTextView'):
            # Large text/list surfaces use the same delayed GTK-native
            # popover bridge as tall scrollbars. A centered GtkTooltip would
            # obscure content even when it misses the pointer; the anchor is
            # placed in free space outside the full owning surface.
            if tooltip_get(child) and not attach_delayed_hint(child):
                if widget_mapped(child):
                    schedule_delayed_hint_retry(child)
                elif not object_data(child,b'gallery-hint-map-bound'):
                    object_set_data(child,b'gallery-hint-map-bound',P(1))
                    signal(child,'map',attach_vertical_hint_on_map)
        elif kind=='GtkMenuButton':
            # Native menu-button tooltips are anchored at the pointer and can
            # extend past a narrow screen edge. Reuse the delayed GTK popover
            # placement so the hint stays visible without covering the button.
            if tooltip_get(child):
                attach_delayed_hint(child)
        elif kind=='GtkModelButton':
            labels=[label_text(node).decode() for node in descendants(child)
                    if type_name(node)==b'GtkLabel' and label_text(node)]
            text=next((menu_text[label] for label in labels if label in menu_text),None)
            if text:
                if not tooltip_get(child):hint(child,text)
                attach_delayed_hint(child)
                counts['menu_rows']+=1
        elif kind=='GtkButton' and button_label(child)==b'Press and release':
            attach_delayed_hint(child)
    return counts

@CALLBACK
def refresh_internal_hints(widget,_data):
    try:
        internal_hints(widget)
    except Exception as error:
        hint_retry_failures.append('late GTK4 native-child inspection: '+str(error))
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
    global hint_layer,root_overlay
    window=app_window(app)
    theme,font=setting("gtk-theme-name"),setting("gtk-font-name")
    theme_title="DomainOS SR10.4" if theme.startswith("DomainOS-SR10-4") else "integrated theme demo"
    window_title(window,("NATIVEAPP GTK4 — %s PID %d" % (theme_title,os.getpid())).encode())
    window_size_px=fitted_window_size(window)
    window_size(window,*window_size_px)
    provider=None
    if args.theme_lab_scrollbar_css:
        class Error(C.Structure):
            _fields_=[('domain',C.c_uint),('code',C.c_int),('message',C.c_char_p)]
        @C.CFUNCTYPE(None,P,P,P,P)
        def parsing_error(_provider,_section,error,_data):
            value=C.cast(error,C.POINTER(Error)).contents
            scrollbar_css_errors.append(value.message.decode('utf-8','replace'))
        provider=provider_new()
        signal(provider,'parsing-error',parsing_error)
        provider_load(provider,str(args.theme_lab_scrollbar_css).encode())
        if scrollbar_css_errors:
            raise RuntimeError('GTK4 scrollbar CSS parse failed: '+'; '.join(scrollbar_css_errors))
        provider_add(widget_display(window),provider,800)
    outer=box_new(1,6)
    for fn in margin: fn(outer,6)
    root_overlay=overlay_new()
    overlay_child(root_overlay,outer)
    hint_layer=fixed_new()
    # The overlay only hosts invisible GtkMenuButton anchors. It must never
    # intercept pointer input intended for the native controls underneath.
    widget_can_target(hint_layer,0)
    overlay_add(root_overlay,hint_layer)
    window_child(window,root_overlay)
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
    menubar=menubar_new(model)
    hint(menubar,'Menu nativo da amostra: acione, alterne opções ou feche somente esta galeria privada.')
    append(outer,menubar)
    book=book_new()
    vexpand(book,1)
    append(outer,book)
    controls=box_new(1,8)
    for fn in margin: fn(controls,8)
    controls_tab=label("Native controls")
    hint(controls_tab,'Seleciona a página com controles nativos da amostra.')
    book_add(book,controls,controls_tab)
    buttons=row()
    button=button_new(b"Press and release")
    signal(button,"clicked",clicked)
    hint(button,'Botão GTK4: mantenha pressionado para observar o relevo; solte para registrar o clique da amostra.')
    toggle=toggle_new(b"Latched toggle")
    toggle_active(toggle,1)
    hint(toggle,'Botão alternável da amostra: clique para ligar ou desligar seu estado.')
    unavailable=button_new(b"Disabled button")
    sensitive(unavailable,0)
    hint(unavailable,'Botão desabilitado da amostra: mostra o estado sem executar uma ação.')
    menu_button=menu_button_new()
    menu_button_label(menu_button,b"Native MenuButton")
    menu_button_model(menu_button,filemenu)
    hint(menu_button,'Abre o menu nativo desta amostra; nenhuma ação inicia aplicações pessoais.')
    for item in (button,toggle,unavailable,menu_button): append(buttons,item)
    append(controls,buttons)
    fields=row()
    for caption,editable,enabled in (("Editable native Gtk.Entry",True,True),("Read only",False,True),("Disabled field",True,False)):
        entry=entry_new()
        entry_set(entry,caption.encode())
        entry_editable(entry,editable)
        sensitive(entry,enabled)
        hint(entry,('Entrada nativa de uma linha: edite o texto da amostra; não modifica o tema.' if editable and enabled
                    else 'Campo não editável.'))
        hexpand(entry,1)
        append(fields,entry)
    append(controls,fields)
    checks=row()
    for caption,active,mixed,enabled in (("Off",False,False,True),("Checked",True,False,True),("Mixed",True,True,True),("Disabled",True,False,False)):
        check=check_new(caption.encode())
        check_active(check,active)
        check_mixed(check,mixed)
        sensitive(check,enabled)
        hint(check,'Marca ou desmarca este controle.')
        append(checks,check)
    radio1=check_new(b"Radio A")
    radio2=check_new(b"Radio B")
    check_group(radio2,radio1)
    for radio in (radio1,radio2):
        hint(radio,'Seleciona uma opção exclusiva do grupo.')
        append(checks,radio)
    append(controls,checks)
    switches=row()
    append(switches,label("Native Gtk.Switch controls:"))
    for active,enabled in ((False,True),(True,True),(True,False)):
        switch=switch_new()
        switch_set(switch,active)
        sensitive(switch,enabled)
        signal(switch,"notify::active",switch_changed)
        hint(switch,'Interruptor nativo da amostra: altera seu estado ligado/desligado quando habilitado.')
        append(switches,switch)
    append(controls,switches)
    values=row()
    strings=(S*4)(b"First option",b"Second option",b"Third option",None)
    dropdown=dropdown_new(strings)
    hint(dropdown,'Escolha uma opção da lista nativa; isso não troca o esquema do desktop.')
    spin=spin_new(0,100,1)
    spin_set(spin,42)
    hint(spin,'Valor da amostra, sem unidade: mínimo 0, máximo 100, passo 1. Edite ou use as setas; não altera medidas do tema em px.')
    scale=scale_new(0,0,100,1)
    range_set(scale,38)
    hint(scale,'Escala 0–100, passo 1; sem unidade.')
    hexpand(scale,1)
    for item in (dropdown,spin,scale): append(values,item)
    append(controls,values)
    progress=progress_new()
    progress_set(progress,.57)
    progress_show(progress,1)
    progress_text(progress,b"Native progress 57% (static test data)")
    hint(progress,'Amostra fixa: 57%; não é progresso real.')
    append(controls,progress)
    listing=list_new()
    hint(listing,'Lista de dados artificiais: selecione uma linha e percorra o conteúdo pelas barras.')
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
    hint(text,'Editor: selecione, copie ou edite a amostra.')
    text_scroll=scroll_new()
    scroll_overlay(text_scroll,0)
    scroll_child(text_scroll,text)
    text_tab=label("Text and scrolling")
    hint(text_tab,'Seleciona o editor nativo e suas barras de rolagem.')
    book_add(book,text_scroll,text_tab)
    append(outer,status)
    window_present(window)
    resources_verified=all(tooltip_get(widget).decode('utf-8')==text
                           for widget,text in hint_widgets)
    report_deadline=time.monotonic()+5.0
    report_state={'internal':None,'allocations':None}

    @C.CFUNCTYPE(I,P)
    def report_open_status(_data):
        now=time.monotonic()
        mapped=bool(widget_mapped(window))
        allocated=[widget_width(window),widget_height(window)]
        if (not mapped or min(allocated)<=0) and now<report_deadline:
            return 1
        try:
            if not resources_verified:
                raise RuntimeError('A GTK4 hint resource did not round-trip as UTF-8')
            if mapped and min(allocated)>0 and report_state['internal'] is None:
                # GtkWidget bounds are valid only after GTK has mapped and laid out
                # the native child tree. This also attaches the side popovers.
                report_state['internal']=internal_hints(window)
            if report_state['internal'] is None:
                report_state['internal']={'status':'not_measured','reason':'window allocation timed out'}
            if report_state['allocations'] is None:
                report_state['allocations']=[{'orientation':'horizontal' if orientation(w)==0 else 'vertical',
                    'width':widget_width(w),'height':widget_height(w),
                    'style_class_applied':bool(css_class_has(w,scrollbar_style_class.encode('ascii')))}
                    for w in styled_scrollbars] if scrollbar_style_class else []
            if (scrollbar_style_class and any(min(row['width'],row['height'])<=0
                    for row in report_state['allocations']) and now<report_deadline):
                report_state['allocations']=None
                return 1
            print(json.dumps({"status":"opened" if mapped and min(allocated)>0 else "allocation_timeout",
                              "toolkit":"GTK4 C ABI","version":".".join(map(str,version)),"pid":os.getpid(),"theme":theme,"font":font,"custom_css":bool(args.theme_lab_scrollbar_css),
                              "window":{"requested_px":list(window_size_px),"mapped":mapped,"allocated_px":allocated,
                                        "allocation_wait_timed_out":not mapped or min(allocated)<=0},
                              "display":display_name(widget_display(window)).decode(),
                              "hintCoverage":{"controls":len(hint_widgets),"utf8_resources_verified":resources_verified,
                                              "internal":report_state['internal'],
                                              "delayed_popovers":[{
                                                  'owner_type':type_name(item.owner).decode() if item.owner else None,
                                                  'owner_has_tooltip':bool(widget_has_tooltip(item.owner)) if item.owner else None,
                                                  'native_text_preserved':bool(tooltip_get(item.owner)) if item.owner else None,
                                                  'position':item.position_strategy,
                                              } for item in hint_popovers],
                                              "callback_errors":hint_retry_failures,
                                              "limits":"Current native child tree; later-created controls and hover not verified"},
                              "scrollbar_css_proof":{"provider_loaded":provider is not None,
                                  "parse_errors":scrollbar_css_errors,'style_class':scrollbar_style_class,
                                  'styled_count':len(styled_scrollbars),'allocations':report_state['allocations'],
                                  'css_selector_applied':bool(report_state['allocations']) and all(x['style_class_applied'] for x in report_state['allocations']),
                                  'scope':'CSS loaded on real GtkScrollbar children; input remains native; no image/pixel claim'}}),flush=True)
        except Exception as error:
            print(json.dumps({"status":"error","toolkit":"GTK4 C ABI","pid":os.getpid(),
                              "error":str(error)}),flush=True)
            app_quit(application)
        return 0

    open_status_callbacks.append(report_open_status)
    if not timeout_add(25,C.cast(report_open_status,P),None):
        raise RuntimeError('Could not schedule GTK4 mapped-window status report')
    for menu in (model,filemenu,section,options): unref(menu)

signal(application,"activate",activate)
def main():
    try:
        return app_run(application,0,None)
    finally:
        unref(application)

if __name__ == '__main__':
    raise SystemExit(main())
