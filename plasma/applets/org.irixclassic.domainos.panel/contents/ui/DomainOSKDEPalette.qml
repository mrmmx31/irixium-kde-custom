// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.core as PlasmaCore

// Plasma reads KColorScheme roles separately from the QApplication palette.
// Kvantum may replace the latter while polishing its application style. Keep
// these native bindings so an ordinary KDE palette change updates our artwork.
QtObject {
    readonly property color window: PlasmaCore.Theme.backgroundColor
    readonly property color windowText: PlasmaCore.Theme.textColor
    readonly property color base: PlasmaCore.Theme.viewBackgroundColor
    readonly property color text: PlasmaCore.Theme.viewTextColor
    readonly property color button: PlasmaCore.Theme.buttonBackgroundColor
    readonly property color buttonText: PlasmaCore.Theme.buttonTextColor
    readonly property color highlight: PlasmaCore.Theme.highlightColor
    readonly property color highlightedText: PlasmaCore.Theme.highlightedTextColor
    // This public getter is KDE's InactiveText role. It is not the full
    // QPalette Disabled color group or its configured contrast effects.
    readonly property color disabledText: PlasmaCore.Theme.disabledTextColor
}
