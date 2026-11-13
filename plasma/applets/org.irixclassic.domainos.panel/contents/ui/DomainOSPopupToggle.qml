// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

// A native popup can dismiss itself when its launcher receives the press.
// Keep the state at that press, as Plasma's own clock and application menu do,
// so releasing the same button closes it instead of reopening it. There is no
// delayed action or presentation timer; pointer cancellation discards the press.
Item {
    id: toggle
    property Item anchor: null
    property bool showing: false
    property bool pressCaptured: false
    property bool wasShowing: false
    property Item lastAnchor: null
    property bool dismissedDuringEvent: false

    // Popup.Window can dismiss on native focus transfer before delivering
    // that same mouse press to its launcher. Retain the dismissal only for
    // the current event dispatch; Escape/other dismissal leaves no latch for
    // a later click. This schedules state cleanup, never the button's action.
    function clearDismissal() { dismissedDuringEvent = false }
    onShowingChanged: if (!showing) {
        dismissedDuringEvent = true
        Qt.callLater(clearDismissal)
    }

    function shouldOpen(nextAnchor) {
        // A shared popup may represent another group or launcher. Switching
        // to that new opener must show its content; only the same one toggles.
        const open = nextAnchor !== lastAnchor ? true
            : nextAnchor === anchor && pressCaptured ? !wasShowing : !showing
        pressCaptured = false
        // Keep an external anchor binding when it already tracks the opener.
        if (nextAnchor !== anchor) anchor = nextAnchor
        lastAnchor = nextAnchor
        return open
    }
    function cancelPress() { pressCaptured = false }
    Connections {
        target: toggle.anchor
        ignoreUnknownSignals: true
        function onPointerPressed() {
            toggle.wasShowing = toggle.showing || toggle.dismissedDuringEvent
            toggle.pressCaptured = true
        }
        function onPointerCancelled() { toggle.cancelPress() }
    }
}
