// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
Item {
    id: relief
    property color face: "#7acac5"
    property color light: "#c5e8e6"
    property color dark: "#406b68"
    property int lineWidth: 1
    property bool down: false
    readonly property color upper: down ? dark : light
    readonly property color lower: down ? light : dark
    Rectangle { anchors.fill: parent; color: relief.face }
    Rectangle { width: parent.width; height: relief.lineWidth; color: relief.upper }
    Rectangle { width: relief.lineWidth; height: parent.height; color: relief.upper }
    Rectangle {
        x: relief.lineWidth; y: parent.height-relief.lineWidth
        width: Math.max(0,parent.width-relief.lineWidth); height: relief.lineWidth
        color: relief.lower
    }
    Rectangle {
        x: parent.width-relief.lineWidth; y: relief.lineWidth
        width: relief.lineWidth; height: Math.max(0,parent.height-relief.lineWidth)
        color: relief.lower
    }
}
