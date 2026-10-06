.pragma library

function metrics(width, maximized) {
    var frame = maximized ? 0 : 7;
    var title = 34;
    var button = 22;
    var y = maximized ? 6 : 9;
    return {
        width: width,
        border: frame,
        top: title,
        frame: frame,
        title: title,
        menu: {x: maximized ? 6 : 9, y: y, w: button, h: button},
        minimize: {x: width - (maximized ? 30 : 79), y: y, w: button, h: button},
        maximize: {x: width - (maximized ? 54 : 55), y: y, w: button, h: button},
        close: {x: width - (maximized ? 78 : 31), y: y, w: button, h: button},
        caption: {
            x: (maximized ? 6 : 14),
            y: 4,
            w: Math.max(0, width - (maximized ? 84 : 112)),
            h: 26
        }
    };
}
