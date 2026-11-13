// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

// Production composition shared with isolated functional hosts. The approved
// reference stays separately available through DomainOSPanel without runtime.
DomainOSPanel {
    id: panel
    property var settings: ({})
    property var hostItem: null
    property rect screenGeometry: Qt.rect(0, 0, 0, 0)
    property rect availableGeometry: screenGeometry
    property string screenName: ""
    property var nativeTray: null
    property string instanceId: "isolated"
    signal configureRequested()
    signal pinListRequested(var pins)
    // Read-only diagnostics for the native host. Nothing is sampled, launched,
    // serialized or written merely by painting/pressing the panel.
    function diagnosticSnapshot() {
        return JSON.stringify({phase:phase,scale:drawingScale,
            timeAvailable:runtime.instruments.timeAvailable,date:dateText,
            sensors:runtime.instruments.sensorSnapshot(),workspaceCount:workspaceCount,
            activity:{lit:runtime.activity.lit,pending:runtime.activity.pendingCount},
            commands:runtime.commands.lastReport,catalogCount:runtime.applications.catalogModel.count,
            pins:runtime.applications.pins,taskCount:taskCount,
            taskProviderAvailable:!!runtime.tasks.tasksModel,
            nativeMenuReady:nativeIconbox && nativeIconbox.nativeMenuBridge
                && nativeIconbox.nativeMenuBridge.contextComponent.status===Component.Ready,
            tray:nativeTrayView ? nativeTrayView.snapshot() : null,
            palette:{background:String(colorPalette.background),recessed:String(colorPalette.recessed),
                text:String(colorPalette.text),blue:String(colorPalette.blue),white:String(colorPalette.white)}})
    }
    integration: runtime
    clockHour: runtime.instruments.clockHour
    clockMinute: runtime.instruments.clockMinute
    dateText: runtime.instruments.dateText
    DomainOSRuntime {
        id: runtime
        settings: panel.settings; hostItem: panel.hostItem; colorPalette: panel.colorPalette
        screenGeometry: panel.screenGeometry; instanceId: panel.instanceId
        availableGeometry: panel.availableGeometry; screenName: panel.screenName
        nativeTray: panel.nativeTray
        onConfigureRequested: panel.configureRequested()
        onPinListRequested: pins => panel.pinListRequested(pins)
    }
}
