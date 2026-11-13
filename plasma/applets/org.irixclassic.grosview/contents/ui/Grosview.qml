// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts

Bevel {
    id: monitor
    objectName: "grosviewInstrument"
    implicitWidth: 280
    implicitHeight: 220
    rim: 2
    readonly property var metricDefinitions: [
        {caption: "CPU", sensorId: "cpu/all/usage", percentage: true},
        {caption: "MEM", sensorId: "memory/physical/usedPercent", percentage: true},
        {caption: "SWAP", sensorId: "memory/swap/usedPercent", percentage: true},
        {caption: "I/O R", sensorId: "disk/all/read", percentage: false},
        {caption: "I/O W", sensorId: "disk/all/write", percentage: false},
        {caption: "NET R", sensorId: "network/all/download", percentage: false},
        {caption: "NET W", sensorId: "network/all/upload", percentage: false}
    ]
    readonly property int unavailableSensors: {
        let unavailable = 0;
        for (let index = 0; index < rows.count; ++index) {
            if (!rows.itemAt(index) || !rows.itemAt(index).available) {
                unavailable += 1;
            }
        }
        return unavailable;
    }

    // Test tooling reads the same objects which draw the production meters.
    function sensorSnapshot() {
        let result = [];
        for (let index = 0; index < rows.count; ++index) {
            const item = rows.itemAt(index);
            if (!item) {
                continue;
            }
            result.push({
                sensorId: item.sensorId,
                status: item.sensor.status,
                available: item.available,
                value: item.available ? Number(item.sensor.value) : null,
                formattedValue: item.displayedValue,
                unit: item.sensor.unit,
                sensorName: item.sensor.name,
                updateInterval: item.sensor.updateInterval,
                updateRateLimit: item.sensor.updateRateLimit,
                percentage: item.percentage,
                scaleMaximum: item.scaleMaximum,
                fraction: item.fraction
            });
        }
        return result;
    }

    Text {
        x: 9
        y: 7
        text: "gr_osview"
        color: "#282824"
        font.family: "monospace"
        font.pixelSize: 12
        font.bold: true
    }
    Text {
        anchors.right: parent.right
        anchors.rightMargin: 9
        y: 8
        text: "IRIX Classic"
        color: "#41413b"
        font.family: "monospace"
        font.pixelSize: 10
    }
    Rectangle {
        x: 8
        y: 25
        width: Math.max(0, parent.width - 16)
        height: 1
        color: "#77776b"
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 9
        anchors.rightMargin: 9
        anchors.topMargin: 30
        anchors.bottomMargin: 23
        spacing: 1
        Repeater {
            id: rows
            model: monitor.metricDefinitions
            SensorRow {
                required property var modelData
                Layout.fillWidth: true
                Layout.fillHeight: true
                caption: modelData.caption
                sensorId: modelData.sensorId
                percentage: modelData.percentage
            }
        }
    }
    Text {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 9
        text: monitor.unavailableSensors > 0
            ? qsTr("Waiting for system sensors (%1)").arg(monitor.unavailableSensors)
            : qsTr("1 s · rates: observed peak per bar")
        color: "#41413b"
        font.family: "monospace"
        font.pixelSize: 9
        elide: Text.ElideRight
    }
}
