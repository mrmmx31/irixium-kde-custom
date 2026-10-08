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
    property bool followSystemColors: true
    // Local visual simulation only; no real workspace or application changes.
    property bool simulateSelection: false
    property int selectedWorkspaceIndex: 1
    property int selectedTaskIndex: -1
    readonly property QtObject colorPalette: colors
    DomainOSPalette { id: colors; followSystem: panel.followSystemColors }
    property int clockHour: 5
    property int clockMinute: 0
    property string dateText: "Feb 27\nThu"
    FontLoader { id: dateFont; source: Qt.resolvedUrl("../fonts/adobe-courier-bold-14.pcf") }
    readonly property url images: Qt.resolvedUrl("../images/")
    readonly property var taskLabels: ["Desk","xterm","winterm","john","Index","Downl","xterm"]
    readonly property var taskIcons: ["desk.png","xterm.png","winterm.png","john.png","index.png","downl.png","xterm.png"]
    readonly property var trayIcons: ["network","speaker","envelope","storage","workstation","indicator"]
    readonly property var lowerIcons: ["terminal","preferences","drawer","lock","help"]

    Item {
        id: drawing
        objectName: "domainosChassis"
        readonly property QtObject domainosPalette: panel.colorPalette
        readonly property real domainosRenderScale: panel.drawingScale
        width: 1942; height: 218
        x: (panel.width-width*panel.drawingScale)/2
        y: (panel.height-height*panel.drawingScale)/2
        scale: panel.drawingScale
        transformOrigin: Item.TopLeft
        Bevel { anchors.fill: parent; thickness: 3; face: colors.shadow }
        Bevel { x: 4; y: 4; width: parent.width-8; height: parent.height-8; sunken: true; face: colors.recessed }

        Item {
            objectName: "domainosInstitutional"
            x: 4; y: 4; width: 668; height: 154
            // The instruments own their right/bottom relief; no outer frame.
            PanelButton {
                objectName: "domainosClock"
                x: 4; y: 4; width: 166; height: 150
                label: "Analog clock"
                bevelThickness: 4; simpleRelief: true
                bevelLight: colors.pale; bevelDark: colors.dark
                face: colors.recessed
                PaletteImage { objectName: "domainosClockFace"; x: 16; y: 8; width: 134; height: 134; assetSource: panel.images+"clock-face.svg"; smooth: false }
                Item {
                    objectName: "domainosClockHands"
                    x: 83; y: 75
                    scale: 134/114; transformOrigin: Item.TopLeft
                    Item {
                        transform: Rotation { angle: panel.clockHour*30+panel.clockMinute/2 }
                        Rectangle { x: -1; y: -30; width: 2; height: 14; color: colors.white }
                        Rectangle { x: -2; y: -16; width: 4; height: 10; color: colors.white }
                        Rectangle { x: -3; y: -6; width: 6; height: 8; color: colors.white }
                    }
                    Item {
                        transform: Rotation { angle: panel.clockMinute*6 }
                        Rectangle { x: -1; y: -46; width: 2; height: 26; color: colors.white }
                        Rectangle { x: -2; y: -20; width: 4; height: 12; color: colors.white }
                        Rectangle { x: -3; y: -8; width: 6; height: 10; color: colors.white }
                    }
                    Rectangle { x: -2; y: -2; width: 4; height: 4; color: colors.white }
                }
            }
            PanelButton {
                objectName: "domainosDate"
                x: 170; y: 4; width: 166; height: 150
                label: "Calendar date"
                bevelThickness: 4; simpleRelief: true
                bevelLight: colors.pale; bevelDark: colors.dark
                face: colors.recessed
                Rectangle { objectName: "domainosDateFace"; anchors.centerIn: parent; width: 152; height: width*35/60; color: colors.blue }
                Item {
                    anchors.centerIn: parent
                    // Center the Courier ink rather than its extra advance and leading.
                    anchors.horizontalCenterOffset: 3
                    anchors.verticalCenterOffset: 4
                    width: dateLabel.implicitWidth*dateLabel.scale
                    height: dateLabel.implicitHeight*dateLabel.scale
                    Text {
                        id: dateLabel
                        objectName: "domainosDateLettering"
                        // Keep the native X11 strike: scaling the item prevents Qt
                        // from substituting an outline font at an unsupported size.
                        scale: 2*75/59; transformOrigin: Item.TopLeft
                        text: panel.dateText; color: colors.white
                        font.family: dateFont.name; font.pixelSize: 14; font.bold: true
                        lineHeightMode: Text.FixedHeight; lineHeight: 17
                        horizontalAlignment: Text.AlignHCenter
                        renderType: Text.NativeRendering
                        textFormat: Text.PlainText
                        // Native font rasterization follows the user's font
                        // settings; keep bitmap enlargement unfiltered.
                        smooth: false
                    }
                }
            }
            PanelButton {
                objectName: "domainosGraph"
                x: 336; y: 4; width: 166; height: 150
                label: "System activity graph"
                bevelThickness: 4; simpleRelief: true
                bevelLight: colors.pale; bevelDark: colors.dark
                face: colors.recessed
                imageSource: panel.images+"graph-reference.svg"; imageWidth: 152; imageHeight: 90
            }
            PanelButton {
                objectName: "domainosMail"
                x: 502; y: 4; width: 166; height: 150
                label: "Mail"
                bevelThickness: 4; simpleRelief: true
                bevelLight: colors.pale; bevelDark: colors.dark
                face: colors.recessed
                imageSource: panel.images+"mail.svg"; imageWidth: 142; imageHeight: 70
            }
        }

        Bevel {
            objectName: "domainosIconbox"
            x: 672; y: 8; width: 594; height: 150
            simpleRelief: true; light: colors.pale; dark: colors.dark
            texture: panel.images+"metal-weave.svg"
            Bevel { objectName: "domainosIconboxWell"; x: 12; y: 18; width: parent.width-24; height: 114; sunken: true; face: colors.recessed }
            PanelButton { objectName: "domainosIconboxPrevious"; x: 12; y: 26; width: 44; height: 98; label: "Previous icons"; imageSource: panel.images+"arrow-left.svg"; imageWidth: 32 }
            Repeater {
                model: 7
                delegate: PanelButton {
                    id: taskButton
                    required property int index
                    objectName: "domainosTask_"+index
                    x: 60+index*68; y: 26; width: 66; height: 98
                    label: panel.taskLabels[index]
                    selectable: true
                    selected: panel.selectedTaskIndex === index
                    onClicked: if (panel.simulateSelection) panel.selectedTaskIndex = index
                    face: colors.recessed
                    PaletteImage {
                        x: 2; y: 4; width: 64; height: 64
                        assetSource: panel.images+"iconbox/"+panel.taskIcons[taskButton.index]
                        smooth: false; mipmap: false
                    }
                    Bevel { objectName: "domainosTaskLabel_"+taskButton.index; x: 2; y: 68; width: 62; height: 26; face: taskButton.selected ? colors.blue : colors.label; thickness: 1; sunken: taskButton.selected }
                    Text {
                        objectName: "domainosTaskLabelText_"+taskButton.index
                        x: 2; y: 68; width: 62; height: 26
                        text: panel.taskLabels[taskButton.index]
                        font.family: "Nimbus Sans"; font.pixelSize: 16
                        color: taskButton.selected ? colors.white : colors.text; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                        renderType: Text.NativeRendering
                    }
                }
            }
            PanelButton { objectName: "domainosIconboxNext"; x: 538; y: 26; width: 44; height: 98; label: "Next icons"; imageSource: panel.images+"arrow-right.svg"; imageWidth: 32 }
        }

        Bevel {
            objectName: "domainosPager"
            x: 1266; y: 8; width: 342; height: 150
            simpleRelief: true; light: colors.pale; dark: colors.dark
            texture: panel.images+"metal-weave.svg"
            WorkspaceTile { objectName: "domainosDeskWork"; x: 8; y: 12; width: 158; height: 126; name: "Work"; selected: panel.selectedWorkspaceIndex === 0; onClicked: if (panel.simulateSelection) panel.selectedWorkspaceIndex = 0 }
            WorkspaceTile { objectName: "domainosDeskProcrastination"; x: 176; y: 12; width: 158; height: 126; name: "Procrastination"; second: true; selected: panel.selectedWorkspaceIndex === 1; onClicked: if (panel.simulateSelection) panel.selectedWorkspaceIndex = 1 }
        }

        Bevel {
            objectName: "domainosTray"
            x: 1608; y: 8; width: 202; height: 150
            simpleRelief: true; light: colors.pale; dark: colors.dark
            texture: panel.images+"metal-weave.svg"
            Bevel { objectName: "domainosTrayWell"; x: 8; y: 14; width: 186; height: 122; sunken: true; face: colors.recessed }
            Repeater {
                model: 6
                delegate: PanelButton {
                    required property int index
                    objectName: "domainosTray_"+panel.trayIcons[index]
                    x: 16+(index%3)*60; y: 24+Math.floor(index/3)*54; width: 50; height: 48
                    label: panel.trayIcons[index]
                    face: colors.recessed
                    imageSource: panel.images+panel.trayIcons[index]+".svg"; imageWidth: 32
                }
            }
        }
        Bevel {
            objectName: "domainosTrayNavigation"
            x: 1810; y: 8; width: 124; height: 150
            simpleRelief: true; light: colors.pale; dark: colors.dark
            texture: panel.images+"metal-weave.svg"
            PanelButton { objectName: "domainosTrayNext"; x: 22; y: 16; width: 80; height: 54; label: "Tray navigation right"; imageSource: panel.images+"arrow-right.svg"; imageWidth: 32 }
            PanelButton { objectName: "domainosTrayExpand"; x: 22; y: 80; width: 80; height: 54; label: "Tray navigation up"; imageSource: panel.images+"arrow-up.svg"; imageWidth: 32 }
        }

        Bevel {
            id: lowerRail
            objectName: "domainosLowerRail"
            x: 8; y: 158; width: 1926; height: 52
            texture: panel.images+"metal-lines.svg"
            simpleRelief: true; light: colors.metalLight; dark: colors.shadow; grooveCount: 4
            PanelButton {
                objectName: "domainosIdentity"
                x: 0; y: 0; width: 256; height: parent.height
                label: "GNU/LINUX"
                face: colors.shadow; simpleRelief: true; bevelThickness: 4
                bevelLight: colors.metalLight; bevelDark: colors.shadow
                texture: panel.images+"metal-lines.svg"
                PaletteImage { x: 24; y: 2; width: 208; height: 48; assetSource: panel.images+"gnu-linux.svg"; smooth: false }
                // Institutional seal remains static until the user confirms help.
            }
            Bevel { objectName: "domainosRailLeft"; x: 256; y: 0; width: 331; height: parent.height; texture: panel.images+"metal-lines.svg"; simpleRelief: true; light: colors.metalLight; dark: colors.shadow; grooveCount: 4 }
            PanelButton {
                objectName: "domainosApplicationsDrawer"
                x: 587; y: 0; width: 118; height: parent.height
                label: "Applications drawer"
                texture: panel.images+"metal-lines.svg"
                simpleRelief: true; bevelLight: colors.metalLight; bevelDark: colors.shadow; grooveCount: 4
                imageSource: panel.images+"applications.svg"; imageWidth: 64; imageHeight: 48
                // Graphic only: pinning and opening the drawer await design approval.
            }
            Repeater {
                model: 5
                delegate: PanelButton {
                    required property int index
                    objectName: "domainosShortcut_"+panel.lowerIcons[index]
                    x: [705,814,930,1048,1166][index]; y: 0; width: [109,116,118,118,119][index]; height: lowerRail.height
                    label: panel.lowerIcons[index]
                    texture: panel.images+"metal-lines.svg"
                    simpleRelief: true; bevelLight: colors.metalLight; bevelDark: colors.shadow; grooveCount: 4
                    imageSource: panel.images+panel.lowerIcons[index]+".svg"; imageWidth: 64; imageHeight: 48
                }
            }
            Bevel { x: 1285; y: 0; width: 641; height: parent.height; texture: panel.images+"metal-lines.svg"; simpleRelief: true; light: colors.metalLight; dark: colors.shadow; grooveCount: 4 }
            Item {
                objectName: "domainosRightIndicator"
                // Keep the reference clearance inside the cyan chassis border.
                x: 1836; y: 10; width: 38; height: 28
                readonly property color face: colors.lens
                PaletteImage { anchors.fill: parent; assetSource: panel.images+"indicator-lens.svg"; smooth: false; mipmap: false }
            }
        }

        // The 26px metal rail ends in a 2px cyan lip and 2px cyan shadow at 50%.
        Rectangle { objectName: "domainosCyanLip"; x: 0; y: 210; width: drawing.width; height: 4; color: colors.cyan }
        Rectangle { objectName: "domainosCyanFootShadow"; x: 0; y: 214; width: drawing.width; height: 4; color: colors.cyanShadow }
        // Reserve the cyan side bands outside the modules' own relief.
        Rectangle { objectName: "domainosTopChassisLight"; x: 0; y: 0; width: drawing.width; height: 4; color: colors.highlight }
        Rectangle { objectName: "domainosTopCyanBorder"; x: 2; y: 4; width: 1936; height: 4; color: colors.cyan }
        Rectangle { objectName: "domainosLeftChassisLight"; x: 0; y: 0; width: 4; height: 216; color: colors.highlight }
        Rectangle { objectName: "domainosLeftCyanBorder"; x: 4; y: 4; width: 4; height: 210; color: colors.cyan }
        Rectangle { x: 0; y: 216; width: 2; height: 2; color: colors.highlight }
        Rectangle { objectName: "domainosRightCyanBorder"; x: 1934; y: 4; width: 4; height: 210; color: colors.cyan }
        Rectangle { objectName: "domainosRightChassisShadow"; x: 1938; y: 4; width: 4; height: 214; color: colors.cyanShadow }
        Rectangle { x: 1940; y: 2; width: 2; height: 2; color: colors.cyanShadow }
    }
}
