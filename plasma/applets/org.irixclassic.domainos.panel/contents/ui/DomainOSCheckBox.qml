// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.components as PlasmaComponents
import org.kde.kirigami as Kirigami

// Keep Qt's checkbox input/state API while painting this panel's indicator
// with the native Plasma SVG and the selected KDE button colors.
PlasmaComponents.CheckBox {
    id: checkbox
    Kirigami.Theme.colorSet: Kirigami.Theme.Button
    DomainOSControlPalette { target: checkbox }
}
