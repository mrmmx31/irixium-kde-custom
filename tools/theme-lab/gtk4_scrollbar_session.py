# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK4 native scrollbar scene/session for separated and embedded views."""
import ctypes as C

from scene_contract import scene
from gtk2_buttons import geometry as button_geometry
from gtk4_hint_popover import DelayedPopoverHint


def scrollbar_records(model):
    records=[row for row in scene(model,'gtk4')
             if row['id'] in ('scroll_h','scroll_v')]
    if not records:
        raise ValueError('GTK4 scrollbar preview requires a visible scroll_h or scroll_v control')
    button_geometry(model['recipes']['gtk4'])
    return records


class ScrollbarScene:
    records_for=staticmethod(scrollbar_records)

    def __init__(self,api,window,builder,model,palette,folder,on_change,prepared=None,on_layout=None):
        records=self.records_for(model)
        self.api,self.window,self.builder=api,window,builder
        self.fixed=self.provider=None;self.handlers=[];self.adjustments={};self.gestures=None
        self.hints=[]
        self.widgets={};self.records={row['index']:row for row in records};self.native_requests={}
        if prepared is None:
            raise ValueError('GTK4 scrollbar scene requires a verified private snapshot')
        self.receipt=prepared
        self.canvas_class=prepared['canvas_class']
        try:
            self.provider=api.css_provider(self.receipt['css'])
            self.fixed=api.ref_sink(api.fixed_new())
            api.add_class(self.fixed,self.canvas_class.encode())
            for record in records:
                orientation=0 if record['id']=='scroll_h' else 1
                # GtkAdjustment may be floating; GtkScrollbar can sink that
                # reference when taking the property. Keep our own strong
                # reference so signal disconnect and teardown remain valid.
                adjustment=api.ref_sink(
                    api.adjustment_new(25.0,0.0,100.0,1.0,10.0,25.0))
                self.adjustments[record['index']]=adjustment
                widget=api.scrollbar_new(orientation,adjustment)
                api.add_class(widget,self.receipt['style_class'].encode())
                if record['forced_state']==1:
                    api.add_class(widget,b'theme-lab-forced-pressed')
                text=('Barra GTK4: arraste o cursor para mover o conteúdo. Valor efetivo 0–75, '
                      'passo 1, página visível 25, avanço de página 10; sem unidade. '
                      'GTK4 não desenha setas neste controle.')
                api.tooltip(widget,text.encode('utf-8'))
                if orientation==1:
                    self.hints.append(DelayedPopoverHint(
                        widget,self.fixed,record['x'],record['y'],
                        record['width'] or 15,record['height'] or 120,text))
                api.put(self.fixed,widget,record['x'],record['y'])
                api.sensitive(widget,record['forced_state']!=2)
                if record['forced_state']==3:api.set_state(widget,64,0)
                callback=C.CFUNCTYPE(None,C.c_void_p,C.c_void_p)(
                    lambda _adjustment,_data,index=record['index'],item=adjustment:
                        on_change(index,float(api.adjustment_value(item))))
                handler=api.connect(adjustment,b'value-changed',C.cast(callback,C.c_void_p),None,None,0)
                self.handlers.append((adjustment,handler,callback))
                self.widgets[record['index']]=widget
            if on_layout is not None:
                from gtk4_gestures import LayoutGestures
                self.gestures=LayoutGestures(self,on_layout)
        except BaseException:
            self.close();raise

    def measure_and_size(self):
        for index,widget in self.widgets.items():
            self.native_requests[index]=dict(
                self.api.native_request(widget,text_child=False),
                scrollbar_style_class=self.receipt['style_class'],
                scrollbar_style_class_present=bool(
                    self.api.has_class(widget,self.receipt['style_class'].encode())),
                forced_pressed_class_present=bool(
                    self.api.has_class(widget,b'theme-lab-forced-pressed')),
                sensitive=bool(self.api.is_sensitive(widget)),
                state_flags=int(self.api.state_flags(widget)),
                forced_state=self.records[index]['forced_state'])
            record=self.records[index]
            self.api.request(widget,record['width'] or -1,record['height'] or -1)

    def close(self):
        for hint in self.hints:
            hint.close()
        self.hints.clear()
        if self.gestures:
            self.gestures.close();self.gestures=None
        for widget,handler,_callback in self.handlers:self.api.disconnect(widget,handler)
        self.handlers.clear()
        for adjustment in self.adjustments.values():self.api.unref(adjustment)
        self.adjustments.clear()
        for attribute in ('fixed','provider'):
            value=getattr(self,attribute)
            if value:self.api.unref(value);setattr(self,attribute,None)
        self.widgets.clear();self.native_requests.clear();self.records.clear()


class ScrollbarSession:
    def __init__(self,api,window,builder,on_change,on_layout=None):
        self.api,self.window,self.builder=api,window,builder
        self.on_change,self.on_layout=on_change,on_layout
        self.scene=None

    def create_scene(self,model,palette,folder,prepared):
        return ScrollbarScene(self.api,self.window,self.builder,model,palette,folder,
                              self.on_change,prepared,self.on_layout)

    def values(self):
        if not self.scene:return {}
        return {index:float(self.api.adjustment_value(adjustment))
                for index,adjustment in self.scene.adjustments.items()}

    def replace(self,model,palette,folder,after_transfer=None,prepared=None):
        candidate=self.create_scene(model,palette,folder,prepared)
        old=self.scene;display=self.api.display(self.window);registered=False
        try:
            self.api.add_provider(display,candidate.provider,800);registered=True
            self.api.child(self.window,candidate.fixed)
            candidate.measure_and_size()
            self.api.queue_resize(self.window)
            self.api.queue_draw(candidate.fixed)
            for widget in candidate.widgets.values():
                self.api.queue_resize(widget)
                self.api.queue_draw(widget)
            self.api.queue_draw(self.window)
            if after_transfer:after_transfer(candidate)
        except BaseException:
            self.api.child(self.window,old.fixed if old else None)
            if registered:self.api.remove_provider(display,candidate.provider)
            candidate.close();raise
        self.scene=candidate
        if old:
            self.api.remove_provider(display,old.provider);old.close()

    def close(self):
        if self.scene:
            self.api.child(self.window,None)
            self.api.remove_provider(self.api.display(self.window),self.scene.provider)
            self.scene.close();self.scene=None
