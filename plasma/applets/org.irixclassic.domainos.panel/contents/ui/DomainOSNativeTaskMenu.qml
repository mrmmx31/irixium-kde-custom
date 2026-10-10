// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtCore
import QtQml.Models
import org.kde.taskmanager as TaskManager
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.private.taskmanager as TaskManagerApplet
import org.kde.plasma.private.mpris as Mpris

Item {
    id: menuHost
    visible:false
    required property var iconbox
    required property var controller
    // These names form the creation context expected by KDE's installed menu.
    readonly property var tasks:iconbox
    readonly property var tasksModel:adapter
    readonly property TaskManager.VirtualDesktopInfo virtualDesktopInfo:TaskManager.VirtualDesktopInfo {}
    readonly property TaskManager.ActivityInfo activityInfo:TaskManager.ActivityInfo {}
    property var pulseAudio:null
    property var openedMenu:null
    property var menuItems:[]
    property var targetRecord:null
    property var targetIndex:null
    property var capturedSelection:[]
    readonly property url contextMenuUrl:StandardPaths.locate(StandardPaths.GenericDataLocation,
        "plasma/plasmoids/org.kde.plasma.taskmanager/contents/ui/ContextMenu.qml")
    readonly property url pulseAudioUrl:StandardPaths.locate(StandardPaths.GenericDataLocation,
        "plasma/plasmoids/org.kde.plasma.taskmanager/contents/ui/PulseAudio.qml")
    property var contextComponent:null
    property int menuGeneration:0
    property var paletteScope:null
    property string paletteError:""
    readonly property var nativePaletteStats:paletteScope ? paletteScope.stats : ({error:paletteError})
    function preparePalette(menu) {
        if (!paletteScope && !paletteError) {
            const component=Qt.createComponent("DomainOSNativeMenuPalette.qml")
            if (component.status===Component.Ready) paletteScope=component.createObject(menuHost)
            if (!paletteScope) paletteError=component.errorString() || qsTr("O suporte de cores do menu nativo está indisponível.")
        }
        if (!paletteScope) return false
        const prepared=paletteScope.prepare(menu)
        paletteError=prepared ? "" : String(paletteScope.stats.error || qsTr("Não foi possível adaptar as cores deste menu."))
        return prepared
    }
    function releasePalette() { if (paletteScope) paletteScope.release() }
    // QMenu measures its QWidget in window coordinates. Passing a task inside
    // our scaled artwork would scale that native height a second time when
    // Plasma maps its popup position. Keep the native anchor unscaled.
    Item {
        id: nativeAnchor
        objectName: "domainosNativeTaskMenuAnchor"
        visible: false
        property var source: null
        readonly property bool hasAudioStream: !!source && !!source.hasAudioStream
        readonly property bool muted: !!source && !!source.muted
        function toggleMuted() { if (source) source.toggleMuted() }
        function showContextMenu(options) { if (source) source.showContextMenu(options) }
        LayoutMirroring.enabled: source ? source.LayoutMirroring.enabled : false
    }
    function prepareAnchor(source) {
        if (!source || !source.Window.window) return false
        const content = source.Window.window.contentItem
        const bounds = source.mapToItem(content, Qt.rect(0, 0, source.width, source.height))
        if (![bounds.x, bounds.y, bounds.width, bounds.height].every(Number.isFinite)
            || bounds.width <= 0 || bounds.height <= 0) return false
        nativeAnchor.parent = content
        nativeAnchor.source = source
        nativeAnchor.x = bounds.x; nativeAnchor.y = bounds.y
        nativeAnchor.width = bounds.width; nativeAnchor.height = bounds.height
        return true
    }
    TaskManagerApplet.Backend { id:backend;objectName:"domainosNativeTaskBackend";highlightWindows:menuHost.iconbox.highlightWindows;onAddLauncher:url=>menuHost.pinURL(url,true) }
    property int launcherRevision:0
    Instantiator {
        id:launcherStatus
        model:menuHost.controller.taskRows
        delegate:Item {
            required property var modelData
            readonly property string key:modelData.key
            readonly property var provider:loader.item
            visible:false
            Loader {
                id:loader
                active:!!modelData.launcherUrl
                sourceComponent:TaskManagerApplet.SmartLauncherItem {
                    launcherUrl:modelData.launcherUrl
                    onUrgentChanged:menuHost.refreshLauncherAttention()
                }
                onLoaded:menuHost.refreshLauncherAttention()
            }
        }
        onObjectAdded:{ ++menuHost.launcherRevision;Qt.callLater(menuHost.refreshLauncherAttention) }
        onObjectRemoved:{ ++menuHost.launcherRevision;Qt.callLater(menuHost.refreshLauncherAttention) }
    }
    function smartLauncherFor(key) {
        const revision=launcherRevision
        for (let index=0;index<launcherStatus.count;++index) {
            const item=launcherStatus.objectAt(index)
            if (item && item.key===key) return item.provider
        }
        return null
    }
    function refreshLauncherAttention() {
        let urgent=false
        for (let index=0;index<launcherStatus.count;++index) {
            const item=launcherStatus.objectAt(index)
            urgent=urgent || !!item && !!item.provider && item.provider.urgent
        }
        controller.launcherDemandsAttention=urgent
    }
    function validHighlightRecord(record) {
        // A member of a group is a child row, not a top-level task row.
        return !!record && iconbox.checkTarget(record) && (record.group ? validRecord(record)
            : !!controller.windowFor(record.key) && controller.windowFor(record.key).pid === record.pid)
    }
    function highlightRecord(record,highlighted) {
        backend.cancelHighlightWindows()
        if (!highlighted || !iconbox.highlightWindows || !validHighlightRecord(record)) return false
        const records=record.group ? controller.membersFor(record.key) : [controller.windowFor(record.key)]
        const ids=records.reduce((ids,window)=>ids.concat(window.windowIds || []),[])
        if (!ids.length) return false
        backend.windowsHovered(ids,true)
        return true
    }
    function validRecord(record) {
        return !!record && controller.taskRowForRecord(record)>=0 && iconbox.checkTarget(record)
    }
    function publishGeometry(task) {
        if (!task || !validRecord(task.record) || typeof controller.tasksModel.requestPublishDelegateGeometry!=="function") return
        const index=modelIndexFor(task.record)
        if (index!==null) controller.tasksModel.requestPublishDelegateGeometry(index,backend.globalRect(task),task)
    }
    function handleDrop(record,urls) {
        if (!validRecord(record) || !urls.length) { iconbox.fail(qsTr("A tarefa de destino mudou."));return }
        if (urls.every(url=>backend.isApplication(url))) for (const url of urls) pinURL(url,true)
        else iconbox.handleResult(controller.openUrls(record,urls))
    }
    onVisibleChanged:if (!visible) backend.cancelHighlightWindows()
    Component.onDestruction:{ releasePalette();backend.cancelHighlightWindows();if (controller) controller.launcherDemandsAttention=false }
    Mpris.Mpris2Model { id:mpris2Source }
    Component.onCompleted: {
        contextComponent=Qt.createComponent(contextMenuUrl)
        const audio=Qt.createComponent(pulseAudioUrl)
        if (audio.status===Component.Ready) pulseAudio=audio.createObject(menuHost)
    }
    Connections {
        target:menuHost.pulseAudio
        ignoreUnknownSignals:true
        function onStreamsChanged() { menuHost.iconbox.refreshAudioStreams() }
    }
    function desktopId(url) {
        const value=decodeURIComponent(String(url)).replace(/^applications:/,"").split("/").pop()
        return /^[A-Za-z0-9_][A-Za-z0-9_.-]*\.desktop$/.test(value) ? value : ""
    }
    function pinURL(url,add) {
        const id=desktopId(url)
        if (!id) { iconbox.fail(qsTr("Esse aplicativo não possui uma entrada de desktop para fixar."));return }
        if (add) iconbox.pinRequested(id);else iconbox.unpinRequested(id)
    }
    function validTarget() {
        if (!targetRecord || !iconbox.checkTarget(targetRecord)) return false
        if (!targetRecord.group) return true
        return targetRecord.members.every(record=>iconbox.checkTarget(record))
    }
    function modelIndexFor(record) {
        const target=controller.nativeTaskTarget(record)
        return target ? target.index : null
    }
    function unavailableRole(role) {
        const atm=TaskManager.AbstractTasksModel
        if ([atm.LauncherUrl,atm.LauncherUrlWithoutIcon,atm.AppId,atm.AppName,Qt.DisplayRole,atm.MimeType].indexOf(role)>=0) return ""
        if ([atm.VirtualDesktops,atm.Activities,atm.WinIdList].indexOf(role)>=0) return []
        if ([atm.ChildCount,atm.AppPid].indexOf(role)>=0) return 0
        return false
    }
    function capturedTargets() {
        if (!targetRecord || !controller.nativeTaskTarget(targetRecord)) return null
        const records=targetRecord.group ? targetRecord.members : [targetRecord]
        const targets=[]
        for (const record of records) {
            const scoped=controller.resolveWindow(record.key)
            const current=controller.nativeTaskTarget(record)
            if (!scoped || scoped.record.pid!==record.pid || !current || current.record.pid!==record.pid) return null
            targets.push(current)
        }
        return targets.length ? targets : null
    }
    function menuRole(role) {
        const targets=capturedTargets()
        if (!targets) return unavailableRole(role)
        const read=target=> {
            const value=target.model.data(target.index,role)
            return value===undefined || value===null ? unavailableRole(role) : value
        }
        if (!targetRecord.group) return read(targets[0])
        const atm=TaskManager.AbstractTasksModel
        // Match KDE TaskGroupingProxyModel's role semantics, using only the
        // captured projected members. Its native parent may include windows
        // temporarily pinned outside the displayed group.
        // KDE/plasma-workspace v6.3.6 libtaskmanager/taskgroupingproxymodel.cpp
        if ([atm.IsClosable,atm.IsMaximizable,atm.IsMaximized,atm.IsMinimizable,atm.IsMinimized,
             atm.IsKeepAbove,atm.IsKeepBelow,atm.IsFullScreenable,atm.IsFullScreen,
             atm.IsShadeable,atm.IsShaded,atm.IsVirtualDesktopsChangeable,atm.SkipTaskbar].indexOf(role)>=0)
            return targets.every(target=>!!read(target))
        if ([atm.IsActive,atm.IsDemandingAttention].indexOf(role)>=0)
            return targets.some(target=>!!read(target))
        if (role===atm.IsMovable || role===atm.IsResizable) return false
        if (role===atm.IsGroupParent) return true
        if (role===atm.ChildCount) return targets.length
        if (role===atm.MimeType) return "windowsystem/multiple-winids"
        if ([atm.WinIdList,atm.VirtualDesktops,atm.Activities].indexOf(role)>=0) {
            const values=targets.reduce((all,target)=>all.concat(Array.from(read(target) || [])),[])
            return role===atm.WinIdList ? values : values.filter((value,index)=>values.indexOf(value)===index)
        }
        if (role===Qt.DisplayRole) return targets[0].record.appName || targets[0].record.appId
        if (role===atm.IsGroupable) {
            const current=controller.nativeTaskTarget(targetRecord)
            return current ? current.model.data(current.index,role) : unavailableRole(role)
        }
        // KDE delegates other metadata to the first child. Choose the first
        // remaining member, rather than an excluded pin's title/PID/launcher.
        return read(targets[0])
    }
    function apply(action,argument) {
        if (!validTarget()) { iconbox.fail(qsTr("A janela do menu não está mais disponível."));return }
        const records=targetRecord.group ? targetRecord.members : [targetRecord]
        for (const record of (action==="newInstance" ? records.slice(0,1) : records)) {
            const current=controller.resolveWindow(record.key)
            if (!current || current.record.pid!==record.pid) continue
            const mapped=action==="toggleMinimized" ? (current.record.minimized ? "restore" : "minimize")
                : action==="toggleMaximized" ? (current.record.maximized ? "unmaximize" : "maximize") : action
            iconbox.handleResult(controller.requestAction(record.key,mapped,argument,record.pid))
        }
    }
    function newVirtualDesktop() {
        // This native operation acts on a whole model row. Unlike apply(), it
        // cannot address the captured members individually. Resolve the row
        // again and reject changed membership/PIDs before creating a desktop.
        const target=controller.nativeTaskTarget(targetRecord)
        if (!target || !validTarget()) {
            iconbox.fail(qsTr("O grupo ou a janela mudou. Reabra o menu antes de criar outra área de trabalho."))
            return false
        }
        const model=target.model, index=target.index
        if (targetRecord.group) {
            const nativeMembers=controller.records(model,true).find(row=>row.group && row.key===targetRecord.key)
            if (!nativeMembers || nativeMembers.members.length!==targetRecord.members.length
                || !nativeMembers.members.every(member=>targetRecord.members.some(captured=>
                    member.key===captured.key && member.pid===captured.pid))) {
                iconbox.fail(qsTr("Esse comando nativo incluiria uma janela fixada fora do grupo. Escolha uma área existente para mover apenas os membros deste grupo."))
                return false
            }
        }
        if (!controller.value(model,index,TaskManager.AbstractTasksModel.IsVirtualDesktopsChangeable,false)) {
            iconbox.fail(qsTr("Essa janela ou grupo não permite mudar de área de trabalho."))
            return false
        }
        model.requestNewVirtualDesktop(index)
        controller.operationRequested({state:"requested",action:"newVirtualDesktop",key:targetRecord.key})
        // Only the native request is observed here, not compositor completion.
        return true
    }
    function toggleGrouping(record) {
        const index=modelIndexFor(record)
        if (index===null || !iconbox.checkTarget(record)) return
        controller.tasksModel.requestToggleGrouping(index)
        controller.groupingAppIdBlacklist=controller.tasksModel.groupingAppIdBlacklist
        controller.groupingLauncherUrlBlacklist=controller.tasksModel.groupingLauncherUrlBlacklist
        iconbox.groupingPreferencesRequested(controller.groupingAppIdBlacklist,controller.groupingLauncherUrlBlacklist)
    }
    function updateStreams(task) {
        if (!pulseAudio || !task || !task.record) return
        const record=task.record
        const records=record.group ? record.members : [record]
        let streams=[]
        for (const window of records) {
            let found=pulseAudio.streamsForAppId(window.appId)
            if (!found.length) {
                found=pulseAudio.streamsForPid(window.pid)
                if (found.length) pulseAudio.registerPidMatch(window.appName)
                else if (!pulseAudio.hasPidMatch(window.appName)) found=pulseAudio.streamsForAppName(window.appName)
            }
            for (const stream of found) if (streams.indexOf(stream)<0) streams.push(stream)
        }
        task.audioStreams=streams
    }
    function audioNavigation(record,direction) {
        const window=record.group ? record.members[0] : record
        if (!window || !iconbox.checkTarget(window)) return
        const player=mpris2Source.playerForLauncherUrl(window.launcherUrl,window.pid)
        if (player) { if (direction<0 && player.canGoPrevious) player.Previous();else if (direction>0 && player.canGoNext) player.Next() }
    }
    function addItem(menu,text,name,enabled,callback,before) {
        const item=Qt.createQmlObject('import org.kde.plasma.extras as PlasmaExtras; PlasmaExtras.MenuItem {}',menu)
        item.objectName=name;item.text=text;item.enabled=enabled
        if (callback) item.clicked.connect(callback)
        if (before) menu.addMenuItem(item,before);else menu.addMenuItem(item)
        menuItems.push(item)
        return item
    }
    function addOperations(menu,title,records,prefix) {
        const parent=addItem(menu,title,prefix,records.length>=1,null)
        const submenu=Qt.createQmlObject('import org.kde.plasma.extras as PlasmaExtras; PlasmaExtras.Menu {}',menu)
        submenu.visualParent=parent.action
        addItem(submenu,qsTr("Fixar temporariamente na Iconbox"),prefix+"_temporaryPin",
            records.length>=1 && records.some(record=>!controller.temporaryPinned(record.key,record.pid)),()=>{
                const result=controller.pinTemporaryWindows(records)
                iconbox.handleResult(result)
                if (result.pinned) iconbox.firstVisible=0
            })
        for (const definition of [
            ["columns",qsTr("Dispor em colunas, lado a lado")],
            ["rows",qsTr("Dispor em linhas, uma sobre a outra")],
            ["mosaic",qsTr("Dispor em mosaico")],
            ["collect",qsTr("Reunir no desktop e monitor atuais")],
            ["maximize",qsTr("Maximizar selecionadas")],
            ["minimize",qsTr("Minimizar selecionadas")]])
            addItem(submenu,definition[1],prefix+"_"+definition[0],iconbox.geometryReady(records,definition[0]),
                ()=>iconbox.batch(definition[0],records))
    }
    function close() {
        ++menuGeneration
        const menu=openedMenu
        openedMenu=null
        if (menu) menu.close()
        releasePalette()
    }
    function chooseGroup(record,anchor) {
        close()
        const generation=menuGeneration
        Qt.callLater(()=>{ if (generation===menuGeneration && iconbox.checkTarget(record)) iconbox.selectRecord(record,0,anchor) })
    }
    function discardPartialMenu(menu,error) {
        if (openedMenu===menu) openedMenu=null
        releasePalette()
        if (menu) {
            menu.close()
            // KDE destroys a menu which reaches Closed. A failure during its
            // construction never opens it, so release that object ourselves.
            if (menu.status===PlasmaExtras.Menu.Closed) menu.destroy()
        }
        iconbox.fail(qsTr("Não foi possível montar o menu nativo: %1").arg(String(error)))
    }
    function open(record,anchor,options) {
        if (!contextComponent || contextComponent.status!==Component.Ready) {
            iconbox.fail(qsTr("O menu nativo do KDE está indisponível."));return false
        }
        close()
        const generation=menuGeneration
        // Close/unmap any old QMenu first. Never replace its visual parent or
        // build the successor while its native popup is still being hidden.
        Qt.callLater(()=>menuHost.createMenu(record,anchor,options,generation))
        return true
    }
    function createMenu(record,anchor,options,generation) {
        if (generation!==menuGeneration || !anchor || !iconbox.checkTarget(record)) return
        targetRecord=record;targetIndex=modelIndexFor(record);capturedSelection=iconbox.selectedSnapshot()
        if (targetIndex===null || !validTarget()) return false
        let menu=null
        try {
        if (!prepareAnchor(anchor)) throw new Error(qsTr("A posição do menu não está disponível."))
        menu=contextComponent.createObject(menuHost,{visualParent:nativeAnchor,modelIndex:targetIndex,
            backend:backend,mpris2Source:mpris2Source,showAllPlaces:options.showAllPlaces || false})
        if (!menu) throw new Error(contextComponent.errorString())
        openedMenu=menu;menuItems=[]
        menu.statusChanged.connect(()=>{
            if (menu.status===PlasmaExtras.Menu.Closed && openedMenu===menu) {
                openedMenu=null
                releasePalette()
            }
        })
        if (!record.group && controller.temporaryPinned(record.key,record.pid))
            addItem(menu,qsTr("Desafixar esta janela da Iconbox"),"domainosNativeUnpinWindow",true,
                ()=>iconbox.toggleTemporaryPin(record),menu.content.length ? menu.content[0] : null)
        // A separator is a QAction only after it is inserted into the QMenu.
        menu.addMenuItem(menu.newSeparator(menu))
        if (record.group) {
            addItem(menu,qsTr("Escolher janelas do grupo…"),"domainosNativeChooseGroup",true,
                ()=>chooseGroup(record,anchor))
            const selectedGroup=record.members.filter(window=>capturedSelection.some(selected=>selected.key===window.key))
            addOperations(menu,qsTr("Organizar escolhidas deste grupo"),selectedGroup,"domainosNativeGroupOperations")
        }
        addOperations(menu,qsTr("Organizar todas as selecionadas"),capturedSelection,"domainosNativeBatchOperations")
        const processItem=addItem(menu,qsTr("Processo"),"domainosNativeProcess",!record.group,null)
        const processMenu=Qt.createQmlObject('import org.kde.plasma.extras as PlasmaExtras; PlasmaExtras.Menu {}',menu)
        processMenu.visualParent=processItem.action
        addItem(processMenu,qsTr("Encerrar à força"),"domainosNativeTerminate",iconbox.processReady(record),
            ()=>iconbox.handleResult(controller.requestTermination(record.key,record.pid)))
        // Keep KDE's QMenu/QActions and all of their dynamic submenus. The
        // optional scope changes only their painting, before the first frame.
        // A missing helper never removes the native menu or its commands.
        preparePalette(menu)
        menu.show()
        } catch(error) {
            discardPartialMenu(menu,error)
            Qt.callLater(()=>{ if (generation===menuGeneration) iconbox.openFallbackContext(record) })
            return false
        }
        return true
    }
    QtObject {
        id:adapter
        function data(index,role) { return menuHost.menuRole(role) }
        function requestActivate(index) { menuHost.apply("activate") }
        function requestClose(index) { menuHost.apply("close") }
        function requestMove(index) { menuHost.apply("move") }
        function requestResize(index) { menuHost.apply("resize") }
        function requestNewInstance(index) { menuHost.apply("newInstance") }
        function requestVirtualDesktops(index,desktops) { menuHost.apply("desktops",desktops) }
        function requestActivities(index,activities) { menuHost.apply("activities",activities) }
        function requestToggleMinimized(index) { menuHost.apply("toggleMinimized") }
        function requestToggleMaximized(index) { menuHost.apply("toggleMaximized") }
        function requestToggleKeepAbove(index) { menuHost.apply("keepAbove") }
        function requestToggleKeepBelow(index) { menuHost.apply("keepBelow") }
        function requestToggleFullScreen(index) { menuHost.apply("fullScreen") }
        function requestToggleShaded(index) { menuHost.apply("shade") }
        function requestToggleGrouping(index) { menuHost.toggleGrouping(menuHost.targetRecord) }
        function requestNewVirtualDesktop(index) {
            menuHost.newVirtualDesktop()
        }
        function launcherActivities(url) {
            return menuHost.iconbox.pinnedApplications.indexOf(menuHost.desktopId(url))>=0 ? [menuHost.activityInfo.nullUuid] : []
        }
        function requestAddLauncher(url) { menuHost.pinURL(url,true) }
        function requestRemoveLauncher(url) { menuHost.pinURL(url,false) }
        function requestAddLauncherToActivity(url,activity) { menuHost.pinURL(url,true) }
        function requestRemoveLauncherFromActivity(url,activity) { menuHost.pinURL(url,false) }
    }
}
