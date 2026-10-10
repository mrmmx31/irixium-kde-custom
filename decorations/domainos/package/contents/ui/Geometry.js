// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library
// SR10.4 reference: client border 11px; title buttons 20px, inset 10px.
function metrics(width, scale, maximized) {
    var s = Math.max(1, Math.min(3, Math.round(scale || 1)));
    var w = Math.max(0, Math.round(width));
    var inset = maximized ? 0 : 10*s;
    var inner = Math.max(0, w-2*inset);
    return {
        scale:s, width:w, border:maximized ? 0 : 11*s,
        top:(maximized ? 20 : 30)*s,
        menu:{x:inset,y:inset,w:20*s,h:20*s,visible:inner >= 20*s},
        minimize:{x:w-inset-40*s,y:inset,w:20*s,h:20*s,visible:inner >= 60*s},
        maximize:{x:w-inset-20*s,y:inset,w:20*s,h:20*s,visible:inner >= 40*s},
        caption:{x:inset+20*s,y:inset,w:Math.max(0,inner-60*s),h:20*s}
    };
}
function contains(rect, x, y) {
    return !!rect.visible && x >= rect.x && y >= rect.y
        && x < rect.x+rect.w && y < rect.y+rect.h;
}
