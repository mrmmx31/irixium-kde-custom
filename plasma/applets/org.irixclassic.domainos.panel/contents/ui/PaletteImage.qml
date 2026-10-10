// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Image {
    id: graphic
    property url assetSource
    readonly property QtObject colorPalette: {
        let ancestor = parent
        while (ancestor) {
            if (ancestor.domainosPalette !== undefined) return ancestor.domainosPalette
            ancestor = ancestor.parent
        }
        return null
    }
    readonly property string assetName: assetSource.toString().split("/").pop()
    source: colorPalette && colorPalette.assetUrls[assetName] !== undefined
        ? colorPalette.assetUrls[assetName] : assetSource
    smooth: false
    mipmap: false
    fillMode: Image.PreserveAspectFit
}
