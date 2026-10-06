// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library
// One source of dimensions for painting, input, title layout and menu anchoring.
function metrics(width, scale, maximized) {
    var s = Math.max(1, Math.min(3, Math.round(scale || 1)));
    var w = Math.max(0, Math.round(width));
    var edge = maximized ? 0 : 8 * s, y = maximized ? 0 : 8 * s;
    var inner = w - 2 * edge;
    return {
        scale: s, width: w, border: edge, top: (maximized ? 24 : 32) * s,
        menu: {x: edge, y: y, w: 26*s, h: 24*s, visible: inner >= 26*s},
        minimize: {x: w-edge-50*s, y: y, w: 26*s, h: 24*s, visible: inner >= 76*s},
        maximize: {x: w-edge-24*s, y: y, w: 24*s, h: 24*s, visible: inner >= 50*s},
        caption: {x: edge+36*s, y: y+s, w: Math.max(0,w-2*edge-98*s), h: 22*s}
    };
}
function contains(rect, x, y) {
    return !!rect.visible && x >= rect.x && y >= rect.y
        && x < rect.x+rect.w && y < rect.y+rect.h;
}
