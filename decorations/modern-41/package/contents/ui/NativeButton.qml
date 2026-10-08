// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.ksvg 1.0 as KSvg
import org.kde.kirigami 2.20 as Kirigami
import "Rendering.js" as Rendering

Item {
    id: control
    property string kind: "menu"
    property url artwork
    property var menuIcon: "application-menu"
    property string label: ""
    property bool available: true
    property bool activeWindow: true
    readonly property bool pressed: pointer.pressed
    readonly property bool hovered: pointer.containsMouse
    readonly property string renderedPrefix: {
        if (!available && atlas.hasElementPrefix(activeWindow ? "deactivated" : "deactivated-inactive"))
            return activeWindow ? "deactivated" : "deactivated-inactive";
        if (pressed && atlas.hasElementPrefix(activeWindow ? "pressed" : "pressed-inactive"))
            return activeWindow ? "pressed" : "pressed-inactive";
        if (hovered && atlas.hasElementPrefix(activeWindow ? "hover" : "hover-inactive"))
            return activeWindow ? "hover" : "hover-inactive";
        return !activeWindow && atlas.hasElementPrefix("inactive") ? "inactive" : "active";
    }
    readonly property bool artworkValid: kind === "menu" ? menuImage.valid : atlas.hasElementPrefix("active")
    signal activate(int mouseButton)
    Accessible.role: Accessible.Button
    Accessible.name: label

    Kirigami.Icon {
        id: menuImage
        anchors.fill: parent
        visible: control.kind === "menu"
        source: control.menuIcon
        active: control.hovered
        enabled: control.available
    }
    KSvg.FrameSvg {
        id: atlas
        imagePath: control.kind === "menu" ? "" : Rendering.localPath(control.artwork)
    }
    KSvg.FrameSvgItem {
        anchors.fill: parent
        visible: control.kind !== "menu"
        imagePath: atlas.imagePath
        prefix: control.renderedPrefix
        smooth: false
    }
    MouseArea {
        id: pointer
        anchors.fill: parent
        enabled: control.available
        hoverEnabled: true
        acceptedButtons: control.kind === "maximize" ? Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                       : control.kind === "menu" ? Qt.LeftButton | Qt.RightButton : Qt.LeftButton
        onClicked: (mouse) => control.activate(mouse.button)
    }
}
