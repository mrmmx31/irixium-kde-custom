// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

// One hover owns the compositor effect. A late exit from the previous cell
// must not cancel the new cell's highlight. Text hints and captures are separate.
QtObject {
    id: highlight
    objectName: "domainosWindowHighlight"
    property bool enabled: false
    property var backend: null
    property var currentRecord: null
    function clear() {
        if (backend) backend.highlightRecord(null, false)
        currentRecord = null
    }
    function enter(record) {
        if (!enabled || !backend) {
            if (currentRecord) clear()
            return false
        }
        if (!backend.validHighlightRecord(record)) {
            clear()
            return false
        }
        clear()
        if (!backend.highlightRecord(record, true)) return false
        currentRecord = record
        return true
    }
    function leave(record) {
        if (currentRecord && record && currentRecord.key === record.key && currentRecord.pid === record.pid) clear()
    }
    function validate() {
        if (currentRecord && (!enabled || !backend || !backend.validHighlightRecord(currentRecord))) clear()
    }
    onEnabledChanged: if (!enabled) clear()
    onBackendChanged: clear()
    Component.onDestruction: clear()
}
