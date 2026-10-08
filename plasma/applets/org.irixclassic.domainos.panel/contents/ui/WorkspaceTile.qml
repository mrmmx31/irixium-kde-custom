// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: workspace
    readonly property QtObject colorPalette: {
        let ancestor = parent
        while (ancestor) {
            if (ancestor.domainosPalette !== undefined) return ancestor.domainosPalette
            ancestor = ancestor.parent
        }
        return null
    }
    required property string name
    property bool selected: false
    property bool second: false
    readonly property bool lit: selected || pagerButton.pressed
    readonly property color lampColor: pagerButton.pressed ? colorPalette.pagerPressedLight : colorPalette.pagerLight
    signal clicked()
    PanelButton {
        id: pagerButton
        objectName: "domainosWorkspace_"+workspace.name
        anchors.fill: parent
        label: workspace.name
        selectable: true
        selected: workspace.selected
        // A new workspace reacts while held; the selected workspace stays lit.
        pressRelief: !workspace.selected
        selectedRelief: false
        onClicked: workspace.clicked()
        face: colorPalette.recessed
        Item {
            anchors.fill: parent
            anchors.margins: 6
            Rectangle {
                objectName: "domainosWorkspaceTitle_"+workspace.name
                x: 0; y: 0; width: parent.width; height: 30
                color: colorPalette.background
                border.width: 2
                border.color: colorPalette.dark
                Rectangle { objectName: "domainosWorkspaceMarker_"+workspace.name; x: 7; y: 7; width: 11; height: 16; color: workspace.lit ? workspace.lampColor : colorPalette.recessed; border.color: colorPalette.dark; border.width: 2 }
                Text {
                    objectName: "domainosWorkspaceTitleText_"+workspace.name
                    x: 26; y: 1; width: parent.width-x-2; height: 28
                    text: workspace.name
                    font.family: "Nimbus Sans"
                    font.pixelSize: 16
                    color: colorPalette.text
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.NativeRendering
                }
            }
            Rectangle {
                id: map
                objectName: "domainosWorkspaceMap_"+workspace.name
                x: 0; y: 32; width: parent.width; height: parent.height-32
                clip: true
                color: colorPalette.followSystem ? colorPalette.dark : "#071709"
                border.color: colorPalette.highlight
                border.width: 2
                // Geometric window samples from the drawing, not live desktops.
                Repeater {
                    model: workspace.second ? [
                        {x:4,y:4,w:64,h:28,c:"#061409"},
                        {x:4,y:38,w:64,h:30,c:"#08190c"},
                        {x:74,y:6,w:70,h:63,c:"#a0575c"},
                        {x:4,y:74,w:106,h:13,c:"#ba7879",footer:true},
                        {x:116,y:74,w:29,h:13,c:"#558193",footer:true}
                    ] : [
                        {x:4,y:4,w:57,h:8,c:"#ba7879"},
                        {x:4,y:74,w:80,h:13,c:"#ba7879",footer:true},
                        {x:90,y:74,w:56,h:13,c:"#558193",footer:true}
                    ]
                    delegate: Rectangle {
                        required property int index
                        required property var modelData
                        objectName: "domainosWorkspaceSample_"+workspace.name+"_"+index
                        x: modelData.x
                        y: modelData.footer === true ? map.height-modelData.h-2 : modelData.y
                        width: modelData.w; height: modelData.h
                        color: modelData.c; border.color: colorPalette.highlight; border.width: 2
                    }
                }
            }
        }
    }
    Rectangle {
        objectName: "domainosWorkspaceSelection_"+workspace.name
        anchors.fill: parent
        color: "transparent"
        visible: workspace.lit
        border.width: 3
        border.color: workspace.lampColor
    }
}
