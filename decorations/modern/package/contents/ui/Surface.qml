// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.ksvg 1.0 as KSvg
import "Rendering.js" as Rendering
import "Geometry.js" as Geometry

Item {
    id: surface
    property bool activeWindow: true
    property bool maximizedWindow: false
    property bool minimizeAllowed: true
    property bool maximizeAllowed: true
    property bool menuOnPress: false
    property bool closeOnDouble: true
    property string caption: ""
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: false
    property bool titleBold: true
    readonly property var metrics: Geometry.metrics(width, maximizedWindow)
    property alias titleItem: titleRegion
    readonly property bool artworkValid: atlasRevision >= 0 && frameAtlas.hasElementPrefix("decoration")
    readonly property string renderedFramePrefix: frameArtwork.prefix
    property int atlasRevision: 0
    Connections {
        target: frameAtlas
        function onRepaintNeeded() { surface.atlasRevision++; }
    }
    signal menuRequested(int mouseButton)
    signal minimizeRequested()
    signal maximizeRequested(int mouseButton)
    signal closeRequested()

    // Own assets; KSvg is a renderer, not a dependency on an Aurorae theme.
    KSvg.FrameSvg {
        id: frameAtlas
        imagePath: Rendering.localPath(Qt.resolvedUrl("../../assets/decoration.svg"))
    }
    KSvg.FrameSvgItem {
        id: frameArtwork
        objectName: "irixiumModernFrame"
        anchors.fill: parent
        imagePath: frameAtlas.imagePath
        prefix: {
            surface.atlasRevision;
            frameAtlas.imagePath;
            return Rendering.framePrefix(frameAtlas, surface.activeWindow, surface.maximizedWindow);
        }
        enabledBorders: surface.maximizedWindow ? KSvg.FrameSvg.NoBorder
            : KSvg.FrameSvg.TopBorder | KSvg.FrameSvg.BottomBorder
              | KSvg.FrameSvg.LeftBorder | KSvg.FrameSvg.RightBorder
        smooth: false
    }
    Text {
        objectName: "irixiumModernCaption"
        x: surface.metrics.caption.x
        y: surface.metrics.caption.y
        width: surface.metrics.caption.w
        height: surface.metrics.caption.h
        text: surface.caption
        textFormat: Text.PlainText
        color: "#000000"
        font.family: surface.titleFamily
        font.pixelSize: surface.titlePixels
        font.bold: surface.titleBold
        font.italic: surface.titleItalic
        renderType: Text.NativeRendering
        antialiasing: false
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        clip: true
    }
    Item {
        id: titleRegion
        x: surface.metrics.caption.x
        y: 0
        width: surface.metrics.caption.w
        height: surface.metrics.title
    }
    ModernButton {
        id: menuButton
        objectName: "irixiumModernMenu"
        activeWindow: surface.activeWindow
        kind: "menu"
        label: "Ações da janela"
        artwork: Qt.resolvedUrl("../../assets/applications.png")
        menuOnPress: surface.menuOnPress
        closeOnDouble: surface.closeOnDouble
        x: surface.metrics.menu.x; y: surface.metrics.menu.y
        width: surface.metrics.menu.w; height: surface.metrics.menu.h
        onActivate: (mouseButton) => surface.menuRequested(mouseButton)
        onCloseRequested: surface.closeRequested()
    }
    ModernButton {
        id: minimizeButton
        objectName: "irixiumModernMinimize"
        activeWindow: surface.activeWindow
        kind: "minimize"
        label: "Minimizar"
        artwork: Qt.resolvedUrl("../../assets/minimize.svg")
        available: surface.minimizeAllowed
        x: surface.metrics.minimize.x; y: surface.metrics.minimize.y
        width: surface.metrics.minimize.w; height: surface.metrics.minimize.h
        onActivate: surface.minimizeRequested()
    }
    ModernButton {
        id: maximizeButton
        objectName: "irixiumModernMaximize"
        activeWindow: surface.activeWindow
        kind: "maximize"
        label: surface.maximizedWindow ? "Restaurar" : "Maximizar"
        artwork: Qt.resolvedUrl("../../assets/" + (surface.maximizedWindow ? "restore.svg" : "maximize.svg"))
        available: surface.maximizeAllowed
        x: surface.metrics.maximize.x; y: surface.metrics.maximize.y
        width: surface.metrics.maximize.w; height: surface.metrics.maximize.h
        onActivate: (mouseButton) => surface.maximizeRequested(mouseButton)
    }
}
