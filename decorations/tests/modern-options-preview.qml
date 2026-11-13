// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "../modern-13/package/contents/ui" as Legacy
import "../modern-41/package/contents/ui" as Current

Rectangle {
    id: gallery
    width: 1000; height: 740
    color: "#e6e6e6"
    property int menuCalls: 0
    property int minimizeCalls: 0
    property int maximizeCalls: 0
    property int maximizeButton: 0
    property url previewIcon: Qt.resolvedUrl("../modern/package/assets/applications.png")
    Text { x: 16; y: 8; text: "Irixium 1.3 e 4.1 — pacotes completos; menu, minimizar e maximizar/restaurar"; color: "black" }
    Legacy.Surface {
        id: legacyActive
        objectName: "legacyActive"
        x: 16; y: 40; width: 968; height: 125
        caption: "Irixium 1.3 — ativa"
        menuIcon: gallery.previewIcon
        onMenuRequested: gallery.menuCalls++
        onMinimizeRequested: gallery.minimizeCalls++
        onMaximizeRequested: (button) => { gallery.maximizeCalls++; gallery.maximizeButton = button; }
        Rectangle { x: parent.metrics.left; y: parent.metrics.title; width: parent.width - parent.metrics.left - parent.metrics.right; height: 60; color: "#c0c0c0" }
    }
    Legacy.Surface {
        objectName: "legacyInactive"
        x: 16; y: 175; width: 968; height: 110
        activeWindow: false; caption: "Irixium 1.3 — inativa"
        menuIcon: gallery.previewIcon
        Rectangle { x: parent.metrics.left; y: parent.metrics.title; width: parent.width - parent.metrics.left - parent.metrics.right; height: 50; color: "#c0c0c0" }
    }
    Legacy.Surface {
        objectName: "legacyMaximized"
        x: 16; y: 295; width: 968; height: 65
        maximizedWindow: true; caption: "Irixium 1.3 — maximizada"
        menuIcon: gallery.previewIcon
        Rectangle { y: parent.metrics.title; width: parent.width; height: 25; color: "#c0c0c0" }
    }
    Current.Surface {
        objectName: "currentActive"
        x: 16; y: 370; width: 968; height: 145
        caption: "Irixium 4.1 — ativa; geometria original com padding"
        menuIcon: gallery.previewIcon
        onMenuRequested: gallery.menuCalls++
        onMinimizeRequested: gallery.minimizeCalls++
        onMaximizeRequested: (button) => { gallery.maximizeCalls++; gallery.maximizeButton = button; }
        Rectangle { x: parent.metrics.left + parent.metrics.paddingLeft; y: parent.metrics.title + parent.metrics.paddingTop; width: parent.width - parent.metrics.left - parent.metrics.right - parent.metrics.paddingLeft - parent.metrics.paddingRight; height: 70; color: "#c0c0c0" }
    }
    Current.Surface {
        objectName: "currentInactive"
        x: 16; y: 525; width: 968; height: 110
        activeWindow: false; minimizeAllowed: false; maximizeAllowed: false
        caption: "Irixium 4.1 — inativa; ações indisponíveis"
        menuIcon: gallery.previewIcon
        Rectangle { x: parent.metrics.left + parent.metrics.paddingLeft; y: parent.metrics.title + parent.metrics.paddingTop; width: parent.width - parent.metrics.left - parent.metrics.right - parent.metrics.paddingLeft - parent.metrics.paddingRight; height: 40; color: "#c0c0c0" }
    }
    Current.Surface {
        objectName: "currentMaximized"
        x: 16; y: 645; width: 968; height: 70
        maximizedWindow: true; caption: "Irixium 4.1 — maximizada"
        menuIcon: gallery.previewIcon
        Rectangle { y: parent.metrics.title; width: parent.width; height: 25; color: "#c0c0c0" }
    }
}
