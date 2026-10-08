// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: root
    objectName: "classicGrosview"

    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    switchWidth: -1
    switchHeight: -1
    Layout.minimumWidth: 248
    Layout.minimumHeight: 208
    Layout.preferredWidth: 280
    Layout.preferredHeight: 220
    toolTipMainText: "gr_osview"
    toolTipSubText: qsTr("CPU, memory, swap, disk and network")

    fullRepresentation: Grosview {
        Layout.minimumWidth: 248
        Layout.minimumHeight: 208
        Layout.preferredWidth: 280
        Layout.preferredHeight: 220
    }
}
