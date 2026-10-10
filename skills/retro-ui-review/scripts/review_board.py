#!/usr/bin/env python3
"""Editable GTK checklists; writes answers, history and an output lock file."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

TECHNICAL = {'proved': 'Evidenciado', 'partial': 'Parcial',
             'pending': 'Pendente', 'deferred': 'Adiado'}
REVIEWS = [('unreviewed', 'Não avaliado'), ('confirmed', 'Confirmado'),
           ('failed', 'Falha'), ('question', 'Dúvida'), ('not_tested', 'Não testei')]
REVIEW_IDS = {key for key, _ in REVIEWS}
MAX_JSON_BYTES = 2 * 1024 * 1024


def read_json(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'r', encoding='utf-8') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_JSON_BYTES:
            raise ValueError('JSON deve ser arquivo regular de até 2 MiB.')
        return json.load(stream)


def load_board(path):
    data = read_json(path)
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Checklist exige schema_version: 1.')
    for key in ('id', 'title', 'revision'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError('Checklist exige ' + key + '.')
    items = data.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= 10:
        raise ValueError('Agrupe cada checklist em até dez itens.')
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Cada item deve ser um objeto JSON.')
        for key in ('id', 'title', 'scope', 'conclusion'):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError('Item exige ' + key + '.')
        if item['id'] in seen or item.get('technical_status') not in TECHNICAL:
            raise ValueError('ID repetido ou estado técnico inválido.')
        seen.add(item['id'])
        for key in ('evidence', 'check_steps', 'requirement_ids'):
            value = item.get(key, [])
            if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
                raise ValueError(key + ' deve ser lista de textos.')
        if len(item.get('check_steps', [])) > 3:
            raise ValueError('Use até três ações curtas por grupo.')
    return data


def definition_hash(item):
    fields = {key: item.get(key) for key in ('id', 'title', 'scope', 'conclusion',
              'technical_status', 'check_steps', 'evidence', 'requirement_ids')}
    return hashlib.sha256(json.dumps(fields, sort_keys=True,
                                    ensure_ascii=False).encode()).hexdigest()


def validate_answers(data):
    if not isinstance(data, dict):
        raise ValueError('Respostas anteriores devem ser um objeto JSON.')
    if not data:
        return
    if (data.get('schema_version') != 1 or data.get('kind') != 'review_answers'
            or data.get('uid') != os.getuid()):
        raise ValueError('Arquivo de respostas incompatível; escolha outro caminho.')
    if not isinstance(data.get('boards'), list):
        raise ValueError('Respostas anteriores exigem uma lista de pranchetas.')
    if 'submitted' in data and not isinstance(data['submitted'], bool):
        raise ValueError('submitted deve ser verdadeiro ou falso.')

    def check_item(item):
        if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                or not item['id'].strip()):
            raise ValueError('Resposta anterior exige um objeto com ID de item.')
        status = item.get('review_status', 'unreviewed')
        if not isinstance(status, str) or status not in REVIEW_IDS:
            raise ValueError('Estado de avaliação anterior desconhecido.')
        if not isinstance(item.get('review_note', ''), str):
            raise ValueError('Observação anterior deve ser texto.')
        fingerprint = item.get('definition_sha256')
        if fingerprint is not None and (not isinstance(fingerprint, str)
                or len(fingerprint) != 64
                or any(c not in '0123456789abcdef' for c in fingerprint)):
            raise ValueError('Hash do critério anterior inválido.')
        if 'prior_response' in item and not isinstance(item['prior_response'], dict):
            raise ValueError('Avaliação anterior preservada deve ser um objeto.')

    seen_boards = set()
    for board in data['boards']:
        if (not isinstance(board, dict) or not isinstance(board.get('id'), str)
                or not board['id'].strip() or not isinstance(board.get('items'), list)):
            raise ValueError('Prancheta anterior exige ID e lista de respostas.')
        if board['id'] in seen_boards:
            raise ValueError('IDs de prancheta repetidos nas respostas anteriores.')
        seen_boards.add(board['id'])
        seen_items = set()
        for item in board['items']:
            check_item(item)
            if item['id'] in seen_items:
                raise ValueError('IDs de item repetidos nas respostas anteriores.')
            seen_items.add(item['id'])
    retired = data.get('retired_items', [])
    if not isinstance(retired, list):
        raise ValueError('Itens retirados devem ser uma lista.')
    for item in retired:
        check_item(item)
        if not isinstance(item.get('board_id'), str) or not item['board_id'].strip():
            raise ValueError('Item retirado exige o ID da prancheta anterior.')


def reconcile(boards, previous):
    validate_answers(previous)
    old = {(b['id'], i['id']): i for b in previous.get('boards', [])
           for i in b.get('items', [])}
    responses = {}
    for board in boards:
        for item in board['items']:
            key = board['id'], item['id']
            answer = dict(old.get(key, {}))
            fingerprint = definition_hash(item)
            if answer and answer.get('definition_sha256') != fingerprint:
                answer = {'prior_response': answer, 'review_status': 'unreviewed',
                          'review_note': '', 'criterion_changed': True}
            answer.setdefault('review_status', 'unreviewed')
            answer.setdefault('review_note', '')
            if answer['review_status'] not in REVIEW_IDS:
                raise ValueError('Estado de avaliação desconhecido.')
            if not isinstance(answer['review_note'], str):
                raise ValueError('Observação deve ser texto.')
            answer['definition_sha256'] = fingerprint
            responses[key] = answer
    retired = [dict(answer, board_id=b) for (b, i), answer in old.items()
               if (b, i) not in responses]
    return responses, retired + previous.get('retired_items', [])


def answer_document(boards, responses, retired, submitted):
    output = []
    for board in boards:
        items = [dict(responses[(board['id'], item['id'])], id=item['id'],
                      title=item['title'], technical_status=item['technical_status'])
                 for item in board['items']]
        output.append({'id': board['id'], 'title': board['title'],
                       'revision': board['revision'], 'items': items})
    return {'schema_version': 1, 'kind': 'review_answers', 'uid': os.getuid(),
            'saved_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'submitted': submitted, 'boards': output, 'retired_items': retired}


def check_output(path):
    if not path.is_absolute():
        raise ValueError('Saída deve ter caminho absoluto.')
    for parent in (path.parent, *path.parents):
        if parent.is_symlink():
            raise ValueError('Diretório de saída não pode ser link.')
    if not path.parent.is_dir() or path.parent.stat().st_uid != os.getuid():
        raise ValueError('Pasta de saída deve existir e pertencer ao usuário.')
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if info.st_uid != os.getuid() or not stat.S_ISREG(info.st_mode):
            raise ValueError('Saída existente deve ser regular e pertencer ao usuário.')


@contextmanager
def output_lock(path):
    check_output(path)
    lock_path = path.parent / (path.name + '.lock')
    fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('Lock de respostas deve ser regular e pertencer ao usuário.')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('Outra prancheta já usa essa saída. Feche-a ou escolha outro arquivo.') from error
        yield
    finally:
        os.close(fd)


def save_answers(path, data):
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(payload) > MAX_JSON_BYTES:
        raise ValueError('Respostas excedem 2 MiB. Encurte as notas; o arquivo anterior foi preservado.')
    check_output(path)
    if path.exists():
        history = path.parent / (path.name + '.history')
        if history.is_symlink():
            raise ValueError('Histórico não pode ser link.')
        history.mkdir(mode=0o700, exist_ok=True)
        if history.stat().st_uid != os.getuid():
            raise ValueError('Histórico deve pertencer ao usuário.')
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        old = read_json(path)
        old_path = history / (stamp + '.json')
        fd = os.open(old_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(old, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        check_output(path)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def self_test():
    board = {'id': 'example', 'title': 'Teste', 'revision': '1', 'items': [
        {'id': 'one', 'title': 'Setas', 'scope': 'GTK', 'conclusion': 'Parcial',
         'technical_status': 'partial', 'check_steps': [], 'evidence': []}]}
    responses, retired = reconcile([board], {})
    assert responses[('example', 'one')]['review_status'] == 'unreviewed'
    responses[('example', 'one')].update(review_status='question', review_note='Luz está clara demais?')
    document = answer_document([board], responses, retired, True)
    with tempfile.TemporaryDirectory(prefix='review-board-') as directory:
        target = Path(directory) / 'answers.json'
        save_answers(target, document)
        assert read_json(target) == document
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
        save_answers(target, document)
        assert len(list(target.parent.glob('answers.json.history/*.json'))) == 1
        resumed, _ = reconcile([board], read_json(target))
        assert resumed[('example', 'one')]['review_note'] == 'Luz está clara demais?'
        board['items'][0]['conclusion'] = 'Critério atualizado'
        changed, _ = reconcile([board], document)
        assert changed[('example', 'one')]['review_status'] == 'unreviewed'
        assert changed[('example', 'one')]['prior_response']['review_status'] == 'question'
        unsafe = target.parent / 'link.json'; unsafe.symlink_to(target)
        try: save_answers(unsafe, document)
        except ValueError: pass
        else: raise AssertionError('A saída aceitou um link.')
    print('OK: estados, notas Unicode, retomada, mudança de critério, histórico e gravação atômica.')


def run_window(boards, output, previous, window_title):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
    responses, retired = reconcile(boards, previous)

    class BoardWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title=window_title)
            self.set_role('retro-ui-review-board')
            self.set_default_size(1060, 790)
            self.set_position(Gtk.WindowPosition.CENTER)
            self.dirty = False
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            box.set_border_width(10); self.add(box)
            intro = Gtk.Label(label='Marque sua avaliação; use Explicar para falhas ou dúvidas.\nA prova técnica e sua confirmação são registros separados.')
            intro.set_xalign(0); box.pack_start(intro, False, False, 0)
            notebook = Gtk.Notebook(); box.pack_start(notebook, True, True, 0)
            self.counters = []
            for board in boards:
                panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                counter = Gtk.Label(); counter.set_xalign(0)
                panel.pack_start(counter, False, False, 0)
                self.counters.append((board, counter))
                scroll = Gtk.ScrolledWindow()
                scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                panel.pack_start(scroll, True, True, 0)
                grid = Gtk.Grid(column_spacing=12, row_spacing=12)
                grid.set_border_width(8); scroll.add(grid)
                for row, item in enumerate(board['items']):
                    key = board['id'], item['id']; answer = responses[key]
                    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
                    title = Gtk.Label(); title.set_xalign(0)
                    title.set_markup('<b>' + GLib.markup_escape_text(item['id'] + ' · ' + item['title']) + '</b>')
                    text.pack_start(title, False, False, 0)
                    label = Gtk.Label(label='Técnico: ' + TECHNICAL[item['technical_status']] + ' — ' + item['conclusion'])
                    label.set_xalign(0); label.set_line_wrap(True); label.set_max_width_chars(85)
                    text.pack_start(label, False, False, 0)
                    note = Gtk.Label(label=answer['review_note'] or ('Critério atualizado; resposta anterior preservada.' if answer.get('criterion_changed') else ''))
                    note.set_xalign(0); note.set_line_wrap(True); note.set_max_width_chars(85)
                    text.pack_start(note, False, False, 0); text.set_hexpand(True)
                    grid.attach(text, 0, row, 1, 1)
                    combo = Gtk.ComboBoxText()
                    for identifier, caption in REVIEWS: combo.append(identifier, caption)
                    combo.set_active_id(answer['review_status'])
                    combo.connect('changed', self.change, key)
                    grid.attach(combo, 1, row, 1, 1)
                    explain = Gtk.Button(label='Explicar…')
                    explain.connect('clicked', self.explain, key, item, note)
                    grid.attach(explain, 2, row, 1, 1)
                notebook.append_page(panel, Gtk.Label(label=board['title']))
            self.status = Gtk.Label(label='Salvar grava em ' + str(output))
            self.status.set_xalign(0); self.status.set_selectable(True)
            box.pack_start(self.status, False, False, 0)
            footer = Gtk.Box(spacing=8)
            for caption, close in [('Salvar respostas', False), ('Salvar e fechar', True)]:
                button = Gtk.Button(label=caption); button.connect('clicked', self.save_click, close)
                footer.pack_end(button, False, False, 0)
            box.pack_start(footer, False, False, 0)
            self.connect('delete-event', self.close_request)
            self.update_counts()

        def update_counts(self):
            for board, label in self.counters:
                states = [responses[(board['id'], i['id'])]['review_status'] for i in board['items']]
                label.set_text('Sua avaliação: %d/%d preenchidos · %d confirmados · %d falhas · %d dúvidas' %
                    (sum(s != 'unreviewed' for s in states), len(states), states.count('confirmed'), states.count('failed'), states.count('question')))

        def change(self, combo, key):
            responses[key]['review_status'] = combo.get_active_id()
            self.dirty = True; self.update_counts()

        def explain(self, _button, key, item, note_label):
            dialog = Gtk.Dialog(title=item['title'], transient_for=self, modal=True)
            dialog.set_default_size(700, 460)
            dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Guardar nota', Gtk.ResponseType.OK)
            area = dialog.get_content_area(); area.set_border_width(10)
            rule = Gtk.Label(label=item['scope'] + '\n\nConferir:\n' + '\n'.join('• ' + s for s in item.get('check_steps', [])))
            rule.set_xalign(0); rule.set_line_wrap(True); rule.set_max_width_chars(90)
            area.pack_start(rule, False, False, 6)
            evidence = Gtk.Expander(label='Evidências técnicas')
            source = Gtk.Label(label='\n'.join(item.get('evidence', [])))
            source.set_xalign(0); source.set_line_wrap(True); source.set_selectable(True)
            evidence.add(source); area.pack_start(evidence, False, False, 4)
            scroll = Gtk.ScrolledWindow(); entry = Gtk.TextView()
            entry.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            buffer = entry.get_buffer(); buffer.set_text(responses[key]['review_note'])
            scroll.add(entry); area.pack_start(scroll, True, True, 6)
            dialog.show_all()
            if dialog.run() == Gtk.ResponseType.OK:
                text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
                responses[key]['review_note'] = text; note_label.set_text(text)
                self.dirty = True
            dialog.destroy()

        def save(self, submitted):
            try:
                save_answers(output, answer_document(boards, responses, retired, submitted))
                self.dirty = False
                self.status.set_text(('Respostas salvas: ' if submitted else 'Rascunho salvo: ') + str(output))
                return True
            except (OSError, ValueError) as error:
                self.status.set_text('Falha ao salvar: ' + str(error)); return False

        def save_click(self, _button, close):
            if self.save(True) and close: self.destroy(); Gtk.main_quit()

        def close_request(self, *_args):
            if self.dirty and not self.save(False): return True
            Gtk.main_quit(); return False

    window = BoardWindow(); window.show_all(); Gtk.main()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, default=Path.cwd() / 'review-answers.json')
    parser.add_argument('--title', default='Pranchetas de avaliação')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test: self_test(); return
    if not args.data: parser.error('Informe ao menos um --data.')
    boards = [load_board(path) for path in args.data]
    if len({b['id'] for b in boards}) != len(boards): parser.error('IDs de prancheta repetidos.')
    if args.validate:
        print(json.dumps({'valid': True, 'boards': [{'id': b['id'], 'items': len(b['items'])} for b in boards]})); return
    output = args.output.absolute()
    try:
        with output_lock(output):
            previous = read_json(output) if output.exists() else {}
            validate_answers(previous)
            run_window(boards, output, previous, args.title)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__': main()
