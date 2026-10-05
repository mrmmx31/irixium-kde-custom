// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "Painter.js" as Painter
Item {
    id: surface
    property bool activeWindow: true
    property bool maximizedWindow: false
    property bool minimizeAllowed: true
    property bool maximizeAllowed: true
    property string caption: ""
    property int pixelScale: 1
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: true
    property bool titleBold: true
    readonly property var metrics: Painter.geometry(width, pixelScale, maximizedWindow)
    property alias titleItem: titleRow
    signal menuActivated(int mouseButton)
    signal menuDoubleActivated(int mouseButton)
    signal minimizeActivated()
    signal maximizeActivated(int mouseButton)
    clip: true
    Canvas {
        id: frame
        anchors.fill: parent
        antialiasing: false
        smooth: false
        renderTarget: Canvas.Image
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d");
            ctx.clearRect(0, 0, width, height);
            Painter.paintFrame(ctx, width, height, surface.pixelScale,
                               surface.activeWindow, surface.maximizedWindow);
        }
    }
    onActiveWindowChanged: frame.requestPaint()
    onMaximizedWindowChanged: frame.requestPaint()
    onPixelScaleChanged: frame.requestPaint()
    Item {
        id: titleRow
        x: surface.metrics.border
        y: surface.maximizedWindow ? 0 : 8 * surface.pixelScale
        width: Math.max(0, surface.width - 2 * x)
        height: 24 * surface.pixelScale
        // No MouseArea over the title: KWin keeps its move/resize/double-click policy.
    }
    Text {
        x: surface.metrics.caption.x
        y: surface.metrics.caption.y
        width: surface.metrics.caption.w
        height: surface.metrics.caption.h
        text: surface.caption
        textFormat: Text.PlainText
        color: "#000000"
        font.family: surface.titleFamily
        font.pixelSize: surface.titlePixels * surface.pixelScale
        font.italic: surface.titleItalic
        font.bold: surface.titleBold
        renderType: Text.NativeRendering
        antialiasing: false
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        clip: true
    }
    ClassicButton {
        kind: "menu"; accessibleLabel: "Menu da janela — mais ações"
        pixelScale: surface.pixelScale; activeWindow: surface.activeWindow
        x: surface.metrics.menu.x; y: surface.metrics.menu.y
        width: surface.metrics.menu.w; height: surface.metrics.menu.h
        onActivated: (mouseButton) => surface.menuActivated(mouseButton)
        onDoubleActivated: (mouseButton) => surface.menuDoubleActivated(mouseButton)
    }
    ClassicButton {
        kind: "minimize"; accessibleLabel: "Minimizar"
        pixelScale: surface.pixelScale; activeWindow: surface.activeWindow
        actionEnabled: surface.minimizeAllowed
        visible: surface.width >= 90 * surface.pixelScale
        x: surface.metrics.minimize.x; y: surface.metrics.minimize.y
        width: surface.metrics.minimize.w; height: surface.metrics.minimize.h
        onActivated: surface.minimizeActivated()
    }
    ClassicButton {
        kind: "maximize"
        accessibleLabel: surface.maximizedWindow ? "Restaurar" : "Maximizar"
        pixelScale: surface.pixelScale; activeWindow: surface.activeWindow
        actionEnabled: surface.maximizeAllowed
        visible: surface.width >= 66 * surface.pixelScale
        x: surface.metrics.maximize.x; y: surface.metrics.maximize.y
        width: surface.metrics.maximize.w; height: surface.metrics.maximize.h
        onActivated: (mouseButton) => surface.maximizeActivated(mouseButton)
        // The historical large-square glyph remains in the maximized state.
    }
}
