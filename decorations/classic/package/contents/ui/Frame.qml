// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

// Fixed textures are reused by the scene graph. Resizing changes geometry only.
Item {
    id: frame
    property bool activeWindow: true
    property bool maximizedWindow: false
    readonly property bool even: Math.round(width + (maximizedWindow ? 16 : 0)) % 2 === 0
    readonly property real dx: maximizedWindow ? -8 : 0
    readonly property real dy: maximizedWindow ? -8 : 0
    readonly property real virtualWidth: width + (maximizedWindow ? 16 : 0)
    clip: true
    component Tile: Image {
        property string tile
        source: "../tiles/" + (frame.activeWindow ? "active-" : "inactive-") + tile + ".svg"
        fillMode: Image.Tile
        horizontalAlignment: Image.AlignLeft
        verticalAlignment: Image.AlignTop
        smooth: false
        antialiasing: false
        mipmap: false
    }
    Item {
        width: parent.width
        height: Math.min(parent.height, frame.maximizedWindow ? 24 : 36)
        clip: true
        Tile { tile: "topLeft"; x: frame.dx; y: frame.dy; width: 36; height: 36 }
        Tile { tile: "topRepeat"; x: 36 + frame.dx; y: frame.dy
            width: Math.max(0, frame.virtualWidth - 100); height: 32 }
        Tile { tile: frame.even ? "topRightEven" : "topRight"
            x: frame.virtualWidth - 64 + frame.dx; y: frame.dy; width: 64; height: 36 }
    }
    Item {
        y: 32
        width: parent.width
        height: Math.max(0, parent.height - 32)
        visible: !frame.maximizedWindow
        clip: true
        Tile { tile: "leftRepeat"; y: 4; width: 8; height: Math.max(0, frame.height - 72) }
        Tile { tile: frame.even ? "rightRepeatEven" : "rightRepeat"
            x: frame.width - 8; y: 4; width: 8; height: Math.max(0, frame.height - 72) }
        Tile { tile: "bottomLeft"; y: frame.height - 68; width: 36; height: 36 }
        Tile { tile: "bottomRight"; x: frame.width - 36; y: frame.height - 68; width: 36; height: 36 }
        Tile { tile: "bottomRepeat"; x: 36; y: frame.height - 40
            width: Math.max(0, frame.width - 72); height: 8 }
    }
}
