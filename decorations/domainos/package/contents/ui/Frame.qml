// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
Item {
    id: frame
    property bool activeWindow: true
    property bool maximizedWindow: false
    property bool resizeAllowed: true
    readonly property int inset:resizeAllowed ? 10 : 5
    readonly property int clientBorder:inset+1
    readonly property int titleBottom:inset+20
    property color face: activeWindow ? "#fe8282" : "#7acac5"
    property color light: activeWindow ? "#ffc8c8" : "#c5e8e6"
    property color dark: activeWindow ? "#864545" : "#406b68"
    // Only decoration bands are filled; the application's client is untouched.
    Rectangle { width: parent.width; height: frame.maximizedWindow ? 20 : frame.titleBottom; color: frame.face }
    Item {
        anchors.fill: parent
        visible: !frame.maximizedWindow
        Rectangle { y:frame.titleBottom; width:frame.clientBorder; height:Math.max(0,parent.height-y); color:frame.face }
        Rectangle { x:parent.width-frame.clientBorder; y:frame.titleBottom; width:frame.clientBorder; height:Math.max(0,parent.height-y); color:frame.face }
        Rectangle { y:parent.height-frame.clientBorder; width:parent.width; height:frame.clientBorder; color:frame.face }
        // Two-pixel outer bevel, with the diagonal corner transition.
        Rectangle { width:parent.width; height:2; color:frame.light }
        Rectangle { width:2; height:parent.height; color:frame.light }
        Rectangle { x:2; y:parent.height-2; width:Math.max(0,parent.width-2); height:2; color:frame.dark }
        Rectangle { x:parent.width-2; y:2; width:2; height:Math.max(0,parent.height-2); color:frame.dark }
        Rectangle { x:parent.width-1; y:1; width:1; height:1; color:frame.dark }
        Rectangle { x:1; y:parent.height-1; width:1; height:1; color:frame.dark }
        // Recessed inner surround; title controls add their own raised relief.
        Rectangle { x:frame.inset-1; y:frame.inset-1; width:Math.max(0,parent.width-2*x); height:1; color:frame.dark }
        Rectangle { x:frame.inset-1; y:frame.inset; width:1; height:Math.max(0,parent.height-2*y); color:frame.dark }
        Rectangle { x:frame.inset; y:frame.titleBottom; width:1; height:Math.max(0,parent.height-y-frame.inset); color:frame.dark }
        Rectangle { x:parent.width-frame.clientBorder; y:frame.inset; width:2; height:Math.max(0,parent.height-2*y); color:frame.light }
        Rectangle { x:frame.inset; y:parent.height-frame.clientBorder; width:Math.max(0,parent.width-2*x); height:2; color:frame.light }
        Rectangle { x:frame.inset; y:parent.height-frame.clientBorder; width:1; height:1; color:frame.dark }
        Rectangle { x:frame.inset-1; y:parent.height-frame.inset; width:1; height:1; color:frame.dark }
        Rectangle { x:parent.width-frame.inset; y:parent.height-frame.inset; width:1; height:1; color:frame.light }
        Rectangle { x:frame.inset; y:frame.titleBottom-1; width:Math.max(0,parent.width-2*x); height:1; color:frame.dark }
        // Thirty-pixel corner grips: one dark line, followed by one light line.
        Repeater {
            model: frame.resizeAllowed ? [29,frame.width-31] : []
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
            model: frame.resizeAllowed ? [29,frame.height-31] : []
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
