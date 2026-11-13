// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Layout and SVG layers follow KDE Aurorae, Martin Gräßlin, GPL-2.0-or-later.
import QtQuick
import org.kde.ksvg 1.0 as KSvg
import "Geometry.js" as Geometry
import "Rendering.js" as Rendering

Item {
    id: surface
    Settings { id: originalSettings }
    property QtObject settings: originalSettings
    property bool activeWindow: true
    property bool maximizedWindow: false
    property bool minimizeAllowed: true
    property bool maximizeAllowed: true
    property string caption: ""
    property var menuIcon: "application-menu"
    property font titleFont: Qt.font({family: "Sans Serif", pixelSize: 14, bold: true})
    readonly property var metrics: Geometry.metrics(settings, width, maximizedWindow)
    property alias titleItem: titleRegion
    property alias decorationMask: maskItem.mask
    readonly property bool supportsMask: atlas.hasElementPrefix("mask")
    readonly property bool artworkValid: atlas.hasElementPrefix("decoration")
    signal menuRequested()
    signal minimizeRequested()
    signal maximizeRequested(int mouseButton)

    KSvg.FrameSvg {
        id: atlas
        imagePath: Rendering.localPath(Qt.resolvedUrl("../../assets/decoration.svg"))
    }
    KSvg.FrameSvgItem {
        objectName: "irixiumNativeFrame"
        anchors.fill: parent
        imagePath: atlas.imagePath
        prefix: Rendering.framePrefix(atlas, surface.activeWindow, surface.maximizedWindow)
        enabledBorders: surface.maximizedWindow ? KSvg.FrameSvg.NoBorder
            : KSvg.FrameSvg.TopBorder | KSvg.FrameSvg.BottomBorder | KSvg.FrameSvg.LeftBorder | KSvg.FrameSvg.RightBorder
        smooth: false
    }
    KSvg.FrameSvgItem {
        anchors {
            fill: parent
            leftMargin: surface.metrics.paddingLeft + surface.metrics.left - margins.left
            rightMargin: surface.metrics.paddingRight + surface.metrics.right - margins.right
            topMargin: surface.metrics.paddingTop + surface.metrics.title - margins.top
            bottomMargin: surface.metrics.paddingBottom + surface.metrics.bottom - margins.bottom
        }
        visible: !surface.maximizedWindow && surface.metrics.left > fixedMargins.left
            && surface.metrics.right > fixedMargins.right && surface.metrics.title > fixedMargins.top
            && surface.metrics.bottom > fixedMargins.bottom
            && atlas.hasElementPrefix(surface.activeWindow ? "innerborder" : "innerborder-inactive")
        imagePath: atlas.imagePath
        prefix: surface.activeWindow ? "innerborder" : "innerborder-inactive"
    }
    KSvg.FrameSvgItem {
        id: maskItem
        anchors.fill: parent
        anchors.margins: 1
        imagePath: atlas.imagePath
        opacity: 0
        enabledBorders: KSvg.FrameSvg.TopBorder | KSvg.FrameSvg.BottomBorder | KSvg.FrameSvg.LeftBorder | KSvg.FrameSvg.RightBorder
    }
    Item {
        id: titleRegion
        x: surface.metrics.left
        y: surface.maximizedWindow ? 0 : surface.metrics.bottom
        width: surface.width - surface.metrics.left - surface.metrics.right
        height: surface.metrics.title
    }
    Text {
        objectName: "irixiumNativeCaption"
        x: surface.metrics.caption.x; y: surface.metrics.caption.y
        width: surface.metrics.caption.w; height: surface.metrics.caption.h
        text: surface.caption
        textFormat: Text.PlainText
        color: surface.activeWindow ? settings.activeTextColor : settings.inactiveTextColor
        font: surface.titleFont
        renderType: Text.NativeRendering
        horizontalAlignment: Text.AlignLeft
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    NativeButton {
        objectName: "irixiumNativeMenu"
        kind: "menu"; label: "Ações da janela"
        menuIcon: surface.menuIcon
        activeWindow: surface.activeWindow
        x: surface.metrics.menu.x; y: surface.metrics.menu.y
        width: surface.metrics.menu.w; height: surface.metrics.menu.h
        onActivate: surface.menuRequested()
    }
    NativeButton {
        objectName: "irixiumNativeMinimize"
        kind: "minimize"; label: "Minimizar"
        artwork: Qt.resolvedUrl("../../assets/minimize.svg")
        activeWindow: surface.activeWindow
        available: surface.minimizeAllowed
        x: surface.metrics.minimize.x; y: surface.metrics.minimize.y
        width: surface.metrics.minimize.w; height: surface.metrics.minimize.h
        onActivate: surface.minimizeRequested()
    }
    NativeButton {
        objectName: "irixiumNativeMaximize"
        kind: "maximize"; label: surface.maximizedWindow ? "Restaurar" : "Maximizar"
        artwork: Qt.resolvedUrl("../../assets/" + (surface.maximizedWindow ? "restore.svg" : "maximize.svg"))
        activeWindow: surface.activeWindow
        available: surface.maximizeAllowed
        x: surface.metrics.maximize.x; y: surface.metrics.maximize.y
        width: surface.metrics.maximize.w; height: surface.metrics.maximize.h
        onActivate: (mouseButton) => surface.maximizeRequested(mouseButton)
    }
}
