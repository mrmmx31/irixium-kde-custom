// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: button
    property string label
    property url imageSource
    property real imageWidth: 32
    property real imageHeight: imageWidth
    property color face: "#7894a7"
    property url texture
    readonly property bool pressed: pointer.pressed && pointer.containsMouse
    readonly property int pressOffset: pressed ? 2 : 0
    default property alias content: contents.data

    Accessible.role: Accessible.Button
    Accessible.name: label
    data: [Bevel {
        anchors.fill: parent
        face: button.face
        texture: button.texture
        sunken: button.pressed
    },
    Item {
        id: contents
        anchors.fill: parent
        anchors.leftMargin: button.pressOffset
        anchors.topMargin: button.pressOffset
        anchors.rightMargin: -button.pressOffset
        anchors.bottomMargin: -button.pressOffset
        Image {
            anchors.centerIn: parent
            width: button.imageWidth
            height: button.imageHeight
            source: button.imageSource
            visible: source.toString().length > 0
            smooth: false
            mipmap: false
            fillMode: Image.PreserveAspectFit
        }
    },
    MouseArea {
        id: pointer
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        preventStealing: false
        // Visual feedback only. No clicked action, command, timer or device call.
    }]
}
