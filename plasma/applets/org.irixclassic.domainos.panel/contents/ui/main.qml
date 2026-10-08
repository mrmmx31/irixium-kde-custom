// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid

PlasmoidItem {
    objectName: "domainosPanelApplet"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    switchWidth: -1
    switchHeight: -1
    Layout.minimumWidth: 971
    Layout.minimumHeight: 109
    Layout.preferredWidth: 1942
    Layout.preferredHeight: 218
    toolTipMainText: "Irix Classic DomainOS"
    toolTipSubText: qsTr("Design preview; button functions await confirmation")
    fullRepresentation: DomainOSPanel {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumWidth: 971
        Layout.minimumHeight: 109
        Layout.preferredWidth: 1942
        Layout.preferredHeight: 218
    }
}
