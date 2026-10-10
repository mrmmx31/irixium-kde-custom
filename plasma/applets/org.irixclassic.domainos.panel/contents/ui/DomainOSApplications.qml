// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.private.kicker as Kicker
import org.kde.kitemmodels as KItemModels
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager
import org.kde.plasma.plasma5support as P5Support
import "../code/ApplicationActions.js" as ApplicationActions

Item {
    id: applications
    objectName: "domainosApplicationsController"
    property var hostItem
    DomainOSPalette { id:scrollPalette }
    property var settings: ({})
    property var commands
    property string favoritesClient: "org.irixclassic.domainos.menu"
    readonly property var pins: settings.pinnedApplications || []
    readonly property alias catalogModel: catalog
    readonly property alias sharedFavoritesModel: catalog.favoritesModel
    readonly property alias pinnedMetadataModel: pinMetadata
    readonly property alias filteredModel: filtered
    readonly property bool usesKdeMenu: settings.applicationsMenuStyle === "kde"
    readonly property bool popupVisible: popup.visible || (kdeMenu.item ? kdeMenu.item.menuVisible : false)
    readonly property bool searching: search.text.trim().length>0
    readonly property var searchResultsModel: searchRunner.count>0 ? searchRunner.modelForRow(0) : null
    property alias searchText: search.text
    property var navigation: []
    property var currentModel: catalog
    property bool drawer: false
    property var externalFavoriteOrder: []
    property string favoriteOrderMessage: ""
    property var favoriteOrderOrigin: ({})
    property string favoriteOrderCommand: ""
    property string favoriteOrderToken: ""
    property int favoriteOrderGeneration: 0
    property int pendingFavoriteOrderGeneration: 0
    property string pendingFavoriteOrderActivity: ""
    property bool favoriteOrderReadAgain: false
    property int favoriteOrderSequence: 0
    readonly property bool favoriteOrderBusy: favoriteOrderCommand.length > 0
    readonly property var orderedFavorites: {
        let rows = []
        for (let row=0;row<favoriteProviderRows.count;++row) {
            const item=favoriteProviderRows.itemAt(row)
            if (item) rows.push({favoriteId:item.favoriteId,title:item.title,icon:item.icon,available:item.available,providerRow:row})
        }
        return orderFavoriteRows(rows,externalFavoriteOrder)
    }
    function orderFavoriteRows(rows,order) {
        if (order.length) rows.sort((a,b)=> {
            const ai=order.indexOf(favoriteKey(a.favoriteId)),bi=order.indexOf(favoriteKey(b.favoriteId))
            return (ai<0 ? order.length : ai)-(bi<0 ? order.length : bi) || a.providerRow-b.providerRow
        })
        return rows
    }
    signal configureRequested()
    signal pinListRequested(var pins)

    TaskManager.ActivityInfo { id:favoriteActivity }
    Connections {
        target:favoriteActivity
        function onCurrentActivityChanged() {
            ++applications.favoriteOrderGeneration
            applications.externalFavoriteOrder=[]
            applications.favoriteOrderMessage=""
            applications.favoriteOrderOrigin=({})
            if (popup.visible && applications.drawer) applications.readFavoriteOrder()
        }
    }
    Repeater {
        id:favoriteProviderRows
        model:catalog.favoritesModel
        delegate:Item {
            required property var model
            readonly property string favoriteId:String(model.favoriteId || model.url || "")
            readonly property string title:String(model.display || "")
            readonly property var icon:model.decoration
            readonly property bool available:!model.disabled && !model.isSeparator && !model.hasChildren
            visible:false
        }
    }
    function favoriteKey(value) {
        let text=String(value)
        try { text=decodeURIComponent(text) } catch (error) { /* keep provider identity */ }
        return text.replace(/^applications:/,"")
    }
    function quoteFavoriteRequest(value) { return "'"+String(value).replace(/'/g,"'\"'\"'")+"'" }
    function readFavoriteOrder() {
        if (favoriteOrderBusy) { favoriteOrderReadAgain=true;return false }
        favoriteOrderReadAgain=false
        const token=String(++favoriteOrderSequence)+"-"+String(Math.random())
        // Opaque identity digests keep file/URL favorites out of process argv;
        // they only rank members, never authorize an application action.
        const request={token:token,activity:favoriteActivity.currentActivity,
            memberHashes:orderedFavorites.map(item=>Qt.md5(favoriteKey(item.favoriteId)))}
        const helperPath=decodeURIComponent(Qt.resolvedUrl("../code/favorite_order.py").toString().replace(/^file:\/\//,""))
        const command="python3 -B "+quoteFavoriteRequest(helperPath)
            +" "+quoteFavoriteRequest(JSON.stringify(request))
        favoriteOrderToken=token;pendingFavoriteOrderGeneration=favoriteOrderGeneration
        pendingFavoriteOrderActivity=favoriteActivity.currentActivity;favoriteOrderCommand=command
        try { favoriteOrderSource.connectSource(command);return true }
        catch (error) {
            favoriteOrderCommand="";favoriteOrderToken=""
            favoriteOrderMessage=qsTr("Não foi possível ler a ordem do menu KDE. A lista atual foi mantida.")
            return false
        }
    }
    function handleFavoriteOrderResult(source,data) {
        if (!favoriteOrderCommand || source!==favoriteOrderCommand) return
        const token=favoriteOrderToken,generation=pendingFavoriteOrderGeneration,activity=pendingFavoriteOrderActivity
        favoriteOrderCommand="";favoriteOrderToken=""
        try { favoriteOrderSource.disconnectSource(source) } catch (error) { console.warn("DomainOS: favorite-order source disconnect failed") }
        if (generation===favoriteOrderGeneration && activity===favoriteActivity.currentActivity && popup.visible && drawer) {
            try {
                const result=JSON.parse(String(data.stdout || ""))
                if (!result || result.token!==token || typeof result.ok!=="boolean") throw new Error("Unexpected favorite order result")
                if (result.ok && Array.isArray(result.order) && result.order.every(item=>typeof item==="string")) {
                    externalFavoriteOrder=result.order.slice()
                    favoriteOrderOrigin={kind:result.kind,client:result.client || "",location:result.location || ""}
                    favoriteOrderMessage=result.kind==="existing" ? qsTr("Ordem do menu Applications do KDE")
                        : result.kind==="legacy" ? qsTr("Ordem preservada do último menu KDE compatível")
                        : qsTr("Nenhuma ordem de menu KDE encontrada; ordem atual dos favoritos.")
                } else {
                    favoriteOrderMessage=result.outcome==="ambiguous"
                        ? qsTr("Os menus KDE existentes têm ordens diferentes. A última ordem lida foi mantida.")
                        : qsTr("Não foi possível ler a ordem do menu KDE. A lista atual foi mantida.")
                }
            } catch (error) { favoriteOrderMessage=qsTr("Não foi possível ler a ordem do menu KDE. A lista atual foi mantida.") }
        }
        if (favoriteOrderReadAgain && popup.visible && drawer) readFavoriteOrder()
        else favoriteOrderReadAgain=false
    }
    P5Support.DataSource {
        id:favoriteOrderSource
        engine:"executable";connectedSources:[]
        onNewData:(source,data)=>applications.handleFavoriteOrderResult(source,data)
    }

    // Unlike the catalog's KAStats favorites, this model is an in-memory list.
    // Its only source is the owning instance's pinnedApplications setting.
    Kicker.FavoritesModel {
        id: pinMetadata
        // Kicker's AppEntry IDs are bare storage IDs. An applications: URL
        // would create a generic URL entry instead of resolving the service.
        favorites: applications.pins
    }
    Repeater {
        id: metadataRows
        model: pinMetadata
        delegate: Item {
            required property var model
            property string desktop: applications.desktopId(model.favoriteId || model.url || "")
            property string title: String(model.display || "")
            property var icon: model.decoration
            property bool available: !model.disabled && !model.isSeparator
            visible: false
        }
    }

    Kicker.RootModel {
        id: catalog
        appletInterface: applications.hostItem
        flat: true
        sorted: true
        showAllApps: true
        showAllAppsCategorized: false
        showRecentApps: true
        showRecentDocs: true
        showPowerSession: false
        showFavoritesPlaceholder: true
        Component.onCompleted: favoritesModel.initForClient(applications.favoritesClient)
    }
    Kicker.RunnerModel {
        id:searchRunner
        objectName:"domainosApplicationsGlobalSearch"
        appletInterface:applications.hostItem
        favoritesModel:catalog.favoritesModel
        mergeResults:true
        runners:["krunner_services"]
        query:applications.drawer || !popup.visible ? "" : search.text
    }
    Loader {
        id:kdeMenu
        active:applications.usesKdeMenu
        sourceComponent:DomainOSKdeApplicationMenu {
            hostItem:applications.hostItem
            catalogModel:catalog
            favoritesClient:applications.favoritesClient
            onFailure:reason=>applications.commands.reported({ok:false,outcome:"unavailable",detail:reason})
        }
    }
    onUsesKdeMenuChanged:close()
    function desktopId(value) {
        const text = String(value).replace(/^applications:/, "")
        return /^[A-Za-z0-9_][A-Za-z0-9_.-]*\.desktop$/.test(text) ? text : ""
    }
    function pin(value) {
        const id = desktopId(value)
        if (!id || pins.indexOf(id) !== -1) return false
        pinListRequested(pins.concat([id]))
        return true
    }
    function unpin(index) {
        if (!Number.isInteger(index) || index < 0 || index >= pins.length) return false
        const next = pins.slice()
        next.splice(index, 1)
        pinListRequested(next)
        return true
    }
    function movePin(index, delta) {
        if (!Number.isInteger(index) || index < 0 || index >= pins.length || !Number.isInteger(delta)) return false
        const destination = index + delta
        if (destination < 0 || destination >= pins.length || destination === index) return false
        const next = pins.slice()
        next.splice(destination, 0, next.splice(index, 1)[0])
        pinListRequested(next)
        return true
    }
    function pinInfo(index) {
        const id = pins[index] || ""
        for (let row = 0; row < metadataRows.count; row++) {
            const item = metadataRows.itemAt(row)
            if (item && item.desktop === id)
                return {desktopId:id,title:item.title,icon:item.icon,available:item.available}
        }
        return {desktopId:id,title:qsTr("Unavailable: %1").arg(id),icon:"application-x-executable",available:false}
    }
    function favoriteInfo(index) {
        const item = favoriteDrawerRows.itemAt(index)
        return item ? {favoriteId:item.favoriteId,title:item.text,available:item.available}
            : {favoriteId:"",title:"",available:false}
    }
    function launchFavorite(favoriteId) {
        // Resolve the current provider row from its identity. Reordering a
        // shared favorite while this drawer is open must not launch a neighbour.
        for (let row = 0; row < favoriteProviderRows.count; ++row) {
            const item = favoriteProviderRows.itemAt(row)
            if (item && item.favoriteId === favoriteId && item.available) {
                const closeRequested = dispatchNative(catalog.favoritesModel,row,"",null)
                if (closeRequested) popup.visible = false
                return closeRequested
            }
        }
        return false
    }
    function launchPin(index) {
        if (!Number.isInteger(index) || index < 0 || index >= pins.length || !pinInfo(index).available) return false
        commands.openApplication(pins[index])
        popup.visible = false
        return true
    }
    DomainOSPopupToggle { id: menuToggle; showing: applications.popupVisible && !applications.drawer }
    DomainOSPopupToggle { id: drawerToggle; showing: popup.visible && applications.drawer }
    function showMenu(anchor) {
        const show = menuToggle.shouldOpen(anchor)
        drawer = false; navigation = []; currentModel = catalog; search.text = ""
        if (usesKdeMenu && kdeMenu.item) {
            popup.visible=false
            if (show) kdeMenu.item.openMenu(anchor)
            else kdeMenu.item.closeMenu()
            return
        }
        popup.visualParent = anchor; popup.visible = show
    }
    function showDrawer(anchor) {
        const show = drawerToggle.shouldOpen(anchor)
        if (kdeMenu.item) kdeMenu.item.closeMenu()
        drawer = true; navigation = []; search.text = ""
        popup.visualParent = anchor; popup.visible = show
        ++favoriteOrderGeneration
        if (show) readFavoriteOrder()
    }
    function dispatchNative(model, row, actionId, argument) {
        const id = String(actionId || "")
        // Favorite editing is metadata management, not an application launch.
        if (id.indexOf("_kicker_favorite_") === 0)
            return ApplicationActions.triggerAction(model, row, id, argument)
        const token = commands.begin("kicker-dispatch")
        try {
            const closeRequested = model.trigger(row, id, argument)
            commands.finish(token, {ok:true, token:token, action:"kicker-dispatch",
                nativeAction:id, outcome:"dispatch-returned", closeRequested:!!closeRequested,
                detail:qsTr("The native launcher dispatch returned. Its result controls menu closure; application acceptance and completion are not observed here.")})
            return closeRequested
        } catch (error) {
            commands.finish(token, {ok:false, token:token, action:"kicker-dispatch",
                nativeAction:id, outcome:"failed", detail:String(error)})
            return false
        }
    }
    function enter(index, record, sourceModel) {
        const model=sourceModel || currentModel
        if (record.hasChildren) {
            navigation = navigation.concat([model])
            currentModel = model.modelForRow(index)
            search.text = ""
        } else {
            // Preserve Kicker's provider for files, favorites and app actions.
            const triggered = dispatchNative(model, index, "", null)
            popup.visible = false
            return triggered
        }
    }
    function enterFiltered(index, record) {
        const source = filtered.mapToSource(filtered.index(index,0))
        return enter(source.row,record,filtered.sourceModel)
    }
    function close() { popup.visible = false;if (kdeMenu.item) kdeMenu.item.closeMenu() }
    function openPreferences() { close();configureRequested() }
    function showFavorites() {
        navigation = navigation.concat([currentModel])
        currentModel = catalog.favoritesModel
        search.text = ""
    }
    function openEntryMenu(anchor, index, record) {
        if (drawer || record.disabled || record.isSeparator) return false
        const source = filtered.mapToSource(filtered.index(index, 0))
        const actions = Array.from(record.actionList || [])
        const favoriteActions = ApplicationActions.createFavoriteActions(
            text => qsTr(text), catalog.favoritesModel, record.favoriteId)
        if (favoriteActions) {
            if (actions.length) actions.push({type:"separator"})
            actions.push({type:"title", text:qsTr("KDE favorites for this user")})
            actions.push(...favoriteActions)
        }
        if (!actions.length) return false
        entryMenu.sourceModel = filtered.sourceModel
        entryMenu.sourceRow = source.row
        entryMenu.actionList = actions
        entryMenu.menu.visualParent = anchor
        entryMenu.menu.openRelative()
        return true
    }
    DomainOSApplicationMenu {
        id: entryMenu
        objectName: "domainosApplicationContextMenu"
        dispatchHandler: (model,row,actionId,argument) => applications.dispatchNative(model,row,actionId,argument)
        onLaunchRequested: popup.visible = false
    }
    KItemModels.KSortFilterProxyModel {
        id: filtered
        objectName: "domainosApplicationsFilter"
        sourceModel: applications.searching ? applications.searchResultsModel : applications.currentModel
        filterRoleName: "display"
        // KRunner already ranks/matches application names, descriptions and
        // keywords. Filtering display text again would hide valid matches.
        filterString: ""
        filterCaseSensitivity: Qt.CaseInsensitive
    }
    PlasmaCore.Dialog {
        id: popup
        onVisibleChanged:if (!visible) { ++applications.favoriteOrderGeneration;applications.favoriteOrderReadAgain=false }
        objectName: "domainosApplicationsPopup"
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowStaysOnTopHint
        hideOnWindowDeactivate: true
        location: PlasmaCore.Types.BottomEdge
        mainItem: Item {
            id: popupContent
            objectName: "domainosApplicationsPopupContent"
            width: 440; height: 430
            DomainOSControlPalette { target: popupContent }
            Rectangle { anchors.fill: parent; color: popupContent.Kirigami.Theme.backgroundColor }
            ColumnLayout {
            anchors.fill: parent; spacing: 4
            Controls.Label { text: applications.drawer ? qsTr("Pinned applications") : qsTr("Applications"); font.bold: true }
            RowLayout {
                visible: !applications.drawer
                DomainOSButton {
                    id: backButton
                    text: qsTr("Back"); enabled: applications.navigation.length > 0
                    onClicked: {
                        const previous = applications.navigation.slice()
                        applications.currentModel = previous.pop()
                        applications.navigation = previous; search.text = ""
                    }
                }
                DomainOSTextField {
                    id: search; objectName:"domainosApplicationsSearch"
                    Layout.fillWidth: true; placeholderText: qsTr("Search applications…")
                }
                DomainOSButton {
                    id: favoritesButton
                    objectName: "domainosApplicationsFavoritesButton"
                    text: qsTr("Favorites")
                    Controls.ToolTip.visible: hovered
                    Controls.ToolTip.text: qsTr("Shared by your KDE application menus.")
                    onClicked: applications.showFavorites()
                }
            }
            Controls.ItemDelegate {
                objectName:"domainosPinnedPreferencesEntry"
                visible:applications.drawer
                Layout.fillWidth:true
                text:qsTr("Preferências do painel…")
                icon.name:"configure"
                onClicked:applications.openPreferences()
                Accessible.description:qsTr("Item permanente desta gaveta; configurar esta instância do painel")
            }
            Controls.MenuSeparator { visible:applications.drawer;Layout.fillWidth:true }
            Controls.ScrollView {
                id:drawerView;objectName:"domainosPinnedDrawerScrollView"
                visible:applications.drawer
                Layout.fillWidth:true;Layout.fillHeight:true
                contentWidth:availableWidth
                contentHeight:drawerColumn.implicitHeight
                Controls.ScrollBar.vertical:DomainOSViewScrollBar { scrollView:drawerView;colorPalette:scrollPalette }
                Controls.ScrollBar.horizontal:DomainOSViewScrollBar { scrollView:drawerView;colorPalette:scrollPalette;policy:Controls.ScrollBar.AlwaysOff }
                clip:true
                Column {
                    id:drawerColumn;objectName:"domainosPinnedDrawerColumn"
                    width:drawerView.availableWidth;spacing:2
                    Controls.Label {
                        objectName:"domainosTaskbarPinsHeading"
                        text:qsTr("Fixados pela barra de tarefas")
                        font.bold:true;visible:applications.pins.length>0
                    }
                    Repeater {
                        model:applications.pins
                        delegate:Controls.ItemDelegate {
                            id:pinEntry
                            required property int index
                            objectName:"domainosApplicationEntry_"+index
                            readonly property var pin:applications.pinInfo(index)
                            width:drawerColumn.width;height:36;padding:4
                            text:pin.title
                            onClicked:applications.launchPin(index)
                            contentItem:RowLayout {
                                spacing:4
                                Kirigami.Icon { source:pinEntry.pin.icon;implicitWidth:20;implicitHeight:20;animated:false }
                                Controls.Label {
                                    objectName:"domainosPinnedName_"+pinEntry.index
                                    text:pinEntry.text;textFormat:Text.PlainText;Layout.fillWidth:true;elide:Text.ElideRight
                                }
                                DomainOSButton {
                                    id:unpinButton;objectName:"domainosPinnedRemove_"+pinEntry.index
                                    Layout.minimumWidth:28;Layout.preferredWidth:28;Layout.maximumWidth:28
                                    Layout.minimumHeight:28;Layout.preferredHeight:28;Layout.maximumHeight:28
                                    padding:2;icon.name:"list-remove";icon.width:16;icon.height:16
                                    Accessible.name:qsTr("Desafixar %1 da barra de tarefas").arg(pinEntry.text)
                                    Controls.ToolTip.visible:hovered;Controls.ToolTip.text:Accessible.name
                                    onClicked:applications.unpin(pinEntry.index)
                                }
                                DomainOSButton {
                                    id:pinUpButton;objectName:"domainosPinnedUp_"+pinEntry.index
                                    Layout.minimumWidth:28;Layout.preferredWidth:28;Layout.maximumWidth:28
                                    Layout.minimumHeight:28;Layout.preferredHeight:28;Layout.maximumHeight:28
                                    padding:2;icon.name:"go-up";icon.width:16;icon.height:16
                                    enabled:pinEntry.index>0
                                    Accessible.name:qsTr("Mover %1 para cima").arg(pinEntry.text)
                                    Controls.ToolTip.visible:hovered;Controls.ToolTip.text:Accessible.name
                                    onClicked:applications.movePin(pinEntry.index,-1)
                                }
                                DomainOSButton {
                                    id:pinDownButton;objectName:"domainosPinnedDown_"+pinEntry.index
                                    Layout.minimumWidth:28;Layout.preferredWidth:28;Layout.maximumWidth:28
                                    Layout.minimumHeight:28;Layout.preferredHeight:28;Layout.maximumHeight:28
                                    padding:2;icon.name:"go-down";icon.width:16;icon.height:16
                                    enabled:pinEntry.index+1<applications.pins.length
                                    Accessible.name:qsTr("Mover %1 para baixo").arg(pinEntry.text)
                                    Controls.ToolTip.visible:hovered;Controls.ToolTip.text:Accessible.name
                                    onClicked:applications.movePin(pinEntry.index,1)
                                }
                            }
                        }
                    }
                    Controls.MenuSeparator {
                        objectName:"domainosPinnedFavoritesSeparator"
                        width:parent.width;visible:applications.pins.length>0 && favoriteDrawerRows.count>0
                    }
                    Controls.Label {
                        objectName:"domainosSharedFavoritesHeading"
                        text:qsTr("Favoritos do menu Applications do KDE")
                        font.bold:true;visible:favoriteDrawerRows.count>0
                    }
                    Controls.Label {
                        objectName:"domainosSharedFavoriteOrderSource"
                        text:applications.favoriteOrderMessage
                        visible:favoriteDrawerRows.count>0 && text.length>0
                        width:parent.width;wrapMode:Text.WordWrap
                    }
                    Repeater {
                        id:favoriteDrawerRows
                        // Membership/actions stay native. The read-only overlay
                        // follows the external menu's persisted identity order.
                        model:applications.orderedFavorites
                        delegate:Controls.ItemDelegate {
                            id:favoriteEntry
                            required property int index
                            required property var modelData
                            objectName:"domainosSharedFavorite_"+index
                            readonly property string favoriteId:String(modelData.favoriteId)
                            readonly property bool available:modelData.available
                            property string pressedFavoriteId:""
                            width:drawerColumn.width;height:36;padding:4
                            enabled:available
                            text:String(modelData.title)
                            icon.name:typeof modelData.icon === "string" ? modelData.icon : ""
                            onPressed:pressedFavoriteId=favoriteId
                            onClicked:applications.launchFavorite(pressedFavoriteId || favoriteId)
                            contentItem:RowLayout {
                                spacing:4
                                Kirigami.Icon { source:favoriteEntry.modelData.icon;implicitWidth:20;implicitHeight:20;animated:false }
                                Controls.Label { text:favoriteEntry.text;textFormat:Text.PlainText;Layout.fillWidth:true;elide:Text.ElideRight }
                            }
                        }
                    }
                    Controls.Label {
                        visible:applications.pins.length===0 && favoriteDrawerRows.count===0
                        text:qsTr("Fixe aplicativos pela barra ou marque favoritos no menu Applications do KDE.")
                        width:parent.width;wrapMode:Text.WordWrap
                    }
                }
            }
            Controls.ScrollView {
                id:applicationsView
                Controls.ScrollBar.vertical:DomainOSViewScrollBar { scrollView:applicationsView;colorPalette:scrollPalette }
                Controls.ScrollBar.horizontal:DomainOSViewScrollBar { scrollView:applicationsView;colorPalette:scrollPalette }
                visible:!applications.drawer
                Layout.fillWidth: true; Layout.fillHeight: true
                ListView {
                    id: entries
                    clip: true
                    model: applications.drawer ? null : filtered
                    delegate: Controls.ItemDelegate {
                        id: entry
                        objectName: "domainosApplicationEntry_"+index
                        required property int index
                        required property var model
                        property var record: applications.drawer ? ({}) : model
                        property var pin: applications.drawer ? applications.pinInfo(index) : ({})
                        width: entries.width
                        text: applications.drawer ? pin.title : String(record.display || "")
                        enabled: applications.drawer || (!record.disabled && !record.isSeparator)
                        onClicked: {
                            if (applications.drawer) {
                                applications.launchPin(index)
                            } else {
                                applications.enterFiltered(index, record)
                            }
                        }
                        Keys.onMenuPressed: applications.openEntryMenu(entry, entry.index, entry.record)
                        Keys.onPressed: event => {
                            if (event.key === Qt.Key_F10 && (event.modifiers & Qt.ShiftModifier)) {
                                applications.openEntryMenu(entry, entry.index, entry.record)
                                event.accepted = true
                            }
                        }
                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.RightButton
                            onClicked: applications.openEntryMenu(entry, entry.index, entry.record)
                        }
                        contentItem: RowLayout {
                            Kirigami.Icon { source: applications.drawer ? entry.pin.icon : entry.record.decoration; implicitWidth: 24; implicitHeight: 24; animated: false }
                            Controls.Label { text: entry.text; Layout.fillWidth: true; elide: Text.ElideRight }
                            DomainOSButton {
                                id: pinButton
                                text: applications.drawer ? qsTr("Remove") : qsTr("Pin")
                                visible: applications.drawer || applications.desktopId(entry.record.favoriteId || entry.record.url).length > 0
                                onClicked: applications.drawer ? applications.unpin(entry.index)
                                    : applications.pin(entry.record.favoriteId || entry.record.url)
                            }
                            DomainOSButton {
                                id: moveUpButton
                                text: "↑"; visible: applications.drawer; enabled: entry.index > 0
                                onClicked: applications.movePin(entry.index, -1)
                            }
                            DomainOSButton {
                                id: moveDownButton
                                text: "↓"; visible: applications.drawer; enabled: entry.index + 1 < applications.pins.length
                                onClicked: applications.movePin(entry.index, 1)
                            }
                        }
                    }
                    Controls.Label {
                        anchors.centerIn: parent
                        visible: applications.drawer && applications.pins.length === 0
                        text: qsTr("Pin an application from the menu, or import a list in panel preferences.")
                        width: parent.width - 20; wrapMode: Text.WordWrap
                    }
                    Controls.Label {
                        anchors.centerIn: parent
                        visible: !applications.drawer && entries.count === 0
                        text: applications.currentModel === catalog.favoritesModel
                            ? qsTr("No favorites supplied by this menu's provider.")
                            : search.text.length > 0 ? qsTr("No applications match this search.")
                            : qsTr("No entries are available in this category.")
                        width: parent.width - 20; wrapMode: Text.WordWrap
                    }
                }
            }
            DomainOSButton {
                id: configureButton; objectName: "domainosApplicationsConfigureButton"
                text: qsTr("Configure panel…");visible:!applications.drawer;onClicked:applications.openPreferences()
            }
            }
        }
    }
}
