# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded, per-control preview history; no GTK imports or project writes."""
import math


def validated_state(value):
    """Validate untrusted UTF-8 text history before touching a native field."""
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError('Estado de texto deve conter texto, cursor, âncora e valor.')
    text, cursor, anchor, number = value
    if not isinstance(text, str) or '\x00' in text:
        raise ValueError('Texto inválido no histórico da amostra.')
    try:
        encoded = text.encode('utf-8')
    except UnicodeError as error:
        raise ValueError('Texto não representa UTF-8 válido.') from error
    if len(encoded) > 16 * 1048576:
        raise ValueError('Estado de texto excede16MiB.')
    for position in (cursor, anchor):
        if type(position) is not int or not 0 <= position <= len(text):
            raise ValueError('Seleção inválida no histórico da amostra.')
    if number is not None and (type(number) not in (int, float) or
                               abs(number) > 1e308 or not math.isfinite(number)):
        raise ValueError('Valor confirmado do spin inválido.')
    return (text, cursor, anchor, number)


class TextHistory:
    def __init__(self, initial, limit=128, byte_limit=1048576):
        self.states = [initial]
        self.position = 0
        self.limit = limit
        self.byte_limit = byte_limit

    def remember_selection(self, state):
        if state[0] == self.states[self.position][0]:
            self.states[self.position] = state

    def push(self, state):
        if state[0] == self.states[self.position][0]:
            self.remember_selection(state)
            return
        self.states[self.position + 1:] = []
        self.states.append(state)
        self.position += 1
        # Keep at least current and previous values, even for a large paste.
        while len(self.states) > 2 and (len(self.states) > self.limit or
                sum(len(s[0].encode('utf-8')) for s in self.states) > self.byte_limit):
            del self.states[0]
            self.position -= 1

    def step(self, direction):
        position = self.position + direction
        if direction not in (-1, 1) or not 0 <= position < len(self.states):
            return None
        self.position = position
        return self.states[position]


    def snapshot(self):
        """Return a detached representation; saving must not change undo position."""
        return {'states': [list(validated_state(s)) for s in self.states],
                'position': self.position, 'limit': self.limit,
                'byte_limit': self.byte_limit}

    @classmethod
    def from_snapshot(cls, value):
        if not isinstance(value, dict) or set(value) != {
                'states', 'position', 'limit', 'byte_limit'}:
            raise ValueError('Contrato do histórico de texto inválido.')
        limit, byte_limit, position = (value[k] for k in ('limit', 'byte_limit', 'position'))
        if type(limit) is not int or not 2 <= limit <= 128:
            raise ValueError('Limite de edições inválido.')
        if type(byte_limit) is not int or not 1 <= byte_limit <= 1048576:
            raise ValueError('Limite de bytes do histórico inválido.')
        states = value['states']
        if not isinstance(states, list) or not 1 <= len(states) <= limit:
            raise ValueError('Quantidade de estados de texto inválida.')
        if type(position) is not int or not 0 <= position < len(states):
            raise ValueError('Posição Undo/Redo inválida.')
        states = [validated_state(s) for s in states]
        if len(states) > 2 and sum(len(s[0].encode('utf-8')) for s in states) > byte_limit:
            raise ValueError('Histórico de texto excede seu limite.')
        result = cls(states[0], limit, byte_limit)
        result.states, result.position = states, position
        return result
