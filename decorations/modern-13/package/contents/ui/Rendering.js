// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
.pragma library

// KSvg takes a local pathname (QString). Decode the URL once so a checkout or
// XDG directory containing spaces/non-ASCII characters works too.
function localPath(value) {
    var text = String(value);
    if (text.indexOf("file://localhost/") === 0)
        return decodeURIComponent(text.substring(16));
    if (text.indexOf("file:///") === 0)
        return decodeURIComponent(text.substring(7));
    return text;
}

function isRaster(value) {
    return /\.png$/i.test(String(value));
}

// SVGs are atlases of states, not individual icons. Never use an empty id:
// KSvg would then paint the entire atlas, reproducing the original defect.
function buttonCandidates(active, available, pressed, hovered) {
    var normal = active ? "active-center" : "inactive-center";
    if (!available)
        return active ? ["deactivated-center", normal]
                      : ["deactivated-inactive-center", "deactivated-center", normal];
    if (pressed)
        return active ? ["pressed-center", normal]
                      : ["pressed-inactive-center", "pressed-center", normal];
    if (hovered)
        return active ? ["hover-center", normal]
                      : ["hover-inactive-center", "hover-center", normal];
    return [normal, "active-center"];
}

function pickElement(svg, candidates) {
    if (svg) {
        for (var i = 0; i < candidates.length; ++i) {
            if (svg.hasElement(candidates[i]))
                return candidates[i];
        }
    }
    return "irixium-missing-state";
}

function framePrefix(svg, active, maximized) {
    var candidates = [];
    if (maximized) {
        if (!active)
            candidates.push("decoration-maximized-inactive");
        if (active)
            candidates.push("decoration-maximized");
    }
    if (!active)
        candidates.push("decoration-inactive");
    candidates.push("decoration");
    for (var i = 0; svg && i < candidates.length; ++i) {
        if (svg.hasElementPrefix(candidates[i]))
            return candidates[i];
    }
    return "irixium-missing-frame";
}
