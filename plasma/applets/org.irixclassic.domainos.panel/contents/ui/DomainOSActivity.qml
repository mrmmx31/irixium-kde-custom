// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.taskmanager as TaskManager

QtObject {
    id: activity
    property bool keepLightAfterCompletion: false
    // Implementation initial value, not a duration chosen by the user.
    property int extraLightMilliseconds: 1000
    property var pending: ({})
    // KDE's real startup records end when startup tracking ends; a launcher's
    // quick reply is a separate event. Never match arbitrary windows by title
    // or PID and never invent a client timeout.
    property var startupModel: null
    property int startupCount: 0
    property int startupObservationFailures: 0
    property bool tailLit: false
    readonly property int pendingCount: Object.keys(pending).length
    readonly property int busyCount: pendingCount + startupCount
    readonly property bool busy: busyCount > 0
    readonly property bool lit: busy || tailLit
    // VUE 2.01 waitingBlinkRate: 500ms per half-cycle. This presentation
    // timer only toggles the LED; it does not submit, postpone or retry work.
    property bool blinkOn: true
    // A synchronous acknowledgement can arrive before Qt paints even one frame.
    // This is a presentation receipt, not a pending operation or extra duration.
    property bool presentationPending: false
    readonly property bool displayLit: presentationPending || tailLit || (busy && blinkOn)
    property int sequence: 0
    property var lastReport: ({})
    property int previousBusyCount: 0
    signal reported(var report)

    function refreshStartups() {
        let count = 0
        try {
            if (startupModel) {
                for (let row = 0; row < startupModel.count; ++row) {
                    const index = startupModel.makeModelIndex(row)
                    if (startupModel.data(index, TaskManager.AbstractTasksModel.IsStartup) === true)
                        ++count
                }
            }
        } catch (error) {
            // An unavailable provider must not strand the wait cursor/light.
            ++startupObservationFailures
            count = 0
        }
        if (count > startupCount) {
            ++sequence
            presentationPending = true
        }
        startupCount = count
    }
    onStartupModelChanged: Qt.callLater(refreshStartups)
    property Connections startupChanges: Connections {
        target: activity.startupModel
        ignoreUnknownSignals: true
        function onCountChanged() { Qt.callLater(activity.refreshStartups) }
        function onDataChanged() { Qt.callLater(activity.refreshStartups) }
        function onRowsInserted() { Qt.callLater(activity.refreshStartups) }
        function onRowsRemoved() { Qt.callLater(activity.refreshStartups) }
        function onModelReset() { Qt.callLater(activity.refreshStartups) }
        function onLayoutChanged() { Qt.callLater(activity.refreshStartups) }
        function onDestroyed() { Qt.callLater(activity.refreshStartups) }
    }

    function begin(label) {
        extinction.stop()
        tailLit = false
        const token = ++sequence
        presentationPending = true
        const next = Object.assign({}, pending)
        next[token] = label
        pending = next
        return token
    }
    function acknowledgePresentation(presentedSequence) {
        if (presentedSequence !== sequence || !presentationPending) return false
        presentationPending = false
        return true
    }
    function finish(token, report) {
        if (pending[token] === undefined) return false
        const next = Object.assign({}, pending)
        delete next[token]
        pending = next
        lastReport = report
        reported(report)
        return true
    }
    onKeepLightAfterCompletionChanged: {
        if (!keepLightAfterCompletion) { extinction.stop(); tailLit = false }
    }
    onBusyCountChanged: {
        if (busyCount > 0) {
            extinction.stop()
            tailLit = false
            if (!previousBusyCount) blinkOn = true
        } else {
            blinkOn = true
            if (previousBusyCount && keepLightAfterCompletion && extraLightMilliseconds > 0) {
                tailLit = true
                extinction.restart()
            }
        }
        previousBusyCount = busyCount
    }
    property Timer busyBlink: Timer {
        objectName: "domainosBusyBlink"
        interval: 500
        repeat: true
        running: activity.busy
        onTriggered: activity.blinkOn=!activity.blinkOn
    }
    // This is the explicitly requested optional light tail. It never starts
    // a command, waits for a click, delays a result or forces a repaint.
    property Timer extinction: Timer {
        interval: Math.max(1, activity.extraLightMilliseconds)
        repeat: false
        onTriggered: activity.tailLit = false
    }
}
