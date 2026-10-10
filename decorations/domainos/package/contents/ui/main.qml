// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kwin.decoration
Decoration {
    id:root
    alpha:true
    Settings { id:localSettings }
    DecorationOptions { id:colors; deco:decoration }
    readonly property int gridScale:Math.max(1,Math.min(3,localSettings.pixelScale))
    readonly property bool resizeAllowed:decoration.client.resizeable
    function updateBorders() {
        if (!borders || !maximizedBorders || !extendedBorders || !padding) return;
        borders.setBorders((resizeAllowed ? 11 : 6)*gridScale);
        borders.setTitle((resizeAllowed ? 30 : 25)*gridScale);
        maximizedBorders.setAllBorders(0);
        maximizedBorders.setTitle(20*gridScale);
        extendedBorders.setAllBorders(0);
        padding.setAllBorders(0);
    }
    PreviewBackground {
        previewHost:root.parent
        expectedDecoration:decoration
        metrics:face.metrics
        frameHeight:root.height
        shaded:decoration.client.shaded
    }
    Surface {
        id:face
        anchors.fill:parent
        activeWindow:decoration.client.active
        faceColor:colors.titleBarColor
        captionColor:colors.fontColor
        maximizedWindow:decoration.client.maximized
        resizeAllowed:root.resizeAllowed
        minimizeAllowed:decoration.client.minimizeable
        maximizeAllowed:decoration.client.maximizeable
        closeOnDouble:decoration.client.closeable
        menuOnPress:false
        caption:decoration.client.caption
        pixelScale:root.gridScale
        titleFamily:localSettings.titleFamily
        titlePixels:Math.max(8,Math.min(24,localSettings.titlePixels))
        titleItalic:localSettings.titleItalic
        titleBold:localSettings.titleBold
        onMenuRequested: {
            var r=face.metrics.menu;
            decoration.requestShowWindowMenu(Qt.rect(r.x,r.y,r.w,r.h));
        }
        onCloseRequested: {
            if (decoration.client.closeable) decoration.requestClose();
        }
        onMinimizeRequested: {
            if (decoration.client.minimizeable) decoration.requestMinimize();
        }
        onMaximizeRequested:(button)=> {
            if (decoration.client.maximizeable) decoration.requestToggleMaximization(button);
        }
    }
    onGridScaleChanged:updateBorders()
    onResizeAllowedChanged:updateBorders()
    Component.onCompleted: {
        updateBorders();
        decoration.installTitleItem(face.titleItem);
    }
}
