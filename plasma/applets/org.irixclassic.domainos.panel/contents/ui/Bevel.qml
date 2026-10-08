// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: frame
    property color face: "#7894a7"
    property color light: "#bed0d4"
    property color dark: "#263f4d"
    property bool sunken: false
    property int thickness: 2
    property url texture
    Rectangle { anchors.fill: parent; color: frame.face; antialiasing: false }
    Image {
        anchors.fill: parent
        anchors.margins: frame.thickness
        source: frame.texture
        fillMode: Image.Tile
        smooth: false
        mipmap: false
    }
    Rectangle { x: 0; y: 0; width: parent.width; height: frame.thickness; color: frame.sunken ? frame.dark : frame.light }
    Rectangle { x: 0; y: 0; width: frame.thickness; height: parent.height; color: frame.sunken ? frame.dark : frame.light }
    Rectangle { x: 0; y: parent.height-height; width: parent.width; height: frame.thickness; color: frame.sunken ? frame.light : frame.dark }
    Rectangle { x: parent.width-width; y: 0; width: frame.thickness; height: parent.height; color: frame.sunken ? frame.light : frame.dark }
}
