// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "Geometry.js" as Geometry
import "Artwork.js" as Artwork
Item {
    id: surface
    property bool activeWindow: true
    property bool maximizedWindow: false
    property bool minimizeAllowed: true
    property bool maximizeAllowed: true
    property bool menuOnPress: true
    property bool closeOnDouble: true
    property string caption: ""
    property int pixelScale: 1
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: true
    property bool titleBold: true
    readonly property var metrics: Geometry.metrics(width,pixelScale,maximizedWindow)
    property alias titleItem: titleRegion
    signal menuRequested(int mouseButton)
    signal closeRequested()
    signal minimizeRequested()
    signal maximizeRequested(int mouseButton)
    clip: true
    function cancelGestures() {
        if (menuInput) menuInput.cancelGesture();
        if (minimizeInput) minimizeInput.cancelGesture();
        if (maximizeInput) maximizeInput.cancelGesture();
    }
    // Focus only changes artwork. Preserve the menu's first click so a native
    // double-click can close an inactive window without an activation step.
    onMaximizedWindowChanged: cancelGestures()
    onPixelScaleChanged: cancelGestures()
    onWidthChanged: cancelGestures()
    onHeightChanged: cancelGestures()
    Frame {
        width: surface.width / surface.metrics.scale
        height: surface.height / surface.metrics.scale
        scale: surface.metrics.scale
        transformOrigin: Item.TopLeft
        activeWindow: surface.activeWindow
        maximizedWindow: surface.maximizedWindow
    }
    component Glyph: Canvas {
        property string kind
        property bool down: false
        property bool allowed: true
        readonly property bool activeWindow: surface.activeWindow
        readonly property int pixelScale: surface.metrics.scale
        readonly property bool maximizedWindow: surface.maximizedWindow
        // Only the pressed relief depends on the frame width/parity.
        readonly property real frameWidth: down ? surface.width : 0
        anchors.fill: parent
        antialiasing: false
        smooth: false
        onDownChanged: requestPaint()
        onAllowedChanged: requestPaint()
        onActiveWindowChanged: requestPaint()
        onPixelScaleChanged: requestPaint()
        onMaximizedWindowChanged: requestPaint()
        onFrameWidthChanged: requestPaint()
        onAvailableChanged: { if (available) requestPaint(); }
        onPaint: {
            var ctx = getContext("2d");
            ctx.clearRect(0, 0, width, height);
            Artwork.paintButton(ctx, kind, width, height, pixelScale,
                activeWindow, false, down, allowed, frameWidth, maximizedWindow);
        }
    }
    Item {
        id: titleRegion
        x: surface.metrics.border
        y: surface.maximizedWindow ? 0 : 8*surface.metrics.scale
        width: Math.max(0,surface.width-2*x)
        height: 24*surface.metrics.scale
        // Deliberately empty: KWin's title hit testing uses this geometry.
        // Buttons consume input separately. No gesture is synthesized for the title.
    }
    Text {
        objectName: "irixCaption"
        x: surface.metrics.caption.x; y: surface.metrics.caption.y
        width: surface.metrics.caption.w; height: surface.metrics.caption.h
        text: surface.caption
        textFormat: Text.PlainText
        color: "#000000"
        font.family: surface.titleFamily
        font.pixelSize: surface.titlePixels*surface.metrics.scale
        font.bold: surface.titleBold; font.italic: surface.titleItalic
        renderType: Text.NativeRendering
        antialiasing: false
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        clip: true
    }
    ButtonInput {
        id: menuInput
        Glyph { kind: "menu"; down: menuInput.down; allowed: menuInput.available }
        objectName: "irixMenu"
        kind: "menu"; label: "Menu da janela — mais ações"
        menuOnPress: surface.menuOnPress; closeOnDouble: surface.closeOnDouble
        x: surface.metrics.menu.x; y: surface.metrics.menu.y
        width: surface.metrics.menu.w; height: surface.metrics.menu.h
        visible: surface.metrics.menu.visible

        onActivate: (button) => surface.menuRequested(button)
        onCloseRequested: surface.closeRequested()
    }
    ButtonInput {
        id: minimizeInput
        Glyph { kind: "minimize"; down: minimizeInput.down; allowed: minimizeInput.available }
        objectName: "irixMinimize"
        kind: "minimize"; label: "Minimizar"
        available: surface.minimizeAllowed
        x: surface.metrics.minimize.x; y: surface.metrics.minimize.y
        width: surface.metrics.minimize.w; height: surface.metrics.minimize.h
        visible: surface.metrics.minimize.visible

        onActivate: surface.minimizeRequested()
    }
    ButtonInput {
        id: maximizeInput
        Glyph { kind: "maximize"; down: maximizeInput.down; allowed: maximizeInput.available }
        objectName: "irixMaximize"
        kind: "maximize"; label: surface.maximizedWindow ? "Restaurar" : "Maximizar"
        available: surface.maximizeAllowed
        x: surface.metrics.maximize.x; y: surface.metrics.maximize.y
        width: surface.metrics.maximize.w; height: surface.metrics.maximize.h
        visible: surface.metrics.maximize.visible

        onActivate: (button) => surface.maximizeRequested(button)
    }
}
