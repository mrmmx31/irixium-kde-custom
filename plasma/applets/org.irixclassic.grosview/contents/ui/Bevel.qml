// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Rectangle {
    id: frame
    property bool inset: false
    property int rim: 2
    color: "#c1c1c1"
    border.color: "#41413b"
    border.width: 1

    Rectangle {
        x: 1
        y: 1
        width: Math.max(0, parent.width - 2)
        height: frame.rim
        color: frame.inset ? "#6c6c62" : "#f4f4e9"
    }
    Rectangle {
        x: 1
        y: 1
        width: frame.rim
        height: Math.max(0, parent.height - 2)
        color: frame.inset ? "#6c6c62" : "#f4f4e9"
    }
    Rectangle {
        x: 1 + frame.rim
        y: parent.height - 1 - frame.rim
        width: Math.max(0, parent.width - 2 - frame.rim)
        height: frame.rim
        color: frame.inset ? "#f4f4e9" : "#6c6c62"
    }
    Rectangle {
        x: parent.width - 1 - frame.rim
        y: 1 + frame.rim
        width: frame.rim
        height: Math.max(0, parent.height - 2 - frame.rim)
        color: frame.inset ? "#f4f4e9" : "#6c6c62"
    }
}
