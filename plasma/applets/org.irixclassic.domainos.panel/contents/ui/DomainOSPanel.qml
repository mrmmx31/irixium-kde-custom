// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: panel
    objectName: "domainosPanel"
    implicitWidth: 1942
    implicitHeight: 218
    readonly property real drawingScale: Math.min(width/1942,height/218)
    readonly property string phase: integration ? "functional-integration" : "design-reference"
    // The sealed-reference preview leaves this null. Native test hosts supply
    // the same live controller that will be used by the completed applet.
    property var integration: null
    signal actionRequested(string action, var anchor)
    onActionRequested: (action, anchor) => { if (integration) integration.dispatch(action, anchor) }
    readonly property int taskCount: integration ? integration.tasks.windowCount : 7
    readonly property int workspaceCount: integration && livePager.item ? livePager.item.desktopCount : 2
    readonly property int trayRows: 2
    readonly property int trayColumns: 3
    property bool followSystemColors: true
    // Local visual simulation only; no real workspace or application changes.
    property bool simulateSelection: false
    property int selectedWorkspaceIndex: 1
    property int selectedTaskIndex: -1
    readonly property QtObject colorPalette: colors
    readonly property var nativeIconbox: liveIconbox.item
    readonly property var nativePager: livePager.item
    readonly property var nativeTrayView: liveTray.item
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
    readonly property bool domainosBusyCursor: !!integration && integration.activity.busy

    // VUE shows a front-panel hourglass during an invocation. This passive
    // handler changes only the cursor; clicks and commands run immediately.
    // Presentation receipts and the optional LED tail are not pending work.
    HoverHandler {
        objectName: "domainosBusyPointer"
        enabled: panel.domainosBusyCursor
        cursorShape: Qt.WaitCursor
    }

    Item {
        id: drawing
        objectName: "domainosChassis"
        readonly property QtObject domainosPalette: panel.colorPalette
        readonly property real domainosRenderScale: panel.drawingScale
        readonly property bool domainosBarHintsEnabled: !!panel.integration && panel.integration.settings.barHintsEnabled === true
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
                onClicked: panel.actionRequested("clock", this)
                bevelThickness: 4; simpleRelief: true
                bevelLight: colors.pale; bevelDark: colors.dark
                face: colors.recessed
                PaletteImage { objectName: "domainosClockFace"; x: 16; y: 8; width: 134; height: 134; assetSource: panel.images+"clock-face.svg"; smooth: false }
                Item {
                    objectName: "domainosClockHands"
                    visible: !panel.integration || panel.integration.instruments.timeAvailable
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
                onClicked: panel.actionRequested("calendar", this)
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
                onClicked: panel.actionRequested("monitor", this)
                bevelThickness: 4; simpleRelief: true
                bevelLight: colors.pale; bevelDark: colors.dark
                face: colors.recessed
                imageSource: panel.integration ? "" : panel.images+"graph-reference.svg"; imageWidth: 152; imageHeight: 90
                Loader {
                    anchors.centerIn: parent; width: 152; height: width*35/60
                    active: !!panel.integration
                    sourceComponent: DomainOSGraph {
                        instruments: panel.integration ? panel.integration.instruments : null
                    }
                }
            }
            PanelButton {
                id: mailButton
                objectName: "domainosMail"
                x: 502; y: 4; width: 166; height: 150
                readonly property var liveInstruments: panel.integration ? panel.integration.instruments : null
                readonly property bool countRequested: !!panel.integration && panel.integration.settings.mailCountsEnabled === true
                label: liveInstruments ? qsTr("Correio")+" · "+(liveInstruments.mailStateAvailable
                    ? qsTr("%1 mensagem(ns) não lida(s)").arg(liveInstruments.mailUnreadCount)
                    : liveInstruments.mailStatusText) : qsTr("Correio")
                onClicked: panel.actionRequested("mail", this)
                bevelThickness: 4; simpleRelief: true
                bevelLight: colors.pale; bevelDark: colors.dark
                face: colors.recessed
                imageSource: panel.images+"mail.svg"; imageWidth: 142; imageHeight: 70
                Item {
                    objectName: "domainosMailUnreadCount"
                    anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 5 }
                    width: parent.width-16; height: 32
                    visible: mailButton.countRequested
                    Text {
                        objectName: "domainosMailUnreadText"
                        anchors.centerIn: parent
                        width: parent.width/scale
                        scale: 24/14
                        text: mailButton.liveInstruments && mailButton.liveInstruments.mailStateAvailable
                            ? String(mailButton.liveInstruments.mailUnreadCount) : "—"
                        textFormat: Text.PlainText
                        font.family: dateFont.status === FontLoader.Ready ? dateFont.name : "Courier"
                        font.pixelSize: 14; font.bold: true
                        color: colors.text
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideLeft
                        renderType: Text.NativeRendering
                        smooth: false
                    }
                }
            }
        }

        Bevel {
            objectName: "domainosIconbox"
            visible: !panel.integration
            x: 672; y: 8; width: 594; height: 150
            simpleRelief: true; light: colors.pale; dark: colors.dark
            texture: panel.images+"metal-weave.svg"
            Bevel { objectName: "domainosIconboxWell"; x: 12; y: 18; width: parent.width-24; height: 114; sunken: true; face: colors.recessed }
            PanelButton { objectName: "domainosIconboxPrevious"; x: 12; y: 26; width: 44; height: 98; label: "Previous icons"; imageSource: panel.images+"arrow-left.svg"; imageWidth: 32 }
            Repeater {
                model: panel.integration ? 0 : 7
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
        Loader {
            id: liveIconbox
            x: 672; y: 8; width: 594; height: 150
            active: !!panel.integration
            sourceComponent: DomainOSIconbox {
                controller: panel.integration.tasks
                colorPalette: colors
                hostItem: panel.integration.hostItem
                pinnedApplications: panel.integration.applications.pins
                middleClickAction: panel.integration.settings.middleClickAction === undefined ? 2 : panel.integration.settings.middleClickAction
                wheelEnabled: panel.integration.settings.wheelEnabled === undefined ? true : panel.integration.settings.wheelEnabled
                iconboxWheelActivates: panel.integration.settings.iconboxWheelActivates === true
                wheelSkipMinimized: panel.integration.settings.wheelSkipMinimized === undefined ? true : panel.integration.settings.wheelSkipMinimized
                interactiveMute: panel.integration.settings.interactiveMute !== false
                highlightWindows: panel.integration.settings.highlightWindows === true
                thumbnailsEnabled: panel.integration.settings.iconboxWindowThumbnails === true
                hintsEnabled: panel.integration.settings.iconboxHintsEnabled !== false
                onPinRequested: desktopId => panel.integration.applications.pin(desktopId)
                onUnpinRequested: desktopId => {
                    const index=panel.integration.applications.pins.indexOf(desktopId)
                    if (index>=0) panel.integration.applications.unpin(index)
                }
                onGroupingPreferencesRequested: (appIds,launcherUrls) => {
                    panel.integration.settings.tasksGroupingAppIdBlacklist=appIds
                    panel.integration.settings.tasksGroupingLauncherUrlBlacklist=launcherUrls
                    if (typeof panel.integration.settings.writeConfig === "function") panel.integration.settings.writeConfig()
                }
                onFailure: message => panel.integration.showFailure(message)
                onOperationStarted: operation => panel.integration.startOperation(operation)
                onOperationFinished: (operation,success,details) => panel.integration.finishOperation(operation,success,details)
            }
        }

        Bevel {
            objectName: "domainosPager"
            visible: !panel.integration
            x: 1266; y: 8; width: 342; height: 150
            simpleRelief: true; light: colors.pale; dark: colors.dark
            texture: panel.images+"metal-weave.svg"
            WorkspaceTile { objectName: "domainosDeskWork"; x: 8; y: 12; width: 158; height: 126; name: "Work"; selected: panel.selectedWorkspaceIndex === 0; onClicked: if (panel.simulateSelection) panel.selectedWorkspaceIndex = 0 }
            WorkspaceTile { objectName: "domainosDeskProcrastination"; x: 176; y: 12; width: 158; height: 126; name: "Procrastination"; second: true; selected: panel.selectedWorkspaceIndex === 1; onClicked: if (panel.simulateSelection) panel.selectedWorkspaceIndex = 1 }
        }
        Loader {
            id: livePager
            x: 1266; y: 8; width: 342; height: 150
            active: !!panel.integration
            sourceComponent: DomainOSPager {
                colorPalette: colors
                screenGeometry: panel.integration.screenGeometry
                showOnlyCurrentScreen: panel.integration.settings.pagerCurrentScreen || false
                wheelActivatesDesktop: panel.integration.settings.pagerWheelActivates || false
                onOperationStarted: operation => panel.integration.startOperation(operation)
                onOperationFinished: (operation, success, details) => panel.integration.finishOperation(operation, success, details)
                onFailure: message => panel.integration.showFailure(message)
            }
        }

        Bevel {
            objectName: "domainosTray"
            visible: !panel.integration
            x: 1608; y: 8; width: 202; height: 150
            simpleRelief: true; light: colors.pale; dark: colors.dark
            texture: panel.images+"metal-weave.svg"
            Bevel { objectName: "domainosTrayWell"; x: 8; y: 14; width: 186; height: 122; sunken: true; face: colors.recessed }
            Repeater {
                model: panel.integration ? 0 : 6
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
            visible: !panel.integration
            x: 1810; y: 8; width: 124; height: 150
            simpleRelief: true; light: colors.pale; dark: colors.dark
            texture: panel.images+"metal-weave.svg"
            PanelButton { objectName: "domainosTrayNext"; x: 22; y: 16; width: 80; height: 54; label: "Tray navigation right"; imageSource: panel.images+"arrow-right.svg"; imageWidth: 32 }
            PanelButton { objectName: "domainosTrayExpand"; x: 22; y: 80; width: 80; height: 54; label: "Tray navigation up"; imageSource: panel.images+"arrow-up.svg"; imageWidth: 32 }
        }
        Loader {
            id: liveTray
            x: 1608; y: 8; width: 326; height: 150
            active: !!panel.integration
            sourceComponent: DomainOSTray {
                nativeTray: panel.integration.nativeTray
                settings: panel.integration.settings
                activity: panel.integration.activity
                colorPalette: colors
                screenGeometry: panel.integration.screenGeometry
                onFailure: message => panel.integration.showFailure(message)
            }
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
                onClicked: panel.actionRequested("applications", this)
                face: colors.shadow; simpleRelief: true; bevelThickness: 4
                bevelLight: colors.metalLight; bevelDark: colors.shadow
                texture: panel.images+"metal-lines.svg"
                PaletteImage { x: 24; y: 2; width: 208; height: 48; assetSource: panel.images+"gnu-linux.svg"; smooth: false }
            }
            Bevel { objectName: "domainosRailLeft"; x: 256; y: 0; width: 331; height: parent.height; texture: panel.images+"metal-lines.svg"; simpleRelief: true; light: colors.metalLight; dark: colors.shadow; grooveCount: 4 }
            PanelButton {
                objectName: "domainosApplicationsDrawer"
                x: 587; y: 0; width: 118; height: parent.height
                label: "Applications drawer"
                onClicked: panel.actionRequested("pins", this)
                texture: panel.images+"metal-lines.svg"
                simpleRelief: true; bevelLight: colors.metalLight; bevelDark: colors.shadow; grooveCount: 4
                imageSource: panel.images+"applications.svg"; imageWidth: 64; imageHeight: 48
            }
            Repeater {
                model: 5
                delegate: PanelButton {
                    required property int index
                    objectName: "domainosShortcut_"+panel.lowerIcons[index]
                    x: [705,814,930,1048,1166][index]; y: 0; width: [109,116,118,118,119][index]; height: lowerRail.height
                    label: panel.lowerIcons[index]
                    onClicked: panel.actionRequested(panel.lowerIcons[index], this)
                    texture: panel.images+"metal-lines.svg"
                    simpleRelief: true; bevelLight: colors.metalLight; bevelDark: colors.shadow; grooveCount: 4
                    imageSource: panel.images+panel.lowerIcons[index]+".svg"; imageWidth: 64; imageHeight: 48
                }
            }
            Bevel { x: 1285; y: 0; width: 641; height: parent.height; texture: panel.images+"metal-lines.svg"; simpleRelief: true; light: colors.metalLight; dark: colors.shadow; grooveCount: 4 }
            Item {
                id: activityIndicator
                objectName: "domainosRightIndicator"
                // Keep the reference clearance inside the cyan chassis border.
                x: 1836; y: 10; width: 38; height: 28
                readonly property color face: colors.lens
                readonly property var tracker: panel.integration ? panel.integration.activity : null
                property int presentedSequence: 0
                PaletteImage { anchors.fill: parent; assetSource: panel.images+"indicator-lens.svg"; smooth: false; mipmap: false }
                Rectangle {
                    objectName: "domainosActivityLamp"
                    // Match the inner lens face at its native 2x drawing scale.
                    x: 6; y: 8; width: 26; height: 14
                    visible: activityIndicator.tracker && activityIndicator.tracker.displayLit
                    color: colors.activityLight
                }
                Connections {
                    target: activityIndicator.Window.window
                    enabled: !!activityIndicator.tracker && activityIndicator.tracker.presentationPending
                    // These handlers are delivered on the GUI thread. No QML
                    // state is changed from before/afterRendering signals.
                    function onAfterAnimating() {
                        activityIndicator.presentedSequence = activityIndicator.tracker.sequence
                    }
                    function onFrameSwapped() {
                        if (activityIndicator.tracker)
                            activityIndicator.tracker.acknowledgePresentation(activityIndicator.presentedSequence)
                    }
                }
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
