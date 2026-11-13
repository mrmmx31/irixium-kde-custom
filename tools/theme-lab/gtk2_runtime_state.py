# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed GTK2 sample values; independent of geometry, palette and text Undo.

No persistence or GTK import here. Validate the whole snapshot before applying
any state, and preserve hidden controls when capturing a partial scene.
"""
import copy
import math

IDS = {1: 'toggle', 2: 'check', 3: 'radio', 5: 'combo',
       8: 'scale_h', 9: 'scale_v', 10: 'scroll_h', 11: 'scroll_v',
       13: 'progress', 14: 'list'}
RANGES = {'scale_h', 'scale_v', 'scroll_h', 'scroll_v'}


def number(value, label, lower=-1e12, upper=1e12):
    if type(value) not in (int, float) or not lower <= value <= upper or not math.isfinite(value):
        raise ValueError('Valor numérico inválido: ' + label)
    return value


def validate(states):
    if not isinstance(states, dict) or not set(states) <= set(IDS.values()):
        raise ValueError('Contrato de estados GTK2 inválido ou controle desconhecido.')
    for control, value in states.items():
        if control in ('toggle', 'check'):
            if type(value) is not bool:
                raise ValueError('Estado marcado GTK2 deve ser booleano.')
        elif control in ('radio', 'combo'):
            choices = (0, 1) if control == 'radio' else (-1, 0, 1, 2)
            if type(value) is not int or value not in choices:
                raise ValueError('Seleção GTK2 fora do catálogo: ' + control)
        elif control == 'progress':
            number(value, control, 0, 1)
        elif control in RANGES:
            if not isinstance(value, dict) or set(value) != {'value', 'lower', 'upper', 'page_size'}:
                raise ValueError('Intervalo GTK2 incompleto: ' + control)
            for key, n in value.items(): number(n, control + '.' + key)
            low, high, page = (value[key] for key in ('lower', 'upper', 'page_size'))
            if high < low or not 0 <= page <= high - low or not low <= value['value'] <= high - page:
                raise ValueError('Intervalo GTK2 inconsistente: ' + control)
        elif control == 'list':
            if not isinstance(value, dict) or set(value) != {'rows', 'selected', 'horizontal', 'vertical'}:
                raise ValueError('Estado de lista GTK2 incompleto.')
            rows, selected = value['rows'], value['selected']
            if not isinstance(rows, list) or len(rows) > 4096:
                raise ValueError('Lista GTK2 excede4096 linhas.')
            total = 0
            for text in rows:
                if not isinstance(text, str) or '\x00' in text:
                    raise ValueError('Texto de lista GTK2 inválido.')
                try: size = len(text.encode('utf-8'))
                except UnicodeError as error: raise ValueError('Lista não contém UTF-8 válido.') from error
                if size > 4096: raise ValueError('Linha de lista GTK2 excede4096 bytes.')
                total += size
            if total > 1048576: raise ValueError('Conteúdo da lista GTK2 excede1MiB.')
            if not isinstance(selected, list) or len(selected) > 1:
                raise ValueError('Lista GTK2 suporta uma seleção nativa por vez.')
            for path in selected:
                if not isinstance(path, str) or not path.isascii() or not path.isdecimal() or \
                        len(path) > 4 or str(int(path)) != path or not 0 <= int(path) < len(rows):
                    raise ValueError('Seleção da lista GTK2 não corresponde a uma linha.')
            number(value['horizontal'], 'list.horizontal', 0)
            number(value['vertical'], 'list.vertical', 0)
    return copy.deepcopy(states)


def adjustment_state(widget):
    adj = widget.get_adjustment()
    return {'value': adj.get_value(), 'lower': adj.get_lower(),
            'upper': adj.get_upper(), 'page_size': adj.get_page_size()}


def capture(scene, previous=None):
    result = validate(previous if previous is not None else {})
    for index, control in IDS.items():
        if index not in scene.widgets: continue
        widget = scene.widgets[index]
        if control in ('toggle', 'check'): value = bool(widget.get_active())
        elif control == 'radio': value = scene.radio_groups[index].selected()
        elif control == 'combo': value = scene.combo_widgets[index].get_active()
        elif control in RANGES: value = adjustment_state(widget)
        elif control == 'progress': value = scene.progress_widgets[index].get_fraction()
        else: value = scene.list_controls[index].snapshot()
        result[control] = value
    return validate(result)


def restore(scene, states):
    values = validate(states)
    # Preflight every present range before changing even a checkbox.
    for index, control in IDS.items():
        if index in scene.widgets and control in values and control in RANGES:
            actual = adjustment_state(scene.widgets[index])
            if any(actual[key] != values[control][key] for key in ('lower', 'upper', 'page_size')):
                raise ValueError('Intervalo nativo mudou; estado anterior preservado: ' + control)
    for index, control in IDS.items():
        if index not in scene.widgets or control not in values: continue
        widget, value = scene.widgets[index], values[control]
        if control in ('toggle', 'check'): widget.set_active(value)
        elif control == 'radio': scene.radio_groups[index].select(value)
        elif control == 'combo': scene.combo_widgets[index].set_active(value)
        elif control in RANGES: widget.get_adjustment().set_value(value['value'])
        elif control == 'progress':
            scene.progress_widgets[index].set_fraction(value)
            scene.progress_values[index].set_text(format(value * 100, 'g') + '%')
        else: scene.list_controls[index].restore(value)
