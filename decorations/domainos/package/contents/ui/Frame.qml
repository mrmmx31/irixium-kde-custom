// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
Item {
    id: frame
    property bool activeWindow: true
    property bool maximizedWindow: false
    readonly property color face: activeWindow ? "#fe8282" : "#7acac5"
    readonly property color light: activeWindow ? "#ffc8c8" : "#c5e8e6"
    readonly property color dark: activeWindow ? "#864545" : "#406b68"
    // Only decoration bands are filled; the application's client is untouched.
    Rectangle { width: parent.width; height: frame.maximizedWindow ? 20 : 30; color: frame.face }
    Item {
        anchors.fill: parent
        visible: !frame.maximizedWindow
        Rectangle { y:30; width:11; height:Math.max(0,parent.height-30); color:frame.face }
        Rectangle { x:parent.width-11; y:30; width:11; height:Math.max(0,parent.height-30); color:frame.face }
        Rectangle { y:parent.height-11; width:parent.width; height:11; color:frame.face }
        // Two-pixel outer bevel, with the diagonal corner transition.
        Rectangle { width:parent.width; height:2; color:frame.light }
        Rectangle { width:2; height:parent.height; color:frame.light }
        Rectangle { x:2; y:parent.height-2; width:Math.max(0,parent.width-2); height:2; color:frame.dark }
        Rectangle { x:parent.width-2; y:2; width:2; height:Math.max(0,parent.height-2); color:frame.dark }
        Rectangle { x:parent.width-1; y:1; width:1; height:1; color:frame.dark }
        Rectangle { x:1; y:parent.height-1; width:1; height:1; color:frame.dark }
        // Recessed inner surround; title controls add their own raised relief.
        Rectangle { x:9; y:9; width:Math.max(0,parent.width-18); height:1; color:frame.dark }
        Rectangle { x:9; y:10; width:1; height:Math.max(0,parent.height-20); color:frame.dark }
        Rectangle { x:10; y:30; width:1; height:Math.max(0,parent.height-40); color:frame.dark }
        Rectangle { x:parent.width-11; y:10; width:2; height:Math.max(0,parent.height-20); color:frame.light }
        Rectangle { x:10; y:parent.height-11; width:Math.max(0,parent.width-20); height:2; color:frame.light }
        Rectangle { x:10; y:parent.height-11; width:1; height:1; color:frame.dark }
        Rectangle { x:9; y:parent.height-10; width:1; height:1; color:frame.dark }
        Rectangle { x:parent.width-10; y:parent.height-10; width:1; height:1; color:frame.light }
        Rectangle { x:10; y:29; width:Math.max(0,parent.width-20); height:1; color:frame.dark }
        // Thirty-pixel corner grips: one dark line, followed by one light line.
        Repeater {
            model: [29,frame.width-31]
            delegate: Item {
                required property var modelData
                x:modelData; width:2; height:frame.height
                Rectangle { y:1; width:1; height:9; color:frame.dark }
                Rectangle { x:1; y:1; width:1; height:9; color:frame.light }
                Rectangle { y:frame.height-9; width:1; height:8; color:frame.dark }
                Rectangle { x:1; y:frame.height-9; width:1; height:8; color:frame.light }
            }
        }
        Repeater {
            model: [29,frame.height-31]
            delegate: Item {
                required property var modelData
                y:modelData; width:frame.width; height:2
                Rectangle { x:1; width:10; height:1; color:frame.dark }
                Rectangle { x:1; y:1; width:9; height:1; color:frame.light }
                Rectangle { x:frame.width-9; width:9; height:1; color:frame.dark }
                Rectangle { x:frame.width-9; y:1; width:8; height:1; color:frame.light }
            }
        }
    }
}
