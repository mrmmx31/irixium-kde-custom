// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import org.kde.ksysguard.sensors as Sensors

RowLayout {
    id: row
    objectName: "grosviewSensorRow"
    required property string caption
    required property string sensorId
    property bool percentage: false
    property int updateRateLimit: 1000
    property real observedPeak: 0
    property alias sensor: source
    readonly property bool available: source.status === Sensors.Sensor.Ready
        && source.value !== undefined && source.value !== null
        && Number.isFinite(Number(source.value)) && Number(source.value) >= 0
    readonly property real sample: available ? Number(source.value) : 0
    readonly property real scaleMaximum: percentage ? 100 : observedPeak
    readonly property real fraction: available && scaleMaximum > 0
        ? Math.max(0, Math.min(1, sample / scaleMaximum)) : 0
    readonly property string displayedValue: available ? source.formattedValue : "—"
    spacing: 5
    implicitHeight: 22

    function recordPeak() {
        // Read the signal source directly. Derived QML bindings may still hold
        // the previous sample while valueChanged handlers are being dispatched.
        const value = source.value;
        if (!row.percentage && source.status === Sensors.Sensor.Ready
                && value !== undefined && value !== null
                && Number.isFinite(Number(value)) && Number(value) >= 0) {
            row.observedPeak = Math.max(row.observedPeak, Number(value));
        }
    }

    Sensors.Sensor {
        id: source
        sensorId: row.sensorId
        updateRateLimit: row.updateRateLimit
        onValueChanged: row.recordPeak()
        onStatusChanged: row.recordPeak()
    }

    Text {
        Layout.preferredWidth: 43
        Layout.fillHeight: true
        text: row.caption
        color: "#282824"
        font.family: "monospace"
        font.pixelSize: 11
        font.bold: true
        verticalAlignment: Text.AlignVCenter
    }
    Bevel {
        id: meter
        objectName: "grosviewMeter"
        Layout.fillWidth: true
        Layout.preferredHeight: 17
        inset: true
        rim: 1
        color: "#b2b2a8"

        Item {
            anchors.fill: parent
            anchors.margins: 2
            clip: true
            Rectangle {
                objectName: "grosviewMeterFill"
                width: Math.round(parent.width * row.fraction)
                height: parent.height
                color: "#9ebfbf"
            }
            Repeater {
                model: 9
                Rectangle {
                    required property int index
                    x: Math.round(parent.width * (index + 1) / 10)
                    width: 1
                    height: parent.height
                    color: "#77776b"
                }
            }
        }
    }
    Text {
        Layout.preferredWidth: 78
        Layout.fillHeight: true
        text: row.displayedValue
        color: row.available ? "#282824" : "#6c6c62"
        font.family: "monospace"
        font.pixelSize: 10
        horizontalAlignment: Text.AlignRight
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
