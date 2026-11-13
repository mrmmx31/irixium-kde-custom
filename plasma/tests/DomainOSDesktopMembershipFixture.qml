// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.taskmanager as TaskManager
import org.kde.plasma.extras as PlasmaExtras
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id:host
    preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        id:fixture;objectName:"domainosDesktopMembershipFixture"
        Layout.minimumWidth:594;Layout.minimumHeight:150
        Layout.preferredWidth:594;Layout.preferredHeight:150
        property var requests:[]
        property var activityReports:[]
        readonly property var tasks:runtime.tasks
        property var frozen:null
        function group() { return tasks.taskRows.find(row=>row.group) }
        function nativeAttention() {
            let rows=[]
            if(tasks.scopeModel)for(let i=0;i<tasks.scopeModel.count;++i) {
                const index=tasks.scopeModel.makeModelIndex(i),record=tasks.windowRecord(tasks.scopeModel,index)
                if(record)rows.push({key:record.key,title:record.title,demandingAttention:tasks.value(tasks.scopeModel,index,TaskManager.AbstractTasksModel.IsDemandingAttention,false)})
            }
            return rows
        }
        function state() {
            const bridge=box.nativeMenuBridge
            return JSON.stringify({rows:tasks.taskRows,windows:tasks.windowRows.filter(row=>row.title.startsWith("DomainOS desktop membership ")),
                attention:nativeAttention(),requests:requests,activity:{sequence:runtime.activity.sequence,pendingCount:runtime.activity.pendingCount,lit:runtime.activity.lit,tailLit:runtime.activity.tailLit,reports:activityReports,lastReport:runtime.activity.lastReport},desktops:desktops.desktopIds,names:desktops.desktopNames,currentDesktop:desktops.currentDesktop,
                count:desktops.numberOfDesktops,group:group(),modelGrouping:tasks.tasksModel ? tasks.tasksModel.groupMode : -1,groupingBlacklist:tasks.tasksModel ? tasks.tasksModel.groupingAppIdBlacklist : [],groupingThreshold:tasks.tasksModel ? tasks.tasksModel.groupingWindowTasksThreshold : -999,groupableRows:tasks.tasksModel ? tasks.records(tasks.tasksModel,false).map(row=>({key:row.key,groupable:tasks.value(tasks.tasksModel,tasks.tasksModel.makeModelIndex(tasks.taskRowForRecord(row)),TaskManager.AbstractTasksModel.IsGroupable,false)})) : [],lastError:box.lastError,menuOpen:!!bridge && !!bridge.openedMenu && bridge.openedMenu.status===PlasmaExtras.Menu.Open,menuStatus:bridge && bridge.openedMenu ? bridge.openedMenu.status : -1,
                menuTarget:bridge ? bridge.targetRecord : null,nativeContextMenu:bridge ? String(bridge.contextMenuUrl) : ""})
        }
        function openCurrent() {
            const record=group()
            return !!record && box.openContext(record,box.buttonForKey(record.key),{})
        }
        function enableGrouping() { runtime.settings=Object.assign({},runtime.settings,{tasksGroupingMode:TaskManager.TasksModel.GroupApplications,tasksOnlyGroupWhenFull:false});return true }
        function bridge() { return box.nativeMenuBridge }
        Panel.DomainOSPalette { id:colors;followSystem:false }
        Panel.DomainOSRuntime {
            id:runtime;hostItem:host;colorPalette:colors
            screenGeometry:Qt.rect(0,0,1200,700);availableGeometry:screenGeometry
            // This private test selects a short tail; it is not a product default
            // or a duration approved for the user's profile.
            settings:({tasksOnlyCurrentDesktop:false,tasksOnlyCurrentActivity:false,tasksOnlyCurrentScreen:false,
                tasksGroupingMode:0,tasksOnlyGroupWhenFull:true,tasksSortMode:1,
                keepActivityLight:true,activityLightMilliseconds:1500})
        }
        Connections {
            target:runtime.tasks
            function onOperationRequested(request) { fixture.requests=fixture.requests.concat([request]) }
        }
        Connections {
            target:runtime.activity
            function onReported(report) { fixture.activityReports=fixture.activityReports.concat([report]) }
        }
        TaskManager.VirtualDesktopInfo { id:desktops }
        Panel.DomainOSIconbox { id:box;anchors.fill:parent;controller:tasks;colorPalette:colors;hostItem:host;nativeMenusEnabled:true }
    }
}
