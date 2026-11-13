// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore

// Presentation adapter for the actual SystemTrayContainer. Its containment,
// delegates, applets, services and QML contexts stay owned by native Plasma.
// The hosting applet must have X-Plasma-RootPath=org.kde.plasma.systemtray.
Item {
    id: tray
    objectName: "domainosRealTray"
    implicitWidth: 326
    implicitHeight: 150
    property Item nativeTray: null
    property var settings: ({})
    property QtObject activity: null
    property QtObject colorPalette: null
    property rect screenGeometry: Qt.rect(0, 0, 0, 0)
    DomainOSPalette { id: fallbackPalette }
    readonly property QtObject domainosPalette: colorPalette || fallbackPalette
    DomainOSPopupPlacement { popup:overflowPopup; popupAnchor:overflowButton; positionAnchor:tray; alignRight:true; gap:6 }
    DomainOSPopupPlacement { popup:statusPopup; popupAnchor:statusButton; positionAnchor:tray; alignRight:true; gap:6 }
    DomainOSPopupWheel { popup:overflowPopup; ownerWindow:tray.Window.window }
    DomainOSPopupWheel { popup:statusPopup; ownerWindow:tray.Window.window }
    readonly property bool available: !!nativeTray && !!nativeTray.visibleLayout && !!nativeTray.hiddenLayout
    readonly property var visibleIds: settings.trayVisibleItems || []
    readonly property var hiddenIds: settings.trayHiddenItems || []
    readonly property var preferredOrder: settings.trayOrder || []
    readonly property bool includeHidden: settings.trayIncludeHiddenInOverflow || false
    readonly property bool barHintsEnabled: settings.barHintsEnabled === true
    readonly property string overflowMode: settings.trayOverflowMode || "continuation"
    property var nativeLoaders: []
    property var entries: []
    readonly property var availableItems: entries.filter(entry => entry.item).map(entry => ({id:entry.id, title:String(entry.item.text),
        type:entry.type, hidden:entry.hidden, status:entry.item.status}))
    readonly property var visibleEntries: entries.filter(entry => !entry.hidden)
    readonly property var hiddenEntries: entries.filter(entry => entry.hidden)
    readonly property var overflowEntries: visibleEntries.slice(6).concat(includeHidden ? hiddenEntries : [])
    readonly property int attentionCount: entries.filter(entry => entry.item &&
        (entry.item.status === PlasmaCore.Types.NeedsAttentionStatus || entry.item.status === PlasmaCore.Types.RequiresAttentionStatus)).length
    readonly property var notificationsEntry: entries.find(entry => entry.id === "org.kde.plasma.notifications") || null
    readonly property real maximumPopupWidth: Math.max(70, (screenGeometry.width > 0 ? screenGeometry.width : Screen.width) - 24)
    readonly property int overflowCellWidth: overflowEntries.some(entry => entry.hidden) ? 190 : 60
    readonly property int desiredOverflowColumns: Math.max(1, Math.ceil(overflowEntries.length / 2))
    readonly property int fittingOverflowColumns: Math.max(1, Math.floor((maximumPopupWidth - 16) / overflowCellWidth))
    readonly property bool overflowPaginated: overflowMode === "pagination" || desiredOverflowColumns > fittingOverflowColumns
    readonly property int overflowColumns: overflowPaginated ? Math.min(3, fittingOverflowColumns) : desiredOverflowColumns
    readonly property int overflowCapacity: Math.max(1, overflowColumns * 2)
    readonly property int overflowPages: Math.max(1, Math.ceil(overflowEntries.length / overflowCapacity))
    property int overflowPage: 0
    property var adoptedEntries: []
    property var tooltipPolicies: []
    property Item originalNativeParent: null
    property bool refreshing: false
    property Item attachedNativeTray: null
    property bool visibilityInitialized: false
    property bool synchronizingVisibility: false
    signal failure(string message)
    DomainOSPopupToggle { id: overflowToggle; showing: overflowPopup.visible; anchor: overflowButton }
    DomainOSPopupToggle { id: statusToggle; showing: statusPopup.visible; anchor: statusButton }

    function sameList(a, b) { return JSON.stringify(Array.from(a || [])) === JSON.stringify(Array.from(b || [])) }
    function applyVisibility() {
        if (!available || !visibilityInitialized || synchronizingVisibility || !nativeTray.plasmoid || !nativeTray.plasmoid.configuration) return
        // These are only this applet's own containment configuration, never the
        // system tray belonging to another panel or user. extraItems is retained.
        const config = nativeTray.plasmoid.configuration
        const hidden = Array.from(hiddenIds)
        const shown = Array.from(visibleIds).filter(id => hidden.indexOf(id) < 0)
        const changed = !sameList(config.hiddenItems, hidden) || !sameList(config.shownItems, shown)
        synchronizingVisibility = true
        try {
            if (!sameList(config.hiddenItems, hidden)) config.hiddenItems = hidden
            if (!sameList(config.shownItems, shown)) config.shownItems = shown
            if (changed) {
                // Commit only this containment's KConfigPropertyMap. The native
                // C++ tray model observes its configuration loader's saved values.
                config.writeConfig()
            }
        } finally {
            synchronizingVisibility = false
        }
        scheduleRefresh()
    }
    function attach() {
        if (!available) return
        if (attachedNativeTray !== nativeTray) {
            attachedNativeTray = nativeTray
            visibilityInitialized = false
        }
        if (nativeTray.parent !== nativeParking) originalNativeParent = nativeTray.parent
        nativeTray.parent = nativeParking
        nativeTray.anchors.fill = nativeParking
        // Keep the original views alive and materialized. Moving their existing
        // items preserves Bound component contexts, provider gestures and menus.
        nativeTray.visibleLayout.parent.opacity = 0
        if (!visibilityInitialized) {
            const config = nativeTray.plasmoid.configuration
            // Empty schema defaults must not erase choices already made with
            // the native menu in this same containment. Copy them once instead.
            synchronizingVisibility = true
            try {
                if (!visibleIds.length && config.shownItems.length) settings.trayVisibleItems = Array.from(config.shownItems)
                if (!hiddenIds.length && config.hiddenItems.length) settings.trayHiddenItems = Array.from(config.hiddenItems)
            } finally {
                synchronizingVisibility = false
            }
            visibilityInitialized = true
        }
        applyVisibility()
        scheduleRefresh()
    }
    function scheduleRefresh() { Qt.callLater(refresh) }
    function viewLoaders(view) {
        if (!view) return []
        view.cacheBuffer = Math.max(view.width, view.height, view.count * Math.max(view.cellWidth, view.cellHeight)) * 2
        view.forceLayout()
        const result = []
        for (let row = 0; row < view.count; ++row) {
            const loader = view.itemAtIndex(row)
            if (loader) result.push(loader)
        }
        return result
    }
    function restore(entry) {
        if (!entry || !entry.item || !entry.loader) return
        entry.item.parent = entry.loader
        entry.item.anchors.fill = entry.loader
        if (entry.item.iconContainer) {
            entry.item.iconContainer.Layout.preferredWidth = entry.originalIconWidth
            entry.item.iconContainer.Layout.preferredHeight = entry.originalIconHeight
        }
    }
    function place(entry, parent) {
        if (!entry || !entry.item || !parent) return
        entry.item.parent = parent
        entry.item.anchors.fill = parent
        // Size this presentation from the approved 50x48 button. Provider code
        // still draws the icon and owns every event; no replacement SVG is used.
        if (entry.item.iconContainer) {
            entry.item.iconContainer.Layout.preferredWidth = 32
            entry.item.iconContainer.Layout.preferredHeight = 32
        }
    }
    function refresh() {
        if (refreshing || !available) return
        refreshing = true
        try {
            const active = viewLoaders(nativeTray.visibleLayout)
            const hidden = viewLoaders(nativeTray.hiddenLayout)
            nativeLoaders = active.concat(hidden)
            let result = []
            for (const [loaders, isHidden] of [[active, false], [hidden, true]]) {
                for (let ordinal = 0; ordinal < loaders.length; ++ordinal) {
                    const loader = loaders[ordinal]
                    if (loader.item && loader.item.itemId) {
                        const previous = adoptedEntries.find(entry => entry.item === loader.item)
                        result.push({loader: loader, item: loader.item,
                            id: String(loader.item.itemId), hidden: isHidden, ordinal: ordinal,
                            type: loader.item.model ? String(loader.item.model.itemType) : "",
                            originalIconWidth: previous ? previous.originalIconWidth : loader.item.iconContainer?.Layout.preferredWidth ?? -1,
                            originalIconHeight: previous ? previous.originalIconHeight : loader.item.iconContainer?.Layout.preferredHeight ?? -1})
                    }
                }
            }
            result.sort((a, b) => {
                const ai = preferredOrder.indexOf(a.id), bi = preferredOrder.indexOf(b.id)
                return (ai < 0 ? preferredOrder.length : ai) - (bi < 0 ? preferredOrder.length : bi) || a.ordinal - b.ordinal
            })
            for (const previous of adoptedEntries) {
                if (!result.some(entry => entry.item === previous.item)) restore(previous)
            }
            synchronizeTooltipPolicies(result)
            adoptedEntries = result
            entries = result
            overflowPage = Math.min(overflowPage, overflowPages - 1)
            layoutItems()
        } finally {
            refreshing = false
        }
    }
    function synchronizeTooltipPolicies(nextEntries) {
        // Loader arrays change during native model updates. Keep one Binding
        // per actual item so overlapping temporary delegates cannot capture
        // another override as the provider's original activation binding.
        const retained=[]
        for (const policy of tooltipPolicies) {
            if (nextEntries.some(entry=>entry.item===policy.item)) retained.push(policy)
            else policy.binding.destroy()
        }
        for (const entry of nextEntries) {
            if (!retained.some(policy=>policy.item===entry.item)) {
                const binding=tooltipPolicy.createObject(tray,{target:entry.item})
                if (binding) retained.push({item:entry.item,binding:binding})
            }
        }
        tooltipPolicies=retained
    }
    function layoutItems() {
        for (const entry of entries) restore(entry)
        for (let slot = 0; slot < Math.min(6, visibleEntries.length); ++slot) place(visibleEntries[slot], slots.itemAt(slot).nativeHost)
        if (overflowPopup.visible) {
            for (let slot = 0; slot < overflowSlots.count; ++slot) {
                const offset = overflowPaginated ? overflowPage * overflowCapacity : 0
                place(overflowEntries[offset + slot], overflowSlots.itemAt(slot).nativeHost)
            }
        } else if (statusPopup.visible) {
            for (let slot = 0; slot < hiddenSlots.count; ++slot) place(hiddenEntries[slot], hiddenSlots.itemAt(slot).nativeHost)
        }
    }
    function present(action, request) {
        const tracker = activity
        let token = null
        let accepted = false
        try {
            if (tracker) token = tracker.begin("presentation-" + action)
            accepted = request() === true
        } catch (error) {
            // Report this adapter's failed view request, never native provider
            // exception text, notification content or a fabricated SNI result.
            failure(qsTr("The requested tray view could not be shown"))
        } finally {
            if (tracker && token !== null) tracker.finish(token, {
                ok: accepted, action: action,
                outcome: accepted ? "presentation-requested" : "failed",
                detail: accepted
                    ? qsTr("The panel accepted the view request; no application completion is implied")
                    : qsTr("The requested tray view could not be shown")})
        }
        return accepted
    }
    function showOverflow() {
        if (!available || !overflowEntries.length) return false
        return present("tray-overflow", () => {
            if (!overflowToggle.shouldOpen(overflowButton)) { overflowPopup.close(); return true }
            statusPopup.close()
            nativeTray.systemTrayState.expanded = false
            overflowPage = 0
            overflowPopup.open()
            Qt.callLater(layoutItems)
            return true
        })
    }
    function showStatus() {
        if (!available) { failure(qsTr("A bandeja nativa do Plasma está indisponível.")); return false }
        return present("tray-status", () => {
            if (!statusToggle.shouldOpen(statusButton)) { statusPopup.close(); return true }
            overflowPopup.close()
            nativeTray.systemTrayState.expanded = false
            statusPopup.open()
            Qt.callLater(layoutItems)
            return true
        })
    }
    function openNotifications() {
        const entry = notificationsEntry
        if (!available || !entry || !entry.item || !entry.item.applet) return false
        return present("tray-notifications", () => {
            statusPopup.close()
            nativeTray.systemTrayState.setActiveApplet(entry.item.applet)
            return true
        })
    }
    function snapshot() {
        return {available: available, visible: visibleEntries.map(entry => entry.id), hidden: hiddenEntries.map(entry => entry.id),
            types: entries.filter(entry => entry.item).map(entry => ({id:entry.id,type:entry.type,status:entry.item.status})), attention:attentionCount,
            overflow: overflowEntries.map(entry => entry.id), overflowOpen:overflowPopup.visible,
            statusOpen:statusPopup.visible, paginated:overflowPaginated, page:overflowPage, pages:overflowPages,
            notificationsAvailable:!!notificationsEntry, nativeExpanded:available && nativeTray.systemTrayState.expanded}
    }
    onNativeTrayChanged: Qt.callLater(attach)
    onVisibleIdsChanged: applyVisibility()
    onHiddenIdsChanged: applyVisibility()
    onPreferredOrderChanged: scheduleRefresh()
    onIncludeHiddenChanged: scheduleRefresh()
    onOverflowModeChanged: { overflowPage = 0; Qt.callLater(layoutItems) }
    onOverflowPageChanged: Qt.callLater(layoutItems)
    Component.onCompleted: attach()
    Component.onDestruction: {
        for (const policy of tooltipPolicies) policy.binding.destroy()
        for (const entry of adoptedEntries) restore(entry)
        if (nativeTray && originalNativeParent) {
            nativeTray.visibleLayout.parent.opacity = 1
            nativeTray.parent = originalNativeParent
            nativeTray.anchors.fill = originalNativeParent
        }
    }
    // Opacity hides painting, but Qt still delivers rejected wheel events to
    // transparent items behind a slot. Keep these original views materialized
    // without input; adopted items inherit their new visual parent's enabled
    // state, and restoring the native parent preserves its original binding.
    Item { id: nativeParking; width: 202; height: 150; enabled: false }
    Connections {
        target: tray.available ? tray.nativeTray.visibleLayout : null
        function onCountChanged() { tray.scheduleRefresh() }
    }
    Connections {
        target: tray.available ? tray.nativeTray.hiddenLayout : null
        function onCountChanged() { tray.scheduleRefresh() }
    }
    Connections {
        target: tray.available ? tray.nativeTray.visibleLayout.contentItem : null
        function onChildrenChanged() { tray.scheduleRefresh() }
    }
    Connections {
        target: tray.available ? tray.nativeTray.hiddenLayout.contentItem : null
        function onChildrenChanged() { tray.scheduleRefresh() }
    }
    // A newly registered SNI can finish loading after GridView's count change
    // and the first itemAtIndex() scan. Observe the actual native models too,
    // so insertions, status updates and proxy moves refresh the adopted list.
    Connections {
        target: tray.available ? tray.nativeTray.visibleLayout.model : null
        function onRowsInserted() { tray.scheduleRefresh() }
        function onRowsRemoved() { tray.scheduleRefresh() }
        function onDataChanged() { tray.scheduleRefresh() }
        function onLayoutChanged() { tray.scheduleRefresh() }
        function onModelReset() { tray.scheduleRefresh() }
    }
    Connections {
        target: tray.available ? tray.nativeTray.hiddenLayout.model : null
        function onRowsInserted() { tray.scheduleRefresh() }
        function onRowsRemoved() { tray.scheduleRefresh() }
        function onDataChanged() { tray.scheduleRefresh() }
        function onLayoutChanged() { tray.scheduleRefresh() }
        function onModelReset() { tray.scheduleRefresh() }
    }
    Connections {
        target: tray.available ? tray.nativeTray.systemTrayState : null
        function onExpandedChanged() {
            if (target.expanded) { overflowPopup.close(); statusPopup.close() }
        }
    }
    Connections {
        target: tray.available ? tray.nativeTray.plasmoid.configuration : null
        function onValueChanged(key, value) {
            if (!tray.visibilityInitialized || tray.synchronizingVisibility) return
            tray.synchronizingVisibility = true
            try {
                if (key === "shownItems" && !tray.sameList(tray.visibleIds, value)) tray.settings.trayVisibleItems = Array.from(value)
                if (key === "hiddenItems" && !tray.sameList(tray.hiddenIds, value)) tray.settings.trayHiddenItems = Array.from(value)
            } finally {
                tray.synchronizingVisibility = false
            }
            tray.scheduleRefresh()
        }
    }
    Instantiator {
        model: tray.nativeLoaders
        delegate: QtObject {
            required property var modelData
            property QtObject loaderWatcher: Connections {
                target: modelData
                function onItemChanged() { tray.scheduleRefresh() }
                function onStatusChanged() { tray.scheduleRefresh() }
            }
            property QtObject itemWatcher: Connections {
                target: modelData.item
                function onStatusChanged() { tray.scheduleRefresh() }
            }
        }
    }
    Component {
        id:tooltipPolicy
        // Suspend only this presentation's native ToolTipArea activation.
        // Re-enabling hints or releasing the item restores its own binding.
        Binding {
            property:"active"
            value:false
            when:!!target && !tray.barHintsEnabled
            restoreMode:Binding.RestoreBindingOrValue
        }
    }
    Bevel {
        width: 202; height: 150
        simpleRelief: true; light: domainosPalette.pale; dark: domainosPalette.dark
        texture: Qt.resolvedUrl("../images/metal-weave.svg")
        Bevel { x:8; y:14; width:186; height:122; sunken:true; face:domainosPalette.recessed }
        Repeater {
            id: slots
            model: 6
            delegate: Item {
                required property int index
                objectName: "domainosTraySlot_" + index
                x: 16 + (index % 3) * 60; y: 24 + Math.floor(index / 3) * 54
                width:50; height:48
                readonly property var entry: tray.visibleEntries[index] || null
                readonly property alias nativeHost: nativeHost
                Bevel {
                    objectName: "domainosTraySlot_" + parent.index + "Relief"
                    anchors.fill:parent; face:domainosPalette.recessed
                    texture: parent.entry ? Qt.resolvedUrl("../images/metal-weave.svg") : ""
                    sunken: !!parent.entry && !!parent.entry.item && !!parent.entry.item.iconContainer && parent.entry.item.iconContainer.scale < 1
                }
                Item { id:nativeHost; anchors.fill:parent; anchors.margins:4 }
                Rectangle {
                    anchors.fill:parent; color:"transparent"; border.width:2; border.color:domainosPalette.pagerLight
                    visible:!!parent.entry && !!parent.entry.item && (parent.entry.item.status === PlasmaCore.Types.NeedsAttentionStatus || parent.entry.item.status === PlasmaCore.Types.RequiresAttentionStatus)
                }
                onEntryChanged: Qt.callLater(tray.layoutItems)
            }
        }
        Text { anchors.centerIn:parent; text:"—"; visible:!tray.available; color:domainosPalette.text; Accessible.name:qsTr("Native system tray unavailable") }
    }
    Bevel {
        x:202; width:124; height:150
        simpleRelief:true; light:domainosPalette.pale; dark:domainosPalette.dark
        texture:Qt.resolvedUrl("../images/metal-weave.svg")
        PanelButton {
            id: overflowButton
            objectName:"domainosTrayNext"; x:22; y:16; width:80; height:54
            label:qsTr("Visible tray overflow"); imageSource:Qt.resolvedUrl("../images/arrow-right.svg"); imageWidth:32
            enabled:tray.available && tray.overflowEntries.length > 0
            onClicked:tray.showOverflow()
        }
        PanelButton {
            id: statusButton
            objectName:"domainosTrayExpand"; x:22; y:80; width:80; height:54
            label:qsTr("Status, notifications and hidden items"); imageSource:Qt.resolvedUrl("../images/arrow-up.svg"); imageWidth:32
            enabled:tray.available
            onClicked:tray.showStatus()
        }
    }
    Controls.Popup {
        id: overflowPopup
        objectName:"domainosTrayOverflowPopup"
        popupType:Controls.Popup.Window
        enter:null; exit:null
        padding:8
        width:tray.overflowColumns * tray.overflowCellWidth + 16
        height:144 + (tray.overflowPaginated ? 38 : 0)
        closePolicy:Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutsideParent
        background:Bevel { paletteOverride:tray.domainosPalette; face:tray.domainosPalette.recessed }
        onVisibleChanged:Qt.callLater(tray.layoutItems)
        contentItem: Item {
            objectName:"domainosTrayOverflowContent"
            Repeater {
                id: overflowSlots
                model:overflowPopup.visible ? (tray.overflowPaginated ? Math.min(tray.overflowCapacity,tray.overflowEntries.length-tray.overflowPage*tray.overflowCapacity) : tray.overflowEntries.length) : 0
                delegate:Item {
                    required property int index
                    objectName:"domainosTrayOverflowSlot_"+index
                    x:(index%tray.overflowColumns)*tray.overflowCellWidth; y:Math.floor(index/tray.overflowColumns)*64
                    width:tray.overflowCellWidth; height:64
                    readonly property alias nativeHost:nativeHost
                    Item { id:nativeHost; anchors.fill:parent; anchors.margins:4 }
                    Component.onCompleted:Qt.callLater(tray.layoutItems)
                }
            }
            RowLayout {
                y:132; width:parent.width; visible:tray.overflowPaginated
                DomainOSButton { text:"◀"; enabled:tray.overflowPage>0; onClicked:--tray.overflowPage }
                Controls.Label { Layout.fillWidth:true; horizontalAlignment:Text.AlignHCenter; text:(tray.overflowPage+1)+" / "+tray.overflowPages }
                DomainOSButton { text:"▶"; enabled:tray.overflowPage<tray.overflowPages-1; onClicked:++tray.overflowPage }
            }
        }
    }
    Controls.Popup {
        id:statusPopup
        objectName:"domainosTrayStatusPopup"
        popupType:Controls.Popup.Window
        enter:null; exit:null
        padding:8; width:400
        implicitHeight:Math.min(420, 88 + Math.ceil(tray.hiddenEntries.length/2)*64)
        onAboutToShow: {
            // A Popup.Window resize can retain the content's previous natural
            // height. Reuse the chooser's public height reset so the native
            // popup item receives this bounded height before its first show.
            height=implicitHeight
            height=undefined
        }
        closePolicy:Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutsideParent
        background:Bevel { paletteOverride:tray.domainosPalette; face:tray.domainosPalette.recessed }
        onVisibleChanged:Qt.callLater(tray.layoutItems)
        contentItem:ColumnLayout {
            objectName:"domainosTrayStatusContent"
            Controls.Label { text:qsTr("Status and notifications"); Layout.fillWidth:true }
            DomainOSButton { text:qsTr("Notifications"); enabled:!!tray.notificationsEntry; onClicked:tray.openNotifications() }
            Controls.ScrollView {
                id:trayStatusView
                Controls.ScrollBar.vertical:DomainOSViewScrollBar { scrollView:trayStatusView;colorPalette:tray.domainosPalette }
                Controls.ScrollBar.horizontal:DomainOSViewScrollBar { scrollView:trayStatusView;colorPalette:tray.domainosPalette }
                Layout.fillWidth:true; Layout.fillHeight:true; Layout.minimumHeight:0
                contentWidth:availableWidth
                contentHeight:Math.ceil(tray.hiddenEntries.length/2)*64
                Item {
                    width:parent.width; height:Math.ceil(tray.hiddenEntries.length/2)*64
                    Repeater {
                        id:hiddenSlots
                        model:statusPopup.visible ? tray.hiddenEntries.length : 0
                        delegate:Item {
                            required property int index
                            objectName:"domainosTrayHiddenSlot_"+index
                            x:(index%2)*190; y:Math.floor(index/2)*64; width:190; height:64
                            readonly property alias nativeHost:nativeHost
                            Item { id:nativeHost; anchors.fill:parent; anchors.margins:4 }
                            Component.onCompleted:Qt.callLater(tray.layoutItems)
                        }
                    }
                }
            }
        }
    }
}
