# SPDX-License-Identifier: GPL-3.0-or-later
"""Initial comparison inputs only; never a user recipe or live text buffer."""
import json
from pathlib import Path

TEXT_KEYS = ('push', 'toggle', 'check', 'entry', 'combo_a', 'combo_b', 'combo_c', 'text', 'frame', 'radio', 'list_a', 'list_b', 'list_c')
NUMBER_KEYS = ('spin', 'scale_h', 'scale_v', 'scroll', 'page_size', 'level')

def load():
    data = json.loads(Path(__file__).with_name('sample_controls.json').read_text(encoding='utf-8'))
    if type(data) is not dict or set(data) != set(TEXT_KEYS + NUMBER_KEYS):
        raise ValueError('Contrato de amostras incompleto ou com campos desconhecidos')
    for key in TEXT_KEYS:
        if type(data[key]) is not str or not data[key] or len(data[key].encode('utf-8')) > 256 or '\0' in data[key]:
            raise ValueError('Texto de amostra inválido: ' + key)
    for key in NUMBER_KEYS:
        if type(data[key]) is not int or not 0 <= data[key] <= 100:
            raise ValueError('Valor de amostra inválido: ' + key)
    if not 1 <= data['page_size'] <= 100 or data['scroll'] > 100 - data['page_size']:
        raise ValueError('Intervalo de rolagem inválido')
    return data

SAMPLES = load()

def c_header():
    lines = ['/* Generated from sample_controls.json; do not edit. */',
             '#ifndef TL_SAMPLE_CONTROLS_H', '#define TL_SAMPLE_CONTROLS_H']
    for key, value in SAMPLES.items():
        literal = json.dumps(value, ensure_ascii=False) if isinstance(value, str) else str(value)
        lines.append('#define TL_SAMPLE_' + key.upper() + ' ' + literal)
    return '\n'.join(lines + ['#endif', ''])

if __name__ == '__main__':
    target = Path(__file__).with_name('include') / 'sample_controls.h'
    import sys
    if '--check' in sys.argv:
        if target.read_text(encoding='utf-8') != c_header():
            raise SystemExit('Header de amostras desatualizado')
    else:
        target.write_text(c_header(), encoding='utf-8')
