#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK3 Theme Lab scene, embedded with XEmbed or in a private window.

Ctrl+click selects a control; Ctrl+drag proposes its position through private
JSON events. Ordinary input remains native widget input. Forced editor states
are demonstrations, not evidence of historical DomainOS behaviour.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import uuid

sys.dont_write_bytecode = True
SOURCE = Path(__file__).resolve().parent
event_spec = importlib.util.spec_from_file_location('theme_lab_event_writer', SOURCE / 'preview_event_writer.py')
event_module = importlib.util.module_from_spec(event_spec)
event_spec.loader.exec_module(event_module)
layout_spec = importlib.util.spec_from_file_location('theme_lab_scene_contract', SOURCE / 'scene_contract.py')
layout_module = importlib.util.module_from_spec(layout_spec)
layout_spec.loader.exec_module(layout_module)
spec = importlib.util.spec_from_file_location('theme_lab_preview_backend', SOURCE / 'backend.py')
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)
sample_spec = importlib.util.spec_from_file_location('theme_lab_samples', SOURCE / 'sample_contract.py')
sample_module = importlib.util.module_from_spec(sample_spec)
sample_spec.loader.exec_module(sample_module)
SAMPLES = sample_module.SAMPLES
hint_spec = importlib.util.spec_from_file_location('theme_lab_control_hints', SOURCE / 'control_hints.py')
hint_module = importlib.util.module_from_spec(hint_spec)
hint_spec.loader.exec_module(hint_module)
parts_spec = importlib.util.spec_from_file_location('theme_lab_native_parts', SOURCE / 'native_parts_gtk.py')
parts_module = importlib.util.module_from_spec(parts_spec)
parts_spec.loader.exec_module(parts_module)
editing_spec = importlib.util.spec_from_file_location('theme_lab_preview_text_editing', SOURCE / 'preview_text_editing.py')
editing_module = importlib.util.module_from_spec(editing_spec)
editing_spec.loader.exec_module(editing_module)
CONTROLS = backend.CONTROLS
CATEGORIES = (0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 4)
EDIT_STATES = ('normal', 'pressed', 'disabled', 'backdrop')


def integer(value, minimum, maximum, field):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{field}: inteiro entre {minimum} e {maximum} esperado.')
    return value


def scene(model, family='gtk3'):
    if family != 'gtk3':
        raise ValueError('Esta montagem contém controles GTK3 reais; outros adaptadores estão pendentes.')
    return layout_module.scene(model, family)


anchor_spec = importlib.util.spec_from_file_location('theme_lab_scene_anchor', SOURCE / 'scene_anchor.py')
anchor_module = importlib.util.module_from_spec(anchor_spec)
anchor_spec.loader.exec_module(anchor_module)
anchor_origin = anchor_module.anchor_origin


def drag_position(origin, delta_x, delta_y):
    if (not isinstance(origin, (tuple, list)) or len(origin) != 2 or
            any(type(value) is not int or not 0 <= value <= 2048 for value in origin) or
            any(type(value) not in (int, float) or not math.isfinite(value)
                for value in (delta_x, delta_y))):
        raise ValueError('Origem e deslocamento de arraste inválidos.')
    return tuple(max(0, min(2048, round(value + delta)))
                 for value, delta in zip(origin, (delta_x, delta_y)))


def root_coordinates(value):
    """Normalize GDK's (success, x, y) out parameters without importing GI."""
    if not isinstance(value, (tuple, list)):
        return None
    if len(value) == 3:
        if value[0] is not True:
            return None
        value = value[1:]
    if len(value) != 2 or any(type(item) not in (int, float) or not math.isfinite(item)
                              for item in value):
        return None
    return tuple(value)


def event_root_position(event):
    """The public getter handles mouse and touch; no union-field guessing."""
    try:
        return root_coordinates(event.get_root_coords()) if event is not None else None
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return None


def root_drag_position(origin, start, current):
    """Stable logical-coordinate delta, independent of the moving widget."""
    start, current = root_coordinates(start), root_coordinates(current)
    if start is None or current is None:
        raise ValueError('Coordenadas estáveis do arraste indisponíveis.')
    # GDK X11 already divides event root coordinates by the window scale,
    # for both core mouse and XI2 mouse/touch events. Do not divide twice.
    return drag_position(origin, current[0] - start[0], current[1] - start[1])


