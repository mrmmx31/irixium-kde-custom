// SPDX-FileCopyrightText: 2009, 2010, 2012 Martin Gräßlin <mgraesslin@kde.org>
// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library

// Match AuroraeTheme::borders(), including the native border-size limits.
function borderSize(value, size) {
    var ranges = [[0, 0], [1, 4], [1, 4], [4, 6], [6, 8], [8, 12],
                  [12, 20], [23, 30], [36, 48]];
    var range = ranges[size] || ranges[3];
    return Math.max(range[0], Math.min(value, range[1]));
}

function metrics(settings, width, maximized) {
    var s = settings;
    var scale = s.buttonSizeFactor;
    var title = Math.max(s.titleHeight, s.buttonHeight * scale + s.buttonMarginTop);
    var top = title + (maximized ? s.titleEdgeTopMaximized + s.titleEdgeBottomMaximized
                                : s.titleEdgeTop + s.titleEdgeBottom);
    var borderLeft = maximized || s.borderSize < 2 ? 0 : borderSize(s.borderLeft, s.borderSize);
    var borderRight = maximized || s.borderSize < 2 ? 0 : borderSize(s.borderRight, s.borderSize);
    var borderBottom = maximized ? 0 : borderSize(s.borderBottom, s.borderSize);
    var paddingLeft = maximized ? 0 : s.paddingLeft;
    var paddingRight = maximized ? 0 : s.paddingRight;
    var paddingTop = maximized ? 0 : s.paddingTop;
    var menuX = maximized ? s.titleEdgeLeftMaximized : s.titleEdgeLeft + paddingLeft;
    var right = width - (maximized ? s.titleEdgeRightMaximized : s.titleEdgeRight + paddingRight);
    var buttonY = maximized ? s.titleEdgeTopMaximized + s.buttonMarginTopMaximized
                           : s.titleEdgeTop + paddingTop + s.buttonMarginTop;
    var buttonHeight = s.buttonHeight * scale;
    var menuWidth = s.buttonWidthMenu * scale;
    var minWidth = s.buttonWidthMinimize * scale;
    var maxWidth = s.buttonWidthMaximizeRestore * scale;
    var spacing = s.buttonSpacing * scale;
    var maxX = right - maxWidth;
    var minX = maxX - spacing - minWidth;
    var captionX = menuX + menuWidth + s.titleBorderLeft;
    return {
        width: width, title: top, left: borderLeft, right: borderRight, bottom: borderBottom,
        paddingLeft: paddingLeft, paddingRight: paddingRight, paddingTop: paddingTop,
        paddingBottom: maximized ? 0 : s.paddingBottom,
        menu: {x: menuX, y: buttonY, w: menuWidth, h: buttonHeight},
        minimize: {x: minX, y: buttonY, w: minWidth, h: buttonHeight},
        maximize: {x: maxX, y: buttonY, w: maxWidth, h: buttonHeight},
        caption: {x: captionX, y: maximized ? s.titleEdgeTopMaximized : s.titleEdgeTop + paddingTop,
                  w: Math.max(0, minX - s.titleBorderRight - captionX),
                  h: Math.max(s.titleHeight, buttonHeight)}
    };
}
