#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native GTK3 Theme Lab scene, embedded with XEmbed or in a private window.

Ctrl+click selects a control; Ctrl+drag proposes its position through private
JSON events. Ordinary input remains native widget input. Forced editor states
are demonstrations, not evidence of historical DomainOS behaviour.
"""
from __future__ import annotations

import argparse
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
spec = importlib.util.spec_from_file_location('theme_lab_preview_backend', SOURCE / 'backend.py')
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)
CONTROLS = backend.CONTROLS
CATEGORIES = (0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 4)
EDIT_STATES = ('normal', 'pressed', 'disabled', 'backdrop')


def integer(value, minimum, maximum, field):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{field}: inteiro entre {minimum} e {maximum} esperado.')
    return value


def scene(model, family='gtk3'):
    """Pure layout specification; never imports GI or mutates a project."""
    if family != 'gtk3':
        raise ValueError('Esta montagem contém controles GTK3 reais; outros adaptadores estão pendentes.')
    recipes = model.get('recipes') if isinstance(model, dict) else None
    recipe = recipes.get(family) if isinstance(recipes, dict) else None
    if not isinstance(recipe, dict):
        raise ValueError('Receita GTK3 ausente.')
    categories = integer(recipe.get('visible_categories', 31), 0, 31, 'visible_categories')
    controls = integer(recipe.get('visible_controls', 65535), 0, 65535, 'visible_controls')
    selected = integer(recipe.get('selected_control', 0), 0, 15, 'selected_control')
    state = integer(recipe.get('edit_state', 0), 0, 3, 'edit_state')
    positions = recipe.get('positions', [[16 + (i % 4)*160, 16 + (i // 4)*80] for i in range(16)])
    if not isinstance(positions, list) or len(positions) != len(CONTROLS):
        raise ValueError('positions deve conter 16 pares de coordenadas.')
    sizes = recipe.get('sizes', [[0, 0] for _ in CONTROLS])
    if not isinstance(sizes, list) or len(sizes) != len(CONTROLS):
        raise ValueError('sizes deve conter 16 pares de dimensões.')
    result = []
    for index, (identifier, category, pair) in enumerate(zip(CONTROLS, CATEGORIES, positions)):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError('Cada posição deve conter somente x e y.')
        x = integer(pair[0], 0, 2048, f'positions[{index}].x')
        y = integer(pair[1], 0, 2048, f'positions[{index}].y')
        dimensions = sizes[index]
        if not isinstance(dimensions, list) or len(dimensions) != 2:
            raise ValueError('Cada tamanho deve conter largura e altura.')
        width = integer(dimensions[0], 0, 2048, f'sizes[{index}].width')
        height = integer(dimensions[1], 0, 2048, f'sizes[{index}].height')
        if not (categories & (1 << category) and controls & (1 << index)):
            continue
        result.append({'id': identifier, 'index': index, 'category': category,
                       'x': x, 'y': y, 'width': width, 'height': height, 'selected': index == selected,
                       'forced_state': state if index == selected else 0})
    return result


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


class EventWriter:
    """Owned 0700 directory, unique 0600 atomic events; no project writes."""
    def __init__(self, directory, root):
        self.directory = backend.private_output(directory, root)

    def emit(self, action, control, project_hash, **fields):
        integer(control, 0, len(CONTROLS) - 1, 'control_index')
        if not re.fullmatch(r'[0-9a-f]{64}', project_hash):
            raise ValueError('Hash da proposta inválido.')
        event = {'schema_version': 1, 'kind': 'theme_lab_preview_event',
                 'event_id': uuid.uuid4().hex, 'family': 'gtk3', 'action': action,
                 'control_id': CONTROLS[control], 'control_index': control,
                 'project_sha256': project_hash,
                 'emitted_at': dt.datetime.now(dt.timezone.utc).isoformat(), **fields}
        payload = (json.dumps(event, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
        if len(payload) > 16384:
            raise ValueError('Evento excede 16 KiB.')
        target = self.directory / f'event-{time.time_ns():020d}-{event["event_id"]}.json'
        fd, temporary = tempfile.mkstemp(prefix='.preview-event-', dir=self.directory)
        try:
            with os.fdopen(fd, 'wb') as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)


def theme_environment(directory):
    if directory is None:
        return
    directory = directory.absolute()
    if '..' in directory.parts or any(item.is_symlink() for item in (directory, *directory.parents)):
        raise ValueError('O tema privado não pode atravessar links ou ..')
    if (not directory.is_dir() or directory.stat().st_uid != os.getuid() or
            not (directory.is_relative_to(Path('/home/domainos-test')) or
                 directory.is_relative_to(Path(tempfile.gettempdir())))):
        raise ValueError('Use o diretório do tema gerado dentro do perfil privado ou /tmp.')
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
        self.widgets, self.gestures, self.dragging = {}, [], {}
        self.destroyed, self.last_error = False, None
        if args.embed_window is not None:
            self.window = Gtk.Plug.new(args.embed_window)
        else:
            self.window = Gtk.Window(title='Theme Lab — GTK3 nativo privado')
            self.window.set_default_size(760, 450)
        self.window.connect('destroy', self.close)
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
        self.reload_source = GLib.timeout_add(500, self.reload)

    def close(self, *_):
        self.destroyed = True
        if hasattr(self, 'reload_source'):
            self.GLib.source_remove(self.reload_source)
        self.Gtk.main_quit()

    def emit(self, action, index, **fields):
        try:
            self.writer.emit(action, index, self.project_hash, **fields)
        except (OSError, ValueError) as error:
            self.status.set_text('Evento não salvo: ' + str(error))

    def changed(self, index, **state):
        self.status.set_text(f'{CONTROLS[index]}: interação nativa; Ctrl+arraste altera o layout.')
        self.emit('native', index, state=state)

    def factory(self, identifier, index):
        Gtk = self.Gtk
        if identifier == 'push':
            widget = Gtk.Button(label='Pressione')
            widget.connect('clicked', lambda *_: self.changed(index, clicked=True))
        elif identifier == 'toggle':
            widget = Gtk.ToggleButton(label='Alternar')
            widget.connect('toggled', lambda w: self.changed(index, active=w.get_active()))
        elif identifier == 'check':
            widget = Gtk.CheckButton(label='Marcar')
            widget.connect('toggled', lambda w: self.changed(index, active=w.get_active()))
        elif identifier == 'radio':
            widget = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            first = Gtk.RadioButton.new_with_label_from_widget(None, 'A')
            second = Gtk.RadioButton.new_with_label_from_widget(first, 'B')
            widget.pack_start(first, False, False, 0)
            widget.pack_start(second, False, False, 0)
            second.connect('toggled', lambda w: self.changed(index, option='B' if w.get_active() else 'A'))
        elif identifier == 'entry':
            widget = Gtk.Entry()
            widget.set_text('Campo editável')
            widget.connect('changed', lambda w: self.changed(index, text_length=w.get_text_length()))
        elif identifier == 'combo':
            widget = Gtk.ComboBoxText()
            for item in ('Primeiro', 'Segundo', 'Terceiro'):
                widget.append_text(item)
            widget.set_active(0)
            widget.connect('changed', lambda w: self.changed(index, active_index=w.get_active()))
        elif identifier == 'spin':
            widget = Gtk.SpinButton.new_with_range(0, 100, 1)
            widget.set_value(42)
            widget.connect('value-changed', lambda w: self.changed(index, value=w.get_value()))
        elif identifier == 'text':
            widget = Gtk.ScrolledWindow()
            widget.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            text = Gtk.TextView()
            text.get_buffer().set_text('Texto nativo\nEdite e role.')
            text.get_buffer().connect('changed', lambda b: self.changed(index, text_length=b.get_char_count()))
            widget.add(text)
        elif identifier in ('scale_h', 'scale_v', 'scroll_h', 'scroll_v'):
            orientation = Gtk.Orientation.HORIZONTAL if identifier.endswith('_h') else Gtk.Orientation.VERTICAL
            if identifier.startswith('scale'):
                widget = Gtk.Scale.new_with_range(orientation, 0, 100, 1)
                widget.set_value(38)
                widget.connect('value-changed', lambda w: self.changed(index, value=w.get_value()))
            else:
                adjustment = Gtk.Adjustment(value=30, lower=0, upper=100, step_increment=1,
                                            page_increment=10, page_size=20)
                widget = Gtk.Scrollbar(orientation=orientation, adjustment=adjustment)
                adjustment.connect('value-changed', lambda a: self.changed(index, value=a.get_value()))
        elif identifier == 'arrow':
            widget = Gtk.Button()
            widget.get_style_context().add_class('theme-lab-arrow')
            widget.connect('clicked', lambda *_: self.changed(index, clicked=True))
        elif identifier == 'progress':
            widget = Gtk.ProgressBar()
            widget.set_fraction(.57)
            widget.set_show_text(True)
        elif identifier == 'list':
            widget = Gtk.ScrolledWindow()
            widget.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            store = Gtk.ListStore(str, str)
            for number in range(1, 16):
                store.append((f'Item {number:02d}', 'Linha artificial longa para rolagem horizontal'))
            tree = Gtk.TreeView(model=store)
            for column, title in enumerate(('Item', 'Descrição')):
                tree.append_column(Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=column))
            def selection_changed(selection):
                selected_model, row = selection.get_selected()
                self.changed(index, row=selected_model.get_path(row).to_string() if row is not None else None)
            tree.get_selection().connect('changed', selection_changed)
            widget.add(tree)
        elif identifier == 'frame':
            widget = Gtk.Frame(label='Moldura nativa')
            widget.add(Gtk.Label(label='Conteúdo'))
        else:
            raise ValueError('Controle não implementado: ' + identifier)
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
        def cancelled(_gesture, _sequence):
            active = self.dragging.pop(index, None)
            if active is not None:
                self.fixed.move(box, *active['origin'])
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
            self.fixed.move(box, *proposed)
        def end(gesture, _x, _y):
            active = self.dragging.pop(index, None)
            if active is None:
                return
            proposed = destination(gesture, active)
            if proposed is None:
                self.fixed.move(box, *active['origin'])
                self.status.set_text('Arraste cancelado: coordenadas ou escala da tela mudaram.')
                return
            self.fixed.move(box, *proposed)
            record['x'], record['y'] = proposed
            if proposed != active['origin']:
                self.emit('move', index, x=proposed[0], y=proposed[1],
                          coordinate_space='gtk_logical_px', scale_factor=active['scale'])
        select.connect('pressed', selected)
        drag.connect('drag-begin', begin)
        drag.connect('drag-update', update)
        drag.connect('drag-end', end)
        drag.connect('cancel', cancelled)
        self.gestures.extend((select, drag))

    def build(self, model):
        records = scene(model, self.args.family)
        for child in self.fixed.get_children():
            child.destroy()
        self.widgets, self.gestures, self.dragging = {}, [], {}
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
                control.set_size_request(width or 140, height or 44)
                if width:
                    control.set_halign(self.Gtk.Align.START)
                box.pack_start(control, not bool(height), not bool(height), 0)
            box.set_size_request(width or 148, max(66, height + 22) if height else 66)
            self.fixed.put(box, record['x'], record['y'])
            self.force_state(control, record['forced_state'])
            self.control_capture(box, record)
            self.widgets[record['index']] = control
        self.fixed.set_size_request(max((item['x'] + max(156, item['width'] + 8) for item in records), default=200),
                                    max((item['y'] + max(74, item['height'] + 30) for item in records), default=100))
        self.fixed.show_all()

    def reload(self):
        if self.destroyed:
            return False
        if self.dragging:
            return True  # Preserve the current input sequence until Ctrl+drag ends.
        try:
            model, current_hash = backend.project(self.args.project)
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
    parser.add_argument('--theme-directory', type=Path)
    parser.add_argument('--events-dir', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=backend.ROOT)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        guards = backend.private_namespace(root)  # Always before GI or display initialization.
        if args.embed_window is not None:
            integer(args.embed_window, 1, 0xffffffff, 'embed_window')
            os.environ['GDK_BACKEND'] = 'x11'
        model, project_hash = backend.project(args.project)
        records = scene(model, args.family)
        theme_environment(args.theme_directory)
        writer = EventWriter(args.events_dir, root)
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
