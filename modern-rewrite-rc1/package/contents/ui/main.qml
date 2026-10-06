// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kwin.decoration

Decoration {
    id: root
    alpha: true
    Settings { id: localSettings }
    function updateBorders() {
        if (!borders || !maximizedBorders || !extendedBorders || !padding)
            return;
        borders.setBorders(7);
        borders.setTitle(34);
        maximizedBorders.setAllBorders(0);
        maximizedBorders.setTitle(34);
        extendedBorders.setAllBorders(0);
        padding.setAllBorders(0);
    }
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
        closeAllowed: decoration.client.closeable
        closeOnDouble: localSettings.menuDoubleClickClosesWindow
        menuOnPress: localSettings.menuOpensOnPress
        caption: decoration.client.caption
        titleFamily: localSettings.titleFamily
        titlePixels: localSettings.titlePixels
        titleItalic: localSettings.titleItalic
        titleBold: localSettings.titleBold
        onMenuRequested: {
            var r = face.metrics.menu;
            decoration.requestShowWindowMenu(Qt.rect(r.x, r.y, r.w, r.h));
        }
        onMinimizeRequested: {
            if (decoration.client.minimizeable)
                decoration.requestMinimize();
        }
        onMaximizeRequested: (button) => {
            if (decoration.client.maximizeable)
                decoration.requestToggleMaximization(button);
        }
        onCloseRequested: {
            if (decoration.client.closeable)
                decoration.requestClose();
        }
    }
    onWidthChanged: updateBorders()
    onHeightChanged: updateBorders()
    Component.onCompleted: {
        updateBorders();
        decoration.installTitleItem(face.titleItem);
    }
}
