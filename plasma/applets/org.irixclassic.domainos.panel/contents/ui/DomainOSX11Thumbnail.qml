// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import org.kde.plasma.core as PlasmaCore

// The same live XComposite provider used by Plasma's Task Manager. It reports
// failure itself; there is no screenshot cache, polling or synthetic preview.
PlasmaCore.WindowThumbnail {
    id: thumbnail
    property var windowId: 0
    readonly property bool available: thumbnailAvailable
    winId: Number(windowId)
}
