#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK4 C ABI push foundation. No installation or public adapter."""
import ctypes as C
import io,json,os,subprocess,sys,time
from pathlib import Path
from PIL import Image
if os.environ.get('T04_PRIVATE_GTK4_PUSH')!='1':raise SystemExit('Use private Gtk4 fixture')
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/theme-lab'))
from test_backend import backend,model
from gtk4_buttons import write_button_css


def bind(lib,name,result,*args):
    f=getattr(lib,name);f.restype=result;f.argtypes=list(args);return f


def main():
    output=Path(sys.argv[1]).resolve();output.mkdir(mode=0o700,parents=True)
    width,height=map(int,sys.argv[3].split('x')) if len(sys.argv)>3 else (160,60)
    assert 80<=width<=400 and 40<=height<=200
    gtk=C.CDLL('libgtk-4.so.1');obj=C.CDLL('libgobject-2.0.so.0');glib=C.CDLL('libglib-2.0.so.0');P=C.c_void_p;I=C.c_int;U=C.c_uint;S=C.c_char_p
    init=bind(gtk,'gtk_init',None);init()
    window_new=bind(gtk,'gtk_window_new',P);window_child=bind(gtk,'gtk_window_set_child',None,P,P)
    decorate=bind(gtk,'gtk_window_set_decorated',None,P,I);size=bind(gtk,'gtk_window_set_default_size',None,P,I,I)
    present=bind(gtk,'gtk_window_present',None,P);destroy=bind(gtk,'gtk_window_destroy',None,P)
    fixed_new=bind(gtk,'gtk_fixed_new',P);put=bind(gtk,'gtk_fixed_put',None,P,P,C.c_double,C.c_double)
    button_new=bind(gtk,'gtk_button_new_with_label',P,S);add_class=bind(gtk,'gtk_widget_add_css_class',None,P,S)
    request=bind(gtk,'gtk_widget_set_size_request',None,P,I,I);focus=bind(gtk,'gtk_widget_set_focusable',None,P,I)
    widget_width=bind(gtk,'gtk_widget_get_allocated_width',I,P);widget_height=bind(gtk,'gtk_widget_get_allocated_height',I,P)
    provider_new=bind(gtk,'gtk_css_provider_new',P);load=bind(gtk,'gtk_css_provider_load_from_path',None,P,S)
    add_provider=bind(gtk,'gtk_style_context_add_provider_for_display',None,P,P,U)
    display=bind(gtk,'gtk_widget_get_display',P,P);surface=bind(gtk,'gtk_native_get_surface',P,P)
    xid=bind(gtk,'gdk_x11_surface_get_xid',C.c_ulong,P)
    set_state=bind(gtk,'gtk_widget_set_state_flags',None,P,U,I);unset_state=bind(gtk,'gtk_widget_unset_state_flags',None,P,U)
    flags=bind(gtk,'gtk_widget_get_state_flags',U,P);sensitive=bind(gtk,'gtk_widget_set_sensitive',None,P,I)
    pending=bind(glib,'g_main_context_pending',I,P);iterate=bind(glib,'g_main_context_iteration',I,P,I)
    connect=bind(obj,'g_signal_connect_data',C.c_ulong,P,S,P,P,P,U)
    class Error(C.Structure):_fields_=[('domain',U),('code',I),('message',S)]
    errors=[];callback=C.CFUNCTYPE(None,P,P,P,P)(lambda _p,_s,error,_d:errors.append(C.cast(error,C.POINTER(Error)).contents.message.decode()))
    def drain():
        end=time.monotonic()+.25
        while time.monotonic()<end:
            while pending(None):iterate(None,0)
            time.sleep(.003)
    builder=backend.load_builder(ROOT);recipe=model()['recipes']['gtk4'];palette_source=Path(sys.argv[2]).resolve()
    palette,origin=backend.native_roles(ROOT,palette_source,builder.art,backend.sha(palette_source.read_bytes()))
    origin=dict(origin,selection_scope='Private GTK4 push recipe only; no host/profile scheme change')
    with backend.recipe_rules(builder,recipe['palette']):receipt=write_button_css(builder,recipe,palette,output/'generated')
    activations=[];click_callback=C.CFUNCTYPE(None,P,P)(lambda _b,_d:activations.append(True))
    provider=provider_new();connect(provider,b'parsing-error',C.cast(callback,P),None,None,0);load(provider,receipt['css'].encode());assert not errors,errors
    window=window_new();decorate(window,0);size(window,width+64,height+64);fixed=fixed_new();button=button_new(b'Pressione')
    connect(button,b'clicked',C.cast(click_callback,P),None,None,0);focus(button,0);request(button,width,height);add_class(button,receipt['style_class'].encode());put(fixed,button,32,32);window_child(window,fixed);add_provider(display(window),provider,800);present(window);drain()
    window_id=xid(surface(window));rows=[];host=None
    if '--embed-host-bin' in sys.argv:
        from gtk4_embed_fixture import MotifHost
        host=MotifHost(sys.argv[sys.argv.index('--embed-host-bin')+1],bind,'--focus' in sys.argv)
        import atexit
        atexit.register(host.close)
        library=sys.argv[sys.argv.index('--host-bridge-bin')+1] if '--host-bridge-bin' in sys.argv else None
        host.attach(window_id,library);drain()
    allocation=(widget_width(button),widget_height(button))
    assert allocation==(width,height), allocation
    for state,bit in [('normal',0),('pressed',1),('disabled',8),('backdrop',64)]:
        sensitive(button,state!='disabled');unset_state(button,1|64);set_state(button,bit,0);drain()
        raw=subprocess.check_output(['import','-window',hex(window_id),'png:-'],timeout=5);screen=Image.open(io.BytesIO(raw)).convert('RGB');screen.save(output/(state+'.png'));actual=screen.crop((32,32,32+width,32+height))
        effective=dict(palette);index=2 if state=='disabled' else 1 if state=='backdrop' else 0
        for role in ('button','button-fg'):effective[builder.art.ROLES[role][0]]=palette[builder.art.ROLES[role][index]]
        shadow=recipe['geometry']['shadow_px']
        with backend.recipe_rules(builder,recipe['palette']):expected=Image.open(io.BytesIO(builder.png(builder.art.bevel(builder.art.blank(width,height,'face'),thickness=shadow,down=state=='pressed'),'button',effective))).convert('RGB')
        edge=[(x,y) for y in range(height) for x in range(width) if x<shadow or y<shadow or x>=width-shadow or y>=height-shadow]
        delta=sum(actual.getpixel(p)!=expected.getpixel(p) for p in edge)
        rows.append({'state':state,'native_flags':flags(button),'edge_pixels':len(edge),'edge_differences':delta})
        (output/'PIXELS.json').write_text(json.dumps(rows,indent=2)+'\n');assert delta==0,rows[-1]
    assert not activations, 'Forced states must not activate the button'
    sensitive(button,1);unset_state(button,1|64);drain()
    physical=None
    if '--physical' in sys.argv:
        from PIL import ImageChops
        crop=(32,32,32+width,32+height)
        normal=Image.open(output/'normal.png').convert('RGB').crop(crop)
        before=Image.open(output/'pressed.png').convert('RGB').crop(crop)
        changed=sum(a!=b for a,b in zip(normal.getdata(),before.getdata()))
        assert changed>0, 'Pressure comparison must not be vacuous'
        try:
            subprocess.run(['xdotool','mousemove','--window',str(window_id),str(32+width//2),str(32+height//2),'mousedown','1'],check=True,timeout=5);drain()
            assert flags(button)&1
            raw=subprocess.check_output(['import','-window',hex(window_id),'png:-'],timeout=5);held=Image.open(io.BytesIO(raw)).convert('RGB');held.save(output/'physical-held.png')
            assert ImageChops.difference(before,held.crop(crop)).getbbox() is None
        finally:subprocess.run(['xdotool','mouseup','1'],check=True,timeout=5);drain()
        assert len(activations)==1
        assert not flags(button)&1
        raw=subprocess.check_output(['import','-window',hex(window_id),'png:-'],timeout=5);released=Image.open(io.BytesIO(raw)).convert('RGB');released.save(output/'physical-released.png')
        assert ImageChops.difference(normal,released.crop(crop)).getbbox() is None
        physical={'forced_equals_held':True,'released_equals_normal':True,'normal_pressed_changed_pixels':changed}
    embedded=host is not None
    host_proof=None
    session_proof=None
    if '--session' in sys.argv:
        from gtk4_session_fixture import verify_session
        session_proof=verify_session(window,window_id,builder,palette,output,drain,bind,gtk)
    focus_proof=None
    if '--focus' in sys.argv:
        from gtk4_focus_fixture import verify_focus
        focus_proof=verify_focus(window,window_id,host,builder,palette,output,drain)
    if host:
        assert host.parent(window_id)==host.canvas
    if host and host.bridge:
        # The separate resize experiment must not cover the Motif "after"
        # button before traversal: raw XResize changes server dimensions,
        # whereas the test RowColumn retains its original Xt geometry.
        resize_fixed=fixed_new();window_child(window,resize_fixed);drain()
        host.resize(host.display,host.canvas,420,280);host.sync(host.display,0)
        assert host.bridge.poll()==(420,280);drain()
        assert (widget_width(resize_fixed),widget_height(resize_fixed))==(420,280)
        host_proof={'canvas_resize':[420,280],'native_fixed_size':[420,280],
                    'guards':host.guard_proof}
        if '--destroy-canvas' in sys.argv:
            destroy_canvas=bind(host.xlib,'XDestroyWindow',I,P,C.c_ulong)
            destroy_canvas(host.display,host.canvas);host.sync(host.display,0)
            assert host.process.poll() is None
            assert host.bridge.poll() is None
            host_proof['canvas_loss_detected_while_process_live']=True
        host.process.terminate();host.process.wait(timeout=3)
        assert host.bridge.poll() is None
        host.bridge.close();host.bridge.close()
        host_proof.update(host_loss_detected=True,close_idempotent=True)
    if host_proof and host_proof.get('host_loss_detected'):
        from gtk4_push_api import PushAPI
        host_proof['cleanup_x11_error']=PushAPI().close_after_host_loss(window)
    else:destroy(window)
    drain()
    if host:host.close()
    (output/'RESULTADO.json').write_text(json.dumps({'status':'passed_scoped_foundation','rows':rows,'allocation':[width,height],'palette_origin':origin,'gtk4_native':True,'motif_embedded':embedded,'session_proof':session_proof,'host_proof':host_proof,'focus_proof':focus_proof,'public_adapter_enabled':False,'focus_excluded':True,'artificial_activations':0,'physical_clicks':len(activations),'physical_proof':physical,'historical_fidelity_claimed':False},indent=2)+'\n');print('GTK4 native push foundation passed')


if __name__=='__main__':main()
