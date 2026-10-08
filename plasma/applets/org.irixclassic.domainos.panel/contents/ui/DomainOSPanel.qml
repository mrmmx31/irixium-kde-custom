// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: panel
    objectName: "domainosPanel"
    implicitWidth: 1942
    implicitHeight: 218
    readonly property real drawingScale: Math.min(width/1942,height/218)
    readonly property string phase: "design-awaiting-button-confirmations"
    readonly property int taskCount: 7
    readonly property int workspaceCount: 2
    readonly property int trayRows: 2
    readonly property int trayColumns: 3
    property int clockHour: 5
    property int clockMinute: 0
    property string dateText: "Feb 27\nThu"
    readonly property url images: Qt.resolvedUrl("../images/")
    readonly property var taskLabels: ["Desk","xterm","winterm","john","Index","Downl","xterm"]
    readonly property var taskIcons: ["desk.png","xterm.png","winterm.png","john.png","index.png","downl.png","xterm.png"]
    readonly property var trayIcons: ["network","speaker","envelope","storage","workstation","indicator"]
    readonly property var lowerIcons: ["terminal","preferences","drawer","lock","help"]

    Item {
        id: drawing
        objectName: "domainosChassis"
        width: 1942; height: 218
        x: (panel.width-width*panel.drawingScale)/2
        y: (panel.height-height*panel.drawingScale)/2
        scale: panel.drawingScale
        transformOrigin: Item.TopLeft
        Bevel { anchors.fill: parent; thickness: 3; face: "#405c6c" }
        Bevel { x: 4; y: 4; width: parent.width-8; height: parent.height-8; sunken: true; face: "#607f91" }

        Bevel {
            objectName: "domainosInstitutional"
            x: 4; y: 4; width: 493; height: 150
            face: "#607f91"; texture: panel.images+"metal-weave.svg"
            Bevel { x: 8; y: 14; width: parent.width-16; height: parent.height-25; sunken: true; face: "#405c6c" }
            PanelButton {
                objectName: "domainosClock"
                x: 12; y: 20; width: 112; height: 112
                label: "Analog clock"
                face: "#607f91"
                Image { x: 6; y: 6; width: 100; height: 100; source: panel.images+"clock-face.svg"; smooth: false }
                Item {
                    x: 56; y: 56
                    Rectangle {
                        x: -3; y: -29; width: 6; height: 33; color: "#ecffff"
                        transform: Rotation { origin.x: 3; origin.y: 29; angle: panel.clockHour*30+panel.clockMinute/2 }
                    }
                    Rectangle {
                        x: -2; y: -42; width: 4; height: 46; color: "#ecffff"
                        transform: Rotation { origin.x: 2; origin.y: 42; angle: panel.clockMinute*6 }
                    }
                    Rectangle { x: -3; y: -3; width: 6; height: 6; color: "#ecffff" }
                }
            }
            PanelButton {
                objectName: "domainosDate"
                x: 130; y: 20; width: 112; height: 112
                label: "Calendar date"
                face: "#607f91"
                Rectangle { x: 10; y: 13; width: 92; height: 84; color: "#3296c4" }
                Text {
                    anchors.centerIn: parent
                    text: panel.dateText; color: "#ecffff"
                    font.family: "DejaVu Sans Mono"; font.pixelSize: 24; font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    renderType: Text.NativeRendering
                }
            }
            PanelButton {
                objectName: "domainosGraph"
                x: 248; y: 20; width: 112; height: 112
                label: "System activity graph"
                face: "#607f91"
                imageSource: panel.images+"graph-reference.svg"; imageWidth: 92; imageHeight: 80
            }
            PanelButton {
                objectName: "domainosMail"
                x: 366; y: 20; width: 108; height: 112
                label: "Mail"
                face: "#607f91"
                imageSource: panel.images+"mail.svg"; imageWidth: 88; imageHeight: 66
            }
        }

        Bevel {
            objectName: "domainosIconbox"
            x: 497; y: 4; width: 774; height: 150
            texture: panel.images+"metal-weave.svg"
            Bevel { x: 12; y: 20; width: parent.width-24; height: 112; sunken: true; face: "#607f91" }
            PanelButton { objectName: "domainosIconboxPrevious"; x: 16; y: 28; width: 43; height: 96; label: "Previous icons"; imageSource: panel.images+"arrow-left.svg"; imageWidth: 32 }
            Repeater {
                model: 7
                delegate: PanelButton {
                    id: taskButton
                    required property int index
                    objectName: "domainosTask_"+index
                    x: 69+index*89; y: 28; width: 80; height: 96
                    label: panel.taskLabels[index]
                    face: "#607f91"
                    Image {
                        x: 8; y: 4; width: 64; height: 64
                        source: panel.images+"iconbox/"+panel.taskIcons[taskButton.index]
                        smooth: false; mipmap: false
                    }
                    Bevel { x: 2; y: 68; width: 76; height: 26; face: "#a2c0ce"; thickness: 1 }
                    Text {
                        x: 2; y: 68; width: 76; height: 26
                        text: panel.taskLabels[taskButton.index]
                        font.family: "Nimbus Sans"; font.pixelSize: 20
                        color: "#102b37"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                        renderType: Text.NativeRendering
                    }
                }
            }
            PanelButton { objectName: "domainosIconboxNext"; x: 707; y: 28; width: 43; height: 96; label: "Next icons"; imageSource: panel.images+"arrow-right.svg"; imageWidth: 32 }
        }

        Bevel {
            objectName: "domainosPager"
            x: 1271; y: 4; width: 341; height: 150
            texture: panel.images+"metal-weave.svg"
            WorkspaceTile { objectName: "domainosDeskWork"; x: 8; y: 12; width: 157; height: 126; name: "Work" }
            WorkspaceTile { objectName: "domainosDeskProcrastination"; x: 174; y: 12; width: 158; height: 126; name: "Procrastination"; second: true; selected: true }
        }

        Bevel {
            objectName: "domainosTray"
            x: 1612; y: 4; width: 202; height: 150
            texture: panel.images+"metal-weave.svg"
            Bevel { x: 8; y: 14; width: 178; height: 121; sunken: true; face: "#607f91" }
            Repeater {
                model: 6
                delegate: PanelButton {
                    required property int index
                    objectName: "domainosTray_"+panel.trayIcons[index]
                    x: 15+(index%3)*56; y: 23+Math.floor(index/3)*51; width: 54; height: 48
                    label: panel.trayIcons[index]
                    face: "#607f91"
                    imageSource: panel.images+panel.trayIcons[index]+".svg"; imageWidth: 32
                }
            }
        }
        Bevel {
            objectName: "domainosTrayNavigation"
            x: 1814; y: 4; width: 124; height: 150
            texture: panel.images+"metal-weave.svg"
            PanelButton { objectName: "domainosTrayNext"; x: 18; y: 15; width: 80; height: 58; label: "Tray navigation right"; imageSource: panel.images+"arrow-right.svg"; imageWidth: 32 }
            PanelButton { objectName: "domainosTrayExpand"; x: 18; y: 80; width: 80; height: 52; label: "Tray navigation up"; imageSource: panel.images+"arrow-up.svg"; imageWidth: 32 }
        }

        Bevel {
            objectName: "domainosLowerRail"
            x: 4; y: 154; width: 1934; height: 60
            texture: panel.images+"metal-lines.svg"
            Bevel {
                objectName: "domainosIdentity"
                x: 0; y: 0; width: 240; height: parent.height
                face: "#7894a7"
                Image { x: 16; y: 6; width: 208; height: 48; source: panel.images+"gnu-linux.svg"; smooth: false }
                // Institutional seal remains static until the user confirms help.
            }
            Bevel { x: 240; y: 0; width: 347; height: parent.height; texture: panel.images+"metal-lines.svg" }
            Bevel { x: 587; y: 0; width: 118; height: parent.height; texture: panel.images+"metal-lines.svg" }
            Repeater {
                model: 5
                delegate: PanelButton {
                    required property int index
                    objectName: "domainosShortcut_"+panel.lowerIcons[index]
                    x: [705,814,930,1048,1166][index]; y: 0; width: [109,116,118,118,119][index]; height: 60
                    label: panel.lowerIcons[index]
                    texture: panel.images+"metal-lines.svg"
                    imageSource: panel.images+panel.lowerIcons[index]+".svg"; imageWidth: 48
                }
            }
            Bevel { x: 1285; y: 0; width: 649; height: parent.height; texture: panel.images+"metal-lines.svg" }
            Bevel { objectName: "domainosRightIndicator"; x: 1857; y: 22; width: 42; height: 25; face: "#a2d0e7"; thickness: 3 }
        }
    }
}