def modifier_value(state):
    """GDK introspection can return its out parameter as (success, mask)."""
    if isinstance(state, tuple):
        if len(state) != 2 or not state[0]:
            return 0
        state = state[1]
    try:
        return int(state)
    except (TypeError, ValueError):
        return 0


class EventWriter(event_module.EventWriter):
    def __init__(self, directory, root, instance_id=None):
        super().__init__(directory, root, backend_api=backend, instance_id=instance_id)


def theme_environment(directory):
    if directory is None:
        return
    directory = directory.absolute()
    if '..' in directory.parts or any(item.is_symlink() for item in (directory, *directory.parents)):
        raise ValueError('O tema privado não pode atravessar links ou ..')
    tempia_root = Path.home() / 'tempia'
    namespace_home = Path('/home/domainos-test')
    in_tempia = directory.is_relative_to(tempia_root) and directory != tempia_root
    in_namespace = (os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') == 'bwrap' and
                    directory.is_relative_to(namespace_home) and directory != namespace_home)
    if (not directory.is_dir() or directory.stat().st_uid != os.getuid() or
            not (in_tempia or in_namespace)):
        raise ValueError('Use uma pasta de tema privada em ~/tempia ou no HOME do namespace.')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', directory.name):
        raise ValueError('Nome de tema GTK privado inválido.')
    backend.read_file(directory / 'gtk-3.0/gtk.css')
    os.environ['GTK_THEME'] = directory.name
    os.environ['GTK_OVERLAY_SCROLLING'] = '0'
    os.environ['XDG_DATA_DIRS'] = str(directory.parents[1]) + ':' + os.environ.get(
        'XDG_DATA_DIRS', '/usr/local/share:/usr/share')


