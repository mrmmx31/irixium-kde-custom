// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Item {
    id: taskbox
    objectName:"domainosLiveIconbox"
    implicitWidth:594;implicitHeight:150
    property var controller:null
    property QtObject colorPalette:null
    property var hostItem:null
    property bool nativeMenusEnabled:true
    property var pinnedApplications:[]
    property var groupDialog:null
    property int middleClickAction:2
    property bool wheelEnabled:true
    property bool wheelSkipMinimized:true
    property bool iconboxWheelActivates:false
    property bool interactiveMute:true
    property bool highlightWindows:false
    property real wheelRotation:0
    property string wheelAnchorKey:""
    property bool thumbnailsEnabled:false
    property bool hintsEnabled:true
    property int firstVisible:0
    readonly property int visibleCapacity:7
    readonly property QtObject domainosPalette:colorPalette || fallbackPalette
    // Expose the drawing scale for existing preview diagnostics. Popup
    // placement itself maps global coordinates instead of dividing by it.
    readonly property real popupAnchorScale: {
        let ancestor=taskbox, factor=1
        while (ancestor) { factor*=ancestor.scale;ancestor=ancestor.parent }
        return Math.max(0.01,factor)
    }
    readonly property var rows:controller ? controller.taskRows : []
    readonly property int pageCount:Math.ceil(rows.length/visibleCapacity)
    readonly property bool canPrevious:firstVisible>0
    readonly property bool canNext:firstVisible+visibleCapacity<rows.length
    readonly property bool groupPopupVisible:groupPicker.visible
    readonly property bool operationsMenuVisible:operationsMenu.visible
    property var groupAnchor:null
    property var menuTarget:null
    property var menuSelection:[]
    property var pendingOperations:[]
    property int operationsGeneration:0
    property int openingOperationsGeneration:0
    property var waitingOperationsPopups:[]
    property bool closingOperationsPopups:false
    property bool presentingOperations:false
    property bool modifierSelectionArmed:false
    property string lastError:""
    property int operationsOpened:0
    readonly property var nativeMenuBridge:nativeLayer.item
    property alias basicContextMenu:basicMenu
    property alias batchContextMenu:operationsMenu
    DomainOSPalette { id:fallbackPalette }
    DomainOSModifierKeys {
        onReleased: (remainingModifiers,key) => taskbox.selectionModifiersReleased(remainingModifiers,key)
    }
    // Plasma's panel focus frame reads logical bounds without our drawing
    // scale. Keep keyboard event propagation to taskbox using a receiver
    // without artwork, rather than giving that frame the scaled Iconbox.
    Item {
        id: keyboardFocus
        objectName: "domainosIconboxKeyboardFocus"
        width: 0; height: 0
        activeFocusOnTab: false
    }
    DomainOSPopupPlacement { id:menuPlacement }
    // A mapped Popup.Window keeps one native parent for its entire lifetime.
    // Its position is independent from the tile used to open this chooser.
    DomainOSPopupPlacement { id:groupPlacement;popup:groupPicker;popupAnchor:taskbox;positionAnchor:taskbox }
    DomainOSPopupToggle { id:groupToggle;anchor:taskbox.groupAnchor;showing:groupPicker.visible }
    ListModel { id:groupMemberModel }
    signal failure(string message)
    signal pinRequested(string desktopId)
    signal unpinRequested(string desktopId)
    signal groupingPreferencesRequested(var appIds,var launcherUrls)
    signal operationStarted(string operation)
    signal operationFinished(string operation,bool success,string details)
    Accessible.role:Accessible.Grouping
    Accessible.name:qsTr("Iconbox; %1 janelas").arg(controller ? controller.windowCount : 0)
    Accessible.description:controller && controller.effectiveMinimizedOnly ? qsTr("Filtro de apresentação: apenas minimizadas") : qsTr("Janelas abertas e minimizadas")

    onVisibleChanged: if (!visible) windowHighlight.clear()

    function fail(message) { lastError=message;failure(message) }
    function checkTarget(record) {
        if (!controller || !record) return false
        if (record.group) return !!controller.taskFor(record.key)
        const target=controller.resolveWindow(record.key)
        return !!target && target.record.pid===record.pid
    }
    function navigate(direction) {
        cancelPendingOperations()
        const next=Math.max(0,Math.min(firstVisible+direction*visibleCapacity,
            Math.max(0,(pageCount-1)*visibleCapacity)))
        if (next===firstVisible) return
        // Tiles are reused on the next page. Dismiss the chooser belonging to
        // the old record before that same launcher receives a different one.
        groupPicker.close()
        if (controller) controller.finishGroupSelection(false)
        groupToggle.cancelPress()
        groupToggle.lastAnchor=null
        groupAnchor=null
        firstVisible=next
    }
    function selectRecord(record,modifiers,anchor) {
        cancelPendingOperations()
        if (!checkTarget(record)) { fail(qsTr("Essa janela não está mais disponível."));return false }
        hideThumbnails()
        const plainClick=!(modifiers & (Qt.ControlModifier | Qt.ShiftModifier))
        if (!plainClick && groupPicker.visible) groupPicker.close()
        if (plainClick && !groupToggle.shouldOpen(anchor || buttonForKey(record.key))) {
            modifierSelectionArmed=false
            groupPicker.close()
            controller.finishGroupSelection(false)
            return true
        }
        modifierSelectionArmed=!plainClick
        keyboardFocus.forceActiveFocus(Qt.MouseFocusReason)
        groupAnchor=anchor
        const selected=controller.selectTask(record.key,modifiers)
        if (selected && plainClick && !record.group) controller.openMemberSelector(record.key)
        return selected
    }
    function activateRecord(record) {
        if (!checkTarget(record)) { fail(qsTr("Essa janela não está mais disponível."));return false }
        if (record.group) return selectRecord(record,0,buttonForKey(record.key))
        return handleResult(controller.requestAction(record.key,"activate",undefined,record.pid))
    }
    function doubleClickRecord(record) {
        modifierSelectionArmed=false
        cancelPendingOperations()
        if (!checkTarget(record)) { fail(qsTr("Essa janela não está mais disponível."));return false }
        if (record.group) {
            hideThumbnails()
            groupAnchor=buttonForKey(record.key)
            // A double click is still an explicit request to choose a member,
            // even when the first click already opened this same selector.
            return controller.selectTask(record.key,0)
        }
        const current=controller.resolveWindow(record.key).record
        groupPicker.close()
        // Opening the member popup can take native focus after the first click.
        // The actual Qt double-click gesture captures that first click's state;
        // never reinterpret popup focus as an inactive application.
        const wasActive=record.doubleClickActive===undefined ? current.active : record.doubleClickActive
        return actionFor(record,wasActive && !current.minimized ? "minimize" : "activate")
    }
    function memberTitleClicked(record) {
        if (!checkTarget(record)) { fail(qsTr("Essa janela não está mais disponível."));return false }
        if (controller.memberSelectionActive)
            return controller.setMemberSelected(record.key,controller.selectedKeys.indexOf(record.key)<0)
        if (!activateRecord(record)) return false
        groupPicker.close()
        return true
    }
    function syncGroupMembers() {
        // Check the source key rather than its derived boolean: on close,
        // groupMembersChanged can arrive before groupSelectorOpenChanged.
        if (!controller || controller.groupSelectorKey.length===0) return
        const members=controller.groupMembers
        for (let index=0;index<members.length;++index) {
            const member=members[index]
            let found=-1
            for (let row=index;row<groupMemberModel.count;++row) {
                const current=groupMemberModel.get(row)
                if (current.windowKey===member.key && current.windowPid===member.pid) { found=row;break }
            }
            if (found<0) groupMemberModel.insert(index,{windowKey:member.key,windowPid:member.pid})
            else if (found!==index) groupMemberModel.move(found,index,1)
        }
        if (groupMemberModel.count>members.length)
            groupMemberModel.remove(members.length,groupMemberModel.count-members.length)
    }
    function hideThumbnails() {
        for (let index=0;index<taskButtons.count;++index) {
            const button=taskButtons.itemAt(index)
            if (button) button.windowPreview.hideImmediately()
        }
    }
    function handleResult(result) {
        if (!result || ["unavailable","failed","rejected"].indexOf(result.state)>=0) {
            fail(result && result.reason ? result.reason : qsTr("A operação está indisponível."));return false
        }
        // Native void requests are not reported as observed success.
        return true
    }
    function actionFor(record,action,argument) {
        if (!checkTarget(record) || record.group) { fail(qsTr("Escolha uma janela individual."));return false }
        return handleResult(controller.requestAction(record.key,action,argument,record.pid))
    }
    function selectedSnapshot() { return controller ? controller.selectedWindows().slice() : [] }
    function geometryReady(windows,action) {
        const mode=action || "columns"
        return !!controller && !!controller.geometryBackend && controller.geometryBackend.available!==false
            && typeof controller.geometryBackend.requestLayout==="function" && windows.length>=2
            && windows.every(window=>checkTarget(window)
                && (mode==="maximize" ? window.maximizable : mode==="minimize" ? window.minimizable : window.movable)
                && (["columns","rows","mosaic"].indexOf(mode)<0 || window.resizable))
    }
    function processReady(record) {
        return !!controller && !!record && !record.group && checkTarget(record) && record.pid>0
            && !!controller.processBackend && controller.processBackend.available!==false
            && typeof controller.processBackend.requestTerminate==="function"
            && !controller.windowRows.some(window=>window.pid===record.pid && window.key!==record.key
                && controller.selectedKeys.indexOf(window.key)<0)
    }
    function batch(action,windows) {
        const snapshot=windows || menuSelection
        if (snapshot.length<2) { fail(qsTr("Selecione ao menos duas janelas."));return false }
        return handleResult(controller.requestTargets(action,snapshot))
    }
    function cancelPendingOperations() {
        ++operationsGeneration
        pendingOperations=[]
        waitingOperationsPopups=[]
        openingOperationsGeneration=0
    }
    function operationsPopupClosed(popup) {
        waitingOperationsPopups=waitingOperationsPopups.filter(candidate=>candidate!==popup)
        showPendingOperations(operationsGeneration)
    }
    function openOperations(windows) {
        modifierSelectionArmed=false
        hideThumbnails()
        const snapshot=windows.slice()
        if (!snapshot.length || !snapshot.every(checkTarget)) {
            fail(qsTr("A seleção mudou antes de abrir as operações."));return false
        }
        const generation=++operationsGeneration
        pendingOperations=snapshot
        // Capture waiters BEFORE close(): closed can be emitted synchronously.
        // An asynchronous close retains the snapshot until its actual signal.
        waitingOperationsPopups=[groupPicker,basicMenu,operationsMenu]
            .filter(popup=>popup.visible || popup.opened)
        closingOperationsPopups=true
        try {
            groupPicker.close()
            basicMenu.close()
            operationsMenu.close()
            if (nativeLayer.item) nativeLayer.item.close()
        } catch (error) {
            cancelPendingOperations()
            fail(qsTr("Não foi possível fechar o menu anterior para abrir as operações."))
            return false
        } finally {
            closingOperationsPopups=false
        }
        return showPendingOperations(generation)
    }
    function showPendingOperations(generation) {
        if (generation!==operationsGeneration || !pendingOperations.length) return false
        if (closingOperationsPopups || presentingOperations || waitingOperationsPopups.length
                || groupPicker.visible || basicMenu.visible || operationsMenu.visible)
            return true // accepted and retained; the corresponding closed signal drains it.
        const snapshot=pendingOperations.slice()
        if (!snapshot.every(checkTarget)) {
            pendingOperations=[]
            fail(qsTr("A seleção mudou antes de abrir as operações."));return false
        }
        presentingOperations=true
        try {
            menuSelection=snapshot
            openingOperationsGeneration=generation
            // The stable owner and all natural row sizes are checked BEFORE
            // open; there is no cursor placement or deferred layout callback.
            if (!operationsMenu.openAt(taskbox)) {
                pendingOperations=[]
                openingOperationsGeneration=0
                return false
            }
            if (generation===operationsGeneration) pendingOperations=[]
            return true
        } catch (error) {
            pendingOperations=[]
            openingOperationsGeneration=0
            operationsMenu.close()
            fail(qsTr("Não foi possível abrir o menu de operações."))
            return false
        } finally {
            presentingOperations=false
        }
    }
    function pinSelectedWindows() {
        if (!controller || !menuSelection.length || !menuSelection.every(checkTarget)) return false
        // Preserve checkbox choice order when several windows are fixed in one
        // operation, without changing the existing layout order of batch jobs.
        const ordered=controller.selectedKeys.map(key=>menuSelection.find(window=>window.key===key)).filter(Boolean)
        for (const window of menuSelection)
            if (!ordered.some(current=>current.key===window.key)) ordered.push(window)
        const result=controller.pinTemporaryWindows(ordered)
        if (result && result.pinned && result.state==="changed") firstVisible=0
        return handleResult(result)
    }
    function toggleTemporaryPin(record) {
        if (!controller || !record || record.group || !checkTarget(record)) return false
        const result=controller.toggleTemporaryPin(record)
        if (result && result.pinned && result.state==="changed") firstVisible=0
        return handleResult(result)
    }
    function openContext(record,anchor,options) {
        if (!checkTarget(record)) { fail(qsTr("Essa janela não está mais disponível."));return false }
        hideThumbnails()
        cancelPendingOperations()
        groupPicker.close();operationsMenu.close();basicMenu.close()
        menuTarget=record;menuSelection=selectedSnapshot()
        if (nativeLayer.item && nativeLayer.item.open(record,anchor,options || {})) return true
        return openFallbackContext(record)
    }
    function openFallbackContext(record) {
        if (!checkTarget(record)) return false
        menuTarget=record;menuSelection=selectedSnapshot()
        // The fallback has the same stable parent as the operations menu.
        menuPlacement.showMenu(basicMenu,taskbox)
        return true
    }
    function middleAction(record) {
        if (!checkTarget(record)) return
        if (middleClickAction===0) return
        if (record.group && [1,3,5].indexOf(middleClickAction)>=0) {
            selectRecord(record,0,buttonForKey(record.key))
            return
        }
        if (middleClickAction===1) actionFor(record,"close")
        else if (middleClickAction===2) {
            if (record.group) handleResult(controller.requestGroupNewInstance(record))
            else actionFor(record,"newInstance")
        }
        else if (middleClickAction===3) actionFor(record,record.minimized ? "restore" : "minimize")
        else if (middleClickAction===4 && nativeLayer.item) nativeLayer.item.toggleGrouping(record)
        else if (middleClickAction===5) actionFor(record,"desktops",[controller.currentDesktopId])
    }
    function reorderAt(sourceRecord,position) {
        if (!controller || !controller.manualOrderAvailable) return false
        for (let index=0;index<taskButtons.count;++index) {
            const button=taskButtons.itemAt(index)
            if (button && position.x>=button.x && position.x<button.x+button.width
                    && position.y>=button.y && position.y<button.y+button.height)
                return controller.moveTask(sourceRecord,button.record)
        }
        return false
    }
    function wheelStep(direction,anchor,steps=1) {
        if (!wheelEnabled || !controller) return
        const rows=anchor && anchor.group ? controller.membersFor(anchor.key)
            : controller.taskRows.reduce((all,task)=>all.concat(task.group ? task.members : [task]),[])
        const windows=rows.filter(window=>!wheelSkipMinimized || !window.minimized)
        if (!windows.length) return
        const active=windows.findIndex(window=>window.active)
        const offset=direction*(steps%windows.length)
        const next=active<0 ? 0 : (active+offset+windows.length)%windows.length
        activateRecord(windows[next])
    }
    function wheelEvent(angle,anchor) {
        if (!wheelEnabled || !controller || !Number.isFinite(angle)) return
        const key=anchor && anchor.group ? anchor.key : ""
        if (key!==wheelAnchorKey) { wheelAnchorKey=key;wheelRotation=0 }
        const total=(Number.isFinite(wheelRotation) ? wheelRotation : 0)+angle/8
        const steps=Math.trunc(total/15)
        wheelRotation=total%15
        if (!steps) return
        const direction=steps>0 ? -1 : 1
        // One event makes at most one native request. Repeated subtraction
        // can stop progressing for very large finite floating-point values.
        if (iconboxWheelActivates) wheelStep(direction,anchor,Math.abs(steps))
        else navigate(direction*Math.min(Math.abs(steps),Math.max(0,pageCount-1)))
    }
    function publishGeometries() {
        if (nativeLayer.item) for (let index=0;index<taskButtons.count;++index)
            nativeLayer.item.publishGeometry(taskButtons.itemAt(index))
    }
    onXChanged:Qt.callLater(publishGeometries)
    onYChanged:Qt.callLater(publishGeometries)
    onWidthChanged:Qt.callLater(publishGeometries)
    onHeightChanged:Qt.callLater(publishGeometries)
    onScaleChanged:Qt.callLater(publishGeometries)
    function refreshAudioStreams() {
        if (nativeLayer.item) for (let index=0;index<taskButtons.count;++index)
            nativeLayer.item.updateStreams(taskButtons.itemAt(index))
    }
    function buttonForKey(key) {
        for (let index=0;index<taskButtons.count;++index) {
            const button=taskButtons.itemAt(index)
            if (button && button.record.key===key) return button
        }
        return null
    }
    onRowsChanged:firstVisible=Math.max(0,Math.min(firstVisible,Math.max(0,(pageCount-1)*visibleCapacity)))
    function selectionModifiersReleased(remainingModifiers,releasedKey) {
        if (!modifierSelectionArmed || !controller) return
        let remaining=remainingModifiers || 0
        if (releasedKey===Qt.Key_Control) remaining &= ~Qt.ControlModifier
        if (releasedKey===Qt.Key_Shift) remaining &= ~Qt.ShiftModifier
        if (remaining & (Qt.ControlModifier | Qt.ShiftModifier)) return
        // Coalesce the native observer and a focused Qt key event. Releasing
        // modifiers later in an unrelated application never reopens a menu.
        modifierSelectionArmed=false
        controller.modifiersReleased(remaining,releasedKey)
    }
    Keys.onReleased: event => {
        if (event.key===Qt.Key_Control || event.key===Qt.Key_Shift)
            selectionModifiersReleased(event.modifiers,event.key)
    }
    Keys.onEscapePressed: {
        modifierSelectionArmed=false
        cancelPendingOperations()
        groupPicker.close();operationsMenu.close();basicMenu.close()
    }
    Connections {
        target:taskbox.controller
        ignoreUnknownSignals:true
        function onGroupSelectionRequested(key,members) {
            // Model changes can destroy the former delegate parent. A native
            // Popup.Window requires a live parent before open(), not only in
            // aboutToShow, which Qt may never deliver for an orphaned popup.
            windowHighlight.clear()
            taskbox.syncGroupMembers()
            groupMembersColumn.forceLayout()
            groupContent.forceLayout()
            groupPicker.prepareNaturalHeight()
            groupPlacement.positionPopup()
            groupPicker.open()
        }
        function onOrganizationRequested(windows) { taskbox.openOperations(windows) }
        function onGroupSelectorOpenChanged() { if (!taskbox.controller.groupSelectorOpen) groupPicker.close() }
        function onGroupMembersChanged() {
            taskbox.syncGroupMembers()
            if (groupPicker.visible && Math.abs(groupPicker.height-groupPicker.preferredHeight)>.5)
                groupPicker.prepareNaturalHeight()
        }
    }
    DomainOSWindowHighlight {
        id: windowHighlight
        enabled: taskbox.highlightWindows
        backend: nativeLayer.item
    }
    Connections {
        target: taskbox.controller
        ignoreUnknownSignals: true
        function onWindowRowsChanged() { windowHighlight.validate() }
    }
    Loader {
        id:nativeLayer
        active:taskbox.nativeMenusEnabled && !!taskbox.controller && taskbox.controller.nativeEnabled && !!taskbox.hostItem
        sourceComponent:DomainOSNativeTaskMenu { iconbox:taskbox;controller:taskbox.controller }
    }
    Bevel {
        objectName:"domainosIconboxFrame"
        anchors.fill:parent
        simpleRelief:true;light:taskbox.domainosPalette.pale;dark:taskbox.domainosPalette.dark
        texture:Qt.resolvedUrl("../images/metal-weave.svg")
    }
    Bevel {
        objectName:"domainosIconboxWell"
        x:12;y:18;width:570;height:114;sunken:true;face:taskbox.domainosPalette.recessed
    }
    Text {
        objectName:"domainosIconboxFilterStatus"
        x:60;y:4;width:476;height:14
        visible:!!taskbox.controller && taskbox.controller.effectiveMinimizedOnly
        text:taskbox.controller && taskbox.controller.filterMode==="automatic" ? qsTr("Apenas minimizadas — filtro automático") : qsTr("Apenas minimizadas")
        color:taskbox.domainosPalette.text;font.family:"Nimbus Sans";font.pixelSize:12
        horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight;renderType:Text.NativeRendering
    }
    PanelButton {
        objectName:"domainosIconboxPrevious"
        x:12;y:26;width:44;height:98
        enabled:taskbox.canPrevious
        label:qsTr("Página anterior de ícones")
        imageSource:Qt.resolvedUrl("../images/arrow-left.svg");imageWidth:32
        onClicked:taskbox.navigate(-1)
        opacity:enabled ? 1 : 0.55
    }
    Repeater {
        id:taskButtons
        model:Math.min(taskbox.visibleCapacity,Math.max(0,taskbox.rows.length-taskbox.firstVisible))
        delegate:DomainOSTaskButton {
            id:task
            required property int index
            x:60+index*68;y:26;width:66;height:98
            objectName:"domainosLiveTask_"+record.key
            record:taskbox.rows[taskbox.firstVisible+index]
            property alias windowPreview:taskPreview
            property var hoverRecordSnapshot:null
            onRecordChanged: {
                if (hoverRecordSnapshot && (hoverRecordSnapshot.key!==record.key || hoverRecordSnapshot.pid!==record.pid)) {
                    windowHighlight.leave(hoverRecordSnapshot)
                    hoverRecordSnapshot=null
                    if (taskHover.hovered && !groupPicker.visible) {
                        hoverRecordSnapshot=record
                        windowHighlight.enter(record)
                    }
                }
                if (nativeLayer.item) nativeLayer.item.updateStreams(task)
            }
            DomainOSWindowThumbnails {
                id:taskPreview
                objectName:"domainosTaskThumbnails_"+task.record.key
                anchors.fill:parent
                previewsEnabled:taskbox.thumbnailsEnabled && !groupPicker.visible
                // A group caption omits its members' titles even when the
                // application name fits; its ordered list remains useful.
                hintsEnabled:taskbox.hintsEnabled && !groupPicker.visible
                    && (task.record.group || task.labelTruncated)
                controller:taskbox.controller
                record:task.record
                colorPalette:taskbox.domainosPalette
                onActivationRequested:record=>taskbox.activateRecord(record)
            }
            HoverHandler {
                id: taskHover
                enabled: taskbox.highlightWindows
                onHoveredChanged: {
                    if (hovered && !groupPicker.visible) {
                        task.hoverRecordSnapshot=task.record
                        windowHighlight.enter(task.hoverRecordSnapshot)
                    } else {
                        windowHighlight.leave(task.hoverRecordSnapshot)
                        task.hoverRecordSnapshot=null
                    }
                }
            }
            Component.onDestruction: if (hoverRecordSnapshot) windowHighlight.leave(hoverRecordSnapshot)
            reorderEnabled:taskbox.controller ? Boolean(taskbox.controller.manualOrderAvailable) : false
            colorPalette:taskbox.domainosPalette
            selected:taskbox.controller.selectionState(record.key).selected
            partiallySelected:taskbox.controller.selectionState(record.key).partial
            selectedMembers:taskbox.controller.selectionState(record.key).count
            onSelectedByPointer:(record,modifiers)=>taskbox.selectRecord(record,modifiers,task)
            onActivatedByPointer:record=>taskbox.doubleClickRecord(record)
            onContextByPointer:(record,anchor,options)=>taskbox.openContext(record,anchor,options)
            onMiddleByPointer:record=>taskbox.middleAction(record)
            onAudioNavigationRequested:(record,direction)=>{ if (nativeLayer.item) nativeLayer.item.audioNavigation(record,direction) }
            interactiveMute:taskbox.interactiveMute
            smartLauncherItem:nativeLayer.item ? nativeLayer.item.smartLauncherFor(record.key) : null
            onWheelRequested:(angle,record)=>taskbox.wheelEvent(angle,record)
            onKeyboardReorderRequested:(record,direction)=>taskbox.controller.moveTaskByKeyboard(record,direction)
            onGeometryPublicationRequested:Qt.callLater(taskbox.publishGeometries)
            onUrlsDropped:(record,urls)=>{
                if (nativeLayer.item) nativeLayer.item.handleDrop(record,urls)
                else taskbox.handleResult(taskbox.controller.openUrls(record,urls))
            }
            onReorderedByPointer:(record,position)=>taskbox.reorderAt(record,position)
            Component.onCompleted:if (nativeLayer.item) nativeLayer.item.updateStreams(task)
        }
    }
    PanelButton {
        objectName:"domainosIconboxNext"
        x:538;y:26;width:44;height:98
        enabled:taskbox.canNext
        label:qsTr("Próxima página de ícones")
        imageSource:Qt.resolvedUrl("../images/arrow-right.svg");imageWidth:32
        onClicked:taskbox.navigate(1)
        opacity:enabled ? 1 : 0.55
    }
    MouseArea {
        anchors.fill:parent;z:-1
        acceptedButtons:Qt.NoButton
        onWheel:wheel=>taskbox.wheelEvent(wheel.angleDelta.y,null)
    }
    Controls.Popup {
        id:groupPicker
        objectName:"domainosGroupPicker"
        popupType:Controls.Popup.Window
        enter:null;exit:null
        property var hintOwner:null
        // Retain closed content geometry. Collapsing it to zero during close
        // can queue a stale native-window resize that clips the next opening.
        readonly property int memberCount:groupMemberModel.count
        readonly property real rowHeight:36
        readonly property real maximumHeight:Math.max(1,(taskbox.groupAnchor || taskbox).Screen.height-8
            -Math.max(0,-topInset)-Math.max(0,-bottomInset))
        readonly property real chromeHeight:topPadding+bottomPadding+groupHeader.implicitHeight
            +groupFooter.implicitHeight+groupContent.spacing*2
        readonly property real listHeight:Math.max(0,Math.min(memberCount*rowHeight,15*rowHeight,
            maximumHeight-chromeHeight))
        readonly property real preferredHeight:Math.min(maximumHeight,chromeHeight+listHeight)
        function prepareNaturalHeight() {
            // A native resize marks Qt's internal popup item height explicit,
            // even when our size comes from implicitHeight. Setting then
            // resetting this public property makes Qt reset that item now;
            // otherwise open() can still observe the former group's height.
            height=preferredHeight
            height=undefined
        }
        width:Math.max(1,Math.min(400,(taskbox.groupAnchor || taskbox).Screen.width-8
            -Math.max(0,-leftInset)-Math.max(0,-rightInset)))
        // Qt 6.8's Popup.Window height setter resizes the native window first;
        // its popup item can still have the last opening's size until a resize
        // event arrives. Keep the popup item's natural size synchronous with
        // this model snapshot, without breaking it with explicit assignments.
        implicitHeight:preferredHeight
        padding:10
        // The opener is the popup parent. Let its press reach the toggle before
        // dismissing, while clicks outside both still close the chooser.
        // Tooltip input first reaches this native popup. While its own preview
        // is under the pointer, let that input reach the card instead of closing
        // the parent and destroying the target before it receives the press.
        closePolicy:Controls.Popup.CloseOnEscape
            | (hintOwner && hintOwner.previewHovered ? Controls.Popup.NoAutoClose
                : Controls.Popup.CloseOnPressOutsideParent)
        onAboutToHide:{
            hintOwner=null
            // Dismissing the selector ends its modifier gesture. Preserve the
            // chosen windows, but a later release must not reopen Operations.
            taskbox.modifierSelectionArmed=false
        }
        onClosed:{
            hintOwner=null;windowHighlight.clear()
            if (taskbox.controller && taskbox.controller.groupSelectorOpen)
                taskbox.controller.finishGroupSelection(false)
            taskbox.operationsPopupClosed(groupPicker)
        }
        background:Bevel { paletteOverride:taskbox.domainosPalette;face:taskbox.domainosPalette.background;light:taskbox.domainosPalette.highlight;dark:taskbox.domainosPalette.dark;texture:Qt.resolvedUrl("../images/metal-weave.svg") }
        contentItem:Column {
            id:groupContent
            spacing:4
            HoverHandler {
                id:selectorHover
                objectName:"domainosGroupSelectorHover"
                parent:groupContent.Window.window ? groupContent.Window.window.contentItem : groupContent
                blocking:false
                onPointChanged:if (hovered && groupPicker.hintOwner)
                    groupPicker.hintOwner.observePointer(parent.mapToGlobal(point.position))
                onHoveredChanged:if (!hovered) Qt.callLater(()=>{
                    const owner=groupPicker.hintOwner
                    // A forwarded move first leaves this popup, then enters
                    // its preview. Decide after that same event has completed.
                    if (owner && !owner.hovered && !owner.previewHovered)
                        owner.hideImmediately()
                })
            }
            Keys.onReleased:event=>{ if (event.key===Qt.Key_Control || event.key===Qt.Key_Shift) taskbox.selectionModifiersReleased(event.modifiers,event.key) }
            Text {
                id:groupHeader;objectName:"domainosGroupHeader"
                width:parent.width;color:taskbox.domainosPalette.text
                text:taskbox.controller ? qsTr("%1 — %2 de %3 selecionadas").arg(taskbox.controller.taskFor(taskbox.controller.groupSelectorKey)?.title || "")
                    .arg(taskbox.controller.pickerSelectionCount).arg(taskbox.controller.groupMembers.length) : ""
                elide:Text.ElideRight;renderType:Text.NativeRendering
            }
            Controls.ScrollView {
                id:groupList;objectName:"domainosGroupScrollView"
                width:parent.width
                height:groupPicker.listHeight
                contentWidth:availableWidth
                contentHeight:groupPicker.memberCount*groupPicker.rowHeight
                clip:true
                Controls.ScrollBar.horizontal:DomainOSViewScrollBar {
                    scrollView:groupList
                    objectName:"domainosGroupHorizontalScrollBar"
                    colorPalette:taskbox.domainosPalette
                    policy:Controls.ScrollBar.AlwaysOff
                }
                Controls.ScrollBar.vertical:DomainOSViewScrollBar {
                    scrollView:groupList
                    objectName:"domainosGroupVerticalScrollBar"
                    colorPalette:taskbox.domainosPalette
                    policy:groupList.contentHeight>groupList.availableHeight
                        ? Controls.ScrollBar.AlwaysOn : Controls.ScrollBar.AlwaysOff
                }
                Connections {
                    target:groupList.contentItem
                    ignoreUnknownSignals:true
                    function onContentYChanged() {
                        if (groupPicker.hintOwner) groupPicker.hintOwner.hideImmediately()
                    }
                }
                Column {
                    id:groupMembersColumn;objectName:"domainosGroupMembersColumn"
                    width:groupList.availableWidth
                    Repeater {
                        model:groupMemberModel
                        delegate:Row {
                            required property string windowKey
                            required property int windowPid
                            readonly property var modelData:taskbox.controller.windowFor(windowKey)
                                || {key:windowKey,pid:windowPid,title:"",windowIds:[],group:false}
                            id:memberRow
                            width:groupMembersColumn.width;height:groupPicker.rowHeight
                            DomainOSCheckBox {
                                objectName:"domainosGroupMember_"+memberRow.modelData.key
                                property var frozenRecord:null
                                property bool wasSelected:false
                                width:36;height:36
                                Accessible.name:qsTr("Selecionar %1").arg(memberRow.modelData.title)
                                checked:taskbox.controller.memberIsSelected(memberRow.modelData.key)
                                onPressed:{ frozenRecord=memberRow.modelData;wasSelected=checked }
                                onClicked:if (taskbox.checkTarget(frozenRecord))
                                    taskbox.controller.setMemberSelected(frozenRecord.key,!wasSelected)
                            }
                            Controls.ItemDelegate {
                                id:memberTitle
                                objectName:"domainosGroupMemberTitle_"+memberRow.modelData.key
                                property var frozenRecord:null
                                width:memberRow.width-36;height:36
                                text:memberRow.modelData.title
                                // The desktop ItemDelegate otherwise opens its
                                // own tooltip for truncated text, competing
                                // with the single native Plasma hint below.
                                Controls.ToolTip.visible:false
                                Accessible.description:taskbox.controller.memberSelectionActive
                                    ? qsTr("Marcar ou desmarcar esta janela") : qsTr("Restaurar e ativar esta janela")
                                contentItem:Text {
                                    id: memberCaption
                                    text:memberTitle.text;textFormat:Text.PlainText;elide:Text.ElideRight
                                    color:taskbox.domainosPalette.text;verticalAlignment:Text.AlignVCenter
                                    renderType:Text.NativeRendering
                                }
                                onPressed:frozenRecord=memberRow.modelData
                                onClicked:taskbox.memberTitleClicked(frozenRecord)
                                DomainOSGroupMemberHint {
                                    objectName:"domainosGroupMemberHint_"+memberRow.modelData.key
                                    anchors.fill:parent
                                    previewsEnabled:taskbox.thumbnailsEnabled
                                    hintsEnabled:taskbox.hintsEnabled
                                    titleTruncated:memberCaption.truncated
                                    ownerRegistry:groupPicker
                                    controller:taskbox.controller
                                    record:memberRow.modelData
                                    colorPalette:taskbox.domainosPalette
                                    onHoveredChanged: {
                                        if (hovered) windowHighlight.enter(memberRow.modelData)
                                        else windowHighlight.leave(memberRow.modelData)
                                    }
                                    Component.onDestruction: windowHighlight.leave(memberRow.modelData)
                                    onActivationRequested:record=>{ if (taskbox.activateRecord(record)) groupPicker.close() }
                                }
                            }
                        }
                    }
                }
            }
            Row {
                id:groupFooter;objectName:"domainosGroupFooter"
                spacing:8
                DomainOSButton { objectName:"domainosGroupContinue";text:qsTr("Continuar seleção");onClicked:groupPicker.close() }
                DomainOSButton {
                    objectName:"domainosGroupOrganize";text:qsTr("Operações…")
                    enabled:taskbox.controller && taskbox.controller.selectionCount>=1
                    onClicked:{ taskbox.controller.finishGroupSelection(true);groupPicker.close() }
                }
            }
        }
    }
    DomainOSOperationsMenu {
        id:operationsMenu
        iconbox:taskbox
        onFailure:message=>taskbox.fail(message)
        onPinRequested:taskbox.pinSelectedWindows()
        onCommandRequested:command=>taskbox.batch(command)
        onOpened:{
            if (taskbox.openingOperationsGeneration!==taskbox.operationsGeneration) {
                close();return
            }
            ++taskbox.operationsOpened
        }
        onClosed:taskbox.operationsPopupClosed(operationsMenu)
    }
    Controls.Menu {
        id:basicMenu
        onClosed:taskbox.operationsPopupClosed(basicMenu)
        objectName:"domainosBasicTaskContext"
        popupType:Controls.Popup.Window
        enter:null;exit:null
        Controls.MenuItem {
            objectName:"domainosTemporaryUnpin"
            text:qsTr("Desafixar esta janela")
            visible:!!taskbox.menuTarget && !taskbox.menuTarget.group && !!taskbox.controller
                && taskbox.controller.temporaryPinned(taskbox.menuTarget.key,taskbox.menuTarget.pid)
            enabled:visible && taskbox.checkTarget(taskbox.menuTarget)
            onTriggered:taskbox.toggleTemporaryPin(taskbox.menuTarget)
        }
        Controls.MenuItem { text:qsTr("Restaurar e ativar");enabled:!!taskbox.menuTarget;onTriggered:taskbox.activateRecord(taskbox.menuTarget) }
        Controls.MenuItem { text:qsTr("Nova janela");enabled:taskbox.menuTarget && !taskbox.menuTarget.group && taskbox.menuTarget.canLaunchNewInstance;onTriggered:taskbox.actionFor(taskbox.menuTarget,"newInstance") }
        Controls.MenuItem { text:qsTr("Maximizar");enabled:taskbox.menuTarget && !taskbox.menuTarget.group && taskbox.menuTarget.maximizable;onTriggered:taskbox.actionFor(taskbox.menuTarget,"maximize") }
        Controls.MenuItem { text:qsTr("Minimizar");enabled:taskbox.menuTarget && !taskbox.menuTarget.group && taskbox.menuTarget.minimizable;onTriggered:taskbox.actionFor(taskbox.menuTarget,"minimize") }
        Controls.MenuItem { text:qsTr("Operações das selecionadas…");enabled:taskbox.menuSelection.length>=1;onTriggered:taskbox.openOperations(taskbox.menuSelection) }
        Controls.Menu {
            title:qsTr("Processo")
            popupType:Controls.Popup.Window
            enter:null;exit:null
            Controls.MenuItem { objectName:"domainosBasicTerminate";text:qsTr("Encerrar à força");enabled:taskbox.processReady(taskbox.menuTarget);onTriggered:taskbox.handleResult(taskbox.controller.requestTermination(taskbox.menuTarget.key,taskbox.menuTarget.pid)) }
        }
        Controls.MenuSeparator {}
        Controls.MenuItem { objectName:"domainosBasicClose";text:qsTr("Fechar");enabled:taskbox.menuTarget && !taskbox.menuTarget.group && taskbox.menuTarget.closable;onTriggered:taskbox.actionFor(taskbox.menuTarget,"close") }
    }
}
