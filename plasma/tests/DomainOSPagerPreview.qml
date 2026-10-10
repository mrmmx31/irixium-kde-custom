// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls
import "../applets/org.irixclassic.domainos.panel/contents/ui" as DomainOS

ApplicationWindow {
    id: window
    objectName: "domainosPagerNativeTestWindow"
    visible: true
    width: 700; height: 400
    flags: Qt.Tool | Qt.WindowStaysOnTopHint
    title: "DomainOS Pager — isolated native test"
    color: "#3e536e"
    property var completedOperations: []
    property var errors: []
    Item {
        x: 12; y: 12
        width: 342; height: 150
        readonly property real domainosRenderScale: 1
        DomainOS.DomainOSPager {
            id: pager
            anchors.fill: parent
            onOperationFinished: (operation,success,details) => {
                window.completedOperations = window.completedOperations.concat([{operation:operation,success:success,details:details}])
            }
            onFailure: message => window.errors = window.errors.concat([message])
        }
    }
}
