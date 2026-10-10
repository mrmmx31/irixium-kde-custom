#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Share Classic GTK2's native STEPPER recipe without changing standalone art.

The pixmap engine combines a scrollbar box and arrow through its native
STEPPER paint function. The static KDE wrapper and runtime palette renderer
both reuse the original eighteen-pixel artwork with its fixed bevel and glyph.
Generic spin/combobox ARROW entries and every widget metric remain unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
from typing import Callable

FORMAT = 1
STATES = {'NORMAL': 'normal', 'PRELIGHT': 'normal', 'ACTIVE': 'pressed',
          'SELECTED': 'toggled', 'INSENSITIVE': 'disabled'}
DIRECTIONS = ('up', 'down', 'left', 'right')


@dataclass(frozen=True)
class ScrollbarRecipe:
    text: str
    assets: dict[str, bytes]
    source_assets: dict[str, bytes]
    manifest: dict


def adapt_scrollbars(text: str, read_asset: Callable[[str], bytes]) -> ScrollbarRecipe:
    """Return twenty own STEPPER rules and their existing source PNG closure.

    This function never writes. ``read_asset`` receives only the sixteen known
    stepper basenames, never a path from arbitrary RC text. Callers include the
    returned source assets and recipe manifest in their final RC/PNG cache
    identity; ``assets`` is empty because no new glyph/artwork is created.
    """
    from PIL import Image
    if 'style "irixclassic-default"' not in text or 'engine "pixmap"' not in text:
        raise ValueError('Expected original IrixClassic pixmap RC')
    if 'function = STEPPER' in text:
        raise ValueError('Classic scrollbar recipe was already applied')
    markers = {state: '    image { function = ARROW  state = '+state+'  arrow_direction = UP'
               for state in STATES}
    if any(text.count(marker) != 1 for marker in markers.values()):
        raise ValueError('Unrecognized Classic generic arrow entries')
    source_assets = {}
    for state in sorted(set(STATES.values())):
        for direction in DIRECTIONS:
            source = f'stepper-{direction}-{state}.png'
            raw = read_asset(source)
            if not isinstance(raw, bytes) or len(raw) > 256 * 1024:
                raise ValueError('Classic stepper reader must return bounded PNG bytes')
            with Image.open(io.BytesIO(raw)) as image:
                if image.format != 'PNG' or image.size != (18, 18):
                    raise ValueError('Classic stepper must be an eighteen-pixel PNG')
                image.load()
            source_assets[source] = raw
    adapted = text
    for state, source_state in STATES.items():
        entries = []
        for detail, directions in (('hscrollbar', ('left', 'right')),
                                   ('vscrollbar', ('up', 'down'))):
            for direction in directions:
                asset = f'stepper-{direction}-{source_state}.png'
                entries.append('    image { function = STEPPER  state = '+state+
                               '  detail = "'+detail+'"  arrow_direction = '+direction.upper()+
                               '  file = "../common/assets/'+asset+'"  stretch = TRUE }')
        adapted = adapted.replace(markers[state], '\n'.join(entries)+'\n'+markers[state])
    manifest = {'format': FORMAT, 'native_recipe': 'pixmap-STEPPER',
                'source_assets': {name: hashlib.sha256(raw).hexdigest()
                                  for name, raw in source_assets.items()},
                'stepper_size': [18, 18], 'specific_stepper_entries': 20,
                'painting': 'stretch source 18px to native 18px box; avoid window-anchored tiling',
                'limits': ['native pixmap engine reconstructs the GTK2 GtkRange button box',
                           'no change to original standalone or generic spin arrows']}
    return ScrollbarRecipe(adapted, {}, source_assets, manifest)
