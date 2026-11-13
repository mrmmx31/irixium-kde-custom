// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

// Persist under Tray, rather than under content that moves between windows.
// A source-only checkout retains the original Qt route without the native helper.
Item {
    id: router
    visible: false
    property var popup: null
    property var ownerWindow: null
    property bool closing: false
    property var helper: null
    property var helperComponent: null
    Component.onCompleted: {
        helperComponent = Qt.createComponent(Qt.resolvedUrl("DomainOSNativePopupWheelForwarder.qml"))
        if (helperComponent.status === Component.Ready)
            helper = helperComponent.createObject(router, {
                ownerWindow: Qt.binding(() => router.ownerWindow),
                popupWindow: Qt.binding(() => router.popup && router.popup.contentItem
                    ? router.popup.contentItem.Window.window : null),
                enabled: Qt.binding(() => router.popup && router.popup.visible && !router.closing)
            })
    }
    Connections {
        target: router.popup
        function onAboutToShow() { router.closing = false }
        function onAboutToHide() { router.closing = true }
    }
}
