// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import "../applets/org.irixclassic.domainos.panel/contents/ui" as Production

// Owned GridView/provider doubles exercise the actual adoption and presentation
// adapter; they register no SNI service or application and contain no user data.
Window {
    id: host
    width: 971
    height: 109
    x: 100
    y: 600
    visible: true
    property alias panel: panel
    property alias activity: tracker
    property alias nativeProvider: nativeProvider
    property alias nativeState: nativeState
    readonly property var tray: panel.nativeTrayView
    property var reports: []
    property var failures: []
    property var pendingOnPresentation: []
    property var lastResult: null
    Production.DomainOSActivity { id: tracker }
    Production.DomainOSPanel { id: panel; anchors.fill: parent }
    QtObject {
        id: integration
        property QtObject activity: tracker
        property Item nativeTray: nativeProvider
        property var settings: ({})
        property rect screenGeometry: Qt.rect(0, 0, 1200, 900)
        property QtObject tasks: QtObject { property int windowCount: 0 }
        property var instruments: ({timeAvailable: false, metricAvailable: false,
            metricScope: "Owned fixture", metricStatus: "No sensor source",
            mailStateAvailable: false, mailStatusText: "Unavailable", mailUnreadCount: null})
        function showFailure(message) { host.failures = host.failures.concat([message]) }
    }
    Connections {
        target: tracker
        function onReported(report) { host.reports = host.reports.concat([report]) }
    }
    Item {
        id: nativeProvider
        width: 202
        height: 150
        property alias visibleLayout: visibleGrid
        property alias hiddenLayout: hiddenGrid
        property alias systemTrayState: nativeState
        property QtObject plasmoid: QtObject {
            property QtObject configuration: QtObject {
                property var hiddenItems: []
                property var shownItems: []
                signal valueChanged(string key, var value)
                function writeConfig() {}
            }
        }
        GridView {
            id: visibleGrid
            width: 202
            height: 150
            cellWidth: 50
            cellHeight: 48
            model: ListModel {
                ListElement { owned: true }
                ListElement { owned: true }
                ListElement { owned: true }
                ListElement { owned: true }
                ListElement { owned: true }
                ListElement { owned: true }
                ListElement { owned: true }
            }
            delegate: Item {
                id: visibleLoader
                required property int index
                width: 50
                height: 48
                property int status: 1
                property alias item: visibleEntry
                Item {
                    id: visibleEntry
                    property string itemId: visibleLoader.index === 0
                        ? "org.kde.plasma.notifications" : "fixture-visible-" + visibleLoader.index
                    property string text: "Owned fixture item"
                    property int status: PlasmaCore.Types.ActiveStatus
                    property var model: ({itemType: "Plasmoid"})
                    property bool active: false
                    property QtObject applet: QtObject {}
                    property alias iconContainer: visibleIcon
                    Item { id: visibleIcon; Layout.preferredWidth: 24; Layout.preferredHeight: 24 }
                }
            }
        }
        GridView {
            id: hiddenGrid
            width: 202
            height: 150
            cellWidth: 50
            cellHeight: 48
            model: ListModel { ListElement { owned: true } }
            delegate: Item {
                id: hiddenLoader
                width: 50
                height: 48
                property int status: 1
                property alias item: hiddenEntry
                Item {
                    id: hiddenEntry
                    property string itemId: "fixture-hidden"
                    property string text: "Owned hidden fixture item"
                    property int status: PlasmaCore.Types.PassiveStatus
                    property var model: ({itemType: "Plasmoid"})
                    property bool active: false
                    property alias iconContainer: hiddenIcon
                    Item { id: hiddenIcon; Layout.preferredWidth: 24; Layout.preferredHeight: 24 }
                }
            }
        }
    }
    QtObject {
        id: nativeState
        property bool expanded: false
        property bool failRequest: false
        property int calls: 0
        property int pendingAtRequest: -1
        property QtObject lastApplet: null
        function setActiveApplet(applet) {
            pendingAtRequest = tracker.pendingCount
            if (failRequest) throw new Error("Sensitive provider details must not escape")
            ++calls
            lastApplet = applet
            expanded = true
        }
    }
    function attach() { panel.integration = integration }
    function invokeAction(action) {
        if (action === "overflow") lastResult = tray.showOverflow()
        else if (action === "status") lastResult = tray.showStatus()
        else if (action === "notifications") lastResult = tray.openNotifications()
        else if (action === "false") lastResult = tray.present("owned-rejected-view", () => false)
        else if (action === "throw") lastResult = tray.present("owned-throwing-view", () => { throw new Error("Private fixture details") })
    }
    function setAvailable(available) { integration.nativeTray = available ? nativeProvider : null }
    function setTracked(tracked) { tray.activity = tracked ? tracker : null }
    function closeOwnPopups() {
        if (tray.snapshot().overflowOpen) tray.showOverflow()
        if (tray.snapshot().statusOpen) tray.showStatus()
        nativeState.expanded = false
    }
}
