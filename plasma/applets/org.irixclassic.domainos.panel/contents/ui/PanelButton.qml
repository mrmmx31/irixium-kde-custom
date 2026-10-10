// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.core as PlasmaCore

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
    readonly property bool hintsEnabled: {
        let ancestor=parent
        while (ancestor) {
            if (ancestor.domainosBarHintsEnabled !== undefined) return ancestor.domainosBarHintsEnabled
            ancestor=ancestor.parent
        }
        return false
    }
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
    activeFocusOnTab: true
    property int pressedKey: 0
    signal clicked()
    signal pointerPressed()
    signal pointerCancelled()
    property color bevelLight: colorPalette ? colorPalette.highlight : "#c5e8e6"
    property color bevelDark: colorPalette ? colorPalette.dark : "#194b63"
    property color face: colorPalette ? colorPalette.background : "#7894a7"
    property url texture: Qt.resolvedUrl("../images/metal-weave.svg")
    readonly property bool pressed: (pointer.pressed && pointer.containsMouse) || pressedKey !== 0
    readonly property int pressOffset: pressRelief && pressed ? 2 : 0
    default property alias content: contents.data

    Accessible.role: Accessible.Button
    Accessible.name: label
    Accessible.checkable: selectable
    Accessible.checked: selected
    Accessible.onPressAction: { if (button.enabled) button.clicked() }
    Keys.onPressed: event => {
        if ([Qt.Key_Space,Qt.Key_Return,Qt.Key_Enter].indexOf(event.key)<0) return
        event.accepted=true
        if (!event.isAutoRepeat && !pressedKey) { pressedKey=event.key; pointerPressed() }
    }
    Keys.onReleased: event => {
        if (event.key!==pressedKey) return
        event.accepted=true
        if (!event.isAutoRepeat) { pressedKey=0; clicked() }
    }
    onActiveFocusChanged: { if (!activeFocus && pressedKey) { pressedKey=0; pointerCancelled() } }
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
    Rectangle {
        anchors.fill: parent
        anchors.margins: Math.max(1, button.bevelThickness)
        visible: button.activeFocus
        color: "transparent"
        border.width: 1
        border.color: button.colorPalette ? button.colorPalette.focus : "#dddd28"
    },
    MouseArea {
        id: pointer
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        preventStealing: false
        // A consumer may simulate selection; no command or device call here.
        onPressed: button.pointerPressed()
        onReleased: { if (!containsMouse) button.pointerCancelled() }
        onCanceled: button.pointerCancelled()
        onClicked: button.clicked()
    },
    PlasmaCore.ToolTipArea {
        objectName:button.objectName+"Hint"
        anchors.fill:parent
        active:button.hintsEnabled && button.label.length>0
        mainText:button.label
        location:PlasmaCore.Types.BottomEdge
    }]
}
