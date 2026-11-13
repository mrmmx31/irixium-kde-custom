// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kirigami as Kirigami

// Read KDE's active scheme roles independently of Kvantum's application palette.
// Keep the scope local and leave the native control's colorGroup untouched.
// Plasma's QML API exposes disabledTextColor (InactiveText), not the complete
// QPalette Inactive/Disabled effects. Do not claim or synthesize those effects.
Item {
    id: scope
    visible: false
    property QtObject target: null
    readonly property QtObject theme: target ? target.Kirigami.Theme : null
    property QtObject colors: DomainOSKDEPalette {}
    readonly property bool tooltip: theme && theme.colorSet === Kirigami.Theme.Tooltip
    readonly property bool view: theme && theme.colorSet === Kirigami.Theme.View
    readonly property bool button: theme && theme.colorSet === Kirigami.Theme.Button
    readonly property bool selection: theme && theme.colorSet === Kirigami.Theme.Selection
    readonly property color surface: selection ? colors.highlight : button ? colors.button
        : view ? colors.base : colors.window
    readonly property color foreground: selection ? colors.highlightedText : button ? colors.buttonText
        : view ? colors.text : colors.windowText

    Binding { target: scope.theme; property: "inherit"; value: false; when: !!scope.theme }
    // No public PlasmaCore.Theme tooltip/alternate getters exist in Plasma 6.3.
    // Preserve those native attached-theme roles instead of inventing a value.
    Binding { target: scope.theme; property: "backgroundColor"; value: scope.surface; when: !!scope.theme && !scope.tooltip }
    Binding { target: scope.theme; property: "textColor"; value: scope.foreground; when: !!scope.theme && !scope.tooltip }
    Binding { target: scope.theme; property: "disabledTextColor"; value: scope.colors.disabledText; when: !!scope.theme && !scope.tooltip }
    Binding { target: scope.theme; property: "highlightColor"; value: scope.colors.highlight; when: !!scope.theme }
    Binding { target: scope.theme; property: "highlightedTextColor"; value: scope.colors.highlightedText; when: !!scope.theme }
    Binding { target: scope.theme; property: "activeBackgroundColor"; value: scope.colors.highlight; when: !!scope.theme }
    Binding { target: scope.theme; property: "activeTextColor"; value: scope.colors.highlightedText; when: !!scope.theme }
    Binding { target: scope.theme; property: "focusColor"; value: scope.colors.highlight; when: !!scope.theme }
    Binding { target: scope.theme; property: "hoverColor"; value: scope.colors.highlight; when: !!scope.theme }
}
