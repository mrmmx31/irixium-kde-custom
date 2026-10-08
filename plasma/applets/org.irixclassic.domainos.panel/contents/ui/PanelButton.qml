// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: button
    readonly property QtObject colorPalette: {
        let ancestor = parent
        while (ancestor) {
            if (ancestor.domainosPalette !== undefined) return ancestor.domainosPalette
            ancestor = ancestor.parent
        }
        return null
    }
    property string label
    property url imageSource
    property real imageWidth: 32
    property real imageHeight: imageWidth
    property int bevelThickness: 4
    property bool simpleRelief: false
    property int grooveCount: 0
    property bool selectable: false
    property bool selected: false
    property bool pressRelief: true
    property bool selectedRelief: true
    signal clicked()
    property color bevelLight: colorPalette ? colorPalette.highlight : "#c5e8e6"
    property color bevelDark: colorPalette ? colorPalette.dark : "#194b63"
    property color face: colorPalette ? colorPalette.background : "#7894a7"
    property url texture: Qt.resolvedUrl("../images/metal-weave.svg")
    readonly property bool pressed: pointer.pressed && pointer.containsMouse
    readonly property int pressOffset: pressRelief && pressed ? 2 : 0
    default property alias content: contents.data

    Accessible.role: Accessible.Button
    Accessible.name: label
    Accessible.checkable: selectable
    Accessible.checked: selected
    data: [Bevel {
        objectName: button.objectName+"Relief"
        anchors.fill: parent
        face: button.face
        texture: button.texture
        thickness: button.bevelThickness
        simpleRelief: button.simpleRelief
        grooveCount: button.grooveCount
        light: button.bevelLight
        dark: button.bevelDark
        sunken: (button.pressRelief && button.pressed) || (button.selectedRelief && button.selected)
    },
    Item {
        id: contents
        anchors.fill: parent
        anchors.leftMargin: button.pressOffset
        anchors.topMargin: button.pressOffset
        anchors.rightMargin: -button.pressOffset
        anchors.bottomMargin: -button.pressOffset
        PaletteImage {
            anchors.centerIn: parent
            width: button.imageWidth
            height: button.imageHeight
            assetSource: button.imageSource
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
        // A consumer may simulate selection; no command or device call here.
        onClicked: button.clicked()
    }]
}
