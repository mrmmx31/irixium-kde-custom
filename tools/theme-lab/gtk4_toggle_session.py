# SPDX-License-Identifier: GPL-3.0-or-later
"""Private push/toggle session; no public routing or capability declaration.

Native selection belongs to this session/origin, never to the visual recipe.
Restoration precedes signal handlers; failed scene transfer retains the old
widgets and their selection. Hidden toggles retain their last accepted value.
"""
from pathlib import Path
from scene_contract import scene
from gtk2_buttons import geometry
from gtk4_push_session import PushScene, PushSession
from gtk4_buttons import write_button_css
from gtk4_toggles import write_toggle_css
from gtk4_checks import write_check_css


def button_records(model):
    records = [record for record in scene(model, 'gtk4')
               if record['id'] in ('push', 'toggle', 'check')]
    geometry(model['recipes']['gtk4'])
    if not records:
        raise ValueError('GTK4 button preview requires a visible push, toggle or check control')
    return records


class ToggleScene(PushScene):
    records_for = staticmethod(button_records)

    def __init__(self, *args, selection=None, **kwargs):
        self.selection = dict(selection or {})
        if any(type(k) is not int or k not in (1, 2) or type(v) is not bool
               for k, v in self.selection.items()):
            raise ValueError('GTK4 selection requires toggle/check index and boolean value')
        super().__init__(*args, **kwargs)

    def generate_receipt(self, builder, recipe, palette, folder):
        folder = Path(folder)
        base = write_button_css(builder, recipe, palette, folder / 'push')
        toggle = write_toggle_css(builder, recipe, palette, folder / 'toggle', base)
        check = write_check_css(builder, recipe, palette, folder / 'check')
        combined = folder / 'buttons.css'
        combined.write_text('@import url("' + toggle['css'] + '");\n@import url("' + check['css'] + '");\n',
                            encoding='utf-8')
        return dict(toggle, css=str(combined), push_style_class=base['style_class'],
                    check_style_class=check['style_class'], check_css=check['css'])

    def create_button(self, record):
        if record['id'] == 'push':
            return self.api.button_new(b'Pressione'), self.receipt['push_style_class']
        if record['id'] == 'check':
            widget = self.api.check_new(b'Marcado')
            self.api.check_set_active(widget, self.selection.get(record['index'], False))
            return widget, self.receipt['check_style_class']
        widget = self.api.toggle_new(b'Alternar')
        self.api.toggle_set_active(widget, self.selection.get(record['index'], False))
        return widget, self.receipt['style_class']

    def selected_values(self):
        return {index: bool(self.api.toggle_active(widget))
                for index, widget in self.widgets.items()
                if self.records[index]['id'] == 'toggle'} | {
            index: bool(self.api.check_active(widget))
            for index, widget in self.widgets.items()
            if self.records[index]['id'] == 'check'}


class ToggleSession(PushSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selection = {}

    def create_scene(self, model, palette, folder, prepared):
        current = dict(self.selection)
        if self.scene:
            current.update(self.scene.selected_values())
        return ToggleScene(self.api, self.builder, model, palette, folder,
                           self.on_click, prepared, self.on_layout,
                           selection=current)

    def replace(self, *args, **kwargs):
        # Commit retained values only after the inherited transfer succeeded.
        previous = dict(self.selection)
        if self.scene:
            previous.update(self.scene.selected_values())
        super().replace(*args, **kwargs)
        self.selection = previous
        self.selection.update(self.scene.selected_values())

    def close(self):
        super().close()
        self.selection.clear()
