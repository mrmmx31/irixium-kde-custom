// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library
// VUE 2.01/SR10.4: resizeBorderWidth=10, frameBorderWidth=5.
// Measured client insets include the WM's one-pixel inner surround (6/11).
// Resize capability and maximize capability are independent.
function metrics(width, scale, maximized, resizeAllowed, minimizeAllowed, maximizeAllowed) {
    var s = Math.max(1, Math.min(3, Math.round(scale || 1)));
    var w = Math.max(0, Math.round(width));
    var inset = maximized ? 0 : (resizeAllowed === false ? 5 : 10)*s;
    var inner = Math.max(0, w-2*inset);
    var showMinimize = minimizeAllowed !== false;
    var showMaximize = maximizeAllowed !== false;
    var rightCount = Number(showMinimize) + Number(showMaximize);
    return {
        scale:s, width:w, inset:inset, border:maximized ? 0 : inset+s,
        top:20*s+inset,
        menu:{x:inset,y:inset,w:20*s,h:20*s,visible:inner >= 20*s},
        minimize:{x:w-inset-rightCount*20*s,y:inset,w:20*s,h:20*s,
                  visible:showMinimize && inner >= (rightCount+1)*20*s},
        maximize:{x:w-inset-20*s,y:inset,w:20*s,h:20*s,
                  visible:showMaximize && inner >= 40*s},
        caption:{x:inset+20*s,y:inset,w:Math.max(0,inner-(rightCount+1)*20*s),h:20*s}
    };
}
function contains(rect, x, y) {
    return !!rect.visible && x >= rect.x && y >= rect.y
        && x < rect.x+rect.w && y < rect.y+rect.h;
}
