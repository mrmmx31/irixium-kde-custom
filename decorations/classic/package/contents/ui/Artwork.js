// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library
.import "Pixels.js" as Pixels
.import "Geometry.js" as Geometry

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
    return Geometry.metrics(width, scale, maximized);
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

// Return one pixel of the SAME title artwork used by paintFrame(). No new bevel
// is layered inside the cell. The pressed effect only exchanges its light/dark
// shades, following the DepressGadget principle in CDE/Motif.
function titlePixel(frameWidth, scale, maximized, x, y) {
    var W = frameWidth / scale + (maximized ? 16 : 0);
    var xx = Math.round(x + (maximized ? 8 : 0));
    var yy = Math.round(y + (maximized ? 8 : 0));
    var t = Pixels.tiles;
    if (yy < 0 || yy >= 32 || xx < 0 || xx >= W) return ".";
    // topRight is drawn last by paintFrame; preserve that order on short windows.
    if (xx >= W - 64) {
        var tr = Math.round(W) % 2 === 0 ? t.topRightEven : t.topRight;
        var col = Math.round(xx - (W - 64));
        return tr[yy].charAt(col) || ".";
    }
    if (xx < 36) return t.topLeft[yy].charAt(xx) || ".";
    return t.topRepeat[yy].charAt((xx - 36) % 2);
}

function pressedRelief(ctx, kind, width, height, scale, active, frameWidth, maximized) {
    var g = geometry(frameWidth, scale, maximized)[kind];
    if (!g) return;
    var rows = [], w = Math.round(width / scale), h = Math.round(height / scale);
    for (var y = 0; y < h; ++y) {
        var row = "";
        for (var x = 0; x < w; ++x) {
            var pixel = titlePixel(frameWidth, scale, maximized,
                                   g.x / scale + x, g.y / scale + y);
            row += pixel === "2" ? "3" : (pixel === "3" ? "2" : ".");
        }
        rows.push(row);
    }
    tile(ctx, rows, 0, 0, scale, palette(active), {x: 0, y: 0, w: width, h: height});
}

// An explicit engraved disabled glyph. This is an explicit accessibility adaptation,
// NOT a claimed pixel-exact reconstruction of an unseen IRIX disabled state.
// The envelope/position never changes and no black outline remains.
function disabledGlyph(kind) {
    var original = Pixels.glyphs[kind];
    if (!original) return [];
    var result = [], h = original.length, w = original[0].length;
    for (var y = 0; y < h; ++y) {
        var row = "";
        for (var x = 0; x < w; ++x) {
            if (original[y].charAt(x) !== "1") row += ".";
            else row += (y === h - 1 || x === w - 1) ? "2" : "3";
        }
        result.push(row);
    }
    return result;
}

function paintButton(ctx, kind, width, height, scale, active, hovered, down,
                     enabled, frameWidth, maximized) {
    if (width <= 0 || height <= 0 || scale <= 0) return;
    var rows = enabled ? Pixels.glyphs[kind] : disabledGlyph(kind);
    if (!rows || rows.length === 0) return;
    var p = palette(active), s = scale;
    var clip = {x: 0, y: 0, w: width, h: height};
    // Hover is intentionally inert. No timers, fade, fill or glyph translation.
    if (enabled && down) {
        pressedRelief(ctx, kind, width, height, s, active,
                      Number(frameWidth) > 0 ? frameWidth : 591 * s, !!maximized);
    }
    var gx = kind === "menu" ? 4 : (kind === "minimize" ? 10 : 5);
    var gy = kind === "maximize" ? 3 : 9;
    tile(ctx, rows, gx, gy, s, p, clip);
}

// One canvas / coordinate system for the complete frame and all three symbols.
// Input elements do not own textures. A state change repaints the same layer.
function paintDecoration(ctx, width, height, scale, active, maximized, state) {
    var g = geometry(width, scale, maximized);
    paintFrame(ctx, width, height, g.scale, active, maximized);
    var names = ["menu", "minimize", "maximize"];
    for (var i = 0; i < names.length; ++i) {
        var kind = names[i], r = g[kind];
        if (!r.visible || r.y >= height) continue;
        var buttonState = state && state[kind] ? state[kind] : {};
        ctx.save();
        ctx.translate(r.x, r.y);
        paintButton(ctx, kind, r.w, Math.min(r.h, height-r.y), g.scale, active,
                    false, !!buttonState.down, buttonState.enabled !== false,
                    width, maximized);
        ctx.restore();
    }
}
