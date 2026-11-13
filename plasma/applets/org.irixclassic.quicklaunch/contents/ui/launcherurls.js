// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-2.0-or-later
.pragma library

// Keep stored URLs unchanged. Only the native backend needs a local desktop
// file URL; Qt searches XDG_DATA_HOME and XDG_DATA_DIRS in their native order.
function resolve(url, paths) {
    const original = String(url);
    if (original.indexOf("applications:") !== 0) {
        return original;
    }

    let desktop;
    try {
        desktop = decodeURIComponent(original.substring("applications:".length));
    } catch (error) {
        return "";
    }
    if (!/\.desktop$/.test(desktop) || desktop.charAt(0) === "/"
            || desktop.indexOf("\\") !== -1 || desktop.indexOf("\0") !== -1) {
        return "";
    }
    const segments = desktop.split("/");
    if (segments.some(function (part) { return !part || part === "." || part === ".."; })) {
        return "";
    }

    return paths.locate(paths.ApplicationsLocation, desktop).toString();
}
