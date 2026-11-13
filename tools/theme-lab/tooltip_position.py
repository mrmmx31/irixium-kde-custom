# SPDX-License-Identifier: GPL-3.0-or-later
"""Geometry-only placement outside the described control; no toolkit/palette."""


def outside_control(control, size, monitor, gap=6):
    bx, by, bw, bh = control
    tw, th = size
    mx, my, mw, mh = monitor
    if min(bw, bh, tw, th, mw, mh) <= 0 or tw > mw or th > mh:
        return None
    x = max(mx, min(bx + (bw - tw) // 2, mx + mw - tw))
    y = max(my, min(by + (bh - th) // 2, my + mh - th))
    candidates = ((x, by + bh + gap), (x, by - th - gap),
                  (bx + bw + gap, y), (bx - tw - gap, y))
    for tx, ty in candidates:
        if (mx <= tx and my <= ty and tx + tw <= mx + mw and ty + th <= my + mh
                and (tx + tw <= bx or bx + bw <= tx or ty + th <= by or by + bh <= ty)):
            return tx, ty
    return None
