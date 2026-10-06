// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kwin.decoration

Item {
    id: control
    property string kind: "menu"
    property url artwork
    property string label: ""
    property bool available: true
    property bool menuOnPress: true
    property bool closeOnDouble: false
    property bool pressed: false
    property bool menuSent: false
    signal activate(int mouseButton)
    signal closeRequested()

    Accessible.role: Accessible.Button
    Accessible.name: control.label
    Accessible.description: control.available ? "" : "Indisponível para esta janela"

    Image {
        anchors.fill: parent
        source: control.artwork
        fillMode: Image.Stretch
        smooth: false
        opacity: control.available ? (control.pressed ? 0.72 : 1.0) : 0.45
    }
    Rectangle {
        anchors.fill: parent
        visible: control.pressed
        color: "#403d31"
        opacity: 0.22
    }
    Timer {
        id: menuTimer
        interval: Math.max(1, Qt.styleHints.mouseDoubleClickInterval)
        repeat: false
        onTriggered: {
            if (control.kind === "menu" && control.closeOnDouble && !control.menuSent) {
                control.menuSent = true;
                control.activate(Qt.LeftButton);
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        enabled: control.available
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: (mouse) => {
            control.pressed = true;
            control.menuSent = false;
            if (control.kind === "menu" && control.menuOnPress && !control.closeOnDouble) {
                control.menuSent = true;
                control.activate(mouse.button);
            } else if (control.kind === "menu" && control.closeOnDouble
                       && mouse.button === Qt.LeftButton) {
                menuTimer.start();
            } else if (control.kind === "menu" && mouse.button === Qt.RightButton) {
                control.menuSent = true;
                control.activate(mouse.button);
            }
        }
        onReleased: control.pressed = false
        onCanceled: {
            control.pressed = false;
            control.menuSent = false;
            menuTimer.stop();
        }
        onClicked: (mouse) => {
            if (control.kind !== "menu" || (!control.menuSent && !control.closeOnDouble))
                control.activate(mouse.button);
            control.menuSent = false;
        }
        onDoubleClicked: (mouse) => {
            if (control.kind === "menu" && control.closeOnDouble && mouse.button === Qt.LeftButton) {
                menuTimer.stop();
                control.closeRequested();
            }
        }
    }
}
