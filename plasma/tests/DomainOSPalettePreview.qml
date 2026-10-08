// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Window
import "../applets/org.irixclassic.domainos.panel/contents/ui" as DomainOS

Window {
    id: window
    objectName: "domainosPalettePreview"
    width: 1051
    height: 410
    visible: true
    color: "white"
    title: "DomainOS — isolated palette validation"
    property real drawingScale: 0.5
    property bool followSystemColors: false
    property url referenceUrl
    readonly property bool referenceReady: reference.status === Loader.Ready
    function imageInventory() {
        let result = {}
        let index = 0
        function inspect(node) {
            if (node.source !== undefined && node.source.toString().length > 0) {
                // Bevel bands add Rectangles at another drawing scale. Index
                // only images so those extra bands do not change identities.
                const key = String(index++)
                const original = node.assetSource !== undefined && node.assetSource.toString().length > 0
                    ? node.assetSource.toString() : node.source.toString()
                result[key] = {
                    name: original.split("/").pop(),
                    url: node.source.toString(),
                    status: node.status,
                    svg: original.toLowerCase().endsWith(".svg")
                }
            }
            for (let child of node.children) inspect(child)
        }
        inspect(candidate)
        return JSON.stringify(result)
    }
    DomainOS.DomainOSPanel {
        id: candidate
        objectName: "domainosPaletteCandidate"
        x: 40
        y: 40
        width: 1942 * window.drawingScale
        height: 218 * window.drawingScale
        followSystemColors: window.followSystemColors
    }
    Loader {
        id: reference
        objectName: "domainosPaletteReferenceLoader"
        x: 40
        y: 250
        width: 971
        height: 109
        source: window.referenceUrl
    }
}
