// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts

Item {
    id: runtime
    property var settings: ({})
    property var hostItem
    property QtObject colorPalette: null
    property rect screenGeometry: Qt.rect(0, 0, 0, 0)
    property rect availableGeometry: screenGeometry
    property string screenName: ""
    property var nativeTray: null
    property string instanceId: "isolated"
    property var operationTokens: ({})
    readonly property alias instruments: instrumentsController
    readonly property alias mailState: mailStateController
    readonly property alias activity: activityTracker
    readonly property alias commands: commandController
    readonly property alias applications: applicationController
    readonly property alias tasks: taskController
    readonly property alias windowOperations: windowOperationsController
    signal configureRequested()
    signal pinListRequested(var pins)
    property string statusMessage: ""
    function showFailure(message) { statusMessage = message; failureDialog.open() }
    function startOperation(operation) {
        const queue = operationTokens[operation] || []
        operationTokens[operation] = queue.concat([activityTracker.begin(operation)])
    }
    function finishOperation(operation, success, details) {
        const queue = operationTokens[operation] || []
        if (!queue.length) return
        const token = queue.shift(); operationTokens[operation] = queue
        activityTracker.finish(token, {ok: success, action: operation, outcome: success ? "confirmed" : "failed", detail: details})
    }
    function present(action, request) {
        const token = activityTracker.begin("presentation-" + action)
        let accepted = false
        try { request(); accepted = true }
        catch (error) { runtime.showFailure(qsTr("The requested panel view could not be shown")) }
        finally {
            activityTracker.finish(token, {ok: accepted, action: action,
                outcome: accepted ? "presentation-requested" : "failed",
                detail: accepted ? qsTr("The panel accepted the view request; no application completion is implied")
                    : qsTr("The requested panel view could not be shown")})
        }
    }
    function openMail() {
        // Metadata refresh is asynchronous and never delays launching the
        // current user-selected client through the command controller.
        mailStateController.refreshDefaultClient()
        return commandController.openMail()
    }
    function dispatch(action, anchor) {
        switch (action) {
        case "clock": present(action, () => instrumentsController.showClock(anchor)); break
        case "calendar": present(action, () => instrumentsController.showCalendar(anchor)); break
        case "monitor": present(action, () => instrumentsController.showMonitor(anchor)); break
        case "mail": runtime.openMail(); break
        case "applications": present(action, () => applicationController.showMenu(anchor)); break
        case "pins": present(action, () => applicationController.showDrawer(anchor)); break
        case "terminal": commandController.openTerminal(); break
        case "preferences": commandController.openAppearance(); break
        case "drawer": present(action, () => commandController.showSession(anchor)); break
        case "lock": commandController.lock(); break
        case "help": present(action, () => commandController.showHelp(anchor)); break
        }
    }
    DomainOSActivity {
        id: activityTracker
        keepLightAfterCompletion: runtime.settings.keepActivityLight || false
        extraLightMilliseconds: runtime.settings.activityLightMilliseconds === undefined ? 1000 : runtime.settings.activityLightMilliseconds
    }
    DomainOSCommands {
        id: commandController
        settings: runtime.settings; palette: runtime.colorPalette; activity: activityTracker
        onReported: report => { if (!report.ok) runtime.showFailure(report.detail) }
        localHelpVisible: localHelp.visible
        onLocalHelpRequested: anchor => { localHelpPlacement.popupAnchor = anchor; localHelp.open() }
        onCloseLocalHelpRequested: localHelp.close()
    }
    DomainOSInstruments {
        id: instrumentsController
        mailStateProvider: mailStateController
        domainosPalette: runtime.colorPalette
        metric: runtime.settings.instrumentMetric || "network"
        networkInterface: runtime.settings.networkInterface || "all"
        timeZones: runtime.settings.timeZones || ["Local", "UTC"]
        calendarPlugins: runtime.settings.calendarPlugins || []
        customSensorId: runtime.settings.customSensorId || ""
        customSecondarySensorId: runtime.settings.customSecondarySensorId || ""
        sampleInterval: runtime.settings.instrumentSampleInterval === undefined ? 1000 : runtime.settings.instrumentSampleInterval
        historyLength: runtime.settings.instrumentHistoryLength === undefined ? 60 : runtime.settings.instrumentHistoryLength
        onMailRequested: runtime.openMail()
    }
    DomainOSMailState {
        id: mailStateController
        enabled: runtime.settings.mailCountsEnabled === true
        desktopId: runtime.settings.mailClient || ""
    }
    DomainOSApplications {
        id: applicationController
        settings: runtime.settings; commands: commandController; hostItem: runtime.hostItem
        favoritesClient: "org.irixclassic.domainos.menu.instance-" + runtime.instanceId
        onConfigureRequested: runtime.configureRequested()
        onPinListRequested: pins => runtime.pinListRequested(pins)
    }
    DomainOSWindowOperations {
        id: windowOperationsController
        activity: activityTracker
        onReported: report => { if (!report.ok) runtime.showFailure(report.detail) }
    }
    DomainOSTasks {
        id: taskController
        geometryBackend: windowOperationsController
        processBackend: windowOperationsController
        currentScreenGeometry: runtime.screenGeometry
        currentAvailableGeometry: runtime.availableGeometry
        currentScreenName: runtime.screenName
        onlyCurrentDesktop: runtime.settings.tasksOnlyCurrentDesktop === undefined ? true : runtime.settings.tasksOnlyCurrentDesktop
        onlyCurrentScreen: runtime.settings.tasksOnlyCurrentScreen || false
        onlyCurrentActivity: runtime.settings.tasksOnlyCurrentActivity === undefined ? true : runtime.settings.tasksOnlyCurrentActivity
        groupingMode: runtime.settings.tasksGroupingMode === undefined ? 1 : runtime.settings.tasksGroupingMode
        onlyGroupWhenFull: runtime.settings.tasksOnlyGroupWhenFull === undefined ? true : runtime.settings.tasksOnlyGroupWhenFull
        sortMode: runtime.settings.tasksSortMode === undefined ? 1 : runtime.settings.tasksSortMode
        groupingAppIdBlacklist: runtime.settings.tasksGroupingAppIdBlacklist || []
        groupingLauncherUrlBlacklist: runtime.settings.tasksGroupingLauncherUrlBlacklist || []
        filterMode: runtime.settings.tasksFilterMode || "normal"
        automaticThreshold: runtime.settings.tasksAutomaticThreshold === undefined ? -1 : runtime.settings.tasksAutomaticThreshold
        onOperationUnavailable: request => runtime.showFailure(request.reason)
        onOperationRequested: request => {
            if (["columns","rows","mosaic","collect","terminate"].indexOf(request.action)>=0 || request.targets) return
            // Native TaskManager methods return void. Their return proves only
            // dispatch; do not invent an application completion or hold a light
            // while waiting for a state that the provider did not promise.
            const token=activityTracker.begin("task-"+request.action)
            activityTracker.finish(token,{ok:true,outcome:"request-accepted",action:request.action,
                detail:qsTr("The window provider accepted the request; completion is not observed here")})
        }
    }
    DomainOSPopupPlacement { popup: failureDialog; popupAnchor: runtime; gap: 8 }
    DomainOSPopupPlacement { id: localHelpPlacement; popup: localHelp; gap: 8 }
    Controls.Dialog {
        id: failureDialog
        objectName: "domainosFailureDialog"
        popupType: Controls.Popup.Window
        enter: null
        exit: null
        focus: true
        width: 450
        title: qsTr("Irix Classic DomainOS")
        modal: false; standardButtons: Controls.Dialog.Ok
        footer: DomainOSDialogButtonBox {}
        contentItem: Controls.Label { text: runtime.statusMessage; wrapMode: Text.WordWrap }
    }
    Controls.Dialog {
        id: localHelp
        objectName: "domainosLocalHelpDialog"
        popupType: Controls.Popup.Window
        enter: null
        exit: null
        focus: true
        width: 510
        title: qsTr("Irix Classic DomainOS help")
        standardButtons: Controls.Dialog.Close
        footer: DomainOSDialogButtonBox {}
        contentItem: ColumnLayout {
            Controls.Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: qsTr("The GNU/LINUX plate opens applications. The separate drawer stores this panel's pins. "
                       + "Clock, calendar and network instruments show session data. The pager selects existing desktops; "
                       + "its wheel browses cards by default. Terminal, appearance, session, lock and help remain in the metal rail. "
                       + "In the Iconbox, one click opens the window list, including a single window. A double click minimizes the active window, "
                       + "restores a minimized window or activates an inactive one. Ctrl/Shift extend the selection; "
                       + "groups let you choose individual windows. Right-click keeps KDE actions and offers organization. "
                       + "Panel preferences are the permanent first item in the pinned applications drawer. They belong to this instance. "
                       + "The activity light follows observable requests. A request acknowledgement does not prove application completion. "
                       + "Dragging windows between pager thumbnails is reserved for the next version.")
            }
            DomainOSButton {
                text: qsTr("Full local guide")
                onClicked: {
                    const token=activityTracker.begin("local-guide")
                    const accepted=Qt.openUrlExternally(Qt.resolvedUrl("../../FUNCTIONAL.md"))
                    activityTracker.finish(token,{ok:accepted,outcome:accepted ? "request-accepted" : "failed",
                        detail:accepted ? qsTr("The document viewer accepted the request") : qsTr("The local guide could not be opened")})
                    if (!accepted) runtime.showFailure(qsTr("The local guide could not be opened"))
                }
            }
        }
    }
}
