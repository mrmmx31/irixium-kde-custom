// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Window
import org.kde.taskmanager as TaskManager
import "../applets/org.irixclassic.domainos.panel/contents/ui" as DomainOS

Window {
    id: host
    width: 1000
    height: 650
    visible: true
    color: "#607f91"
    property alias controller: tasks
    property var windows: []
    property int screen: 0
    property var requests: []
    property var layouts: []
    property var terminations: []
    property int organizationRequests: 0
    property int contextRequests: 0
    property bool legacyInterface:true
    function appendRequest(request) { requests=requests.concat([request]) }
    function seed() {
        const result=[]
        for (let index=1; index<=9; ++index) result.push({ids:[index],pid:500+index,title:"Window "+index,
            appId:index<=3 ? "terminal" : index<=5 ? "browser" : "app"+index, launcher:"applications:app"+index+".desktop",
            desktops:index===9 ? [2] : [1],activities:["activity"],screen:index===8 ? 1 : 0,
            minimized:index===2 || index===5,maximized:false,active:index===1,
            closable:true,movable:true,resizable:true,minimizable:true,maximizable:true,
            desktopsChangeable:true,canLaunchNewInstance:true,x:index*10,y:index*20})
        windows=result
    }
    function mutate(id,field,value) {
        const copy=JSON.parse(JSON.stringify(windows))
        const window=copy.find(window=>window.ids[0]===id)
        if (window) window[field]=value
        windows=copy
    }
    function removeWindow(id) { windows=windows.filter(window=>window.ids[0]!==id) }
    function addWindow(id,appId) {
        const row=JSON.parse(JSON.stringify(windows.find(window=>window.desktops.indexOf(tasks.currentDesktopId)>=0)))
        row.ids=[id]; row.pid=500+id; row.title="Window "+id; row.appId=appId; row.minimized=false
        windows=windows.concat([row])
    }
    function reverseWindows() { windows=windows.slice().reverse() }
    function state() { return JSON.stringify({windowCount:tasks.windowCount,rows:tasks.taskRows,
        selected:tasks.selectedKeys,group:tasks.groupSelectorKey,members:tasks.groupMembers,
        filter:tasks.effectiveMinimizedOnly,thresholdRequired:tasks.automaticThresholdRequired,
        requests:requests,layouts:layouts,terminations:terminations,
        identitiesUnavailable:tasks.identityUnavailableCount,
        organizationRequests:organizationRequests,contextRequests:contextRequests}) }
    function act(key,action,argument) { return JSON.stringify(tasks.requestAction(key,action,argument)) }
    function actExpected(key,action,pid) { return JSON.stringify(tasks.requestAction(key,action,undefined,pid)) }
    function terminate(key) { return JSON.stringify(tasks.requestTermination(key)) }
    function batch(action) { return JSON.stringify(tasks.requestBatch(action)) }
    function finishGroup(openOperations) { tasks.finishGroupSelection(openOperations) }
    function addGeometryBackend() { tasks.geometryBackend=geometry }
    function addProcessBackend() { tasks.processBackend=process }
    function releaseModifiers(modifiers) { tasks.modifiersReleased(modifiers) }
    DomainOSFixtureTasks { id: scoped; host:host }
    DomainOSFixtureTasks {
        id: viewed
        host:host
        grouped:tasks.groupingMode===TaskManager.TasksModel.GroupApplications
        minimizedOnly:tasks.effectiveMinimizedOnly
    }
    QtObject {
        id: geometry
        function requestLayout(payload) { host.layouts=host.layouts.concat([payload]); return {state:"requested"} }
    }
    QtObject {
        id: process
        function requestTerminate(payload) { host.terminations=host.terminations.concat([payload]); return {state:"requested"} }
    }
    DomainOS.DomainOSTasks {
        id: tasks
        nativeEnabled:false
        tasksModel:viewed
        scopeModel:scoped
        currentDesktopId:1
        currentActivityId:"activity"
        currentScreenGeometry:Qt.rect(0,0,1200,900)
        currentAvailableGeometry:Qt.rect(0,0,1200,850)
        onlyGroupWhenFull:false
        onOrganizationRequested:host.organizationRequests++
        onNativeContextMenuRequested:host.contextRequests++
    }
    Item {
        anchors.fill:parent
        visible:host.legacyInterface
        focus:true
        Keys.onReleased: event => {
            if (event.key===Qt.Key_Control || event.key===Qt.Key_Shift) tasks.modifiersReleased(event.modifiers,event.key)
        }
        Repeater {
            model:tasks.taskRows
            delegate: Rectangle {
                required property var modelData
                required property int index
                objectName:"task:"+modelData.key
                x:20+index*140;y:20;width:130;height:70
                color:tasks.selectedKeys.length>=0 && tasks.selectionState(modelData.key).selected ? "#3297c7" : "#7894a7"
                Text { anchors.centerIn:parent;text:parent.modelData.title;color:"white" }
                MouseArea {
                    anchors.fill:parent
                    acceptedButtons:Qt.LeftButton|Qt.RightButton
                    onClicked: mouse => {
                        if (mouse.button===Qt.RightButton) tasks.requestContextMenu(parent.modelData.key)
                        else tasks.selectTask(parent.modelData.key,mouse.modifiers)
                    }
                    onDoubleClicked:tasks.activateTask(parent.modelData.key)
                }
            }
        }
        Rectangle {
            x:20;y:120;width:500;height:360
            visible:tasks.groupSelectorOpen
            color:"#7894a7"
            Repeater {
                model:tasks.groupMembers
                delegate: Rectangle {
                    required property var modelData
                    required property int index
                    objectName:"member:"+modelData.key
                    x:20;y:20+index*44;width:460;height:36
                    color:tasks.selectedKeys.indexOf(modelData.key)>=0 ? "#3297c7" : "#607f91"
                    Text { anchors.centerIn:parent;text:(tasks.selectedKeys.indexOf(parent.modelData.key)>=0 ? "[x] " : "[ ] ")+parent.modelData.title;color:"white" }
                    MouseArea { anchors.fill:parent;onClicked:tasks.setMemberSelected(parent.modelData.key,tasks.selectedKeys.indexOf(parent.modelData.key)<0) }
                }
            }
        }
    }
    Component.onCompleted:seed()
}
