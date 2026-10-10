// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: tile
    required property string desktopId
    required property string desktopName
    required property var windowModel
    property size virtualSize: Qt.size(1, 1)
    property bool selected: false
    // Keep the identity of a gesture even if KWin reorders the model while
    // the pointer is held. A cancelled gesture must not target a replacement.
    property string pressedDesktopId: ""
    readonly property QtObject colorPalette: {
        let ancestor = parent
        while (ancestor) {
            if (ancestor.domainosPalette !== undefined) return ancestor.domainosPalette
            ancestor = ancestor.parent
        }
        return null
    }
    readonly property bool lit: selected || button.pressed
    readonly property color lampColor: button.pressed ? colorPalette.pagerPressedLight : colorPalette.pagerLight
    signal activated(string desktopId)
    signal windowActivated(string desktopId, var identity)

    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: desktopName
    Accessible.checkable: true
    Accessible.checked: selected
    Keys.onPressed: event => {
        if ([Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select].indexOf(event.key) >= 0) {
            activated(desktopId)
            event.accepted = true
        }
    }
    PanelButton {
        id: button
        objectName: "domainosNativeWorkspace_" + tile.desktopId
        anchors.fill: parent
        label: tile.desktopName
        selectable: true
        selected: tile.selected
        selectedRelief: false
        pressRelief: !tile.selected
        face: colorPalette.recessed
        onPointerPressed: tile.pressedDesktopId = tile.desktopId
        onPointerCancelled: tile.pressedDesktopId = ""
        onClicked: {
            tile.forceActiveFocus()
            const id = tile.pressedDesktopId
            tile.pressedDesktopId = ""
            if (id.length) tile.activated(id)
        }
    }
        // Keep the geometry's input above the card's MouseArea. Merely adding
        // a child under PanelButton.content would leave its whole-card pointer
        // on top and turn every window click into a desktop-only activation.
        Item {
            x: 6 + button.pressOffset; y: 6 + button.pressOffset
            width: tile.width - 12; height: tile.height - 12
            z: 2
            Rectangle {
                x: 0; y: 0; width: parent.width; height: 30
                color: colorPalette.background
                border.width: 2; border.color: colorPalette.dark
                Rectangle {
                    objectName: "domainosNativeWorkspaceMarker_" + tile.desktopId
                    x: 7; y: 7; width: 11; height: 16
                    color: tile.lit ? tile.lampColor : colorPalette.recessed
                    border.color: colorPalette.dark; border.width: 2
                }
                Text {
                    x: 26; y: 1; width: parent.width - x - 2; height: 28
                    text: tile.desktopName
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    font.family: "Nimbus Sans"; font.pixelSize: 16
                    color: colorPalette.text
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.NativeRendering
                }
            }
            Rectangle {
                id: map
                objectName: "domainosNativeWorkspaceMap_" + tile.desktopId
                x: 0; y: 32; width: parent.width; height: parent.height - 32
                clip: true
                color: colorPalette.dark
                border.width: 2; border.color: colorPalette.highlight
                readonly property real widthRatio: Math.max(0, width - 4) / Math.max(1, tile.virtualSize.width)
                readonly property real heightRatio: Math.max(0, height - 4) / Math.max(1, tile.virtualSize.height)
                Repeater {
                    model: tile.windowModel
                    delegate: Rectangle {
                        id: windowRectangle
                        required property int index
                        required property var model
                        objectName: "domainosNativeWindow_" + tile.desktopId + "_" + index
                        readonly property rect windowGeometry: model.Geometry
                        readonly property bool minimized: model.IsMinimized
                        readonly property bool activeWindow: model.IsActive
                        readonly property bool onAllDesktops: model.IsOnAllVirtualDesktops
                        readonly property string windowTitle: model.display
                        readonly property var nativeWindowIds: Array.from(model.WinIdList || [])
                        readonly property int nativePid: Number(model.AppPid || 0)
                        property var pressedIdentity: null
                        property string pressedDesktop: ""
                        property int pressedKey: 0
                        function captureIdentity() {
                            return {windowIds:nativeWindowIds.slice(),pid:nativePid}
                        }
                        function cancelActivation() {
                            pressedIdentity=null; pressedDesktop=""; pressedKey=0
                        }
                        function activateCapturedWindow() {
                            const identity=pressedIdentity, desktop=pressedDesktop
                            cancelActivation()
                            if (identity && desktop.length) tile.windowActivated(desktop,identity)
                        }
                        x: 2 + Math.round(windowGeometry.x * map.widthRatio)
                        y: 2 + Math.round(windowGeometry.y * map.heightRatio)
                        width: Math.max(2, Math.round(windowGeometry.width * map.widthRatio))
                        height: Math.max(2, Math.round(windowGeometry.height * map.heightRatio))
                        z: 1 + model.StackingOrder
                        visible: windowGeometry.width > 0 && windowGeometry.height > 0
                        // The last real geometry remains an outline when minimized.
                        // No WindowThumbnail, screenshot, or drag handler is used.
                        color: minimized ? "transparent" : activeWindow ? colorPalette.blue : colorPalette.label
                        border.width: 2
                        border.color: minimized ? colorPalette.shadow : colorPalette.highlight
                        antialiasing: false
                        activeFocusOnTab: true
                        Accessible.role: Accessible.Button
                        Accessible.name: windowTitle
                        Accessible.description: qsTr("Ativar esta janela")
                        Accessible.onPressAction: tile.windowActivated(tile.desktopId,captureIdentity())
                        Keys.onPressed: event => {
                            if ([Qt.Key_Space,Qt.Key_Return,Qt.Key_Enter].indexOf(event.key)<0) return
                            event.accepted=true
                            if (!event.isAutoRepeat && !pressedKey) {
                                pressedKey=event.key; pressedIdentity=captureIdentity(); pressedDesktop=tile.desktopId
                            }
                        }
                        Keys.onReleased: event => {
                            if (event.key!==pressedKey) return
                            event.accepted=true
                            if (!event.isAutoRepeat) activateCapturedWindow()
                        }
                        onActiveFocusChanged: if (!activeFocus && pressedKey) cancelActivation()
                        MouseArea {
                            objectName: windowRectangle.objectName+"Pointer"
                            anchors.fill: parent
                            acceptedButtons: Qt.LeftButton
                            onPressed: {
                                windowRectangle.forceActiveFocus()
                                windowRectangle.pressedIdentity=windowRectangle.captureIdentity()
                                windowRectangle.pressedDesktop=tile.desktopId
                            }
                            onCanceled: windowRectangle.cancelActivation()
                            onReleased: if (!containsMouse) windowRectangle.cancelActivation()
                            onClicked: windowRectangle.activateCapturedWindow()
                        }
                    }
                }
            }
        }
    Rectangle {
        objectName: "domainosNativeWorkspaceSelection_" + tile.desktopId
        anchors.fill: parent
        color: "transparent"
        visible: tile.lit
        border.width: 3; border.color: tile.lampColor
    }
}
