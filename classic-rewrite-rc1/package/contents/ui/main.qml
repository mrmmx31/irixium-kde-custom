// SPDX-License-Identifier: GPL-3.0-or-later
// KWin adapter. Artwork and gesture components do not depend on the native API.
import QtQuick
import org.kde.kwin.decoration
Decoration {
    id: root
    alpha: true
    Settings { id: localSettings }
    readonly property int gridScale: Math.max(1,Math.min(3,localSettings.pixelScale))
    function updateBorders() {
        if (!borders || !maximizedBorders || !extendedBorders || !padding) return;
        borders.setBorders(8*gridScale);
        borders.setTitle(32*gridScale);
        maximizedBorders.setAllBorders(0);
        maximizedBorders.setTitle(24*gridScale);
        extendedBorders.setAllBorders(0);
        padding.setAllBorders(0);
    }
    // Aurorae disables PreviewItem's automatic background. Restore only the
    // thumbnail's client area, using the preview host's window palette color.
    PreviewBackground {
        previewHost: root.parent
        expectedDecoration: decoration
        metrics: face.metrics
        frameHeight: root.height
        shaded: decoration.client.shaded
    }
    Surface {
        id: face
        anchors.fill: parent
        activeWindow: decoration.client.active
        maximizedWindow: decoration.client.maximized
        minimizeAllowed: decoration.client.minimizeable
        maximizeAllowed: decoration.client.maximizeable
        // IRIX_CLASSIC_IMMEDIATE_MENU_R1: enforce dispatch on press here.
        // The installer preserves old Settings.qml values, so changing only
        // their defaults would silently restore the unwanted waiting policy.
        // Title-bar and application double-click behavior remain native.
        closeOnDouble: false
        menuOnPress: true
        caption: decoration.client.caption
        pixelScale: root.gridScale
        titleFamily: localSettings.titleFamily
        titlePixels: Math.max(10,Math.min(18,localSettings.titlePixels))
        titleItalic: localSettings.titleItalic
        titleBold: localSettings.titleBold
        onMenuRequested: {
            var r = face.metrics.menu;
            decoration.requestShowWindowMenu(Qt.rect(r.x,r.y,r.w,r.h));
        }
        onMinimizeRequested: {
            if (decoration.client.minimizeable) decoration.requestMinimize();
        }
        onMaximizeRequested: (button) => {
            if (decoration.client.maximizeable) decoration.requestToggleMaximization(button);
        }
    }
    onGridScaleChanged: updateBorders()
    Component.onCompleted: {
        updateBorders();
        decoration.installTitleItem(face.titleItem);
    }
}
