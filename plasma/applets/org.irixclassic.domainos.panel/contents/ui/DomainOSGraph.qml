// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: graph
    property var instruments
    readonly property QtObject colorPalette: {
        let ancestor = parent
        while (ancestor) {
            if (ancestor.domainosPalette !== undefined) return ancestor.domainosPalette
            ancestor = ancestor.parent
        }
        return null
    }
    readonly property bool measurementAvailable: !!instruments && instruments.metricAvailable
    readonly property int samples: measurementAvailable
        ? Math.max(instruments.primaryHistory.length, instruments.secondaryHistory.length) : 0
    clip: true
    Rectangle { anchors.fill: parent; color: graph.colorPalette.blue }
    Repeater {
        model: graph.measurementAvailable ? graph.instruments.primaryHistory : []
        Rectangle {
            required property int index
            required property var modelData
            x: graph.width - (graph.samples - index) * graph.width / Math.max(1, graph.instruments.historyLength)
            width: Math.max(1, graph.width / Math.max(1, graph.instruments.historyLength))
            height: modelData === null || graph.instruments.scaleMaximum <= 0 ? 0
                : Math.min(graph.height, Math.max(1, Number(modelData) / graph.instruments.scaleMaximum * graph.height))
            y: graph.height - height
            color: graph.colorPalette.white
            visible: modelData !== null
        }
    }
    // Preserve the approved face's three divisions at 8/35, 16/35 and 24/35.
    Repeater {
        model: 3
        Rectangle {
            required property int index
            y: graph.height * (index + 1) * 8 / 35
            width: graph.width; height: graph.height / 35
            color: graph.colorPalette.black
        }
    }
    Repeater {
        model: graph.measurementAvailable ? graph.instruments.secondaryHistory : []
        Rectangle {
            required property int index
            required property var modelData
            x: graph.width - (graph.samples - index) * graph.width / Math.max(1, graph.instruments.historyLength)
            width: Math.max(1, graph.width / Math.max(1, graph.instruments.historyLength))
            height: 2
            y: graph.height - (modelData === null || graph.instruments.scaleMaximum <= 0 ? 0
                : Math.min(graph.height, Number(modelData) / graph.instruments.scaleMaximum * graph.height))
            color: graph.colorPalette.text
            visible: modelData !== null
        }
    }
    Text {
        anchors.centerIn: parent; text: "—"
        visible: !graph.measurementAvailable
        color: graph.colorPalette.white; font.pixelSize: 24
    }
    Accessible.name: graph.instruments ? graph.instruments.metricScope : ""
    Accessible.description: graph.instruments ? graph.instruments.metricStatus : ""
}
