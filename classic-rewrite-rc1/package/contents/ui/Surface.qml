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
    property bool closeOnDouble: false
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
    // IRIX_CLASSIC_RESIZE_DIRECT_R1: invalidate the canvas without a QML timer.
    // requestPaint() schedules the render itself; it is not a synchronous draw.
    // Initial loading is still handled by onAvailableChanged/Component.onCompleted.
    function repaint() {
        if (art && art.available)
            art.requestPaint();
    }
    function cancelGestures() {
        if (menuInput) menuInput.cancelGesture();
        if (minimizeInput) minimizeInput.cancelGesture();
        if (maximizeInput) maximizeInput.cancelGesture();
    }
    onActiveWindowChanged: {
        if (!activeWindow) cancelGestures();
        repaint();
    }
    onMaximizedWindowChanged: { cancelGestures(); repaint(); }
    onMinimizeAllowedChanged: repaint()
    onMaximizeAllowedChanged: repaint()
    onPixelScaleChanged: { cancelGestures(); repaint(); }
    onWidthChanged: { cancelGestures(); repaint(); }
    onHeightChanged: { cancelGestures(); repaint(); }
    Canvas {
        id: art
        objectName: "irixArtwork"
        anchors.fill: parent
        antialiasing: false
        smooth: false
        renderTarget: Canvas.Image
        renderStrategy: Canvas.Cooperative
        onAvailableChanged: { if (available) requestPaint(); }
        Component.onCompleted: requestPaint()
        onPaint: {
            var ctx = getContext("2d");
            ctx.clearRect(0,0,width,height);
            Artwork.paintDecoration(ctx,width,height,surface.pixelScale,
                surface.activeWindow,surface.maximizedWindow,{
                    menu:{enabled:true,down:menuInput.down},
                    minimize:{enabled:surface.minimizeAllowed,down:minimizeInput.down},
                    maximize:{enabled:surface.maximizeAllowed,down:maximizeInput.down}
                });
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
        objectName: "irixMenu"
        kind: "menu"; label: "Menu da janela — mais ações"
        menuOnPress: surface.menuOnPress; closeOnDouble: surface.closeOnDouble
        x: surface.metrics.menu.x; y: surface.metrics.menu.y
        width: surface.metrics.menu.w; height: surface.metrics.menu.h
        visible: surface.metrics.menu.visible
        onDownChanged: surface.repaint()
        onActivate: (button) => surface.menuRequested(button)
        onCloseRequested: surface.closeRequested()
    }
    ButtonInput {
        id: minimizeInput
        objectName: "irixMinimize"
        kind: "minimize"; label: "Minimizar"
        available: surface.minimizeAllowed
        x: surface.metrics.minimize.x; y: surface.metrics.minimize.y
        width: surface.metrics.minimize.w; height: surface.metrics.minimize.h
        visible: surface.metrics.minimize.visible
        onDownChanged: surface.repaint()
        onActivate: surface.minimizeRequested()
    }
    ButtonInput {
        id: maximizeInput
        objectName: "irixMaximize"
        kind: "maximize"; label: surface.maximizedWindow ? "Restaurar" : "Maximizar"
        available: surface.maximizeAllowed
        x: surface.metrics.maximize.x; y: surface.metrics.maximize.y
        width: surface.metrics.maximize.w; height: surface.metrics.maximize.h
        visible: surface.metrics.maximize.visible
        onDownChanged: surface.repaint()
        onActivate: (button) => surface.maximizeRequested(button)
    }
}
