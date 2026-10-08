// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: frame
    property color face: "#7894a7"
    property color light: "#bed0d4"
    property color dark: "#263f4d"
    property bool sunken: false
    property int thickness: 4
    property url texture
    // Four solid one-pixel bands, matching the native Style's compound relief.
    readonly property var raisedTop: [dark, light, "#405c6c", "#a2d0e7"]
    readonly property var raisedBottom: [dark, "#6a889a", "#a2d0e7", "#405c6c"]
    function edgeColor(layer, upper) {
        if (thickness === 1)
            return (upper !== sunken) ? light : dark
        const colors = (upper !== sunken) ? raisedTop : raisedBottom
        return colors[Math.min(layer, colors.length-1)]
    }
    Rectangle { anchors.fill: parent; color: frame.face; antialiasing: false }
    Image {
        anchors.fill: parent
        anchors.margins: frame.thickness
        source: frame.texture
        fillMode: Image.Tile
        smooth: false
        mipmap: false
    }
    Repeater {
        model: Math.max(1, frame.thickness)
        delegate: Item {
            required property int index
            anchors.fill: parent
            Rectangle { x: index; y: index; width: frame.width-2*index; height: 1; color: frame.edgeColor(index, true) }
            Rectangle { x: index; y: index; width: 1; height: frame.height-2*index; color: frame.edgeColor(index, true) }
            Rectangle { x: index; y: frame.height-index-1; width: frame.width-2*index; height: 1; color: frame.edgeColor(index, false) }
            Rectangle { x: frame.width-index-1; y: index; width: 1; height: frame.height-2*index; color: frame.edgeColor(index, false) }
        }
    }
}
