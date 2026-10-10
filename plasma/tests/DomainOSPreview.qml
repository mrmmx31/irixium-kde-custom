// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Window
import "../applets/org.irixclassic.domainos.panel/contents/ui" as DomainOS

Window {
    id: window
    objectName: "domainosDesignPreview"
    width: 2103
    height: 748
    visible: true
    color: "white"
    title: "Irix Classic DomainOS — design review"
    property real drawingScale: 1
    DomainOS.DomainOSPanel {
        id: panel
        followSystemColors: false
        x: 112
        y: 296
        width: 1942*window.drawingScale
        height: 218*window.drawingScale
    }
}
