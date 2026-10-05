// SPDX-License-Identifier: GPL-3.0-or-later
// Uses the public Aurorae Decoration/Borders interface; no shared QML is patched.
import QtQuick
import org.kde.kwin.decoration
Decoration {
    id: root
    alpha: true
    Appearance { id: appearance }
    readonly property int pixelScale: Math.max(1, Math.min(3, appearance.pixelScale))
    function configureBorders() {
        if (!borders || !maximizedBorders || !extendedBorders || !padding) return;
        borders.setBorders(8 * pixelScale);
        borders.setTitle(32 * pixelScale);
        maximizedBorders.setAllBorders(0);
        maximizedBorders.setTitle(24 * pixelScale);
        extendedBorders.setAllBorders(0);
        padding.setAllBorders(0);
    }
    ClassicSurface {
        id: face
        anchors.fill: parent
        activeWindow: decoration.client.active
        maximizedWindow: decoration.client.maximized
        minimizeAllowed: decoration.client.minimizeable
        maximizeAllowed: decoration.client.maximizeable
        caption: decoration.client.caption
        pixelScale: root.pixelScale
        titleFamily: appearance.titleFamily
        titlePixels: Math.max(10, Math.min(18, appearance.titlePixels))
        titleItalic: appearance.titleItalic
        titleBold: appearance.titleBold
        onMenuActivated: (mouseButton) => decoration.requestShowWindowMenu()
        onMenuDoubleActivated: (mouseButton) => {
            if (mouseButton === Qt.LeftButton
                    && decorationSettings.closeOnDoubleClickOnMenu
                    && decoration.client.closeable)
                decoration.requestClose();
        }
        onMinimizeActivated: decoration.requestMinimize()
        onMaximizeActivated: (mouseButton) => decoration.requestToggleMaximization(mouseButton)
    }
    onPixelScaleChanged: configureBorders()
    Component.onCompleted: {
        configureBorders();
        decoration.installTitleItem(face.titleItem);
    }
}
