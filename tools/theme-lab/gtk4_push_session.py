# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK4 push scene: staged CSS/widget replacement, persistent window.

Caller must establish a private display/profile before initializing GTK.
No installer, controller routing or public capability here. Layout gestures
are optional and use their own reversible transaction.
"""
import ctypes as C
from gtk4_buttons import write_button_css
from gtk4_scene_contract import push_records
from backend import recipe_rules
from gtk4_canvas import canvas_css
from pathlib import Path
from control_hints import CONTROL_HINTS


class PushScene:
    records_for = staticmethod(push_records)

    def create_button(self, record):
        return self.api.button_new(b'Pressione'), self.receipt['style_class']

    def generate_receipt(self, builder, recipe, palette, folder):
        return write_button_css(builder, recipe, palette, folder)

    def __init__(self, api, builder, model, palette, folder, on_click, prepared=None, on_layout=None):
        records = self.records_for(model)
        self.api = api
        self.fixed = self.provider = None
        self.handlers = []
        self.gestures = None
        self.focus_widget = None
        if prepared is not None:
            self.receipt = prepared
            self.canvas_class = prepared['canvas_class']
        else:
            self.canvas_class, canvas_source = canvas_css(builder.art, palette)
            recipe = model['recipes']['gtk4']
            with recipe_rules(builder, recipe['palette']):
                self.receipt = self.generate_receipt(builder, recipe, palette, folder)
            with Path(self.receipt['css']).open('a', encoding='utf-8') as css:
                css.write(canvas_source)
        self.widgets = {}
        self.records = {record['index']:record for record in records}
        self.native_requests = {}
        try:
            self.provider = api.css_provider(self.receipt['css'])
            self.fixed = api.ref_sink(api.fixed_new())
            api.add_class(self.fixed, self.canvas_class.encode())
            for record in records:
                button, style_class = self.create_button(record)
                api.tooltip(button, ('GTK4 nativo. ' + CONTROL_HINTS[record['id']]).encode('utf-8'))
                api.add_class(button, style_class.encode())
                api.put(self.fixed, button, record['x'], record['y'])
                state = record['forced_state']
                api.sensitive(button, state != 2)
                if state != 2:
                    self.focus_widget = button
                if state in (1, 3):
                    api.set_state(button, 1 if state == 1 else 64, 0)
                callback = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p)(
                    lambda _button, _data, index=record['index']: on_click(index))
                signal = b'toggled' if record['id'] == 'check' else b'clicked'
                handler = api.connect(button, signal, C.cast(callback, C.c_void_p),
                                       None, None, 0)
                self.handlers.append((button, handler, callback))
                self.widgets[record['index']] = button
            if on_layout is not None:
                from gtk4_gestures import LayoutGestures
                self.gestures = LayoutGestures(self, on_layout)
        except BaseException:
            self.close()
            raise

    def measure_and_size(self):
        # Rooted CSS/provider is active, but explicit requests have not yet
        # contaminated the toolkit's minimum/natural measurement.
        for index, widget in self.widgets.items():
            record = self.records[index]
            self.native_requests[index] = self.api.native_request(
                widget, check=record['id'] == 'check')
            self.api.request(widget, record['width'] or -1, record['height'] or -1)

    def close(self):
        if self.gestures:
            self.gestures.close()
            self.gestures = None
        for widget, handler, _callback in self.handlers:
            self.api.disconnect(widget, handler)
        self.handlers.clear()
        for attribute in ('fixed', 'provider'):
            pointer = getattr(self, attribute)
            if pointer:
                self.api.unref(pointer)
                setattr(self, attribute, None)
        self.widgets.clear()
        self.native_requests.clear()
        self.focus_widget = None


class PushSession:
    def __init__(self, api, window, builder, on_click, on_layout=None):
        self.api, self.window, self.builder = api, window, builder
        self.on_click = on_click
        self.on_layout = on_layout
        self.scene = None

    def create_scene(self, model, palette, folder, prepared):
        return PushScene(self.api, self.builder, model, palette, folder, self.on_click, prepared, self.on_layout)

    def replace(self, model, palette, folder, after_transfer=None, prepared=None):
        candidate = self.create_scene(model, palette, folder, prepared)
        old = self.scene
        display = self.api.display(self.window)
        registered = False
        try:
            self.api.add_provider(display, candidate.provider, 800)
            registered = True
            self.api.child(self.window, candidate.fixed)
            candidate.measure_and_size()
            self.api.focus(self.window, candidate.focus_widget)
            if after_transfer:
                after_transfer(candidate)
        except BaseException:
            self.api.child(self.window, old.fixed if old else None)
            self.api.focus(self.window, old.focus_widget if old else None)
            if registered:
                self.api.remove_provider(display, candidate.provider)
            candidate.close()
            raise
        self.scene = candidate
        if old:
            self.api.remove_provider(display, old.provider)
            old.close()

    def close(self):
        if self.scene:
            self.api.child(self.window, None)
            self.api.remove_provider(self.api.display(self.window), self.scene.provider)
            self.scene.close()
            self.scene = None
