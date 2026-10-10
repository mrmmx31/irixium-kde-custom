// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "PreviewSupport.js" as PreviewSupport

Loader {
    id: previewFill
    objectName: "irixClassicPreviewBackground"
    property var previewHost: null
    property var expectedDecoration: null
    property var metrics: null
    property real frameHeight: 0
    property bool shaded: false

    readonly property bool isPreview: PreviewSupport.isPreviewHost(previewHost, expectedDecoration)
    readonly property var clientRect: PreviewSupport.clientRect(metrics, frameHeight, shaded)
    readonly property color windowColor: isPreview ? previewHost.windowColor : "transparent"

    x: clientRect.x
    y: clientRect.y
    width: clientRect.w
    height: clientRect.h
    active: PreviewSupport.needsFill(previewHost, expectedDecoration) && width > 0 && height > 0
    visible: active
    enabled: false // Presentation only: never intercept title/menu/pointer input.

    // No Rectangle is instantiated for a real window. Keep the native client
    // area transparent and leave alpha handling and the shared artwork untouched.
    sourceComponent: Rectangle {
        objectName: "irixClassicPreviewClientFill"
        color: Qt.rgba(previewFill.windowColor.r,
                       previewFill.windowColor.g,
                       previewFill.windowColor.b, 1)
        antialiasing: false
    }
}
