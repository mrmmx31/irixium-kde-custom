// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kwin.decoration
import "Geometry.js" as Geometry

Decoration {
    id: root
    alpha: true
    property alias decorationMask: face.decorationMask
    property alias supportsMask: face.supportsMask
    Settings {
        id: localSettings
        borderSize: decorationSettings.borderSize
    }
    DecorationOptions { id: options; deco: decoration }
    readonly property var normalMetrics: Geometry.metrics(localSettings, 0, false)
    readonly property var maximizedMetrics: Geometry.metrics(localSettings, 0, true)
    property bool initialized: false
    function updateBorders() {
        if (!initialized)
            return;
        var normal = normalMetrics;
        var maximized = maximizedMetrics;
        borders.left = normal.left; borders.right = normal.right;
        borders.top = normal.title; borders.bottom = normal.bottom;
        maximizedBorders.left = 0; maximizedBorders.right = 0;
        maximizedBorders.bottom = 0; maximizedBorders.top = maximized.title;
        extendedBorders.setAllBorders(0);
        padding.left = localSettings.paddingLeft; padding.right = localSettings.paddingRight;
        padding.top = localSettings.paddingTop; padding.bottom = localSettings.paddingBottom;
    }
    Surface {
        id: face
        anchors.fill: parent
        settings: localSettings
        activeWindow: decoration.client.active
        maximizedWindow: decoration.client.maximized
        minimizeAllowed: decoration.client.minimizeable
        maximizeAllowed: decoration.client.maximizeable
        caption: decoration.client.caption
        menuIcon: decoration.client.icon
        titleFont: options.titleFont
        onMenuRequested: decoration.requestShowWindowMenu()
        onMinimizeRequested: decoration.requestMinimize()
        onMaximizeRequested: (button) => decoration.requestToggleMaximization(button)
    }
    PreviewBackground {
        previewHost: root.parent
        expectedDecoration: decoration
        metrics: face.metrics
        frameHeight: root.height
        shaded: decoration.client.shaded
    }
    onNormalMetricsChanged: updateBorders()
    onMaximizedMetricsChanged: updateBorders()
    Component.onCompleted: {
        initialized = true;
        updateBorders();
        decoration.installTitleItem(face.titleItem);
    }
}
