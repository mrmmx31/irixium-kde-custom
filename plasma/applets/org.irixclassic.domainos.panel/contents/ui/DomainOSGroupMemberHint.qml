// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Window
import QtQuick.Controls as Controls
import org.kde.kwindowsystem
import org.kde.kirigami as Kirigami

// One selector owns one native tooltip lease. Its parent and role are fixed
// before mapping, and it is destroyed before the next lease or parent closes.
// This window never joins Controls' popup/grab stack or Plasma's shared dialog.
Item {
    id: memberHint
    property bool previewsEnabled: false
    property bool hintsEnabled: true
    property bool titleTruncated: false
    property QtObject ownerRegistry: null
    property var controller: null
    property var record: null
    property QtObject colorPalette: null
    property bool leaseActive: false
    property bool hoverSuppressed: false
    property bool releasing: false
    property int anchorGeneration: 0
    readonly property bool hovered: hover.hovered
    readonly property bool tooltipVisible: !!nativeWindow.item && nativeWindow.item.visible
    readonly property bool previewHovered: !!nativeWindow.item && nativeWindow.item.previewHovered
    readonly property var tooltipPopup: nativeWindow.item
    readonly property var contentsLoader: nativeWindow.item ? nativeWindow.item.contentsLoader : null
    readonly property bool providersLoaded: !!contentsLoader && !!contentsLoader.item
        && tooltipVisible && previewsEnabled
    readonly property string recordIdentity: record ? JSON.stringify([record.key, record.pid]) : ""
    readonly property string backend: KWindowSystem.isPlatformWayland ? "wayland"
        : KWindowSystem.isPlatformX11 ? "x11" : "unavailable"
    readonly property var windowRecords: {
        if (!controller || !record) return []
        const current = controller.windowFor(record.key)
        return current && current.pid === record.pid ? [current] : []
    }
    readonly property bool eligible: windowRecords.length > 0 && !!Window.window && Window.window.visible
        && placementAvailable
        && (previewsEnabled || (hintsEnabled && titleTruncated))
    readonly property int columnCount: 1
    // Width/height bound this monitor. The desktopAvailable* values can instead
    // describe a collection of monitors in the virtual desktop.
    readonly property real screenLeft: Screen.virtualX + 8
    readonly property real screenTop: Screen.virtualY + 8
    readonly property real screenRight: Screen.virtualX + Screen.width - 8
    readonly property real screenBottom: Screen.virtualY + Screen.height - 8
    readonly property point rowPosition: {
        memberHint.anchorGeneration
        const host = Window.window
        if (host) { host.x; host.y }
        return mapToGlobal(0, 0)
    }
    readonly property var selectorWindow: ownerRegistry && ownerRegistry.contentItem
        ? ownerRegistry.contentItem.Window.window : Window.window
    readonly property real selectorLeft: selectorWindow ? selectorWindow.x : rowPosition.x
    readonly property real selectorTop: selectorWindow ? selectorWindow.y : rowPosition.y
    readonly property real selectorRight: selectorWindow ? selectorWindow.x + selectorWindow.width
        : rowPosition.x + width
    readonly property real selectorBottom: selectorWindow ? selectorWindow.y + selectorWindow.height
        : rowPosition.y + height
    readonly property real maximumWidth: Math.max(1, Math.min(560, screenRight - screenLeft))
    readonly property real previewWidth: Math.max(1, Math.min(264, maximumWidth - 16))
    readonly property real contentHeight: windowRecords.length * 190 + 16
    readonly property real textWidth: Math.max(1, Math.min(480, maximumWidth - 8))
    readonly property real desiredWidth: previewsEnabled ? previewWidth + 24 : textWidth + 8
    readonly property real desiredHeight: previewsEnabled ? contentHeight + 8 : measuredTitle.implicitHeight + 8
    // Keep the entire list readable. A side is the first fallback, followed by
    // the area below the selector, with bounded height if the screen is small.
    readonly property string placement: selectorTop - screenTop >= desiredHeight ? "above"
        : screenRight - selectorRight >= desiredWidth ? "right"
        : selectorLeft - screenLeft >= desiredWidth ? "left"
        : screenBottom - selectorBottom >= desiredHeight ? "below"
        : selectorTop - screenTop >= screenBottom - selectorBottom ? "above" : "below"
    readonly property real maximumHeight: Math.max(1, Math.min(screenBottom - screenTop - 8,
        placement === "above" ? selectorTop - screenTop - 8
        : placement === "below" ? screenBottom - selectorBottom - 8 : screenBottom - screenTop - 8))
    // A screen-filling selector has no safe exterior space. Keep the title row
    // readable rather than mapping a clipped strip over the list.
    readonly property bool placementAvailable: maximumHeight >= Math.min(100, desiredHeight - 8)
    signal activationRequested(var windowRecord)
    Text {
        id: measuredTitle
        visible: false
        width: memberHint.textWidth
        text: memberHint.windowRecords.length ? memberHint.windowRecords[0].title || "" : ""
        textFormat: Text.PlainText; wrapMode: Text.Wrap
        font.family: "Nimbus Sans"; font.pixelSize: 13; renderType: Text.NativeRendering
    }

    function hideImmediately() {
        if (releasing) return
        releasing = true
        hoverSuppressed = true
        wakeUp.stop()
        const window = nativeWindow.item
        if (window) {
            if (window.contentsLoader && window.contentsLoader.item)
                window.contentsLoader.item.closeCaptionHints()
            window.visible = false
        }
        leaseActive = false
        if (ownerRegistry && ownerRegistry.hintOwner === memberHint) ownerRegistry.hintOwner = null
        releasing = false
    }
    function acquireLease() {
        // mapToGlobal does not notify QML when a ScrollView ancestor moved.
        // Recompute from the actual delegate for every new lease.
        anchorGeneration++
        if (!eligible || hoverSuppressed || leaseActive) return
        if (ownerRegistry) {
            const previous = ownerRegistry.hintOwner
            if (previous && previous !== memberHint) previous.hideImmediately()
            ownerRegistry.hintOwner = memberHint
        }
        leaseActive = true
    }
    function showToolTip() {
        if (eligible && !hoverSuppressed && !leaseActive) wakeUp.restart()
    }
    function pointerInPreviewOrBridge(point) {
        const window = nativeWindow.item
        if (!window || !previewsEnabled || !window.visible) return false
        if (point.x >= window.x && point.x <= window.x + window.width
                && point.y >= window.y && point.y <= window.y + window.height) return true
        // A narrow explicit corridor connects the row to the preview. Moving
        // sideways outside both surfaces closes immediately. Hovering another
        // row can still transfer ownership while crossing this corridor.
        if (placement === "above" || placement === "below") {
            const left = Math.max(rowPosition.x, window.x)
            const right = Math.min(rowPosition.x + width, window.x + window.width)
            const top = Math.min(window.y + window.height, rowPosition.y + height)
            const bottom = Math.max(window.y, rowPosition.y)
            return point.x >= left && point.x <= right && point.y >= top && point.y <= bottom
        }
        const top = Math.max(rowPosition.y, window.y)
        const bottom = Math.min(rowPosition.y + height, window.y + window.height)
        const left = Math.min(rowPosition.x + width, window.x + window.width)
        const right = Math.max(rowPosition.x, window.x)
        return point.y >= top && point.y <= bottom && point.x >= left && point.x <= right
    }
    function pointerBelongsToLease(point) {
        const inRow = point.x >= rowPosition.x && point.x <= rowPosition.x + width
            && point.y >= rowPosition.y && point.y <= rowPosition.y + height
        return inRow || pointerInPreviewOrBridge(point)
    }
    function observePointer(point) {
        if (leaseActive && !pointerBelongsToLease(point)) hideImmediately()
    }
    onRecordIdentityChanged: hideImmediately()
    onPreviewsEnabledChanged: hideImmediately()
    onEligibleChanged: if (!eligible) hideImmediately()
    Connections {
        target: memberHint.ownerRegistry
        function onHintOwnerChanged() {
            if (memberHint.ownerRegistry.hintOwner !== memberHint && memberHint.leaseActive)
                memberHint.hideImmediately()
        }
    }
    Connections {
        target: memberHint.Window.window
        function onVisibleChanged() {
            if (!memberHint.Window.window || !memberHint.Window.window.visible) memberHint.hideImmediately()
        }
    }
    HoverHandler {
        id: hover
        onHoveredChanged: {
            if (hovered) {
                memberHint.anchorGeneration++
                memberHint.hoverSuppressed = false
                if (memberHint.ownerRegistry && memberHint.ownerRegistry.hintOwner
                        && memberHint.ownerRegistry.hintOwner !== memberHint)
                    memberHint.ownerRegistry.hintOwner.hideImmediately()
                memberHint.showToolTip()
            } else if (!memberHint.pointerBelongsToLease(memberHint.mapToGlobal(point.position))) {
                // On leave Qt can still expose the last position inside this
                // row. The selector observes the next actual global position;
                // do not destroy an interactive preview from that stale point.
                memberHint.hideImmediately()
            }
        }
    }
    Timer {
        id: wakeUp
        interval: Kirigami.Units.toolTipDelay
        repeat: false
        onTriggered: if (memberHint.hovered && memberHint.eligible) memberHint.acquireLease()
    }
    Loader {
        id: nativeWindow
        active: memberHint.leaseActive
        onLoaded: {
            // Assign stable role and transient parent before the first map.
            item.previewMode = memberHint.previewsEnabled
            item.transientParent = memberHint.Window.window
            item.visible = true
        }
        sourceComponent: Window {
            id: hintWindow
            objectName: "domainosMemberTooltip"
            property bool previewMode: false
            readonly property bool previewHovered: previewHover.hovered
            readonly property alias contentsLoader: contents
            visible: false
            flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
                | (previewMode ? 0 : Qt.WindowTransparentForInput)
            color: "transparent"
            width: Math.min(memberHint.maximumWidth, tooltipBody.implicitWidth + 8)
            height: Math.min(memberHint.maximumHeight + 8, tooltipBody.implicitHeight + 8)
            x: Math.max(memberHint.screenLeft, Math.min(memberHint.screenRight - width,
                memberHint.placement === "right" ? memberHint.selectorRight
                : memberHint.placement === "left" ? memberHint.selectorLeft - width : memberHint.rowPosition.x))
            y: Math.max(memberHint.screenTop, Math.min(memberHint.screenBottom - height,
                memberHint.placement === "above" ? memberHint.selectorTop - height
                : memberHint.placement === "below" ? memberHint.selectorBottom : memberHint.rowPosition.y))
            DomainOSControlPalette { target: hintWindow.contentItem }
            Bevel {
                anchors.fill: parent
                paletteOverride: memberHint.colorPalette
                thickness: 1; simpleRelief: true
            }
            Item {
                id: tooltipBody
                objectName: "domainosMemberTooltipBody"
                x: 4; y: 4; width: hintWindow.width - 8; height: hintWindow.height - 8
                implicitWidth: hintWindow.previewMode ? memberHint.previewWidth + 16
                    : memberHint.textWidth
                implicitHeight: hintWindow.previewMode ? Math.min(memberHint.contentHeight, memberHint.maximumHeight)
                    : titleText.implicitHeight
                clip: true
                Text {
                    id: titleText
                    objectName: "domainosMemberHintText"
                    visible: !hintWindow.previewMode
                    width: parent.width
                    text: memberHint.windowRecords.length ? memberHint.windowRecords[0].title || "" : ""
                    textFormat: Text.PlainText; wrapMode: Text.Wrap
                    color: memberHint.colorPalette ? memberHint.colorPalette.text
                        : hintWindow.contentItem.Kirigami.Theme.textColor
                    font: measuredTitle.font; renderType: Text.NativeRendering
                }
                Loader {
                    id: contents
                    objectName: "domainosThumbnailContentsLoader"
                    active: hintWindow.previewMode && memberHint.leaseActive
                    visible: hintWindow.visible && hintWindow.previewMode
                    anchors.fill: parent
                    sourceComponent: DomainOSWindowPreviewContents { preview: memberHint }
                }
            }
            HoverHandler {
                id: previewHover
                parent: hintWindow.contentItem
                enabled: hintWindow.previewMode
                onPointChanged: if (hovered)
                    memberHint.observePointer(hintWindow.contentItem.mapToGlobal(point.position))
                onHoveredChanged: if (!hovered) {
                    const owner = memberHint
                    // Leave retains HandlerPoint's previous position. Let the
                    // matching Enter finish before checking the current owner
                    // surfaces; returning to the row preserves its lease.
                    Qt.callLater(() => {
                        if (owner && owner.leaseActive && !owner.hovered && !owner.previewHovered)
                            owner.hideImmediately()
                    })
                }
            }
            onVisibleChanged: if (!visible && memberHint.leaseActive && !memberHint.releasing)
                memberHint.hideImmediately()
        }
    }
    Component.onDestruction: hideImmediately()
}
