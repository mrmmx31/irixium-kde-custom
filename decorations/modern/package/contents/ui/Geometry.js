// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library

function metrics(width, maximized) {
    var frame = maximized ? 0 : 7;
    var title = 34;
    var button = 22;
    var edge = maximized ? 6 : 9;
    var gap = 6;
    var titleTop = maximized ? 4 : 7;
    var y = titleTop + 2;
    var maximizeX = width - edge - button;
    var minimizeX = maximizeX - button - gap;
    var captionX = edge + button + 12;
    return {
        width: width,
        border: frame,
        top: title,
        frame: frame,
        title: title,
        menu: {x: edge, y: y, w: button, h: button},
        minimize: {x: minimizeX, y: y, w: button, h: button},
        maximize: {x: maximizeX, y: y, w: button, h: button},
        caption: {
            x: captionX,
            y: titleTop,
            w: Math.max(0, minimizeX - 12 - captionX),
            h: 26
        }
    };
}
