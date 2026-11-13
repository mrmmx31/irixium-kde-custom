# SPDX-License-Identifier: GPL-3.0-or-later
"""Validated nontext sample journal; not a recipe or a text Undo history."""
import json
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('runtime_sample_storage',
    Path(__file__).with_name('preview_sample_journal.py'))
_sample = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sample)
PrivateJsonStore, parse_json = _sample.PrivateJsonStore, _sample.parse_json
validate = _sample.sibling('gtk2_runtime_state').validate


def decode(raw, family, origin):
    value = parse_json(raw)
    if not isinstance(value, dict) or set(value) != {
            'schema_version', 'kind', 'family', 'origin', 'states'}:
        raise ValueError('Contrato do journal de estados inválido.')
    if type(value['schema_version']) is not int or value['schema_version'] != 1 or \
            value['kind'] != 'theme_lab_sample_runtime_state' or \
            value['family'] != family or value['origin'] != origin:
        raise ValueError('Journal de estados pertence a outra família/origem ou versão.')
    return validate(value['states'])


class RuntimeJournal(PrivateJsonStore):
    def __init__(self, directory, family, origin):
        if family != 'gtk2' or origin not in ('coupled', 'separate'):
            raise ValueError('Família/origem ainda não suporta journal de estados.')
        self.family, self.origin = family, origin
        super().__init__(directory, 'runtime-' + family + '-' + origin + '.json')

    def load(self):
        return self.read_loaded(lambda raw: decode(raw, self.family, self.origin))

    def save(self, states):
        value = {'schema_version': 1, 'kind': 'theme_lab_sample_runtime_state',
                 'family': self.family, 'origin': self.origin, 'states': validate(states)}
        raw = (json.dumps(value, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':')) + '\n').encode('utf-8')
        decode(raw, self.family, self.origin)
        return self.write_payload(raw)
