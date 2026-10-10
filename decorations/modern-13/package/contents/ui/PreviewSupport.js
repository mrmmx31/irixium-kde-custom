// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library

// KWin 6.3.6 gives an Aurorae preview a PreviewItem visual parent, exposing
// decoration, windowColor and drawBackground. Real offscreen content items do
// not have this contract. Identity matters: never recognize a different preview.
function isPreviewHost(host, expectedDecoration) {
    return host !== null && host !== undefined
        && expectedDecoration !== null && expectedDecoration !== undefined
        && typeof host.drawBackground === "boolean"
        && host.windowColor !== null && host.windowColor !== undefined
        && host.decoration === expectedDecoration;
}

function needsFill(host, expectedDecoration) {
    // If a future host paints its own client background, avoid painting it twice.
    return isPreviewHost(host, expectedDecoration) && !host.drawBackground;
}

function clientRect(metrics, height, shaded) {
    if (!metrics) return {x: 0, y: 0, w: 0, h: 0};
    // Use Surface's shared geometry, not another set of border constants.
    return {
        x: metrics.left + metrics.paddingLeft,
        y: metrics.title + metrics.paddingTop,
        w: Math.max(0, metrics.width - metrics.left - metrics.right - metrics.paddingLeft - metrics.paddingRight),
        h: shaded ? 0 : Math.max(0, height - metrics.title - metrics.paddingTop - metrics.bottom - metrics.paddingBottom)
    };
}
