// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "Painter.js" as Painter
Item {
    id: control
    property string kind: "menu"
    property int pixelScale: 1
    property bool activeWindow: true
    property bool actionEnabled: true
    property string accessibleLabel: ""
    readonly property bool hovered: area.containsMouse
    readonly property bool down: (area.pressed && area.containsMouse) || flash.running
    signal activated(int mouseButton)
    signal doubleActivated(int mouseButton)
    Accessible.role: Accessible.Button
    Accessible.name: accessibleLabel
    Accessible.onPressAction: { if (actionEnabled) activated(Qt.LeftButton) }
    Canvas {
        id: art
        anchors.fill: parent
        antialiasing: false
        smooth: false
        renderTarget: Canvas.Image
        onPaint: {
            var ctx = getContext("2d");
            ctx.clearRect(0, 0, width, height);
            Painter.paintButton(ctx, control.kind, width, height, control.pixelScale,
                                control.activeWindow, control.hovered, control.down,
                                control.actionEnabled);
        }
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }
    onHoveredChanged: art.requestPaint()
    onDownChanged: art.requestPaint()
    onActiveWindowChanged: art.requestPaint()
    onActionEnabledChanged: art.requestPaint()
    onKindChanged: art.requestPaint()
    onPixelScaleChanged: art.requestPaint()
    Timer { id: flash; interval: 90; repeat: false }
    MouseArea {
        id: area
        anchors.fill: parent
        enabled: control.actionEnabled
        hoverEnabled: true
        acceptedButtons: control.kind === "maximize"
            ? Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
            : (control.kind === "menu" ? Qt.LeftButton | Qt.RightButton : Qt.LeftButton)
        onPressed: flash.restart()
        onCanceled: flash.stop()
        onExited: flash.stop()
        onClicked: (mouse) => control.activated(mouse.button)
        onDoubleClicked: (mouse) => control.doubleActivated(mouse.button)
    }
}
