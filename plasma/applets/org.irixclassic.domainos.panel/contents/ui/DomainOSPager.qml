// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import org.kde.plasma.private.pager 2.0 as NativePager
import org.kde.taskmanager as TaskManager
import org.kde.plasma.workspace.dbus as DBus
import org.kde.config as KConfig

Item {
    id: pager
    objectName: "domainosRealPager"
    implicitWidth: 342
    implicitHeight: 150
    property QtObject colorPalette: null
    DomainOSPalette { id: fallbackPalette }
    DomainOSPopupPlacement { id: menuPlacement }
    readonly property QtObject domainosPalette: colorPalette || fallbackPalette
    property rect screenGeometry: Qt.rect(0, 0, 0, 0)
    property bool showOnlyCurrentScreen: false
    property bool wheelActivatesDesktop: false
    property int firstVisible: 0
    property string lastError: ""
    property bool mutationPending: false
    property bool activationPending: false
    property var activationQueue: []
    readonly property int pendingActivations: activationQueue.length + (activationPending ? 1 : 0)
    property var desktopRecords: []
    property string currentDesktopId: ""
    readonly property int desktopCount: desktopRecords.length
    readonly property bool available: service.registered && desktopCount > 0 && desktopCount === nativeModel.count
    readonly property bool canManageDesktops: available && !mutationPending && KConfig.KAuthorized.authorize("kcm_kwin_virtualdesktops")
    readonly property bool navigationVisible: desktopCount > 2
    readonly property int visibleSlots: Math.min(2, desktopCount)
    readonly property real cardWidth: visibleSlots === 1 ? width - 16 : (width - 26) / 2
    readonly property real cardHeight: height - 24 - (navigationVisible ? 28 : 0)
    readonly property QtObject pagerBackend: nativeModel
    property real wheelRemainder: 0
    property int readSequence: 0
    property int appliedSequence: 0
    property var pendingReplies: []
    property string menuDesktopId: ""
    property string editingDesktopId: ""
    property bool creatingDesktop: false
    signal operationStarted(string operation)
    signal operationFinished(string operation, bool success, string details)
    signal failure(string message)

    function unbox(value) {
        return value !== null && typeof value === "object" && value.value !== undefined ? value.value : value
    }
    function fail(message) {
        lastError = message
        failure(message)
    }
    function recordById(id) {
        return desktopRecords.find(record => record.id === id) || null
    }
    function recordAt(position) {
        return desktopRecords.find(record => record.position === position) || null
    }
    function matchingWindow(model,identity) {
        if (!model || !identity || !Array.isArray(identity.windowIds) || !identity.windowIds.length
                || !Number.isInteger(identity.pid) || identity.pid<=0) return null
        const expected=identity.windowIds.map(id=>typeof id+":"+String(id)).sort()
        for (let row=0;row<model.rowCount();++row) {
            const index=model.index(row,0), roles=TaskManager.AbstractTasksModel
            if (!model.data(index,roles.IsWindow) || model.data(index,roles.IsGroupParent)
                    || Number(model.data(index,roles.AppPid))!==identity.pid) continue
            const ids=Array.from(model.data(index,roles.WinIdList) || [])
            if (ids.length!==expected.length) continue
            const current=ids.map(id=>typeof id+":"+String(id)).sort()
            if (current.every((id,position)=>id===expected[position])) return {model:model,index:index}
        }
        return null
    }
    function activateWindow(desktopId,identity) {
        const desktop=available ? recordById(desktopId) : null
        const scope=desktop ? nativeModel.data(nativeModel.index(desktop.position,0),NativePager.PagerModel.TasksModel) : null
        // Both identities must still exist together. Model indexes and card
        // positions can change while the pointer is held; neither is a target.
        if (!scope || !matchingWindow(scope,identity)) {
            fail(qsTr("Essa janela não está mais disponível nesta área de trabalho."))
            return false
        }
        const target=matchingWindow(windowActivationModel,identity)
        if (!target || typeof target.model.requestActivate!=="function") {
            fail(qsTr("O provedor nativo não permite ativar esta janela."))
            return false
        }
        lastError=""
        operationStarted("activate-pager-window")
        target.model.requestActivate(target.index)
        // TaskManager's method is void: report the request, not a fabricated
        // focus confirmation. KWin remains the authority for focus/restoration.
        operationFinished("activate-pager-window",true,qsTr("Ativação da janela solicitada ao KWin."))
        return true
    }
    function callRemote(iface, member, args, callback) {
        if (!service.registered) {
            callback(null, qsTr("O gerenciador de áreas de trabalho está indisponível."))
            return
        }
        const reply = DBus.SessionBus.asyncCall({
            service: "org.kde.KWin", path: "/VirtualDesktopManager",
            iface: iface, member: member, arguments: args
        })
        pendingReplies = pendingReplies.concat([reply])
        const finish = function() {
            // A D-Bus watcher can finish after its applet was removed or the
            // shell restarted. Its reply no longer has a receiving component.
            if (!pager) return
            // Void replies have no value. Keep the native watcher alive until
            // its finished signal has unwound, without delaying the operation.
            callback(reply.isError || member !== "GetAll" ? null : reply.value,
                     reply.isError ? reply.error.message : "")
            Qt.callLater(function() {
                if (pager) pendingReplies = pendingReplies.filter(item => item !== reply)
            })
        }
        if (reply.isFinished) finish()
        else reply.finished.connect(finish)
    }
    function readState(callback) {
        const sequence = ++readSequence
        callRemote("org.freedesktop.DBus.Properties", "GetAll", ["org.kde.KWin.VirtualDesktopManager"], function(value, error) {
            if (!pager) return
            if (error) {
                if (sequence >= appliedSequence) fail(error)
                if (callback) callback(null, error)
                return
            }
            const rows = value && value.desktops
            let records = []
            if (rows && rows.length !== undefined) {
                for (let index = 0; index < rows.length; ++index) {
                    const row = rows[index]
                    records.push({position:Number(unbox(row[0])), id:String(unbox(row[1])), name:String(unbox(row[2]))})
                }
                records.sort((a,b) => a.position - b.position)
            }
            const current = value ? String(unbox(value.current)) : ""
            const valid = records.length > 0 && records.every((record,index) =>
                record.position === index && record.id.length > 0)
                && new Set(records.map(record => record.id)).size === records.length
                && records.some(record => record.id === current)
            if (!valid) {
                const message = qsTr("O gerenciador não forneceu identidades válidas para as áreas de trabalho.")
                if (sequence >= appliedSequence) fail(message)
                if (callback) callback(null,message)
                return
            }
            const state = {records:records, current:current}
            if (sequence >= appliedSequence) {
                appliedSequence = sequence
                desktopRecords = records
                currentDesktopId = current
                firstVisible = Math.max(0, Math.min(firstVisible, Math.max(0,records.length - Math.min(2,records.length))))
            }
            if (callback) callback(state, "")
        })
    }
    function activateDesktop(id) {
        if (!available || !recordById(id)) {
            fail(qsTr("Essa área de trabalho não está mais disponível."))
            return false
        }
        if (id === currentDesktopId && !pendingActivations) return true
        lastError = ""
        activationQueue = activationQueue.concat([id])
        operationStarted("activate-desktop")
        runNextActivation()
        return true
    }
    function runNextActivation() {
        if (activationPending || !activationQueue.length) return
        const id = activationQueue[0]
        activationQueue = activationQueue.slice(1)
        if (!available || !recordById(id)) {
            const error = qsTr("Essa área de trabalho não está mais disponível.")
            fail(error)
            operationFinished("activate-desktop", false, error)
            runNextActivation()
            return
        }
        // Observe each native result before the next request. Rapidly returning
        // to the old area must not be discarded while currentDesktopId catches
        // up. There is no timer, animation wait, or optimistic selection here.
        activationPending = true
        callRemote("org.freedesktop.DBus.Properties", "Set", [
            "org.kde.KWin.VirtualDesktopManager", "current", new DBus.variant(id)
        ], function(value,error) {
            if (error) {
                activationPending = false
                fail(error); operationFinished("activate-desktop",false,error)
                runNextActivation()
                return
            }
            readState(function(state,readError) {
                activationPending = false
                const success = !!state && state.current === id
                const details = success ? "" : readError || qsTr("A troca de área de trabalho não foi confirmada.")
                if (!success) fail(details)
                operationFinished("activate-desktop",success,details)
                runNextActivation()
            })
        })
    }
    function mutate(operation, member, args, verify) {
        if (!canManageDesktops) {
            fail(qsTr("Não é possível alterar as áreas de trabalho neste momento."))
            return false
        }
        lastError = ""
        mutationPending = true
        operationStarted(operation)
        callRemote("org.kde.KWin.VirtualDesktopManager",member,args,function(value,error) {
            if (error) {
                mutationPending = false
                fail(error); operationFinished(operation,false,error)
                return
            }
            readState(function(state,readError) {
                mutationPending = false
                const success = !!state && verify(state)
                const details = success ? "" : readError || qsTr("A alteração da área de trabalho não foi confirmada.")
                if (!success) fail(details)
                operationFinished(operation,success,details)
            })
        })
        return true
    }
    function createDesktop(name) {
        const title = name.trim()
        if (!title) { fail(qsTr("Informe um nome para a área de trabalho.")); return false }
        const previous = desktopRecords.map(record => record.id)
        return mutate("create-desktop","createDesktop",[new DBus.uint32(desktopCount),title],state =>
            state.records.length === previous.length + 1 && previous.every(id => state.records.some(record => record.id === id))
            && state.records.some(record => previous.indexOf(record.id) < 0 && record.name === title))
    }
    function renameDesktop(id,name) {
        const title = name.trim()
        if (!recordById(id) || !title) { fail(qsTr("Informe uma área existente e um nome válido.")); return false }
        return mutate("rename-desktop","setDesktopName",[id,title],state =>
            state.records.some(record => record.id === id && record.name === title))
    }
    function removeDesktop(id) {
        if (desktopCount <= 1) { fail(qsTr("É necessário manter ao menos uma área de trabalho.")); return false }
        if (!recordById(id)) { fail(qsTr("Essa área de trabalho não está mais disponível.")); return false }
        const previous = desktopRecords.map(record => record.id)
        return mutate("remove-desktop","removeDesktop",[id],state =>
            state.records.length === previous.length - 1 && !state.records.some(record => record.id === id)
            && state.records.every(record => previous.indexOf(record.id) >= 0))
    }
    function navigate(direction) {
        if (!available || desktopCount <= 2) return
        firstVisible = Math.max(0, Math.min(firstVisible + direction * 2, desktopCount - 2))
    }
    function wheelStep(direction) {
        if (!available) return
        if (wheelActivatesDesktop) {
            const current = recordById(currentDesktopId)
            if (!current) return
            const target = recordAt(Math.max(0,Math.min(current.position + direction,desktopCount - 1)))
            if (target) {
                firstVisible = Math.max(0,Math.min(target.position,Math.max(0,desktopCount - 2)))
                activateDesktop(target.id)
            }
        } else if (desktopCount > 2) {
            firstVisible = Math.max(0, Math.min(firstVisible + direction, desktopCount - 2))
        }
    }
    function wheelEvent(angle) {
        if (typeof angle !== "number" || !Number.isFinite(angle) || angle === 0) return
        const previous = Number.isFinite(wheelRemainder) ? wheelRemainder : 0
        const total = previous + angle
        if (!Number.isFinite(total)) return
        const steps = Math.trunc(total / 120)
        wheelRemainder = total % 120
        if (!steps || !available) return
        // One event chooses its final target. Replaying every detent can block
        // the QML loop or enqueue repeated D-Bus requests while KWin catches up.
        const distance = Math.min(Math.abs(steps), desktopCount)
        wheelStep((steps > 0 ? -1 : 1) * distance)
    }
    function openNameDialog(id) {
        editingDesktopId = id
        creatingDesktop = id.length === 0
        const record = recordById(id)
        nameInput.text = record ? record.name : ""
        nameDialog.open()
        nameInput.forceActiveFocus()
    }
    function openContextMenu(x,y) {
        const position = desktopCount === 1 ? 0 : firstVisible + Math.max(0,Math.min(1,Math.floor((x - 8)/(cardWidth + 10))))
        const record = recordAt(position)
        menuDesktopId = record ? record.id : ""
        menuPlacement.showMenu(contextMenu, pager, Qt.point(x,y))
    }

    DBus.DBusServiceWatcher {
        id: service
        busType: DBus.BusType.Session
        watchedService: "org.kde.KWin"
        onRegisteredChanged: {
            if (registered) pager.readState()
            else { pager.desktopRecords=[]; pager.currentDesktopId="" }
        }
    }
    TaskManager.VirtualDesktopInfo { id: desktopInfo }
    TaskManager.TasksModel {
        id: windowActivationModel
        launcherList: []
        groupMode: TaskManager.TasksModel.GroupDisabled
        filterByVirtualDesktop:false; filterByActivity:false; filterByScreen:false
    }
    NativePager.PagerModel {
        id: nativeModel
        enabled: pager.visible && service.registered
        pagerType: NativePager.PagerModel.VirtualDesktops
        showDesktop: false
        showOnlyCurrentScreen: pager.showOnlyCurrentScreen
        screenGeometry: pager.screenGeometry
        onCountChanged: if (service.registered) pager.readState()
        onCurrentPageChanged: if (service.registered) pager.readState()
    }
    Connections {
        target: desktopInfo
        function onDesktopIdsChanged() { if (service.registered) pager.readState() }
        function onDesktopNamesChanged() { if (service.registered) pager.readState() }
    }
    Component.onCompleted: if (service.registered) readState()
    Bevel {
        anchors.fill: parent
        simpleRelief: true
        light: pager.domainosPalette.pale; dark: pager.domainosPalette.dark
        texture: Qt.resolvedUrl("../images/metal-weave.svg")
    }
    Repeater {
        model: nativeModel
        delegate: DomainOSDesktopTile {
            required property int index
            required property var model
            readonly property var desktopRecord: pager.recordAt(index)
            objectName: "domainosDesktopTile_" + index
            desktopId: desktopRecord ? desktopRecord.id : ""
            desktopName: desktopRecord ? desktopRecord.name : ""
            windowModel: model.TasksModel
            virtualSize: nativeModel.pagerItemSize
            selected: desktopId.length > 0 && desktopId === pager.currentDesktopId
            visible: pager.available && index >= pager.firstVisible && index < pager.firstVisible + pager.visibleSlots
            enabled: pager.available && desktopId.length > 0
            x: 8 + (index - pager.firstVisible) * (pager.cardWidth + 10)
            y: 12; width: pager.cardWidth; height: pager.cardHeight
            onActivated: id => pager.activateDesktop(id)
            onWindowActivated: (id,identity) => pager.activateWindow(id,identity)
        }
    }
    Text {
        anchors.centerIn: parent
        visible: !pager.available
        text: qsTr("Áreas indisponíveis")
        color: pager.domainosPalette.text
        font.family: "Nimbus Sans"; font.pixelSize: 16
        textFormat: Text.PlainText; renderType: Text.NativeRendering
    }
    Row {
        visible: pager.navigationVisible && pager.available
        x: 8; y: pager.height - 34
        spacing: 10
        PanelButton {
            objectName: "domainosDesktopPrevious"
            width: pager.cardWidth; height: 22
            label: qsTr("Áreas anteriores")
            enabled: pager.firstVisible > 0
            opacity: enabled ? 1 : 0.45
            imageSource: Qt.resolvedUrl("../images/arrow-left.svg")
            imageWidth: 18; imageHeight: 18
            onClicked: pager.navigate(-1)
        }
        PanelButton {
            objectName: "domainosDesktopNext"
            width: pager.cardWidth; height: 22
            label: qsTr("Áreas seguintes")
            enabled: pager.firstVisible < pager.desktopCount - 2
            opacity: enabled ? 1 : 0.45
            imageSource: Qt.resolvedUrl("../images/arrow-right.svg")
            imageWidth: 18; imageHeight: 18
            onClicked: pager.navigate(1)
        }
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        z: 100
        onClicked: mouse => pager.openContextMenu(mouse.x,mouse.y)
        onWheel: wheel => {
            pager.wheelEvent(wheel.angleDelta.y || wheel.angleDelta.x)
            wheel.accepted = true
        }
    }
    Controls.Menu {
        id: contextMenu
        objectName:"domainosDesktopContextMenu"
        popupType:Controls.Popup.Window
        enter:null; exit:null
        Controls.MenuItem { text: qsTr("Criar área de trabalho…"); enabled: pager.canManageDesktops; onTriggered: pager.openNameDialog("") }
        Controls.MenuItem { text: qsTr("Renomear área de trabalho…"); enabled: pager.canManageDesktops && pager.menuDesktopId.length > 0; onTriggered: pager.openNameDialog(pager.menuDesktopId) }
        Controls.MenuItem { text: qsTr("Remover área de trabalho…"); enabled: pager.canManageDesktops && pager.desktopCount > 1 && pager.menuDesktopId.length > 0; onTriggered: removeDialog.open() }
    }
    DomainOSPopupPlacement {
        popup:nameDialog
        popupAnchor:pager.Window.window ? pager.Window.window.contentItem : pager
        centerOnAnchor:true
    }
    DomainOSPopupPlacement {
        popup:removeDialog
        popupAnchor:pager.Window.window ? pager.Window.window.contentItem : pager
        centerOnAnchor:true
    }
    Controls.Dialog {
        id: nameDialog
        objectName:"domainosDesktopNameDialog"
        popupType:Controls.Popup.Window
        focus:true
        enter:null; exit:null
        width: 360
        modal: true
        title: pager.creatingDesktop ? qsTr("Criar área de trabalho") : qsTr("Renomear área de trabalho")
        standardButtons: Controls.Dialog.Ok | Controls.Dialog.Cancel
        footer: DomainOSDialogButtonBox {}
        contentItem: DomainOSTextField { id: nameInput; objectName: "domainosDesktopNameInput"; placeholderText: qsTr("Nome"); selectByMouse: true }
        onAccepted: {
            if (pager.creatingDesktop) pager.createDesktop(nameInput.text)
            else pager.renameDesktop(pager.editingDesktopId,nameInput.text)
        }
    }
    Controls.Dialog {
        id: removeDialog
        objectName:"domainosDesktopRemoveDialog"
        popupType:Controls.Popup.Window
        focus:true
        enter:null; exit:null
        width: 420
        modal: true
        title: qsTr("Remover área de trabalho")
        standardButtons: Controls.Dialog.Ok | Controls.Dialog.Cancel
        footer: DomainOSDialogButtonBox {}
        contentItem: Controls.Label { text: qsTr("Remover esta área? As janelas continuarão abertas.") }
        onAccepted: pager.removeDesktop(pager.menuDesktopId)
    }
}
