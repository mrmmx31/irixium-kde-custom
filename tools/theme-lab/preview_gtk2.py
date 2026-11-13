#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK2 native preview for controls declared by the partial recipe."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
import backend
from gtk2_session import NativeSession
from native_scene_gtk2 import scene_records
from preview_event_writer import EventWriter
from scene_contract import integer


def pump_events(Gtk, rounds=8):
    for _ in range(rounds):
        if not Gtk.events_pending():
            break
        Gtk.main_iteration_do(False)


def range_stepper_event(widget, Gdk, event_type, x, y):
    event = Gdk.Event.new(event_type)
    window = widget.get_window()
    if window is None:
        raise ValueError('GtkRange não tem janela para o evento nativo da seta.')
    event.button.window = window
    event.button.send_event = True
    event.button.time = Gdk.CURRENT_TIME
    event.button.x = float(x)
    event.button.y = float(y)
    event.button.x_root = float(x)
    event.button.y_root = float(y)
    event.button.state = 0
    event.button.button = 1
    return widget.event(event)


def stepper_event_position(control_id, width, height, direction=None):
    """Return the center of one real GTK2 scrollbar stepper in local pixels."""
    if control_id == 'scroll_h':
        if direction is None:
            direction = 'right'
        if direction not in ('left', 'right'):
            raise ValueError('Barra horizontal aceita somente as setas left/right.')
        return (7 if direction == 'left' else width - 8, height // 2, direction)
    if control_id == 'scroll_v':
        if direction is None:
            direction = 'down'
        if direction not in ('up', 'down'):
            raise ValueError('Barra vertical aceita somente as setas up/down.')
        return (width // 2, 7 if direction == 'up' else height - 8, direction)
    raise ValueError('Captura de seta exige um GtkScrollbar traduzido.')


def capture_probe(args):
    """Validate a private scrollbar probe without changing the project file."""
    probe = {'length_px': args.capture_length,
             'thickness_px': args.capture_thickness,
             'value': args.capture_value,
             'page_size': args.capture_page_size,
             'part': args.capture_part,
             'direction': args.capture_direction}
    if probe['length_px'] and not 15 <= probe['length_px'] <= 2048:
        raise ValueError('Comprimento privado GTK2 deve ser natural ou 15–2048 px.')
    if probe['thickness_px'] and not 1 <= probe['thickness_px'] <= 512:
        raise ValueError('Espessura privada GTK2 deve ser natural ou 1–512 px.')
    if not 1 <= probe['page_size'] <= 100 or not 0 <= probe['value'] <= 100 - probe['page_size']:
        raise ValueError('Faixa privada GTK2 usa 0–100; valor deve caber antes do fim da página.')
    scrollbar = args.capture_control in (10, 11)
    if not scrollbar and probe != {'length_px': 0, 'thickness_px': 0,
            'value': 25, 'page_size': 25, 'part': 'whole', 'direction': 'auto'}:
        raise ValueError('Geometria, faixa, peça e direção privadas exigem GtkScrollbar.')
    if args.capture_control == 10 and probe['direction'] not in ('auto', 'left', 'right'):
        raise ValueError('Barra horizontal GTK2 aceita direção auto/left/right.')
    if args.capture_control == 11 and probe['direction'] not in ('auto', 'up', 'down'):
        raise ValueError('Barra vertical GTK2 aceita direção auto/up/down.')
    return probe


def private_capture_model(model, control, probe):
    """Return an isolated capture scene; the loaded project remains untouched."""
    candidate = copy.deepcopy(model)
    recipe = candidate['recipes']['gtk2']
    recipe['visible_controls'] = 1 << control
    recipe['visible_categories'] = 31
    recipe['selected_control'] = control
    recipe['edit_state'] = 0
    recipe['positions'][control] = [0, 0]
    if control in (10, 11):
        recipe['sizes'][control] = (
            [probe['length_px'], probe['thickness_px']] if control == 10 else
            [probe['thickness_px'], probe['length_px']])
    return candidate


def slider_range(widget):
    """Normalize the GTK2 GI variants of gtk_range_get_slider_range()."""
    result = widget.get_slider_range()
    if not isinstance(result, tuple):
        raise ValueError('GTK2 não forneceu a faixa nativa do thumb.')
    if len(result) == 3 and isinstance(result[0], bool):
        if not result[0]:
            raise ValueError('GTK2 ainda não calculou a faixa nativa do thumb.')
        result = result[1:]
    if len(result) != 2:
        raise ValueError('GTK2 retornou uma faixa de thumb inesperada.')
    start, end = (int(value) for value in result)
    if end <= start:
        raise ValueError('GTK2 retornou um thumb sem comprimento observável.')
    return start, end


def sample_piece(widget, sample, control_id, part, direction, width, height):
    """Crop one measured GTK2 scrollbar piece from the allocated widget."""
    if part == 'whole':
        return sample, 'auto' if direction == 'auto' else direction
    if part == 'fitting':
        raise ValueError('GTK2: fitting pertence ao contêiner rolável, não ao GtkScrollbar capturado.')
    horizontal = control_id == 'scroll_h'
    if control_id not in ('scroll_h', 'scroll_v'):
        raise ValueError('Captura de peça GTK2 exige scroll_h ou scroll_v.')
    if direction == 'auto':
        direction = 'right' if horizontal else 'down'
    if horizontal and direction not in ('left', 'right'):
        raise ValueError('Peça da barra horizontal exige left ou right.')
    if not horizontal and direction not in ('up', 'down'):
        raise ValueError('Peça da barra vertical exige up ou down.')
    cross = height if horizontal else width
    length = width if horizontal else height
    button = min(15, cross, length // 2)
    if button < 1:
        raise ValueError('Alocação GTK2 pequena demais para medir uma peça.')
    if part in ('arrow', 'arrow_button'):
        piece = button if part == 'arrow_button' else min(11, button)
        cross_start = max(0, (cross - piece) // 2)
        leading = direction in ('left', 'up')
        axis_start = ((button - piece) // 2 if leading else
                      length - button + (button - piece) // 2)
        box = ((axis_start, cross_start, piece, piece) if horizontal else
               (cross_start, axis_start, piece, piece))
    elif part == 'trough':
        if length <= button * 2:
            raise ValueError('Barra GTK2 curta demais para expor o trilho entre as setas.')
        box = ((button, 0, length - button * 2, cross) if horizontal else
               (0, button, cross, length - button * 2))
    elif part == 'thumb':
        start, end = slider_range(widget)
        start = max(0, min(length, start)); end = max(start, min(length, end))
        if end <= start:
            raise ValueError('Thumb GTK2 ficou fora da alocação capturada.')
        box = ((start, 0, end - start, cross) if horizontal else
               (0, start, cross, end - start))
    else:
        raise ValueError('Peça GTK2 desconhecida.')
    x, y, piece_width, piece_height = box
    return sample.new_subpixbuf(x, y, piece_width, piece_height), direction


def capture_sample(session, control, state, destination, events_directory, Gdk, Gtk,
                   stepper_direction=None, probe=None):
    if state == 4:
        return {'status': 'unavailable', 'reason': 'GTK2 não expõe o estado backdrop usado pelo editor.'}
    if (probe or {}).get('part', 'whole') == 'fitting':
        return {'status': 'unavailable', 'reason':
                'GTK2: fitting pertence ao contêiner rolável, não ao GtkScrollbar capturado.'}
    if control not in session.scene.widgets:
        raise ValueError('Controle GTK2 ausente ou não traduzido na receita atual.')
    destination = destination.absolute()
    events_directory = events_directory.absolute()
    if (destination.parent != events_directory or destination.exists() or
            not re.fullmatch(r'paint-sample-[0-9a-f]{32}\.png', destination.name)):
        raise ValueError('Destino da amostra deve ser único dentro do diretório privado de eventos.')
    widget = session.scene.widgets[control]
    state_types = (Gtk.StateType.NORMAL, Gtk.StateType.PRELIGHT,
                   Gtk.StateType.ACTIVE, Gtk.StateType.INSENSITIVE)
    if state == 3:
        widget.set_sensitive(False)
    range_record = session.scene.records[control]
    range_stepper = state == 2 and range_record['id'] in ('scroll_h', 'scroll_v')
    if range_stepper:
        # GtkRange does not draw an arrow as pressed when only the parent
        # GtkScrollbar state is set to ACTIVE. Deliver the real GTK2 button
        # event to the final stepper and release it immediately after capture.
        widget.set_state(Gtk.StateType.NORMAL)
    else:
        widget.set_state(state_types[state])
    session.scene.window.show_all()
    session.scene.window.queue_draw()
    for _ in range(8):
        pump_events(Gtk)
        session.scene.window.queue_draw()
    allocation = widget.get_allocation()
    position = widget.translate_coordinates(session.scene.window, 0, 0)
    pixbuf = session.scene.window.get_pixbuf()
    if (position is None or allocation.width < 1 or allocation.height < 1 or
            pixbuf is None):
        raise ValueError('GTK2 ainda não alocou o controle para a captura.')
    x, y = position
    if (x < 0 or y < 0 or x + allocation.width > pixbuf.get_width() or
            y + allocation.height > pixbuf.get_height()):
        raise ValueError('A captura GTK2 não cobre toda a alocação do controle.')
    input_result = None
    before_pixels = None
    if range_stepper:
        axis_x, axis_y, stepper_direction = stepper_event_position(
            range_record['id'], allocation.width, allocation.height,
            stepper_direction)
        before_pixels = pixbuf.get_pixels()
        pressed = False
        press_attempted = False
        try:
            press_attempted = True
            pressed = range_stepper_event(widget, Gdk, Gdk.EventType.BUTTON_PRESS,
                                          axis_x, axis_y)
            pump_events(Gtk)
            session.scene.window.queue_draw()
            pump_events(Gtk)
            if not pressed:
                raise ValueError('GTK2 não tratou o pressionamento do botão de seta.')
        except Exception:
            if press_attempted:
                range_stepper_event(widget, Gdk, Gdk.EventType.BUTTON_RELEASE,
                                    axis_x, axis_y)
                pump_events(Gtk)
            raise
        pixbuf = session.scene.window.get_pixbuf()
        if pixbuf is None or x + allocation.width > pixbuf.get_width() or y + allocation.height > pixbuf.get_height():
            range_stepper_event(widget, Gdk, Gdk.EventType.BUTTON_RELEASE, axis_x, axis_y)
            pump_events(Gtk)
            raise ValueError('GTK2 não manteve a alocação do controle durante a pressão da seta.')
    part = (probe or {}).get('part', 'whole')
    direction = (probe or {}).get('direction', 'auto')
    sample = None
    effective_direction = direction
    try:
        sample = pixbuf.new_subpixbuf(x, y, allocation.width, allocation.height)
        sample, effective_direction = sample_piece(
            widget, sample, range_record['id'], part, direction,
            allocation.width, allocation.height)
        if not sample.savev(str(destination), 'png', [], []):
            raise OSError('GTK2 não conseguiu salvar a amostra PNG.')
    finally:
        if range_stepper:
            released = range_stepper_event(widget, Gdk, Gdk.EventType.BUTTON_RELEASE,
                                           axis_x, axis_y)
            pump_events(Gtk)
            session.scene.window.queue_draw()
            pump_events(Gtk)
            after_pixels = session.scene.window.get_pixbuf().get_pixels()
            input_result = {
                'event': 'BUTTON_PRESS then BUTTON_RELEASE',
                'direction': stepper_direction,
                'position_px': [axis_x, axis_y],
                'press_handled': bool(pressed),
                'release_handled': bool(released),
                'released_pixels_match_before': before_pixels == after_pixels,
            }
    os.chmod(destination, 0o600)
    result = {'status': 'captured', 'widget_source': 'native_gtk2',
              'control': control, 'state': state,
              'width': sample.get_width(), 'height': sample.get_height(),
              'whole_allocation': [allocation.width, allocation.height],
              'part': part, 'direction': effective_direction,
              'range': {'lower': 0, 'upper': 100,
                        'value': (probe or {}).get('value', 25),
                        'page_size': (probe or {}).get('page_size', 25)},
              'scale': 1, 'historical_fidelity_claimed': False}
    if input_result is not None:
        result['native_input'] = input_result
    return result


class ProjectWatcher:
    """Keep the previous scene on an invalid or unsupported project revision."""
    def __init__(self, session, project, project_hash):
        self.session, self.project = session, project
        self.project_hash = project_hash
        self.last_error = None
        self.metrics_signature = None
        self.sample_error = None

    def poll(self):
        try:
            model, digest = self.session.api.project(self.project)
            if digest != self.project_hash:
                self.session.replace(model, digest)
                self.project_hash = digest
                self.last_error = None
                self.session.scene.window.set_title('Theme Lab — GTK2 nativo; receita parcial')
            metrics = self.session.scene.metrics()
            signature = (self.project_hash, json.dumps(metrics, sort_keys=True))
            if signature != self.metrics_signature:
                self.session.scene.emit_metrics()
                self.metrics_signature = signature
        except (OSError, ValueError, RuntimeError, TypeError) as error:
            message = str(error)
            if message != self.last_error:
                self.last_error = message
                self.session.scene.window.set_title('Prévia GTK2 anterior preservada: ' + message[:160])
                print('Recarga GTK2 recusada: ' + message, file=sys.stderr, flush=True)
        self.checkpoint()
        return True

    def checkpoint(self, capture=True):
        try:
            self.session.checkpoint(capture)
        except (OSError, ValueError, RuntimeError, TypeError) as error:
            message = str(error)
            if message != self.sample_error:
                self.sample_error = message
                print('Amostras GTK2 não salvas: ' + message,
                      file=sys.stderr, flush=True)
            self.session.scene.window.set_title('Amostras GTK2 preservadas na memória; não salvas: ' + message[:120])
            return False
        if self.sample_error is not None:
            self.sample_error = None
            self.session.scene.window.set_title(
                'Theme Lab — GTK2 nativo; histórico das amostras recuperado')
        return True

    def delete_event(self, *_):
        return not self.checkpoint()  # Native close must not silently discard text.


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--rc', type=Path, required=True)
    parser.add_argument('--events-dir', type=Path, required=True)
    parser.add_argument('--preview-instance')
    parser.add_argument('--embed-window', type=lambda value: int(value, 0))
    parser.add_argument('--host-session-root', type=Path,
                        help='Permite somente GTK2 XEmbed ou captura offscreen na sessão privada do Theme Lab em ~/tempia.')
    parser.add_argument('--runtime-toggle-active', type=int, choices=(0,1))
    parser.add_argument('--runtime-check-active', type=int, choices=(0,1))
    parser.add_argument('--runtime-radio-member', type=int, choices=(0,1))
    parser.add_argument('--trace-input', action='store_true',
                        help='Write a bounded GTK2 event-signal trace for the isolated preview.')
    parser.add_argument('--capture-control', type=int)
    parser.add_argument('--capture-state', type=int, default=0)
    parser.add_argument('--capture-stepper', choices=('left', 'right', 'up', 'down'),
                        help='Choose one native GTK2 scrollbar arrow for a pressed-state sample.')
    parser.add_argument('--capture-length', type=int, default=0,
                        help='Comprimento privado da barra; 0 usa a requisição natural.')
    parser.add_argument('--capture-thickness', type=int, default=0,
                        help='Espessura privada da barra; 0 usa a requisição natural.')
    parser.add_argument('--capture-value', type=int, default=25)
    parser.add_argument('--capture-page-size', type=int, default=25)
    parser.add_argument('--capture-part',
                        choices=('whole', 'arrow', 'arrow_button', 'trough', 'thumb', 'fitting'),
                        default='whole')
    parser.add_argument('--capture-direction',
                        choices=('auto', 'left', 'right', 'up', 'down'), default='auto')
    parser.add_argument('--capture-output', type=Path)
    parser.add_argument('--root', type=Path, default=backend.ROOT)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        capture_mode = (args.capture_control is not None or args.capture_output is not None
                        or args.capture_state != 0 or args.capture_stepper is not None or
                        args.capture_length != 0 or args.capture_thickness != 0 or
                        args.capture_value != 25 or args.capture_page_size != 25 or
                        args.capture_part != 'whole' or args.capture_direction != 'auto')
        if args.host_session_root is not None and os.environ.get('IRIX_DOMAINOS_PRIVATE_NAMESPACE') != 'bwrap':
            guards = backend.embedded_user_preview_guard(
                root, args.project, args.rc, args.events_dir,
                args.host_session_root, args.embed_window,
                capture_mode=capture_mode, capture_output=args.capture_output)
        else:
            guards = backend.private_namespace(root)  # Before GI/display initialization.
        if args.embed_window is not None:
            integer(args.embed_window, 1, 0xffffffff, 'embed_window')
        model, digest = backend.project(args.project)
        probe = capture_probe(args) if capture_mode else None
        if capture_mode:
            if args.capture_control is None or args.capture_output is None:
                raise ValueError('Captura GTK2 exige controle, estado e arquivo PNG.')
            integer(args.capture_control, 0, 15, 'capture_control')
            integer(args.capture_state, 0, 4, 'capture_state')
            if args.capture_stepper is not None:
                if args.capture_state != 2 or args.capture_control not in (10, 11):
                    raise ValueError('--capture-stepper exige uma seta GTK2 e o estado pressionado.')
                if args.capture_direction != 'auto' and args.capture_direction != args.capture_stepper:
                    raise ValueError('--capture-stepper e --capture-direction precisam indicar a mesma seta.')
                probe['direction'] = args.capture_stepper
                stepper_event_position('scroll_h' if args.capture_control == 10 else 'scroll_v',
                                       220 if args.capture_control == 10 else 15,
                                       15 if args.capture_control == 10 else 180,
                                       args.capture_stepper)
            if args.capture_state == 4:
                print(json.dumps({'status': 'unavailable', 'reason':
                    'GTK2 não expõe o estado backdrop usado pelo editor.'}, ensure_ascii=False), flush=True)
                return 0
            model = private_capture_model(model, args.capture_control, probe)
        else:
            # The editor's state selector describes the source fragment being
            # inspected. It is not a request to synthesize a GTK interaction.
            # Keep the saved recipe untouched and show the real widgets in
            # their normal state; users can press an arrow in this live scene
            # to inspect GTK2's actual pressed rendering.
            model = copy.deepcopy(model)
            model['recipes']['gtk2']['edit_state'] = 0
        bridge = NativeSession.pressure_bridge(root, model)
        records = scene_records(model, allow_button_pressed=bridge is not None)
        # GTK2 defaults and modules must not leak the personal theme into this child.
        os.environ['GTK2_RC_FILES'] = '/dev/null'
        os.environ['GTK_MODULES'] = ''
        writer = EventWriter(args.events_dir, root, family='gtk2', backend_api=backend,
                             instance_id=args.preview_instance)
        import gi
        gi.require_version('Gtk', '2.0')
        gi.require_version('Gdk', '2.0')
        from gi.repository import Gtk, Gdk, GLib
        ready, _remaining = Gtk.init_check([])
        if not ready:
            raise backend.Unavailable('GTK2 não conseguiu abrir a tela privada.')
        session = NativeSession(backend, Gtk, Gdk, root, args.rc, model, digest, writer,
                                args.embed_window, sample_directory=None if capture_mode else writer.directory,
                                trace_input=args.trace_input, capture_mode=capture_mode,
                                capture_probe=probe)
        if capture_mode:
            result = capture_sample(session, args.capture_control, args.capture_state,
                                    args.capture_output, args.events_dir, Gdk, Gtk,
                                    args.capture_stepper or
                                    (probe['direction'] if probe['direction'] != 'auto' else None),
                                    probe)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            session.scene.gestures.close()
            session.scene.window.destroy()
            return 0
        session.samples.seed_runtime(session.scene, args.runtime_toggle_active,
                                     args.runtime_check_active, args.runtime_radio_member)
        watcher = ProjectWatcher(session, args.project, digest)
        source = GLib.timeout_add(250, watcher.poll)
        session.scene.window.connect('delete-event', watcher.delete_event)
        session.scene.window.connect('destroy', lambda _window: Gtk.main_quit())
        print(json.dumps({'status': 'started', 'family': 'gtk2', 'pid': os.getpid(),
                          'embedded': args.embed_window is not None,
                          'sample_history': str(session.samples.journal.path),
                          'sample_runtime': str(session.samples.runtime_journal.path),
                          'sample_checkpoint_ms': 250,
                          'controls': [record['id'] for record in records],
                          'project_sha256': digest, 'guards': guards,
                          'recipe_scope': 'translated_controls', 'widget_source': 'native_gtk2',
                          'historical_fidelity_claimed': False, 'host_changed': False}), flush=True)
        try:
            Gtk.main()
        finally:
            GLib.source_remove(source)
            watcher.checkpoint(capture=False)
            session.scene.gestures.close()
            if session.scene.input_trace is not None:
                session.scene.input_trace.close()
        return 0
    except (OSError, ValueError, ImportError, RuntimeError, TypeError) as error:
        print('Prévia GTK2 indisponível: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
