// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

Item {
    id: frame
    // Popups are visually reparented into Qt's overlay, outside the drawing.
    // An explicit palette keeps their relief/texture on the same scheme.
    property QtObject paletteOverride: null
    readonly property QtObject colorPalette: {
        if (frame.paletteOverride) return frame.paletteOverride
        let ancestor = parent
        while (ancestor) {
            if (ancestor.domainosPalette !== undefined) return ancestor.domainosPalette
            ancestor = ancestor.parent
        }
        return null
    }
    readonly property QtObject domainosPalette: colorPalette
    property color face: colorPalette ? colorPalette.background : "#7894a7"
    property color light: colorPalette ? colorPalette.highlight : "#c5e8e6"
    property color dark: colorPalette ? colorPalette.dark : "#194b63"
    property bool sunken: false
    property int thickness: 4
    property url texture
    property bool simpleRelief: false
    property int grooveCount: 0
    // Find the enclosing drawing's scale; outlines and texture stay on its
    // rendered pixel grid rather than losing half-pixel highlights at 50%.
    readonly property real pixelScale: {
        var ancestor = parent
        while (ancestor) {
            if (ancestor.domainosRenderScale !== undefined)
                return Math.max(0.01, ancestor.domainosRenderScale)
            ancestor = ancestor.parent
        }
        return 1
    }
    readonly property int bandCount: Math.max(1, Math.round(thickness * pixelScale))
    readonly property real pixelStep: 1 / pixelScale
    readonly property real inset: bandCount * pixelStep
    readonly property var raisedTop: [light, colorPalette ? colorPalette.cyan : "#7acac5", colorPalette ? colorPalette.shadow : "#3e536e", colorPalette ? colorPalette.pale : "#a3d0e6"]
    readonly property var raisedBottom: [dark, colorPalette ? colorPalette.shadow : "#3e536e", colorPalette ? colorPalette.pale : "#a3d0e6", face]
    function edgeColor(layer, upper) {
        if (thickness === 1 || simpleRelief)
            return (upper !== sunken) ? light : dark
        const colors = (upper !== sunken) ? raisedTop : raisedBottom
        return colors[Math.min(layer, colors.length-1)]
    }
    Rectangle { anchors.fill: parent; color: frame.face; antialiasing: false }
    Item {
        id: textureLayer
        x: frame.inset; y: frame.inset
        // Image.Tile uses the destination size to center its pattern. Keep
        // that phase on an integer physical pixel even at fractional scales.
        width: Math.ceil(Math.max(0, frame.width-2*frame.inset) * frame.pixelScale)
        height: Math.ceil(Math.max(0, frame.height-2*frame.inset) * frame.pixelScale)
        scale: frame.pixelStep
        transformOrigin: Item.TopLeft
        clip: true
        PaletteImage {
            anchors.fill: parent
            assetSource: frame.texture
            fillMode: Image.Tile
            smooth: false
            mipmap: false
        }
        readonly property int grooveTop: Math.floor((height-frame.grooveCount*3)/2)
        Rectangle {
            visible: frame.grooveCount > 0
            x: 0; y: textureLayer.grooveTop-1
            width: parent.width; height: 1; color: frame.dark
        }
        Repeater {
            model: frame.grooveCount
            delegate: Item {
                required property int index
                x: 0; y: textureLayer.grooveTop+index*3
                width: textureLayer.width; height: 3
                Rectangle { width: parent.width; height: 1; color: frame.light }
                PaletteImage { y: 1; width: parent.width; height: 1; assetSource: frame.texture; fillMode: Image.Tile; smooth: false; mipmap: false }
                Rectangle { y: 2; width: parent.width; height: 1; color: frame.dark }
            }
        }
        Rectangle {
            visible: frame.grooveCount > 0
            x: 0; y: textureLayer.grooveTop+frame.grooveCount*3
            width: parent.width; height: 1; color: frame.light
        }
    }
    Repeater {
        model: frame.bandCount
        delegate: Item {
            required property int index
            anchors.fill: parent
            readonly property real offset: index * frame.pixelStep
            Rectangle { x: offset; y: offset; width: frame.width-2*offset; height: frame.pixelStep; color: frame.edgeColor(index, true) }
            Rectangle { x: offset; y: offset; width: frame.pixelStep; height: frame.height-2*offset; color: frame.edgeColor(index, true) }
            Rectangle { x: offset; y: frame.height-offset-frame.pixelStep; width: frame.width-2*offset; height: frame.pixelStep; color: frame.edgeColor(index, false) }
            Rectangle { x: frame.width-offset-frame.pixelStep; y: offset; width: frame.pixelStep; height: frame.height-2*offset; color: frame.edgeColor(index, false) }
        }
    }
}