class NativeScene:
    def __init__(self, Gtk, Gdk, GLib, args, model, project_hash, writer):
        self.Gtk, self.Gdk, self.GLib = Gtk, Gdk, GLib
        self.args, self.project_hash, self.writer = args, project_hash, writer
        self.parts_reader = parts_module.Reader(Gtk)
        self.widgets, self.gestures, self.dragging = {}, [], {}
        self.text_histories = {}
        self.boxes, self.records = {}, {}
        self.anchor_pending = {}
        self.last_metrics = {}
        self.gesture_handlers = []
        self.destroyed, self.last_error = False, None
        self.capture_mode = args.capture_control is not None
        if self.capture_mode:
            self.window = Gtk.OffscreenWindow()
        elif args.embed_window is not None:
            self.window = Gtk.Plug.new(args.embed_window)
        else:
            self.window = Gtk.Window(title='Theme Lab — GTK3 nativo privado')
            self.window.set_default_size(760, 450)
        self.window.connect('destroy', self.close)
        self.window.connect('map', self.queue_window_measurements)
        if self.capture_mode:
            self.fixed = Gtk.Fixed()
            self.window.add(self.fixed)
            self.status = Gtk.Label()
            self.build(model)
            self.window.show_all()
            return
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.window.add(outer)
        self.status = Gtk.Label(label='Ctrl+clique seleciona; Ctrl+arraste move. Estado forçado é uma demonstração.')
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)
        outer.pack_start(self.status, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        outer.pack_start(scroll, True, True, 0)
        self.fixed = Gtk.Fixed()
        scroll.add_with_viewport(self.fixed)
        self.build(model)
        self.window.show_all()
        self.restore_spin_fields()
        self.reload_source = GLib.timeout_add(500, self.reload)

    def close(self, *_):
        self.destroyed = True
        self.release_anchor_updates()
        self.release_gestures()
        if hasattr(self, 'reload_source'):
            self.GLib.source_remove(self.reload_source)
        if self.Gtk.main_level():
            self.Gtk.main_quit()

    def release_gestures(self):
        for gesture, handler in self.gesture_handlers:
            if gesture.handler_is_connected(handler):
                gesture.disconnect(handler)
        self.gesture_handlers, self.gestures, self.dragging = [], [], {}

    def emit(self, action, index, **fields):
        try:
            self.writer.emit(action, index, self.project_hash, **fields)
        except (OSError, ValueError) as error:
            self.status.set_text('Evento não salvo: ' + str(error))

    def changed(self, index, **state):
        self.status.set_text(f'{CONTROLS[index]}: interação nativa; Ctrl+arraste altera o layout.')
        self.emit('native', index, state=state)

    def release_anchor_updates(self):
        for source in self.anchor_pending.values():
            self.GLib.source_remove(source)
        self.anchor_pending.clear()

    def settle_anchor(self, widget, index):
        self.anchor_pending.pop(index, None)
        if self.destroyed or self.widgets.get(index) is not widget or index in self.dragging:
            return False
        box, record = self.boxes[index], self.records[index]
        offset = widget.translate_coordinates(box, 0, 0)
        if offset is None:
            self.status.set_text('Ancoragem pendente: controle ainda não disposto pelo GTK.')
            return False
        try:
            origin = anchor_origin(record, widget.get_allocated_width(),
                                   widget.get_allocated_height(), offset)
            current = (self.fixed.child_get_property(box, 'x'),
                       self.fixed.child_get_property(box, 'y'))
            if current != origin:
                self.fixed.move(box, *origin)
        except ValueError as error:
            box.set_no_show_all(True)
            box.hide()
            self.status.set_text(str(error))
        return False

    def settle_measurement(self, widget, index):
        self.anchor_pending.pop(index, None)
        if not self.destroyed and self.widgets.get(index) is widget:
            if widget.translate_coordinates(self.boxes[index], 0, 0) is not None:
                self.measured(widget, widget.get_allocation(), index)
        return False

    def queue_window_measurements(self, *_):
        # Mapping/allocation of descendants can finish after their individual
        # notifications. One bounded refresh also covers a rebuilt live scene.
        previous=self.anchor_pending.pop(-1,None)
        if previous is not None:
            self.GLib.source_remove(previous)
        self.anchor_pending[-1]=self.GLib.timeout_add(50,self.settle_window_measurements)

    def settle_window_measurements(self):
        self.anchor_pending.pop(-1,None)
        if not self.destroyed:
            for index,widget in tuple(self.widgets.items()):
                self.measured(widget,widget.get_allocation(),index)
        return False

    def measured(self, widget, allocation, index):
        # Destroyed controls and old-scene callbacks must not describe the
        # current project. GTK reports allocations in logical pixels.
        if (self.destroyed or self.widgets.get(index) is not widget or
                allocation.width < 1 or allocation.height < 1):
            return
        record=self.records.get(index)
        box=self.boxes.get(index)
        offset=widget.translate_coordinates(box,0,0) if box is not None else None
        if offset is None:
            if index not in self.anchor_pending:
                self.anchor_pending[index]=self.GLib.idle_add(self.settle_measurement,widget,index)
        if offset is not None and record is not None and box is not None and record.get('length_anchor'):
            # Parent allocation/realization may still be in progress. One
            # bounded idle update uses the actual widget-to-cell offset.
            if index not in self.anchor_pending:
                self.anchor_pending[index] = self.GLib.idle_add(self.settle_anchor, widget, index)
        minimum_width, natural_width = widget.get_preferred_width()
        minimum_height, natural_height = widget.get_preferred_height()
        fields = dict(width=allocation.width, height=allocation.height,
                      minimum_width=minimum_width, minimum_height=minimum_height,
                      natural_width=natural_width, natural_height=natural_height,
                      scale_factor=widget.get_scale_factor(),
                      coordinate_space='gtk_logical_px',
                      sensitive=bool(widget.is_sensitive()),
                      origin='coupled' if self.args.embed_window is not None else 'separate')
        # A scrollbar/arrow has no text of its own. For text controls this
        # identifies the loaded context font, not all per-glyph fallbacks.
        if index in (10, 11, 12):
            fields.update(font_kind=2, font_description='')
        else:
            target=widget
            if index in (0,1,2,3,7):
                target=widget.get_child() or widget
            elif index==14:
                listing=widget.get_child()
                # GtkScrolledWindow may insert a GtkViewport for ListBox.
                if isinstance(listing, self.Gtk.Viewport):listing=listing.get_child()
                row=listing.get_row_at_index(0)
                if row is not None:target=row.get_child()
            elif index==15:
                target=widget.get_child() or widget
            context=target.get_pango_context()
            font=context.load_font(context.get_font_description())
            if font is not None:
                description='Pango contexto de '+target.__class__.__name__+' carregado: '+font.describe().to_string()
                if len(description.encode('utf-8'))<384:
                    fields.update(font_kind=1,font_description=description)
        if offset is not None:
            fields.update(cell_offset_x=offset[0],cell_offset_y=offset[1])
        position=widget.translate_coordinates(self.fixed,0,0)
        if position is not None:
            fields.update(position_x=position[0],position_y=position[1])
        if index in (10,11):
            area=widget.get_range_rect()
            start,end=widget.get_slider_range()
            if area.width>0 and area.height>0 and end>start:
                fields['range_geometry']={'axis':0 if index==10 else 1,
                    'slider_start':start,'slider_end':end,'area_x':area.x,'area_y':area.y,
                    'area_width':area.width,'area_height':area.height,
                    'coordinate_space':'gtk_widget_window_px'}
            pieces=self.parts_reader.measure(widget)
            if pieces is not None:fields['pieces_geometry']=pieces
        signature = (self.project_hash, json.dumps(fields,sort_keys=True,ensure_ascii=False))
        if self.last_metrics.get(index) != signature:
            self.emit('metrics', index, **fields)
            self.last_metrics[index] = signature

    def bind_text_editor(self, widget, index):
        editor = editing_module.bind(widget, self.Gtk, self.Gdk, self.GLib,
                                     self.text_histories.get(index))
        self.text_histories[index] = editor.history

    def factory(self, identifier, index):
        Gtk = self.Gtk
        if identifier == 'push':
            widget = Gtk.Button(label=SAMPLES['push'])
            widget.connect('clicked', lambda *_: self.changed(index, clicked=True))
        elif identifier == 'toggle':
            widget = Gtk.ToggleButton(label=SAMPLES['toggle'])
            widget.connect('toggled', lambda w: self.changed(index, active=w.get_active()))
        elif identifier == 'check':
            widget = Gtk.CheckButton(label=SAMPLES['check'])
            widget.set_active(True)
            widget.connect('toggled', lambda w: self.changed(index, active=w.get_active()))
        elif identifier == 'radio':
            widget = Gtk.RadioButton.new_with_label_from_widget(None, SAMPLES['radio'])
            widget.set_active(True)
            widget.connect('toggled', lambda w: self.changed(index, active=w.get_active()))
        elif identifier == 'entry':
            widget = Gtk.Entry()
            widget.set_text(SAMPLES['entry'])
            self.bind_text_editor(widget, index)
            widget.connect('changed', lambda w: self.changed(index, text_length=w.get_text_length()))
        elif identifier == 'combo':
            widget = Gtk.ComboBoxText()
            for item in (SAMPLES['combo_a'], SAMPLES['combo_b'], SAMPLES['combo_c']):
                widget.append_text(item)
            widget.set_active(0)
            widget.connect('changed', lambda w: self.changed(index, active_index=w.get_active()))
        elif identifier == 'spin':
            widget = Gtk.SpinButton.new_with_range(0, 100, 1)
            widget.set_value(SAMPLES['spin'])
            self.bind_text_editor(widget, index)
            widget.connect('value-changed', lambda w: self.changed(index, value=w.get_value()))
        elif identifier == 'text':
            widget = Gtk.ScrolledWindow()
            widget.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            text = Gtk.TextView()
            text.get_buffer().set_text(SAMPLES['text'])
            self.bind_text_editor(text, index)
            text.get_buffer().connect('changed', lambda b: self.changed(index, text_length=b.get_char_count()))
            widget.add(text)
        elif identifier in ('scale_h', 'scale_v', 'scroll_h', 'scroll_v'):
            orientation = Gtk.Orientation.HORIZONTAL if identifier.endswith('_h') else Gtk.Orientation.VERTICAL
            if identifier.startswith('scale'):
                widget = Gtk.Scale.new_with_range(orientation, 0, 100, 1)
                widget.set_value(SAMPLES['scale_h' if identifier.endswith('_h') else 'scale_v'])
                widget.connect('value-changed', lambda w: self.changed(index, value=w.get_value()))
            else:
                adjustment = Gtk.Adjustment(value=SAMPLES['scroll'], lower=0, upper=100, step_increment=1,
                                            page_increment=10, page_size=SAMPLES['page_size'])
                widget = Gtk.Scrollbar(orientation=orientation, adjustment=adjustment)
                adjustment.connect('value-changed', lambda a: self.changed(index, value=a.get_value()))
                adjustment.connect('value-changed', self.queue_window_measurements)
        elif identifier == 'arrow':
            widget = Gtk.Button()
            widget.get_style_context().add_class('theme-lab-arrow')
            widget.connect('clicked', lambda *_: self.changed(index, clicked=True))
        elif identifier == 'progress':
            widget = Gtk.ProgressBar()
            widget.set_fraction(SAMPLES['level'] / 100)
            widget.set_show_text(True)
        elif identifier == 'list':
            widget = Gtk.ScrolledWindow()
            widget.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            listing = Gtk.ListBox()
            listing.set_selection_mode(Gtk.SelectionMode.SINGLE)
            for key in ('list_a', 'list_b', 'list_c'):
                listing.add(Gtk.Label(label=SAMPLES[key], xalign=0))
            listing.select_row(listing.get_row_at_index(1))
            listing.connect('row-selected', lambda _, row:
                            self.changed(index, row=row.get_index() if row else None))
            widget.add(listing)
        elif identifier == 'frame':
            # XmFrame reference contains one content label, no title label.
            widget = Gtk.Frame()
            widget.add(Gtk.Label(label=SAMPLES['frame']))
        else:
            raise ValueError('Controle não implementado: ' + identifier)
        hint_module.bind_control_hint(widget, identifier, 'gtk3')
        return widget

    def force_state(self, widget, state):
        Gtk = self.Gtk
        if state == 0:
            return
        flag = (Gtk.StateFlags.ACTIVE if state == 1 else
                Gtk.StateFlags.INSENSITIVE if state == 2 else Gtk.StateFlags.BACKDROP)
        if state == 2:
            widget.set_sensitive(False)
        widget.set_state_flags(flag, False)
        def maintain(w, _previous):
            if not w.get_state_flags() & flag:
                w.set_state_flags(flag, False)
        widget.connect('state-flags-changed', maintain)
        if isinstance(widget, Gtk.Container):
            for child in widget.get_children():
                self.force_state(child, state)

    def control_capture(self, box, record):
        Gtk, Gdk = self.Gtk, self.Gdk
        index = record['index']
        select = Gtk.GestureMultiPress.new(box)
        drag = Gtk.GestureDrag.new(box)
        for gesture in (select, drag):
            gesture.set_button(1)
            gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        select.group(drag)
        def modifier(gesture):
            event = gesture.get_last_event(gesture.get_current_sequence())
            return bool(event and modifier_value(event.get_state()) & int(Gdk.ModifierType.CONTROL_MASK))
        def selected(gesture, _count, _x, _y):
            if not modifier(gesture):
                gesture.set_state(Gtk.EventSequenceState.DENIED)
                return
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)
            self.emit('select', index)
            self.status.set_text(f'Seleção proposta: {record["id"]}; arraste com Ctrl para mover.')
        def begin(gesture, _x, _y):
            if not modifier(gesture):
                gesture.set_state(Gtk.EventSequenceState.DENIED)
                return
            event = gesture.get_last_event(gesture.get_current_sequence())
            pointer = event_root_position(event)
            if pointer is None:
                gesture.set_state(Gtk.EventSequenceState.DENIED)
                self.status.set_text('Arraste não iniciado: evento sem coordenadas da tela.')
                return
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)
            self.dragging[index] = {'origin': (record['x'], record['y']), 'pointer': pointer,
                                    'scale': box.get_scale_factor()}
        def destination(gesture, active):
            if box.get_scale_factor() != active['scale']:
                return None  # A monitor/scale change invalidates the starting coordinate unit.
            event = gesture.get_last_event(gesture.get_current_sequence())
            pointer = event_root_position(event)
            return root_drag_position(active['origin'], active['pointer'], pointer) if pointer is not None else None
        def place_boundary(point):
            if not record.get('length_anchor'):
                self.fixed.move(box,*point);return
            control=self.widgets[index]
            proposal=dict(record,x=point[0],y=point[1])
            offset=control.translate_coordinates(box,0,0)
            if offset is None:
                raise ValueError('Arraste indisponível: controle ainda não disposto pelo GTK.')
            origin=anchor_origin(proposal,control.get_allocated_width(),control.get_allocated_height(),
                                 offset)
            self.fixed.move(box,*origin)
        def cancelled(_gesture, _sequence):
            active = self.dragging.pop(index, None)
            if active is not None:
                try:
                    place_boundary(active['origin'])
                except ValueError as error:
                    self.status.set_text(str(error))
        def update(gesture, _x, _y):
            active = self.dragging.get(index)
            if active is None:
                return
            proposed = destination(gesture, active)
            if proposed is None:
                cancelled(gesture, None)
                gesture.set_state(Gtk.EventSequenceState.DENIED)
                self.status.set_text('Arraste cancelado: coordenadas ou escala da tela mudaram.')
                return
            try:
                place_boundary(proposed)
            except ValueError as error:
                self.status.set_text(str(error));return
        def end(gesture, _x, _y):
            active = self.dragging.pop(index, None)
            if active is None:
                return
            proposed = destination(gesture, active)
            if proposed is None:
                cancelled_origin=active['origin']
                try:
                    place_boundary(cancelled_origin)
                    self.status.set_text('Arraste cancelado: coordenadas ou escala da tela mudaram.')
                except ValueError as error:
                    self.status.set_text(str(error))
                return
            try:
                place_boundary(proposed)
            except ValueError as error:
                # An invalid final boundary must not leave a previous valid
                # intermediate drag painted without a corresponding event.
                try:
                    place_boundary(active['origin'])
                except ValueError:
                    pass
                self.status.set_text(str(error));return
            record['x'], record['y'] = proposed
            if proposed != active['origin']:
                self.emit('move', index, x=proposed[0], y=proposed[1],
                          coordinate_space='gtk_logical_px', scale_factor=active['scale'])
        for gesture, signal, callback in ((select, 'pressed', selected),
                                         (drag, 'drag-begin', begin),
                                         (drag, 'drag-update', update),
                                         (drag, 'drag-end', end),
                                         (drag, 'cancel', cancelled)):
            self.gesture_handlers.append((gesture, gesture.connect(signal, callback)))
        self.gestures.extend((select, drag))

    def restore_spin_fields(self):
        # Mapping may format the committed value over an unconfirmed edit.
        for widget in self.widgets.values():
            if isinstance(widget, self.Gtk.SpinButton):
                editor = getattr(widget, '_theme_lab_text_editing', None)
                if editor is not None:
                    editor.restore(editor.history.states[editor.history.position])

    def build(self, model):
        records = scene(model, self.args.family)
        self.release_anchor_updates()
        # Release gesture objects while their widgets still exist.
        self.release_gestures()
        old_children=self.fixed.get_children()
        self.widgets, self.gestures, self.dragging = {}, [], {}
        self.boxes, self.records = {}, {}
        self.last_metrics = {}
        # Destruction can emit allocation signals synchronously. Invalidate
        # the old scene before destroying any of its widgets.
        for child in old_children:
            child.destroy()
        for record in records:
            box = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL, spacing=2)
            label = self.Gtk.Label(label=f'{record["index"] + 1}. {record["id"]}')
            label.set_xalign(0)
            box.pack_start(label, False, False, 0)
            control = self.factory(record['id'], record['index'])
            width, height = record['width'], record['height']
            if record['id'] == 'arrow':
                # Keep the triangle's intrinsic pixels and the enclosing
                # shadow instead of stretching it across the scene cell.
                geometry = model['recipes']['gtk3']['geometry']
                extent = geometry['arrow_px'] + 2 * geometry['shadow_px']
                control.set_size_request(width or extent, height or extent)
                control.set_halign(self.Gtk.Align.START)
                control.set_valign(self.Gtk.Align.START)
                box.pack_start(control, False, False, 0)
            else:
                # Zero delegates to native measurement rather than imposing
                # an undocumented 140x44 minimum on every control.
                control.set_size_request(width or -1, height or -1)
                control.set_halign(self.Gtk.Align.START)
                control.set_valign(self.Gtk.Align.START)
                box.pack_start(control, False, False, 0)
            box.set_size_request(width or 148, max(66, height + 22) if height else 66)
            self.fixed.put(box, record['x'], record['y'])
            self.force_state(control, record['forced_state'])
            self.control_capture(box, record)
            self.widgets[record['index']] = control
            self.boxes[record['index']],self.records[record['index']]=box,record
            control.connect('size-allocate', self.measured, record['index'])
            control.connect('map', lambda widget, index=record['index']:
                            self.measured(widget,widget.get_allocation(),index))
        self.fixed.set_size_request(max((item['x'] + max(156, item['width'] + 8) for item in records), default=200),
                                    max((item['y'] + max(74, item['height'] + 30) for item in records), default=100))
        self.fixed.show_all()
        self.restore_spin_fields()
        self.queue_window_measurements()

    def capture_control(self, control, state, output):
        """Save one real GTK3 widget from the offscreen native scene."""
        widget = self.widgets.get(control)
        if widget is None:
            raise ValueError('Controle GTK3 não existe na cena atual.')
        flags = (self.Gtk.StateFlags.NORMAL, self.Gtk.StateFlags.PRELIGHT,
                 self.Gtk.StateFlags.ACTIVE, self.Gtk.StateFlags.INSENSITIVE,
                 self.Gtk.StateFlags.BACKDROP)
        if state < 0 or state >= len(flags):
            raise ValueError('Estado GTK3 fora do intervalo.')
        if state == 3:
            widget.set_sensitive(False)
        widget.set_state_flags(flags[state], False)
        self.window.queue_draw()
        while self.Gtk.events_pending():
            self.Gtk.main_iteration_do(False)
        allocation = widget.get_allocation()
        position = widget.translate_coordinates(self.window, 0, 0)
        pixbuf = self.window.get_pixbuf()
        if (position is None or allocation.width < 1 or allocation.height < 1 or
                pixbuf is None):
            raise ValueError('GTK3 ainda não alocou o controle para a captura.')
        x, y = position
        if (x < 0 or y < 0 or x + allocation.width > pixbuf.get_width() or
                y + allocation.height > pixbuf.get_height()):
            raise ValueError('A captura GTK3 não cobre toda a alocação do controle.')
        sample = pixbuf.new_subpixbuf(x, y, allocation.width, allocation.height)
        if not sample.savev(str(output), 'png', [], []):
            raise OSError('GTK3 não conseguiu salvar a amostra PNG.')
        os.chmod(output, 0o600)

    def reload(self):
        if self.destroyed:
            return False
        if self.dragging:
            return True  # Preserve the current input sequence until Ctrl+drag ends.
        try:
            model, current_hash = backend.project(self.args.project)
            backend.require_scroll_parts_adapter(model["recipes"]["gtk3"])
            if current_hash != self.project_hash:
                scene(model, self.args.family)  # Reject layout before replacing the live scene.
                self.project_hash = current_hash
                self.build(model)
                self.last_error = None
                self.status.set_text('Proposta recarregada. Pintura usa o tema privado selecionado neste processo.')
        except (OSError, ValueError) as error:
            if str(error) != self.last_error:
                self.last_error = str(error)
                self.status.set_text('Prévia anterior preservada: ' + self.last_error)
        return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--family', choices=('gtk3',), default='gtk3')
    parser.add_argument('--embed-window', type=lambda value: int(value, 0))
    parser.add_argument('--capture-control', type=int)
    parser.add_argument('--capture-state', type=int, default=0)
    parser.add_argument('--capture-output', type=Path)
    parser.add_argument('--theme-directory', type=Path)
    parser.add_argument('--events-dir', type=Path, required=True)
    parser.add_argument('--preview-instance')
    parser.add_argument('--host-session-root', type=Path,
                        help='Permite somente GTK3 XEmbed ou captura offscreen na sessão privada do Theme Lab em ~/tempia.')
    parser.add_argument('--root', type=Path, default=backend.ROOT)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if args.host_session_root is not None and os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') != 'bwrap':
            guards = backend.embedded_user_preview_guard(
                root, args.project, args.theme_directory, args.events_dir,
                args.host_session_root, args.embed_window, family='gtk3',
                capture_mode=args.capture_control is not None,
                capture_output=args.capture_output)
        else:
            guards = backend.private_namespace(root)  # Always before GI or display initialization.
        if args.embed_window is not None:
            integer(args.embed_window, 1, 0xffffffff, 'embed_window')
            os.environ['GDK_BACKEND'] = 'x11'
        model, project_hash = backend.project(args.project)
        backend.require_scroll_parts_adapter(model["recipes"]["gtk3"])
        records = scene(model, args.family)
        if args.capture_control is not None:
            if args.capture_output is None or args.family != 'gtk3':
                raise ValueError('Captura nativa disponível somente para GTK3 com destino PNG.')
            integer(args.capture_control, 0, 15, 'capture_control')
            integer(args.capture_state, 0, 4, 'capture_state')
            record = next((item for item in records
                           if item['index'] == args.capture_control), None)
            if record is None:
                raise ValueError('Controle GTK3 não encontrado na receita.')
            model = copy.deepcopy(model)
            recipe = model['recipes']['gtk3']
            recipe['visible_controls'] = 1 << args.capture_control
            recipe['visible_categories'] = 31
            recipe['selected_control'] = args.capture_control
            recipe['edit_state'] = 0
            recipe['positions'][args.capture_control] = [0, 0]
            records = scene(model, args.family)
            destination = args.capture_output.absolute()
            events = args.events_dir.absolute()
            if (destination.parent != events or destination.exists() or
                    not re.fullmatch(r'paint-sample-[0-9a-f]{32}\.png', destination.name)):
                raise ValueError('Destino da amostra deve ser único dentro do diretório privado de eventos.')
        theme_environment(args.theme_directory)
        writer = EventWriter(args.events_dir, root, instance_id=args.preview_instance)
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gtk, Gdk, GLib
        ready, _remaining = Gtk.init_check(None)
        if not ready:
            raise backend.Unavailable('GTK3 não conseguiu abrir a tela privada.')
        provider = None
        if args.theme_directory is not None:
            provider = Gtk.CssProvider()
            try:
                provider.load_from_path(str(args.theme_directory.absolute() / 'gtk-3.0/gtk.css'))
            except GLib.Error as error:
                raise backend.Unavailable('CSS da proposta não foi carregado: ' + str(error)) from error
            # Providers are process-local; this child contains only preview widgets.
            # Named-role definitions must outrank this fake profile's colors.css.
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                     Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
        native = NativeScene(Gtk, Gdk, GLib, args, model, project_hash, writer)
        if args.capture_control is not None:
            def save_capture():
                try:
                    native.capture_control(args.capture_control, args.capture_state,
                                           destination)
                    print(json.dumps({'status': 'captured', 'family': 'gtk3',
                                      'control': args.capture_control,
                                      'state': args.capture_state,
                                      'width': native.widgets[args.capture_control].get_allocated_width(),
                                      'height': native.widgets[args.capture_control].get_allocated_height(),
                                      'widget_source': 'native_gtk3',
                                      'historical_fidelity_claimed': False}, ensure_ascii=False),
                          flush=True)
                except (OSError, ValueError) as error:
                    print('Amostra GTK3 indisponível: ' + str(error), file=sys.stderr)
                    native.close()
                Gtk.main_quit()
                return False
            GLib.timeout_add(100, save_capture)
            Gtk.main()
            return 0 if destination.is_file() else 2
        print(json.dumps({'status': 'started', 'family': 'gtk3', 'pid': os.getpid(),
                          'embedded': args.embed_window is not None, 'controls': [item['id'] for item in records],
                          'project_sha256': project_hash, 'guards': guards,
                          'widget_source': 'native_gtk3', 'historical_fidelity_claimed': False,
                          'css_scope': 'child_process_only' if provider else 'private_native_theme',
                          'forced_states': 'Editor demonstration only', 'host_changed': False}, ensure_ascii=False), flush=True)
        Gtk.main()
        del native
        return 0
    except (OSError, ValueError, ImportError, RuntimeError) as error:
        print('Prévia GTK3 indisponível: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
