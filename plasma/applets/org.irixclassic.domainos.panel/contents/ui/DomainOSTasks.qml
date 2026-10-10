// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.taskmanager as TaskManager
import "DomainOSTaskSelection.js" as Selection

Item {
    id: controller
    objectName: "domainosTasks"
    visible: false
    // Native providers can be replaced by isolated model doubles in tests.
    property bool nativeEnabled: true
    property var tasksModel: nativeLayer.item ? nativeLayer.item.viewModel : null
    property var scopeModel: nativeLayer.item ? nativeLayer.item.scopeModel : null
    // Window pins are presentation state of this instance, never launchers or
    // KConfig entries. An unfiltered provider distinguishes leaving the scope
    // from closing the exact window or reusing its identity with another PID.
    property var identityModel: nativeLayer.item ? nativeLayer.item.identityModel : null
    property var temporaryWindowPins: []
    property var geometryBackend: null
    property var processBackend: null
    property var currentDesktopId: nativeLayer.item ? nativeLayer.item.desktops.currentDesktop : null
    property string currentActivityId: nativeLayer.item ? nativeLayer.item.activities.currentActivity : ""
    property rect currentScreenGeometry: Qt.rect(0,0,0,0)
    property rect currentAvailableGeometry: currentScreenGeometry
    property string currentScreenName: ""
    property bool onlyCurrentDesktop: true
    property bool onlyCurrentScreen: false
    property bool onlyCurrentActivity: true
    property int groupingMode: TaskManager.TasksModel.GroupApplications
    property bool onlyGroupWhenFull: true
    property int visibleCapacity: 7
    property int sortMode: TaskManager.TasksModel.SortManual
    property var groupingAppIdBlacklist: []
    property var groupingLauncherUrlBlacklist: []
    property string filterMode: "normal"
    // Unset until the user chooses it. Enabling automatic filtering requires L.
    property int automaticThreshold: -1
    property int scopedWindowCount: 0
    readonly property int windowCount: scopedWindowCount
    readonly property bool effectiveMinimizedOnly: Selection.minimizedOnly(filterMode,automaticThreshold,windowCount)
    readonly property bool automaticThresholdRequired: filterMode === "automatic" && automaticThreshold < 0
    readonly property bool scopeReady: !onlyCurrentScreen || (currentScreenGeometry.width > 0 && currentScreenGeometry.height > 0)
    property var windowRows: []
    property var taskRows: []
    readonly property bool anyTaskDemandsAttention: windowRows.some(window=>window.demandsAttention)
    property bool launcherDemandsAttention:false
    readonly property bool demandsAttention:anyTaskDemandsAttention || launcherDemandsAttention
    property var selectedKeys: []
    property var selectedIdentities: ({})
    // Selecting an ordinary task is distinct from starting a checkbox batch.
    // Keep that intention across groups, and discard it with stale identities.
    property var memberSelectionKeys: []
    property string anchorKey: ""
    readonly property int selectionCount: selectedKeys.length
    property string groupSelectorKey: ""
    readonly property bool groupSelectorOpen: groupSelectorKey.length > 0
    readonly property var groupMembers: membersFor(groupSelectorKey)
    readonly property bool memberSelectionActive: memberSelectionKeys.length > 0
    property bool organizationPending: false
    property bool refreshing: false
    property int identityUnavailableCount: 0
    property int refreshFailureCount: 0

    signal groupSelectionRequested(string groupKey, var members)
    signal organizationRequested(var windows)
    signal nativeContextMenuRequested(var descriptor)
    signal operationRequested(var request)
    signal operationUnavailable(var request)
    signal refreshFailed(string code)

    Loader {
        id: nativeLayer
        active: controller.nativeEnabled
        sourceComponent: Component {
            Item {
                property alias viewModel: visibleTasks
                property alias scopeModel: countedTasks
                property alias identityModel: identityTasks
                property alias desktops: desktopInfo
                property alias activities: activityInfo
                TaskManager.VirtualDesktopInfo { id: desktopInfo }
                TaskManager.ActivityInfo { id: activityInfo }
                TaskManager.TasksModel {
                    id: identityTasks
                    filterByVirtualDesktop: false
                    filterByScreen: false
                    filterByActivity: false
                    filterNotMinimized: false
                    filterMinimized: false
                    filterHidden: false
                    groupMode: TaskManager.TasksModel.GroupDisabled
                    launcherList: []
                }
                TaskManager.TasksModel {
                    id: countedTasks
                    virtualDesktop: controller.currentDesktopId
                    activity: controller.currentActivityId
                    screenGeometry: controller.currentScreenGeometry
                    filterByVirtualDesktop: controller.onlyCurrentDesktop
                    filterByScreen: controller.onlyCurrentScreen
                    filterByActivity: controller.onlyCurrentActivity
                    filterNotMinimized: false
                    filterMinimized: false
                    groupMode: TaskManager.TasksModel.GroupDisabled
                    launcherList: []
                }
                TaskManager.TasksModel {
                    id: visibleTasks
                    virtualDesktop: controller.currentDesktopId
                    activity: controller.currentActivityId
                    screenGeometry: controller.currentScreenGeometry
                    filterByVirtualDesktop: controller.onlyCurrentDesktop
                    filterByScreen: controller.onlyCurrentScreen
                    filterByActivity: controller.onlyCurrentActivity
                    filterNotMinimized: controller.effectiveMinimizedOnly
                    filterMinimized: false
                    groupMode: controller.groupingMode
                    groupInline: false
                    groupingWindowTasksThreshold: controller.onlyGroupWhenFull ? controller.visibleCapacity+1 : -1
                    groupingAppIdBlacklist: controller.groupingAppIdBlacklist
                    groupingLauncherUrlBlacklist: controller.groupingLauncherUrlBlacklist
                    sortMode: controller.sortMode
                    launcherList: []
                }
            }
        }
    }

    Connections {
        target: controller.identityModel
        ignoreUnknownSignals: true
        function onCountChanged() { if (controller.temporaryWindowPins.length) controller.queueRefresh() }
        function onDataChanged() { if (controller.temporaryWindowPins.length) controller.queueRefresh() }
        function onRowsInserted() { if (controller.temporaryWindowPins.length) controller.queueRefresh() }
        function onRowsRemoved() { if (controller.temporaryWindowPins.length) controller.queueRefresh() }
        function onModelReset() { if (controller.temporaryWindowPins.length) controller.queueRefresh() }
        function onLayoutChanged() { if (controller.temporaryWindowPins.length) controller.queueRefresh() }
    }
    Connections {
        target: controller.scopeModel
        ignoreUnknownSignals: true
        function onCountChanged() { controller.queueRefresh() }
        function onDataChanged() { controller.queueRefresh() }
        function onRowsInserted() { controller.queueRefresh() }
        function onRowsRemoved() { controller.queueRefresh() }
        function onModelReset() { controller.queueRefresh() }
        function onLayoutChanged() { controller.queueRefresh() }
    }
    Connections {
        target: controller.tasksModel
        ignoreUnknownSignals: true
        function onCountChanged() { controller.queueRefresh() }
        function onDataChanged() { controller.queueRefresh() }
        function onRowsInserted() { controller.queueRefresh() }
        function onRowsRemoved() { controller.queueRefresh() }
        function onModelReset() { controller.queueRefresh() }
        function onLayoutChanged() { controller.queueRefresh() }
    }
    onTasksModelChanged: queueRefresh()
    onScopeModelChanged: queueRefresh()
    onIdentityModelChanged: if (temporaryWindowPins.length) queueRefresh()
    onTemporaryWindowPinsChanged: queueRefresh()
    Component.onCompleted: queueRefresh()

    function queueRefresh() { Qt.callLater(refresh) }
    function value(model,index,role,fallback) {
        const result = model.data(index,role)
        return result === undefined || result === null ? fallback : result
    }
    function windowRecord(model,index) {
        const roles = TaskManager.AbstractTasksModel
        if (!value(model,index,roles.IsWindow,false) || value(model,index,roles.IsGroupParent,false)) return null
        const ids = value(model,index,roles.WinIdList,[])
        if (!ids.length) return null
        return {
            key: "window:"+String(ids[0]), windowIds: Array.from(ids),
            title: String(value(model,index,Qt.DisplayRole,"")), icon: value(model,index,Qt.DecorationRole,""),
            appId: String(value(model,index,roles.AppId,"")), appName: String(value(model,index,roles.AppName,"")),
            launcherUrl: String(value(model,index,roles.LauncherUrlWithoutIcon,"")),
            pid: Number(value(model,index,roles.AppPid,0)),
            active: Boolean(value(model,index,roles.IsActive,false)),
            demandsAttention: Boolean(value(model,index,roles.IsDemandingAttention,false)),
            minimized: Boolean(value(model,index,roles.IsMinimized,false)),
            maximized: Boolean(value(model,index,roles.IsMaximized,false)),
            closable: Boolean(value(model,index,roles.IsClosable,false)),
            movable: Boolean(value(model,index,roles.IsMovable,false)),
            resizable: Boolean(value(model,index,roles.IsResizable,false)),
            minimizable: Boolean(value(model,index,roles.IsMinimizable,false)),
            maximizable: Boolean(value(model,index,roles.IsMaximizable,false)),
            fullScreenable: Boolean(value(model,index,roles.IsFullScreenable,false)),
            shadeable: Boolean(value(model,index,roles.IsShadeable,false)),
            canLaunchNewInstance: Boolean(value(model,index,roles.CanLaunchNewInstance,false)),
            keepAbove: Boolean(value(model,index,roles.IsKeepAbove,false)),
            keepBelow: Boolean(value(model,index,roles.IsKeepBelow,false)),
            fullScreen: Boolean(value(model,index,roles.IsFullScreen,false)),
            shaded: Boolean(value(model,index,roles.IsShaded,false)),
            desktopsChangeable: Boolean(value(model,index,roles.IsVirtualDesktopsChangeable,false)),
            desktopIds: Array.from(value(model,index,roles.VirtualDesktops,[])),
            onAllDesktops: Boolean(value(model,index,roles.IsOnAllVirtualDesktops,false)),
            activities: Array.from(value(model,index,roles.Activities,[])),
            geometry: value(model,index,roles.Geometry,Qt.rect(0,0,0,0)),
            screenGeometry: value(model,index,roles.ScreenGeometry,Qt.rect(0,0,0,0)),
            group: false, memberKeys: []
        }
    }
    function records(model,groups) {
        const result = []
        if (!model) return result
        const roles = TaskManager.AbstractTasksModel
        for (let row=0; row<model.count; ++row) {
            const index = model.makeModelIndex(row)
            if (groups && value(model,index,roles.IsGroupParent,false)) {
                const members = []
                for (let child=0; child<model.rowCount(index); ++child) {
                    const record = windowRecord(model,model.makeModelIndex(row,child))
                    if (record) members.push(record)
                }
                const appId = String(value(model,index,roles.AppId,""))
                const launcherUrl = String(value(model,index,roles.LauncherUrlWithoutIcon,""))
                const key = "group:"+(appId || launcherUrl || members.map(member=>member.key).sort().join("|"))
                result.push({key:key, title:String(value(model,index,Qt.DisplayRole,"")),
                    icon:value(model,index,Qt.DecorationRole,""), appId:appId, launcherUrl:launcherUrl,
                    group:true, memberKeys:members.map(member=>member.key), members:members})
            } else {
                const record = windowRecord(model,index)
                if (record) result.push(record)
            }
        }
        return result
    }
    function temporaryPinned(key,pid) {
        return temporaryWindowPins.some(pin=>pin.key===key && pin.pid===pid)
    }
    function copyTask(record) {
        const result={}
        for (const key of Object.keys(record)) result[key]=record[key]
        return result
    }
    function projectTaskRows(nativeRows,pins) {
        if (!pins.length) return nativeRows
        const pinned=[], remaining=[]
        const allWindows=nativeRows.reduce((all,task)=>all.concat(task.group ? task.members : [task]),[])
        const isPinned=window=>pins.some(pin=>pin.key===window.key && pin.pid===window.pid)
        for (const pin of pins) {
            const current=allWindows.find(window=>window.key===pin.key && window.pid===pin.pid)
            if (current) { const item=copyTask(current);item.temporaryPinned=true;pinned.push(item) }
        }
        for (const task of nativeRows) {
            if (!task.group) {
                if (!isPinned(task)) remaining.push(task)
                continue
            }
            const members=task.members.filter(window=>!isPinned(window))
            if (!members.length) continue
            if (members.length===1) { remaining.push(members[0]);continue }
            const group=copyTask(task)
            group.members=members;group.memberKeys=members.map(window=>window.key)
            remaining.push(group)
        }
        return pinned.concat(remaining)
    }
    function pinTemporaryWindows(recordsToPin) {
        if (!Array.isArray(recordsToPin) || !recordsToPin.length)
            return unavailable("temporaryPin","","Select a window to pin")
        // Validate the complete snapshot before changing its presentation.
        try {
            for (const record of recordsToPin) {
                const current=record && resolveWindow(record.key)
                if (!current || current.record.pid!==record.pid || !Number.isInteger(record.pid) || record.pid<=0)
                    return unavailable("temporaryPin",record ? record.key : "","The selected window identity changed")
            }
        } catch (error) { return unavailable("temporaryPin","","The window provider is unavailable") }
        const next=temporaryWindowPins.slice()
        for (const record of recordsToPin)
            if (!next.some(pin=>pin.key===record.key && pin.pid===record.pid))
                next.push({key:record.key,pid:record.pid})
        const changed=next.length!==temporaryWindowPins.length
        if (changed) { temporaryWindowPins=next;refresh() }
        return {state:changed ? "changed" : "already-satisfied",action:"temporaryPin",pinned:true}
    }
    function toggleTemporaryPin(record) {
        let current
        try { current=record && resolveWindow(record.key) }
        catch (error) { return unavailable("temporaryPin",record ? record.key : "","The window provider is unavailable") }
        if (!current || current.record.pid!==record.pid)
            return unavailable("temporaryPin",record ? record.key : "","The selected window identity changed")
        if (!temporaryPinned(record.key,record.pid)) return pinTemporaryWindows([record])
        temporaryWindowPins=temporaryWindowPins.filter(pin=>pin.key!==record.key || pin.pid!==record.pid)
        refresh()
        return {state:"changed",action:"temporaryUnpin",pinned:false,key:record.key}
    }
    function refresh() {
        if (refreshing) return
        refreshing = true
        try {
            // Read providers before publishing any new state. A model can
            // disappear or reject a read during teardown; retain the last
            // complete snapshot and its selection in that case.
            const nextWindows=records(scopeModel,false)
            let counted=0, unavailable=0
            if (scopeModel) for (let row=0; row<scopeModel.count; ++row) {
                const index=scopeModel.makeModelIndex(row)
                if (value(scopeModel,index,TaskManager.AbstractTasksModel.IsWindow,false)
                        && !value(scopeModel,index,TaskManager.AbstractTasksModel.IsGroupParent,false)) {
                    ++counted
                    if (!value(scopeModel,index,TaskManager.AbstractTasksModel.WinIdList,[]).length)
                        ++unavailable
                }
            }
            const nativeTasks=records(tasksModel,true)
            const aliveModel=identityModel || (!nativeEnabled ? scopeModel : null)
            const aliveWindows=temporaryWindowPins.length && aliveModel ? records(aliveModel,false) : null
            const nextPins=aliveWindows ? temporaryWindowPins.filter(pin=>
                aliveWindows.some(window=>window.key===pin.key && window.pid===pin.pid)) : temporaryWindowPins
            const nextTasks=projectTaskRows(nativeTasks,nextPins)
            const surviving=Selection.reconcile(selectedKeys,nextWindows).filter(key => {
                const current=nextWindows.find(window=>window.key===key)
                return selectedIdentities[key]===undefined || current.pid===selectedIdentities[key]
            })
            const nextIdentities={}
            for (const key of surviving)
                nextIdentities[key]=nextWindows.find(window=>window.key===key).pid
            const nextMemberKeys=memberSelectionKeys.filter(key=>surviving.indexOf(key)>=0)
            const nextAnchor=nextWindows.some(window=>window.key===anchorKey) ? anchorKey : ""
            const nextGroup=nextTasks.some(task=>task.key===groupSelectorKey) ? groupSelectorKey : ""

            windowRows=nextWindows
            identityUnavailableCount=unavailable
            scopedWindowCount=counted
            if (nextPins.length!==temporaryWindowPins.length) temporaryWindowPins=nextPins
            taskRows=nextTasks
            selectedIdentities=nextIdentities
            selectedKeys=surviving
            memberSelectionKeys=nextMemberKeys
            anchorKey=nextAnchor
            groupSelectorKey=nextGroup
            refreshFailureCount=0
        } catch (error) {
            ++refreshFailureCount
            // Emit once per failure episode. Provider errors may include
            // private window titles; neither the log nor this signal stores
            // their text. Wait for a new provider/user event instead of retrying.
            if (refreshFailureCount===1) {
                console.warn("DomainOS: task snapshot refresh failed; previous state retained")
                refreshFailed("task-model-unavailable")
            }
        } finally {
            refreshing=false
        }
    }
    function taskFor(key) { return taskRows.find(task=>task.key===key) || null }
    function windowFor(key) { return windowRows.find(window=>window.key===key) || null }
    function membersFor(key) {
        const task = taskFor(key)
        return task ? (task.group ? task.members : [task]) : []
    }
    function openMemberSelector(key) {
        if (!taskFor(key)) return false
        groupSelectorKey=key
        groupSelectionRequested(key,membersFor(key))
        return true
    }
    function selectionState(key) {
        const task = taskFor(key)
        return Selection.memberState(selectedKeys,task ? (task.group ? task.memberKeys : [key]) : [])
    }
    function memberIsSelected(key) {
        return memberSelectionKeys.indexOf(key)>=0
    }
    readonly property int pickerSelectionCount:groupMembers.filter(member=>memberIsSelected(member.key)).length
    function storeSelection(keys) {
        const identities={}
        for (const key of keys) {
            const window=windowFor(key)
            if (window) identities[key]=window.pid
        }
        selectedIdentities=identities
        selectedKeys=keys
        memberSelectionKeys=memberSelectionKeys.filter(key=>keys.indexOf(key)>=0)
    }
    function selectTask(key,modifiers) {
        const task = taskFor(key)
        if (!task) return false
        if (task.group) {
            return openMemberSelector(task.key)
        }
        // Continue keeps an explicit checkbox batch. Opening an individual
        // chooser must not replace it with an implicit single-click selection.
        if (memberSelectionActive && !(modifiers & (Qt.ControlModifier | Qt.ShiftModifier)))
            return openMemberSelector(task.key)
        const order = taskRows.filter(row=>!row.group).map(row=>row.key)
        const decision = Selection.click(selectedKeys,anchorKey,order,key,
                         Boolean(modifiers & Qt.ControlModifier),Boolean(modifiers & Qt.ShiftModifier))
        storeSelection(decision.keys)
        anchorKey = decision.anchor
        return true
    }
    function setMemberSelected(key,checked) {
        if (!windowFor(key)) return false
        // An ordinary single-task click is not a checkbox choice. Starting a
        // batch replaces that implicit selection, while retaining an explicit
        // multiple selection made with Ctrl/Shift.
        const previous=!memberSelectionActive && selectedKeys.length<2 ? [] : selectedKeys
        storeSelection(Selection.toggle(previous,key,checked))
        if (checked && memberSelectionKeys.indexOf(key)<0)
            memberSelectionKeys=memberSelectionKeys.concat([key])
        return true
    }
    function modifiersReleased(remainingModifiers,releasedKey) {
        let remaining=remainingModifiers || 0
        // QKeyEvent reports the modifier state before its own release.
        if (releasedKey===Qt.Key_Control) remaining &= ~Qt.ControlModifier
        if (releasedKey===Qt.Key_Shift) remaining &= ~Qt.ShiftModifier
        if (remaining & (Qt.ControlModifier | Qt.ShiftModifier)) return
        if (selectionCount < 2) return
        if (groupSelectorOpen) organizationPending = true
        else organizationRequested(selectedWindows())
    }
    function finishGroupSelection(openOperations) {
        groupSelectorKey = ""
        organizationPending = false
        if (openOperations && selectionCount >= 1) organizationRequested(selectedWindows())
    }
    function selectedWindows() { return windowRows.filter(window=>selectedKeys.indexOf(window.key)>=0) }
    function clearSelection() { storeSelection([]); anchorKey=""; organizationPending=false }
    function resolveWindow(key) {
        if (!scopeModel) return null
        for (let row=0; row<scopeModel.count; ++row) {
            const index = scopeModel.makeModelIndex(row)
            const record = windowRecord(scopeModel,index)
            if (record && record.key===key) {
                const expected=selectedIdentities[key]
                if (expected!==undefined && expected!==record.pid) return null
                return {model:scopeModel,index:index,record:record}
            }
        }
        return null
    }
    function unavailable(action,key,reason) {
        const result={state:"unavailable",action:action,key:key,reason:reason}
        operationUnavailable(result)
        return result
    }
    function activateTask(key) {
        const task=taskFor(key)
        if (task && task.group) { selectTask(key,0); return {state:"members-required",key:key} }
        return requestAction(key,"activate")
    }
    // Resolve the native model again by identity. A temporarily separated
    // window can remain a child in KDE's grouping model.
    function nativeTaskTarget(record) {
        if (!record || !tasksModel) return null
        if (record.group) {
            const row=taskRowForRecord(record)
            return row<0 ? null : {model:tasksModel,index:tasksModel.makeModelIndex(row),row:row,child:-1,record:record}
        }
        for (let row=0;row<tasksModel.count;++row) {
            const index=tasksModel.makeModelIndex(row)
            if (value(tasksModel,index,TaskManager.AbstractTasksModel.IsGroupParent,false)) {
                for (let child=0;child<tasksModel.rowCount(index);++child) {
                    const childIndex=tasksModel.makeModelIndex(row,child)
                    const current=windowRecord(tasksModel,childIndex)
                    if (current && current.key===record.key && current.pid===record.pid)
                        return {model:tasksModel,index:childIndex,row:row,child:child,record:current}
                }
            } else {
                const current=windowRecord(tasksModel,index)
                if (current && current.key===record.key && current.pid===record.pid)
                    return {model:tasksModel,index:index,row:row,child:-1,record:current}
            }
        }
        return null
    }
    // KDE maps a native group-parent launch/drop to its first child. That
    // child may now be pinned outside the projected group. Validate the full
    // captured projection first, then use its first remaining exact window.
    function nativeTaskActionTarget(record) {
        const target=nativeTaskTarget(record)
        if (!target) return null
        return record.group ? nativeTaskTarget(record.members[0]) : target
    }
    // Group membership is compared with the projected presentation, rather
    // than including windows explicitly pinned outside that group.
    function taskRowForRecord(record) {
        if (!record || !tasksModel) return -1
        const fresh=records(tasksModel,true)
        if (!record.group) {
            const target=nativeTaskTarget(record)
            return target ? target.row : -1
        }
        const projected=projectTaskRows(fresh,temporaryWindowPins)
        const matches=projected.some(task=>{
            if (task.key!==record.key || task.group!==record.group) return false
            if (!task.group) return task.pid===record.pid
            return Array.isArray(record.members) && task.members.length===record.members.length && task.members.every(member=>
                record.members.some(expected=>expected.key===member.key && expected.pid===member.pid))
        })
        return matches ? fresh.findIndex(task=>task.group && task.key===record.key) : -1
    }
    readonly property bool manualOrderAvailable: sortMode===TaskManager.TasksModel.SortManual
        && !!tasksModel && tasksModel.sortMode===TaskManager.TasksModel.SortManual && typeof tasksModel.move==="function"
    function moveTask(sourceRecord,targetRecord) {
        if (!manualOrderAvailable) return false
        const sourceTarget=nativeTaskTarget(sourceRecord),targetTarget=nativeTaskTarget(targetRecord)
        if (!sourceTarget || !targetTarget || sourceTarget.child>=0 || targetTarget.child>=0
                || temporaryPinned(sourceRecord.key,sourceRecord.pid) || temporaryPinned(targetRecord.key,targetRecord.pid)) return false
        const source=taskRowForRecord(sourceRecord), target=taskRowForRecord(targetRecord)
        if (source<0 || target<0 || source===target) return false
        const accepted=tasksModel.move(source,target)
        if (accepted) {
            queueRefresh()
            operationRequested({state:"requested",action:"reorder",key:sourceRecord.key,targetKey:targetRecord.key})
        }
        return accepted
    }
    function moveTaskByKeyboard(record,direction) {
        if (!manualOrderAvailable || (direction!==-1 && direction!==1)) return false
        const nativeTarget=nativeTaskTarget(record)
        if (!nativeTarget || nativeTarget.child>=0 || temporaryPinned(record.key,record.pid)) return false
        const row=taskRowForRecord(record), rows=records(tasksModel,true), target=row+direction
        return row>=0 && target>=0 && target<rows.length ? moveTask(record,rows[target]) : false
    }
    function openUrls(record,urls) {
        const target=nativeTaskActionTarget(record)
        if (!target || !Array.isArray(urls) || !urls.length || typeof tasksModel.requestOpenUrls!=="function")
            return unavailable("openUrls",record ? record.key : "","This task cannot accept dropped URLs")
        tasksModel.requestOpenUrls(target.index,urls)
        const result={state:"requested",action:"openUrls",key:record.key}
        operationRequested(result)
        return result
    }
    function requestGroupNewInstance(record) {
        const target=record && record.group ? nativeTaskActionTarget(record) : null
        if (!target) return unavailable("newInstance",record ? record.key : "","The group identity changed")
        // CanLaunchNewInstance controls visibility of the generic menu action.
        // KDE also clears it when a Desktop Entry already offers a New Window
        // action (for example VS Code). Its middle-click gesture still calls
        // requestNewInstance, using the current validated native task index.
        if (typeof tasksModel.requestNewInstance!=="function")
            return unavailable("newInstance",record.key,"This provider cannot launch an application instance")
        tasksModel.requestNewInstance(target.index)
        const result={state:"requested",action:"newInstance",key:record.key}
        operationRequested(result)
        return result
    }
    function requestAction(key,action,argument,expectedPid) {
        const target=resolveWindow(key)
        if (!target) return unavailable(action,key,"The selected window is no longer in this scope")
        const model=target.model, index=target.index, record=target.record
        if (expectedPid!==undefined && expectedPid!==record.pid)
            return unavailable(action,key,"The window now belongs to a different process")
        const methods={activate:"requestActivate",close:"requestClose",minimize:"requestToggleMinimized",
            restore:"requestToggleMinimized",maximize:"requestToggleMaximized",unmaximize:"requestToggleMaximized",
            move:"requestMove",resize:"requestResize",desktops:"requestVirtualDesktops",activities:"requestActivities",
            keepAbove:"requestToggleKeepAbove",keepBelow:"requestToggleKeepBelow",fullScreen:"requestToggleFullScreen",
            shade:"requestToggleShaded",newInstance:"requestNewInstance"}
        const required={close:"closable",minimize:"minimizable",restore:"minimizable",maximize:"maximizable",
            unmaximize:"maximizable",move:"movable",resize:"resizable",desktops:"desktopsChangeable",
            fullScreen:"fullScreenable",shade:"shadeable"}
        const method=methods[action]
        if (!method || typeof model[method]!=="function" || (required[action] && !record[required[action]]))
            return unavailable(action,key,"This window/provider does not support the requested action")
        if ((action==="minimize" && record.minimized) || (action==="restore" && !record.minimized)
                || (action==="maximize" && record.maximized) || (action==="unmaximize" && !record.maximized))
            return {state:"already-satisfied",action:action,key:key}
        if (action==="desktops" || action==="activities") model[method](index,argument)
        else model[method](index)
        const result={state:"requested",action:action,key:key}
        operationRequested(result)
        return result
    }
    function requestContextMenu(key) {
        const task=taskFor(key)
        if (!task) return false
        nativeContextMenuRequested({key:key,group:task.group,record:task,
            selectedWindows:selectedWindows(),model:tasksModel})
        return true
    }
    function requestTermination(key,expectedPid) {
        const target=resolveWindow(key)
        if (!target || target.record.pid<=0)
            return unavailable("terminate",key,"The window/process identity is not available")
        if (expectedPid!==undefined && expectedPid!==target.record.pid)
            return unavailable("terminate",key,"The window now belongs to a different process")
        if (!processBackend || typeof processBackend.requestTerminate!=="function")
            return unavailable("terminate",key,"Process termination backend is not available in this session")
        const affected=records(scopeModel,false).filter(window=>window.pid===target.record.pid)
        if (affected.some(window=>window.key!==key && selectedKeys.indexOf(window.key)<0))
            return unavailable("terminate",key,"The process also owns an unselected window")
        // The helper must verify identity again and check windows outside this
        // filtered scope. A process request is never equivalent to native Close.
        const payload={window:target.record,knownProcessWindows:affected,
            selectedKeys:selectedKeys.slice(),desktopId:currentDesktopId}
        const reply=processBackend.requestTerminate(payload)
        if (!reply || ["unavailable","failed","rejected"].indexOf(reply.state)>=0)
            return unavailable("terminate",key,reply && reply.reason ? reply.reason : "Process provider rejected the request")
        const result={state:"requested",action:"terminate",key:key}
        operationRequested(result)
        return result
    }
    function requestBatch(action) {
        return requestTargets(action,selectedWindows())
    }
    function requestTargets(action,windows) {
        if (windows.length < 2) return unavailable(action,"","Select at least two windows")
        if (["columns","rows","mosaic","collect","maximize","minimize"].indexOf(action)<0)
            return unavailable(action,"","Unknown organization command")
        if (!geometryBackend || typeof geometryBackend.requestLayout!=="function")
            return unavailable(action,"","Window geometry backend is not available in this session")
        if (currentDesktopId===null || currentAvailableGeometry.width<=0 || currentAvailableGeometry.height<=0)
            return unavailable(action,"","The current desktop/monitor is not known")
        const freshWindows=[]
        for (const window of windows) {
            const target=resolveWindow(window.key)
            if (!target || target.record.pid!==window.pid)
                return unavailable(action,window.key,"The selected window identity changed")
            const capability=action==="maximize" ? "maximizable" : action==="minimize" ? "minimizable" : "movable"
            if (!target.record[capability] || (["columns","rows","mosaic"].indexOf(action)>=0 && !target.record.resizable))
                return unavailable(action,window.key,"A selected window cannot be moved/resized")
            freshWindows.push(target.record)
        }
        const payload={mode:action,windows:freshWindows,desktopId:currentDesktopId,
            screenName:currentScreenName,screenGeometry:currentScreenGeometry,
            availableGeometry:currentAvailableGeometry}
        const reply=geometryBackend.requestLayout(payload)
        if (reply===false || (reply && ["unavailable","failed","rejected"].indexOf(reply.state)>=0))
            return unavailable(action,"",reply && reply.reason ? reply.reason : "Window geometry provider rejected the request")
        const result={state:"requested",action:action,targets:windows.map(window=>window.key)}
        operationRequested(result)
        return result
    }
}
