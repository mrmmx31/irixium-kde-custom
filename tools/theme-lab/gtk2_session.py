# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK2 snapshot validation and transactional native scene replacement.

Callers must enforce the private namespace before initializing GTK. This module
does not install themes, modify projects or provide missing control renderers.
"""
import json
from pathlib import Path
import re
from native_scene_gtk2 import ScrollbarScene, scene_records
from gestures_gtk2 import LayoutGestures
from gtk2_canvas import canvas_sensitivity
from gtk2_sample_state import SampleState


def combo_popup_color(api, rc_file, model, receipt, allow_button_pressed=False):
    combo_records = [item for item in scene_records(
        model, allow_button_pressed=allow_button_pressed)
                     if item['id'] == 'combo']
    if not combo_records:
        return None
    state = combo_records[0]['forced_state']
    prefix = ('themeLabInsensitiveCombo' if state == 2 else
              'themeLabBackdropCombo' if state == 3 else 'themeLabCombo')
    from combo_popup_gtk2 import resolved_header_color
    return resolved_header_color(api.read_file(rc_file).decode('utf-8'), prefix,
                                 receipt['combo_style_id'])


def validate_snapshot(api, root, rc_file, model, allow_button_pressed=False):
    records = scene_records(model, allow_button_pressed=allow_button_pressed)  # Reject before changing GTK style.
    rc_file = Path(rc_file).absolute()
    folder = api.private_output(rc_file.parent.parent, root)
    receipt = json.loads(api.read_file(folder / 'GTK2-SCROLLBAR-PROPOSAL.json'))
    if receipt.get('family') != 'gtk2' or receipt.get('rc') != str(rc_file):
        raise ValueError('Origem GTK2 não corresponde ao RC solicitado.')
    rc_content = api.read_file(rc_file).decode('utf-8')
    scrollbar_records = [item for item in records if item['id'] in ('scroll_h', 'scroll_v')]
    if scrollbar_records:
        scroll_style_id = receipt.get('scrollbar_style_id')
        if not isinstance(scroll_style_id, str) or not re.fullmatch('[0-9a-f]{16}', scroll_style_id):
            raise ValueError('Identidade de estilo da barra GTK2 ausente ou inválida.')
        for name, binding in (
                ('theme-lab-gtk2-scroll-geometry-' + scroll_style_id,
                 'class "GtkScrollbar" style : highest "theme-lab-gtk2-scroll-paint-' + scroll_style_id + '"'),
                ('theme-lab-gtk2-scroll-paint-' + scroll_style_id,
                 'class "GtkScrollbar" style : highest "theme-lab-gtk2-scroll-paint-' + scroll_style_id + '"'),
                ('theme-lab-gtk2-scroll-insensitive-' + scroll_style_id,
                 'widget "*themeLabInsensitiveScroll" style : highest "theme-lab-gtk2-scroll-insensitive-' + scroll_style_id + '"'),
                ('theme-lab-gtk2-scroll-backdrop-' + scroll_style_id,
                 'widget "*themeLabBackdropScroll" style : highest "theme-lab-gtk2-scroll-backdrop-' + scroll_style_id + '"')):
            if 'style "' + name + '"' not in rc_content or binding not in rc_content:
                raise ValueError('Identidade de estilo da barra GTK2 não corresponde aos recursos.')
    translated = receipt.get('translated_controls', [])
    if not isinstance(translated, list) or any(item['id'] not in translated for item in records):
        raise ValueError('Snapshot GTK2 não contém todos os controles solicitados.')
    if any(item['id']=='progress' for item in records):
        style_id=receipt.get('progress_style_id')
        if not isinstance(style_id,str) or not re.fullmatch('[0-9a-f]{16}',style_id):
            raise ValueError('Identidade do estilo GTK2 de progresso ausente ou inválida.')
    if any(item['id']=='entry' for item in records):
        entry_style=receipt.get('entry_style_id')
        if not isinstance(entry_style,str) or not re.fullmatch('[0-9a-f]{16}',entry_style):
            raise ValueError('Identidade do estilo GTK2 de entrada ausente ou inválida.')
    if any(item['id']=='text' for item in records):
        text_style=receipt.get('text_style_id')
        if not isinstance(text_style,str) or not re.fullmatch('[0-9a-f]{16}',text_style):
            raise ValueError('Identidade do estilo GTK2 multilinha ausente ou inválida.')
    if any(item['id']=='combo' for item in records):
        combo_style=receipt.get('combo_style_id')
        if not isinstance(combo_style,str) or not re.fullmatch('[0-9a-f]{16}',combo_style):
            raise ValueError('Identidade do estilo GTK2 combobox ausente ou inválida.')
    if any(item['id']=='spin' for item in records):
        spin_style=receipt.get('spin_style_id')
        if not isinstance(spin_style,str) or not re.fullmatch('[0-9a-f]{16}',spin_style):
            raise ValueError('Identidade do estilo GTK2 spin ausente ou inválida.')
    if any(item['id'] in ('scale_h','scale_v') for item in records):
        scale_style=receipt.get('scale_style_id')
        if not isinstance(scale_style,str) or not re.fullmatch('[0-9a-f]{16}',scale_style):
            raise ValueError('Identidade do estilo GTK2 escala ausente ou inválida.')
    if any(item['id']=='arrow' for item in records):
        arrow_style=receipt.get('arrow_style_id')
        if not isinstance(arrow_style,str) or not re.fullmatch('[0-9a-f]{16}',arrow_style):
            raise ValueError('Identidade do estilo GTK2 seta isolada ausente ou inválida.')
    if any(item['id']=='list' for item in records):
        listing_style=receipt.get('list_style_id')
        if not isinstance(listing_style,str) or not re.fullmatch('[0-9a-f]{16}',listing_style):
            raise ValueError('Identidade do estilo GTK2 lista ausente ou inválida.')
    if any(item['id']=='frame' for item in records):
        frame_style=receipt.get('frame_style_id')
        if not isinstance(frame_style,str) or not re.fullmatch('[0-9a-f]{16}',frame_style):
            raise ValueError('Identidade do estilo GTK2 moldura ausente ou inválida.')
    recipe = model['recipes']['gtk2']
    for field in ('geometry', 'palette', 'scrollbar_parts'):
        if recipe.get(field, {}) != receipt.get('recipe', {}).get(field, {}):
            raise ValueError('Pintura GTK2 não corresponde à receita atual: ' + field)
    if not api.palette_inputs_current(receipt):
        raise ValueError('Papéis KDE mudaram; gere novamente a prévia GTK2.')
    if not api.generation_sources_current(receipt, root):
        raise ValueError('Código GTK2 mudou desde a geração; gere novamente a prévia.')
    if api.sha(api.read_file(rc_file)) != receipt.get('rc_sha256'):
        raise ValueError('RC GTK2 alterado após a geração.')
    if any(item['id']=='progress' for item in records):
        binding='widget "*themeLabProgress_'+style_id+'" style : highest "theme-lab-gtk2-progress-'+style_id+'"'
        if binding not in api.read_file(rc_file).decode('utf-8'):
            raise ValueError('Identidade de progresso não corresponde aos recursos GTK2.')
    if any(item['id']=='entry' for item in records):
        binding='widget \"*themeLabEntry_'+entry_style+'\" style : highest \"themeLabEntry-'+entry_style+'\"'
        if binding not in api.read_file(rc_file).decode('utf-8'):
            raise ValueError('Identidade de entrada não corresponde aos recursos GTK2.')
    if any(item['id']=='text' for item in records):
        binding='widget \"*themeLabTextEditor_'+text_style+'\" style : highest \"themeLabText-'+text_style+'\"'
        if binding not in api.read_file(rc_file).decode('utf-8'):
            raise ValueError('Identidade multilinha não corresponde aos recursos GTK2.')
    if any(item['id']=='combo' for item in records):
        binding='widget \"*themeLabCombo_'+combo_style+'\" style : highest \"themeLabCombo-'+combo_style+'\"'
        if binding not in api.read_file(rc_file).decode('utf-8'):
            raise ValueError('Identidade combobox não corresponde aos recursos GTK2.')
        content=api.read_file(rc_file).decode('utf-8')
        for prefix in ('themeLabCombo', 'themeLabBackdropCombo', 'themeLabInsensitiveCombo'):
            binding='widget \"*'+prefix+'PopupWindow_'+combo_style+'\" style : highest \"'+prefix+'-'+combo_style+'-popup-window\"'
            if binding not in content:
                raise ValueError('Identidade da janela popup do combobox não corresponde aos recursos GTK2.')
    if any(item['id']=='spin' for item in records):
        binding='widget "*themeLabSpin_'+spin_style+'" style : highest "themeLabSpin-'+spin_style+'"'
        if binding not in api.read_file(rc_file).decode('utf-8'):
            raise ValueError('Identidade spin não corresponde aos recursos GTK2.')
    if any(item['id'] in ('scale_h','scale_v') for item in records):
        binding='widget "*themeLabScale_'+scale_style+'" style : highest "themeLabScale-'+scale_style+'"'
        if binding not in api.read_file(rc_file).decode('utf-8'):
            raise ValueError('Identidade escala não corresponde aos recursos GTK2.')
    if any(item['id']=='arrow' for item in records):
        binding='widget "*themeLabArrow_'+arrow_style+'" style : highest "themeLabArrow-'+arrow_style+'"'
        if binding not in api.read_file(rc_file).decode('utf-8'):
            raise ValueError('Identidade seta isolada não corresponde aos recursos GTK2.')
    if any(item['id']=='list' for item in records):
        content=api.read_file(rc_file).decode('utf-8')
        for suffix,style_suffix in (('View',''),('Enclosure','-enclosure')):
            binding='widget "*themeLabList'+suffix+'_'+listing_style+'" style : highest "themeLabList-'+listing_style+style_suffix+'"'
            if binding not in content:
                raise ValueError('Identidade lista não corresponde aos recursos GTK2.')
    if any(item['id']=='frame' for item in records):
        content=api.read_file(rc_file).decode('utf-8')
        for suffix in ('','Content'):
            binding='widget "*themeLabFrame'+suffix+'_'+frame_style+'" style : highest "themeLabFrame-'+frame_style+'"'
            if binding not in content:
                raise ValueError('Identidade moldura não corresponde aos recursos GTK2.')
    assets = receipt.get('asset_sha256')
    if not isinstance(assets, dict) or set(assets) != set(receipt.get('assets', [])):
        raise ValueError('Manifesto de imagens GTK2 incompleto.')
    for name, expected in assets.items():
        if not isinstance(name, str) or Path(name).name != name or not name.endswith('.png'):
            raise ValueError('Nome de imagem GTK2 inválido.')
        if api.sha(api.read_file(rc_file.parent / name)) != expected:
            raise ValueError('Imagem GTK2 alterada após a geração: ' + name)
    engine = receipt.get('engine', {})
    if api.sha(api.read_file(Path(engine.get('path', '')), 16 * api.LIMIT)) != engine.get('sha256'):
        raise ValueError('Engine GTK2 mudou desde a geração.')
    return receipt


class NativeSession:
    @staticmethod
    def pressure_bridge(root, model):
        records = scene_records(model, allow_button_pressed=True)
        if any(record['forced_state'] == 1 for record in records):
            from gtk2_press_bridge import Gtk2PressBridge
            return Gtk2PressBridge(root)
        return None

    def __init__(self, api, Gtk, Gdk, root, rc_file, model, project_hash, writer,
                 embed_window=None, sample_directory=None, trace_input=False,
                 capture_mode=False, capture_probe=None):
        self.api, self.Gtk, self.Gdk, self.root = api, Gtk, Gdk, root
        self.writer, self.rc_file = writer, Path(rc_file)
        self.press_bridge = self.pressure_bridge(root, model)
        receipt=validate_snapshot(api, root, rc_file, model,
                                  allow_button_pressed=self.press_bridge is not None)
        popup_color = combo_popup_color(
            api, rc_file, model, receipt,
            allow_button_pressed=self.press_bridge is not None)
        self.check_hash(project_hash)
        self.samples = (SampleState(sample_directory,
                        'coupled' if embed_window is not None else 'separate')
                        if sample_directory is not None else None)
        if self.samples is not None:
            # Native GTK2 auto-selects Entry text on initial focus, replacing the
            # restored cursor/anchor. This setting belongs only to the private
            # preview process; user clicks can still select normally.
            Gtk.Settings.get_default().set_property('gtk-entry-select-on-focus', False)
        Gtk.rc_parse(str(rc_file))
        self.scene = ScrollbarScene(Gtk, model, embed_window, writer, project_hash, Gdk, progress_style_id=receipt.get('progress_style_id'), entry_style_id=receipt.get('entry_style_id'), text_style_id=receipt.get('text_style_id'), combo_style_id=receipt.get('combo_style_id'), combo_popup_color=popup_color, spin_style_id=receipt.get('spin_style_id'), scale_style_id=receipt.get('scale_style_id'), arrow_style_id=receipt.get('arrow_style_id'), list_style_id=receipt.get('list_style_id'), frame_style_id=receipt.get('frame_style_id'), text_histories=self.samples.histories if self.samples else None, press_bridge=self.press_bridge, trace_input=trace_input, capture_mode=capture_mode, capture_probe=capture_probe)

        if self.samples is not None:
            try:
                self.samples.restore_runtime(self.scene)
            except (OSError, ValueError, RuntimeError, TypeError):
                self.scene.gestures.close()
                self.scene.window.destroy()
                raise

    @staticmethod
    def check_hash(value):
        if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
            raise ValueError('Hash da proposta GTK2 inválido.')

    def replace(self, model, project_hash, rc_file=None):
        rc_file = Path(rc_file or self.rc_file)
        press_bridge = self.pressure_bridge(self.root, model)
        receipt=validate_snapshot(self.api, self.root, rc_file, model,
                                  allow_button_pressed=press_bridge is not None)
        popup_color = combo_popup_color(
            self.api, rc_file, model, receipt,
            allow_button_pressed=press_bridge is not None)
        self.check_hash(project_hash)
        self.checkpoint()  # Refuse destructive rebuild if the text is not protected.
        old = self.scene
        for editor in old.text_editors.values():
            editor.flush()
        list_states={index:listing.snapshot() for index,listing in old.list_controls.items()}
        self.Gtk.rc_parse(str(rc_file))
        candidate = None
        try:
            candidate = ScrollbarScene(self.Gtk, model, writer=self.writer,
                                       project_hash=project_hash, show=False, progress_style_id=receipt.get('progress_style_id'), entry_style_id=receipt.get('entry_style_id'), text_style_id=receipt.get('text_style_id'), combo_style_id=receipt.get('combo_style_id'), combo_popup_color=popup_color, spin_style_id=receipt.get('spin_style_id'), scale_style_id=receipt.get('scale_style_id'), arrow_style_id=receipt.get('arrow_style_id'), list_style_id=receipt.get('list_style_id'), frame_style_id=receipt.get('frame_style_id'),
                                       Gdk=self.Gdk, text_histories=old.text_histories,
                                       press_bridge=press_bridge)
            if self.samples is not None:
                self.samples.restore_runtime(candidate)
            staging_window = candidate.window
            # Candidate already bound widget handlers while staged. Disconnect
            # before rebinding to the retained window: otherwise the first
            # handler consumes Ctrl input and owns an inaccessible GTK grab.
            candidate.gestures.close()
            staging_window.remove(candidate.fixed)
            old.gestures.close()
            old.window.remove(old.fixed)
            old.window.add(candidate.fixed)
            canvas_sensitivity(old.window)
            candidate.window = old.window
            staging_window.destroy()
            candidate.gestures = LayoutGestures(candidate, self.Gdk)
            for index, widget in (candidate.widgets.items() if self.samples is None else ()):
                if index not in candidate.text_editors and index in old.widgets and hasattr(widget, 'get_adjustment'):
                    widget.get_adjustment().set_value(old.widgets[index].get_adjustment().get_value())
                elif index in (1,2) and index in old.widgets:
                    widget.set_active(old.widgets[index].get_active())
                elif index==5 and index in old.combo_widgets:
                    candidate.combo_widgets[index].set_active(old.combo_widgets[index].get_active())
                elif index==3 and index in old.radio_groups:
                    candidate.radio_groups[index].select(old.radio_groups[index].selected())
            candidate.window.show_all()
            candidate.restore_spin_fields()
            for index,listing in candidate.list_controls.items():
                if self.samples is None and index in list_states: listing.restore(list_states[index])
            self.scene, self.rc_file = candidate, rc_file
            self.press_bridge = press_bridge
            old.fixed.destroy()
        except (OSError, ValueError, RuntimeError, TypeError):
            self.Gtk.rc_parse(str(self.rc_file))
            if old.window.get_child() is not old.fixed:
                child = old.window.get_child()
                if child is not None: old.window.remove(child)
                old.window.add(old.fixed)
            canvas_sensitivity(old.window)
            if not old.gestures.handlers:
                old.gestures = LayoutGestures(old, self.Gdk)
            old.window.show_all()
            if candidate is not None and hasattr(candidate, 'gestures'):
                candidate.gestures.close()
            if candidate is not None and candidate.window is not old.window:
                candidate.window.destroy()
            elif candidate is not None:
                candidate.fixed.destroy()
            raise

    def checkpoint(self, capture=True):
        if self.samples is not None:
            return self.samples.checkpoint(self.scene, capture)
        return False

    def close(self):
        self.checkpoint()
        self.scene.gestures.close()
        self.scene.window.destroy()
