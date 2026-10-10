// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

QtObject {
    id: activity
    property bool keepLightAfterCompletion: false
    // Implementation initial value, not a duration chosen by the user.
    property int extraLightMilliseconds: 1000
    property var pending: ({})
    property bool tailLit: false
    readonly property int pendingCount: Object.keys(pending).length
    readonly property bool lit: pendingCount > 0 || tailLit
    // A synchronous acknowledgement can arrive before Qt paints even one frame.
    // This is a presentation receipt, not a pending operation or extra duration.
    property bool presentationPending: false
    readonly property bool displayLit: lit || presentationPending
    property int sequence: 0
    property var lastReport: ({})
    signal reported(var report)

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
        if (!pendingCount && keepLightAfterCompletion && extraLightMilliseconds > 0) {
            tailLit = true
            extinction.restart()
        }
        return true
    }
    onKeepLightAfterCompletionChanged: {
        if (!keepLightAfterCompletion) { extinction.stop(); tailLit = false }
    }
    // This is the explicitly requested optional light tail. It never starts
    // a command, waits for a click, delays a result or forces a repaint.
    property Timer extinction: Timer {
        interval: Math.max(1, activity.extraLightMilliseconds)
        repeat: false
        onTriggered: activity.tailLit = false
    }
}
