// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

// Retains only a rendered in-memory frame. The QQuickItemGrabResult is held
// strongly so its image:// URL remains valid while the tooltip is hidden.
Item {
    id: cache
    objectName: "domainosThumbnailFrameCache"
    property Item sourceItem: null
    property string identity: ""
    // Keep the result reachable from the QML/JavaScript heap. Qt documents
    // itemgrabber URLs as valid only while the ItemGrabResult is referenced.
    property var frameReference: null
    property url retainedUrl: ""
    property bool capturePending: false
    property int generation: 0
    readonly property bool hasFrame: typeof frameReference === "function"
        && retainedUrl.toString().length > 0
    readonly property url frameUrl: hasFrame ? retainedUrl : ""

    function clear() {
        generation += 1
        capturePending = false
        frameReference = null
        retainedUrl = ""
    }

    function capture() {
        const source = sourceItem
        if (!source || !source.visible || capturePending || !identity)
            return false
        const requestedIdentity = identity
        const requestedGeneration = ++generation
        capturePending = true
        const accepted = source.grabToImage(function(result) {
            if (requestedGeneration !== cache.generation
                    || requestedIdentity !== cache.identity) return
            cache.capturePending = false
            if (result && result.url.toString().length > 0) {
                const capturedResult = result
                cache.frameReference = function() { return capturedResult }
                cache.retainedUrl = capturedResult.url
            }
        })
        if (!accepted) {
            capturePending = false
        }
        return accepted
    }

    onIdentityChanged: clear()
}
