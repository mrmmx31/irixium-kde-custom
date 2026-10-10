// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.kwindowsystem

// Native ToolTipArea keeps the ordinary task's pointer/keyboard gestures and
// the Plasma hover policy. Only its visible preview creates native providers.
PlasmaCore.ToolTipArea {
    id: previewArea
    objectName: "domainosWindowThumbnails"
    property bool previewsEnabled: false
    property bool hintsEnabled: true
    property var controller: null
    property var record: null
    property QtObject colorPalette: null
    // ToolTipArea shares one native dialog between all cells. Its visibility
    // signal is broadcast to former owners too; only this content's actual
    // window and mainItem identify a visible preview belonging to this cell.
    readonly property bool tooltipVisible: !!tooltipContent.Window.window
        && tooltipContent.Window.window !== previewArea.Window.window
        && tooltipContent.Window.window.mainItem === tooltipContent
        && tooltipContent.Window.window.visible
    property bool preparingContents: false
    readonly property string recordIdentity: record ? JSON.stringify([record.key, record.pid]) : ""
    readonly property string backend: KWindowSystem.isPlatformWayland ? "wayland"
        : KWindowSystem.isPlatformX11 ? "x11" : "unavailable"
    readonly property var windowRecords: {
        if (!controller || !record) return []
        if (record.group) return controller.membersFor(record.key) || []
        const current = controller.windowFor(record.key)
        return current && current.pid === record.pid ? [current] : []
    }
    readonly property bool providersLoaded: !!previewLoader.item && tooltipVisible && previewsEnabled
    readonly property var contentsLoader: previewLoader
    readonly property int columnCount: Math.min(2, Math.max(1, windowRecords.length))
    readonly property real maximumWidth: Math.max(160, Math.min(560, Screen.desktopAvailableWidth - 40))
    readonly property real previewWidth: Math.min(264, (maximumWidth - 16 - (columnCount - 1) * 12) / columnCount)
    readonly property real contentHeight: Math.ceil(windowRecords.length / columnCount) * 190 + 16
    readonly property real maximumHeight: Math.max(100, Screen.desktopAvailableHeight - 40)
    signal activationRequested(var windowRecord)

    active: (previewsEnabled || hintsEnabled) && windowRecords.length > 0
    interactive: previewsEnabled
    location: PlasmaCore.Types.BottomEdge
    // Plain text preserves literal titles (<, &, quotes) and the controller's
    // member order. A group identifies every window before the user opens it.
    textFormat: Qt.PlainText
    mainText: record ? record.title || "" : ""
    subText: record && record.group
        ? windowRecords.map((window, index) => (index + 1) + ". " + window.title).join("\n") : ""
    onAboutToShow: preparingContents = true
    onTooltipVisibleChanged: preparingContents = false
    function releaseOwnedContents() {
        preparingContents = false
        // An unowned cell must never hide the new owner's shared dialog.
        if (tooltipVisible) hideImmediately()
    }
    onRecordIdentityChanged: releaseOwnedContents()
    onPreviewsEnabledChanged: if (!previewsEnabled) releaseOwnedContents()
    onHintsEnabledChanged: if (!hintsEnabled && !previewsEnabled) releaseOwnedContents()
    onWindowRecordsChanged: if (!windowRecords.length) releaseOwnedContents()
    // A stable item avoids leaving the previous Loader attached to the
    // shared dialog after changing preferences. Qt measures implicit sizes,
    // before a provider is ready; empty cards must already be clickable.
    mainItem: tooltipContent
    Item {
        id: tooltipContent
        objectName: "domainosOwnedTooltipContents"
        visible: previewArea.tooltipVisible
        implicitWidth: previewArea.previewsEnabled
            ? previewArea.previewWidth * previewArea.columnCount + (previewArea.columnCount - 1) * 12 + 16
            : Math.min(480, previewArea.maximumWidth)
        implicitHeight: previewArea.previewsEnabled
            ? Math.min(previewArea.contentHeight, previewArea.maximumHeight)
            : hintLoader.item ? hintLoader.item.implicitHeight : 32
        DomainOSControlPalette {
            target: tooltipContent.Window.window && tooltipContent.Window.window.mainItem === tooltipContent
                ? tooltipContent.Window.window.contentItem : null
        }
        Loader {
            id: hintLoader
            objectName: "domainosWindowTitlesLoader"
            visible: previewArea.tooltipVisible && !previewArea.previewsEnabled
            active: previewArea.hintsEnabled && !previewArea.previewsEnabled
                && (previewArea.tooltipVisible || previewArea.preparingContents)
            anchors.fill: parent
            sourceComponent: DomainOSWindowTitles {
                groupTitle: previewArea.mainText
                windows: previewArea.record && previewArea.record.group ? previewArea.windowRecords : []
                colorPalette: previewArea.colorPalette
                hintWidth: hintLoader.width
                maximumHeight: previewArea.maximumHeight
            }
        }
        Loader {
            id: previewLoader
            objectName: "domainosThumbnailContentsLoader"
            visible: previewArea.tooltipVisible && previewArea.previewsEnabled
            // Build labels before Plasma measures the native tooltip; live image
            // providers below still wait for its visibility signal.
            active: previewArea.previewsEnabled && (previewArea.tooltipVisible || previewArea.preparingContents)
            anchors.fill: parent
            sourceComponent: DomainOSWindowPreviewContents { preview: previewArea }
        }
    }
}
