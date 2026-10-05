// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library
.import "Pixels.js" as Pixels

function palette(active) {
    return active ? ["#a59f80", "#000000", "#dad7ca", "#5b5746"]
                  : ["#808080", "#000000", "#c6c6c6", "#424242"];
}

// Runs are clipped and snapped at BOTH ends. No filtered SVGs, gradients or shadows.
function tile(ctx, rows, x, y, scale, pal, clip) {
    for (var j = 0; j < rows.length; ++j) {
        var row = rows[j];
        var top = Math.max(clip.y, Math.round((y + j) * scale));
        var bottom = Math.min(clip.y + clip.h, Math.round((y + j + 1) * scale));
        if (bottom <= top) continue;
        for (var i = 0; i < row.length;) {
            var c = row.charAt(i), end = i + 1;
            while (end < row.length && row.charAt(end) === c) ++end;
            if (c !== ".") {
                var left = Math.max(clip.x, Math.round((x + i) * scale));
                var right = Math.min(clip.x + clip.w, Math.round((x + end) * scale));
                if (right > left) {
                    ctx.fillStyle = pal[Number(c)];
                    ctx.fillRect(left, top, right - left, bottom - top);
                }
            }
            i = end;
        }
    }
}

function geometry(width, scale, maximized) {
    var s = scale, inset = maximized ? 0 : 8 * s;
    var y = maximized ? 0 : 8 * s;
    // Keep visible glyphs independent from the size of their hit areas.
    return {
        border: maximized ? 0 : 8 * s,
        top: (maximized ? 24 : 32) * s,
        menu: {x: inset, y: y, w: 26 * s, h: 24 * s},
        minimize: {x: width - inset - 50 * s, y: y, w: 26 * s, h: 24 * s},
        maximize: {x: width - inset - 24 * s, y: y, w: 24 * s, h: 24 * s},
        caption: {x: inset + 36 * s, y: y + 1 * s,
                  w: Math.max(0, width - 2 * inset - 98 * s), h: 22 * s}
    };
}

function paintFrame(ctx, width, height, scale, active, maximized) {
    if (width <= 0 || height <= 0 || scale <= 0) return;
    var pal = palette(active), t = Pixels.tiles;
    var clip = {x: 0, y: 0, w: width, h: maximized ? Math.min(height, 24 * scale) : height};
    var W = width / scale, H = height / scale;
    // The maximized title is the SAME 24-row band, without the external frame.
    // This preserves button centres and does not resurrect the old offset bug.
    var dx = maximized ? -8 : 0, dy = maximized ? -8 : 0;
    var virtualW = W + (maximized ? 16 : 0);
    var evenWidth = Math.round(virtualW) % 2 === 0;
    tile(ctx, t.topLeft, dx, dy, scale, pal, clip);
    var middle = {x: Math.max(0, (36 + dx) * scale), y: 0,
                  w: Math.max(0, (virtualW - 100) * scale), h: Math.min(height, (32 + dy) * scale)};
    for (var x = 36; x < virtualW - 64; x += 2)
        tile(ctx, t.topRepeat, x + dx, dy, scale, pal, middle);
    tile(ctx, evenWidth ? t.topRightEven : t.topRight, virtualW - 64 + dx, dy, scale, pal, clip);
    if (maximized || H <= 32) return;
    // Short windows do not let lower corners overwrite the title bar.
    var bodyClip = {x: 0, y: 32 * scale, w: width, h: Math.max(0, height - 32 * scale)};
    var cornerTop = Math.max(36, H - 36);
    for (var y = 36; y < cornerTop; y += 2) {
        tile(ctx, t.leftRepeat, 0, y, scale, pal, bodyClip);
        tile(ctx, evenWidth ? t.rightRepeatEven : t.rightRepeat, W - 8, y, scale, pal, bodyClip);
    }
    tile(ctx, t.bottomLeft, 0, H - 36, scale, pal, bodyClip);
    tile(ctx, t.bottomRight, W - 36, H - 36, scale, pal, bodyClip);
    var bottomClip = {x: 36 * scale, y: Math.max(32 * scale, height - 8 * scale),
                      w: Math.max(0, width - 72 * scale), h: 8 * scale};
    for (x = 36; x < W - 36; x += 2)
        tile(ctx, t.bottomRepeat, x, H - 8, scale, pal, bottomClip);
}

function paintButton(ctx, kind, width, height, scale, active, hovered, down, enabled) {
    var p = palette(active), s = scale;
    var clip = {x: 0, y: 0, w: width, h: height};
    // The references do not show a pressed state. Use the same four colours
    // and an inverted inset, not the glossy modern button effect.
    if (enabled && (hovered || down)) {
        var d = down ? p[3] : p[2], l = down ? p[2] : p[3];
        ctx.fillStyle = d;
        ctx.fillRect(2*s, 2*s, width-5*s, s);
        ctx.fillRect(2*s, 2*s, s, height-5*s);
        ctx.fillStyle = l;
        ctx.fillRect(3*s, height-4*s, width-6*s, s);
        ctx.fillRect(width-4*s, 3*s, s, height-7*s);
    }
    var rows = Pixels.glyphs[kind];
    if (!rows) return;
    // Relative to the cells in geometry(): exactly the reference positions.
    var gx = kind === "menu" ? 4 : (kind === "minimize" ? 10 : 5);
    var gy = kind === "maximize" ? 3 : 9;
    var shift = down && enabled ? 1 : 0;
    if (!enabled) p[1] = p[3];
    tile(ctx, rows, gx + shift, gy + shift, s, p, clip);
}
