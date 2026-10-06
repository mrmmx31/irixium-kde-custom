// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "Geometry.js" as Geometry

Item {
    id: surface
    property bool activeWindow: true
    property bool maximizedWindow: false
    property bool minimizeAllowed: true
    property bool maximizeAllowed: true
    property bool closeAllowed: true
    property bool menuOnPress: true
    property bool closeOnDouble: false
    property string caption: ""
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: false
    property bool titleBold: true
    readonly property var metrics: Geometry.metrics(width, maximizedWindow)
    property alias titleItem: titleRegion
    signal menuRequested(int mouseButton)
    signal minimizeRequested()
    signal maximizeRequested(int mouseButton)
    signal closeRequested()

    Rectangle {
        anchors.fill: parent
        color: surface.activeWindow ? "#c1bca7" : "#b4b4b4"
    }
    Rectangle {
        x: 0
        y: 0
        width: parent.width
        height: surface.metrics.title
        color: surface.activeWindow ? "#a59f80" : "#868686"
    }
    Rectangle {
        x: 0
        y: surface.metrics.title - 2
        width: parent.width
        height: 2
        color: surface.activeWindow ? "#5b5746" : "#515151"
    }
    Rectangle {
        x: 0
        y: surface.metrics.title
        width: parent.width
        height: 1
        color: surface.activeWindow ? "#dad7ca" : "#d2d2d2"
    }
    Rectangle {
        visible: !surface.maximizedWindow
        x: 0; y: 0; width: 1; height: parent.height
        color: surface.activeWindow ? "#5b5746" : "#515151"
    }
    Rectangle {
        visible: !surface.maximizedWindow
        x: parent.width - 1; y: 0; width: 1; height: parent.height
        color: surface.activeWindow ? "#dad7ca" : "#d2d2d2"
    }
    Rectangle {
        visible: !surface.maximizedWindow
        x: 0; y: parent.height - 1; width: parent.width; height: 1
        color: surface.activeWindow ? "#5b5746" : "#515151"
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
        x: surface.metrics.frame
        y: 0
        width: Math.max(0, surface.width - 2 * surface.metrics.frame)
        height: surface.metrics.title
    }
    ModernButton {
        id: menuButton
        objectName: "irixiumModernMenu"
        kind: "menu"
        label: "Ações da janela"
        artwork: Qt.resolvedUrl("../../assets/applications.png")
        menuOnPress: surface.menuOnPress
        closeOnDouble: surface.closeOnDouble
        x: surface.metrics.menu.x; y: surface.metrics.menu.y
        width: surface.metrics.menu.w; height: surface.metrics.menu.h
        onActivate: surface.menuRequested(mouseButton)
        onCloseRequested: surface.closeRequested()
    }
    ModernButton {
        id: minimizeButton
        objectName: "irixiumModernMinimize"
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
        kind: "maximize"
        label: surface.maximizedWindow ? "Restaurar" : "Maximizar"
        artwork: Qt.resolvedUrl("../../assets/" + (surface.maximizedWindow ? "restore.svg" : "maximize.svg"))
        available: surface.maximizeAllowed
        x: surface.metrics.maximize.x; y: surface.metrics.maximize.y
        width: surface.metrics.maximize.w; height: surface.metrics.maximize.h
        onActivate: surface.maximizeRequested(mouseButton)
    }
    ModernButton {
        id: closeButton
        objectName: "irixiumModernClose"
        kind: "close"
        label: "Fechar"
        artwork: Qt.resolvedUrl("../../assets/close.svg")
        available: surface.closeAllowed
        x: surface.metrics.close.x; y: surface.metrics.close.y
        width: surface.metrics.close.w; height: surface.metrics.close.h
        onActivate: surface.closeRequested()
    }
}
