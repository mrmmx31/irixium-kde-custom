# SPDX-License-Identifier: GPL-3.0-or-later
"""Real GTK4 toggle, physical press/release, private KDE-derived relief."""
import ctypes as C
import io,json,os,subprocess,sys,time
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools/theme-lab'),str(ROOT/'tools/theme-lab/tests')]
import backend
from test_backend import model
from gtk4_push_api import PushAPI,bind
from gtk4_buttons import write_button_css
from gtk4_toggles import write_toggle_css


def main():
    guards=backend.private_namespace(ROOT)
    home=Path(os.environ['HOME']);gtk=C.CDLL('libgtk-4.so.1');glib=C.CDLL('libglib-2.0.so.0')
    p,i,u=C.c_void_p,C.c_int,C.c_uint
    bind(gtk,'gtk_init',None)();api=PushAPI();builder=backend.load_builder(ROOT)
    recipe=model()['recipes']['gtk4'];source=home/'.config/kdeglobals'
    palette,origin=backend.native_roles(ROOT,source,builder.art,backend.sha(source.read_bytes()))
    with backend.recipe_rules(builder,recipe['palette']):
        base=write_button_css(builder,recipe,palette,home/'toggle-base')
        receipt=write_toggle_css(builder,recipe,palette,home/'toggle-assets',base)
    provider=api.css_provider(receipt['css']);window=bind(gtk,'gtk_window_new',p)()
    bind(gtk,'gtk_window_set_decorated',None,p,i)(window,0)
    bind(gtk,'gtk_window_set_default_size',None,p,i,i)(window,320,180)
    fixed=api.fixed_new();button=bind(gtk,'gtk_toggle_button_new_with_label',p,C.c_char_p)(b'Alternar')
    active=bind(gtk,'gtk_toggle_button_get_active',i,p)
    set_active=bind(gtk,'gtk_toggle_button_set_active',None,p,i)
    unset=bind(gtk,'gtk_widget_unset_state_flags',None,p,u)
    flags=bind(gtk,'gtk_widget_get_state_flags',u,p)
    api.add_class(button,receipt['style_class'].encode());api.request(button,180,50)
    bind(gtk,'gtk_widget_set_focusable',None,p,i)(button,0)
    api.put(fixed,button,32,32);api.child(window,fixed)
    clicks=[];changes=[]
    click_callback=C.CFUNCTYPE(None,p,p)(lambda *_args:clicks.append(bool(active(button))))
    toggle_callback=C.CFUNCTYPE(None,p,p)(lambda *_args:changes.append(bool(active(button))))
    api.connect(button,b'clicked',C.cast(click_callback,p),None,None,0)
    api.connect(button,b'toggled',C.cast(toggle_callback,p),None,None,0)
    api.add_provider(api.display(window),provider,800)
    bind(gtk,'gtk_window_present',None,p)(window)
    pending=bind(glib,'g_main_context_pending',i,p);iterate=bind(glib,'g_main_context_iteration',i,p,i)
    def drain():
        end=time.monotonic()+.12
        while time.monotonic()<end:
            while pending(None):iterate(None,0)
            time.sleep(.003)
    drain();wid=bind(gtk,'gdk_x11_surface_get_xid',C.c_ulong,p)(bind(gtk,'gtk_native_get_surface',p,p)(window))
    def pointer(*arguments):
        subprocess.run(['xdotool',*map(str,arguments)],check=True,timeout=5);drain()
    rows=[]
    def capture(label,down,index=0):
        drain();path=home/(label+'.png')
        subprocess.run(['import','-window',str(wid),str(path)],check=True,timeout=5)
        actual=Image.open(path).convert('RGB').crop((32,32,212,82));effective=dict(palette)
        for role in ('button','button-fg'):
            effective[builder.art.ROLES[role][0]]=palette[builder.art.ROLES[role][index]]
        shadow=recipe['geometry']['shadow_px']
        with backend.recipe_rules(builder,recipe['palette']):
            symbolic=builder.art.bevel(builder.art.blank(180,50,'face'),thickness=shadow,down=down)
            expected=Image.open(io.BytesIO(builder.png(symbolic,'button',effective))).convert('RGB')
        edges=[(x,y) for y in range(50) for x in range(180) if x<shadow or y<shadow or x>=180-shadow or y>=50-shadow]
        differences=sum(actual.getpixel(v)!=expected.getpixel(v) for v in edges)
        rows.append({'label':label,'selected':bool(active(button)),'native_flags':flags(button),
                     'edge_pixels':len(edges),'differences':differences,'capture':str(path)})
        backend.write_json(home/'TOGGLE-PIXELS.json',rows);assert differences==0,rows[-1]
    try:
        pointer('mousemove','--window',wid,260,120);capture('normal',False)
        pointer('mousemove','--window',wid,80,50);capture('hover',False)
        pointer('mousedown',1);assert not active(button) and not clicks;capture('pressed',True)
        pointer('mouseup',1);assert active(button) and len(clicks)==1;capture('selected-hover',True)
        pointer('mousemove','--window',wid,260,120);capture('selected',True)
        pointer('mousemove','--window',wid,80,50,'mousedown',1)
        assert active(button) and len(clicks)==1;capture('selected-pressed',False)
        pointer('mouseup',1);assert not active(button) and len(clicks)==2;capture('released-unselected',False)
        set_active(button,1);api.sensitive(button,0);drain();capture('disabled-selected',True,2)
        pointer('click',1);assert active(button) and len(clicks)==2
        set_active(button,0);drain();capture('disabled-unselected',False,2)
        api.sensitive(button,1);pointer('mousemove','--window',wid,260,120)
        unset(button,1|64);api.set_state(button,64,0);drain();capture('backdrop-unselected',False,1)
        set_active(button,1);drain();capture('backdrop-selected',True,1)
        assert len(clicks)==2
        backend.write_json(home/'WORKER-RESULTADO.json',{'status':'passed_toggle_foundation',
            'toolkit':'GTK4','fixture_scheme':os.environ.get('T04_FIXTURE_SCHEME','DomainOS-SR10.4'),
            'guards':guards,'captures':rows,'physical_clicks':len(clicks),'toggle_changes':changes,
            'source_palette':origin,'selected_disabled_retained':True,'disabled_click_ignored':True,
            'prospective_selected_press':True,'public_support_announced':False,
            'historical_fidelity_claimed':False})
    finally:
        subprocess.run(['xdotool','mouseup','1'],check=False,timeout=5)
        api.destroy_window(window);api.unref(provider)


if __name__=='__main__':main()
