# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed sample text journal; recipes and editor histories remain separate."""
import importlib.util
import json
import os
from pathlib import Path


def sibling(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TextHistory = sibling('preview_text_history').TextHistory
_store = sibling('private_json_store')
PrivateJsonStore = _store.PrivateJsonStore
MAX_BYTES = _store.MAX_BYTES
TEXT_CONTROLS = {'entry', 'text', 'spin'}


def parse_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Chave duplicada no journal de amostras.')
            result[key] = value
        return result
    if len(raw) > MAX_BYTES:
        raise ValueError('Journal de amostras excede32MiB.')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('Journal de amostras não contém JSON UTF-8 válido.') from error
    return value


def decode(raw, family, origin):
    value = parse_json(raw)
    if not isinstance(value, dict) or set(value) != {
            'schema_version', 'kind', 'family', 'origin', 'histories'}:
        raise ValueError('Contrato do journal de amostras inválido.')
    if type(value['schema_version']) is not int or value['schema_version'] != 1 or \
            value['kind'] != 'theme_lab_sample_text_history' or \
            value['family'] != family or value['origin'] != origin:
        raise ValueError('Journal pertence a outra família/origem ou versão.')
    histories = value['histories']
    if not isinstance(histories, dict) or not set(histories) <= TEXT_CONTROLS:
        raise ValueError('Controle desconhecido no journal de amostras.')
    return {key: TextHistory.from_snapshot(snapshot) for key, snapshot in histories.items()}


class SampleJournal(PrivateJsonStore):
    def __init__(self, directory, family, origin):
        if family not in ('gtk2', 'gtk3') or origin not in ('coupled', 'separate'):
            raise ValueError('Família/origem inválida para journal de amostras.')
        self.family, self.origin = family, origin
        super().__init__(directory, 'sample-' + family + '-' + origin + '.json')

    def load(self):
        return self.read_loaded(lambda raw: decode(raw, self.family, self.origin))

    def save(self, histories):
        value = {'schema_version': 1, 'kind': 'theme_lab_sample_text_history',
                 'family': self.family, 'origin': self.origin,
                 'histories': {key: history.snapshot() for key, history in histories.items()}}
        raw = (json.dumps(value, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':')) + '\n').encode('utf-8')
        decode(raw, self.family, self.origin)
        return self.write_payload(raw)
