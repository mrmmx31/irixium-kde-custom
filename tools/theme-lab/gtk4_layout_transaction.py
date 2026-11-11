# SPDX-License-Identifier: GPL-3.0-or-later
"""A reversible layout gesture, independent of GTK event delivery.

Pointer coordinates belong to the surface, not the moving control. A move is
committed only after its event has been durably accepted by the caller.
"""
import math


def layout_modifier(modifiers):
    return bool(modifiers & 4) and not bool(modifiers & (8 | (7 << 26)))


def point(x, y):
    if not all(math.isfinite(value) for value in (x, y)):
        raise ValueError('Non-finite GTK4 pointer coordinate')
    return x, y


class LayoutTransaction:
    def __init__(self, records, place, emit):
        self.records, self.place, self.emit = records, place, emit
        self.active = None

    def begin(self, index, x, y, surface, scale):
        self.cancel()
        point(x, y)
        if not surface or not isinstance(scale, int) or scale < 1:
            raise ValueError('Invalid GTK4 gesture surface/scale')
        record = self.records[index]
        # Selection failure must not start an unreported drag.
        self.emit('select', index, {})
        self.active = {'index': index, 'pointer': (x, y),
                       'origin': (record['x'], record['y']),
                       'position': (record['x'], record['y']),
                       'surface': surface, 'scale': scale}

    def update(self, x, y, surface, scale):
        if self.active is None:
            return False
        a = self.active
        try:
            point(x, y)
            if surface != a['surface'] or scale != a['scale']:
                raise ValueError('GTK4 gesture surface/scale changed')
            position = tuple(max(0, min(2048, round(origin + cursor - start)))
                             for origin, cursor, start in
                             zip(a['origin'], (x, y), a['pointer']))
            self.place(a['index'], *position)
            a['position'] = position
            return True
        except Exception:
            self.cancel()
            raise

    def finish(self):
        if self.active is None:
            return False
        a = self.active
        if a['position'] == a['origin']:
            self.active = None
            return False
        x, y = a['position']
        try:
            self.emit('move', a['index'], {
                'x': x, 'y': y, 'coordinate_space': 'gtk_logical_px',
                'scale_factor': a['scale']})
        except Exception:
            self.cancel()
            raise
        self.records[a['index']].update(x=x, y=y)
        self.active = None
        return True

    def cancel(self):
        if self.active is not None:
            a = self.active
            self.place(a['index'], *a['origin'])
            self.active = None
