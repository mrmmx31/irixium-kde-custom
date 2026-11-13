# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared trailing native scrollbar edge; independent of GTK and colors."""

def anchor_origin(record, width, height, offset=(0,0)):
    """Native control edge, including its measured offset inside the scene cell.

    Old leading coordinates remain cell origins. A trailing coordinate denotes
    the actual control edge, not the surrounding label/container minimum.
    """
    x,y=record['x'],record['y']
    if record.get('length_anchor',0):
        if record['id']=='scroll_h':x-=width+offset[0]
        elif record['id']=='scroll_v':y-=height+offset[1]
        else:raise ValueError('Controle sem eixo de ancoragem.')
    if x<0 or y<0 or x>2048 or y>2048:
        raise ValueError('Âncora e tamanho nativo colocam o controle fora do canvas.')
    return x,y

