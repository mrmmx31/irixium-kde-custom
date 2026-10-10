// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Window
import "../applets/org.irixclassic.domainos.panel/contents/ui" as DomainOS

Window {
    id: window
    objectName: "domainosSelectionPreview"
    width: 1051
    height: 189
    visible: true
    color: "#303030"
    title: "DomainOS — isolated selection validation"
    function imageInventory() {
        let result = {}
        let index = 0
        function inspect(node) {
            if (node.source !== undefined && node.source.toString().length > 0) {
                const original = node.assetSource !== undefined && node.assetSource.toString().length > 0
                    ? node.assetSource.toString() : node.source.toString()
                result[String(index++)] = {
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
        objectName: "domainosSelectionCandidate"
        x: 40
        y: 40
        width: 971
        height: 109
        followSystemColors: true
        simulateSelection: true
        selectedTaskIndex: 0
    }
}
