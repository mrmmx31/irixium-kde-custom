// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: workspace
    required property string name
    property bool selected: false
    property bool second: false
    PanelButton {
        objectName: "domainosWorkspace_"+workspace.name
        anchors.fill: parent
        label: workspace.name
        face: "#607f91"
        Item {
            anchors.fill: parent
            anchors.margins: 6
            Rectangle {
                x: 0; y: 0; width: parent.width; height: 30
                color: "#7894a7"
                border.width: 2
                border.color: "#263f4d"
                Rectangle { objectName: "domainosWorkspaceMarker_"+workspace.name; x: 7; y: 7; width: 11; height: 16; color: workspace.selected ? "#dddd28" : "#607f91"; border.color: "#263f4d"; border.width: 2 }
                Text {
                    x: 26; y: 1; width: parent.width-x-2; height: 28
                    text: workspace.name
                    font.family: "Nimbus Sans"
                    font.pixelSize: 16
                    color: "#102b37"
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.NativeRendering
                }
            }
            Rectangle {
                id: map
                x: 0; y: 32; width: parent.width; height: parent.height-32
                color: "#071709"
                border.color: "#bed0d4"
                border.width: 2
                // Geometric window samples from the drawing, not live desktops.
                Repeater {
                    model: workspace.second ? [
                        {x:4,y:4,w:64,h:28,c:"#061409"},
                        {x:4,y:38,w:64,h:30,c:"#08190c"},
                        {x:74,y:6,w:70,h:63,c:"#a0575c"},
                        {x:4,y:74,w:106,h:13,c:"#ba7879"},
                        {x:116,y:74,w:29,h:13,c:"#558193"}
                    ] : [
                        {x:4,y:4,w:57,h:8,c:"#ba7879"},
                        {x:4,y:74,w:80,h:13,c:"#ba7879"},
                        {x:90,y:74,w:56,h:13,c:"#558193"}
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        x: modelData.x; y: modelData.y; width: modelData.w; height: modelData.h
                        color: modelData.c; border.color: "#bed0d4"; border.width: 2
                    }
                }
            }
        }
    }
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        visible: workspace.selected
        border.width: 3
        border.color: "#dddd28"
    }
}
