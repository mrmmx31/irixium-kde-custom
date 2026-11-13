// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.taskmanager as TaskManager

QtObject {
    id: fixture
    required property var host
    property bool grouped: false
    property bool minimizedOnly: false
    property int sortMode:1
    readonly property var rows: buildRows()
    readonly property int count: rows.length
    signal modelReset()
    onRowsChanged: modelReset()
    function buildRows() {
        const windows=host.windows.filter(window => (!host.controller.onlyCurrentDesktop
                    || window.desktops.indexOf(host.controller.currentDesktopId)>=0)
                && (!host.controller.onlyCurrentActivity || window.activities.indexOf(host.controller.currentActivityId)>=0)
                && (!host.controller.onlyCurrentScreen || window.screen===host.screen)
                && (!minimizedOnly || window.minimized))
        if (!grouped) return windows
        const result=[]
        for (const window of windows) {
            const previous=result.find(row=>row.appId===window.appId)
            if (!previous) result.push(window)
            else if (previous.children) previous.children.push(window)
            else result[result.indexOf(previous)]={appId:window.appId,title:window.appId,children:[previous,window]}
        }
        return result
    }
    function makeModelIndex(row,childRow) { return {row:row,child:childRow===undefined ? -1 : childRow} }
    function rowCount(index) { return index && rows[index.row] && rows[index.row].children ? rows[index.row].children.length : 0 }
    function node(index) {
        const row=rows[index.row]
        return row && index.child>=0 && row.children ? row.children[index.child] : row
    }
    function data(index,role) {
        const row=node(index), atm=TaskManager.AbstractTasksModel
        if (!row) return undefined
        if (role===Qt.DisplayRole) return row.title
        if (role===Qt.DecorationRole) return "application-x-executable"
        if (role===atm.IsGroupParent) return Boolean(row.children)
        if (role===atm.IsWindow) return !row.children && row.type!=="launcher" && row.type!=="startup"
        if (role===atm.ChildCount) return row.children ? row.children.length : 0
        const fields={}
        fields[atm.AppId]="appId"; fields[atm.AppName]="appId"; fields[atm.AppPid]="pid"
        fields[atm.WinIdList]="ids"; fields[atm.LauncherUrlWithoutIcon]="launcher"
        fields[atm.IsActive]="active"; fields[atm.IsMinimized]="minimized"; fields[atm.IsMaximized]="maximized"
        fields[atm.IsDemandingAttention]="demandsAttention"
        fields[atm.VirtualDesktops]="desktops"; fields[atm.Activities]="activities"
        fields[atm.IsClosable]="closable"; fields[atm.IsMovable]="movable"; fields[atm.IsResizable]="resizable"
        fields[atm.IsMinimizable]="minimizable"; fields[atm.IsMaximizable]="maximizable"
        fields[atm.IsVirtualDesktopsChangeable]="desktopsChangeable"; fields[atm.CanLaunchNewInstance]="canLaunchNewInstance"
        if (role===atm.Geometry) return Qt.rect(row.x || 0,row.y || 0,200,120)
        if (role===atm.ScreenGeometry) return Qt.rect(row.screen===0 ? 0 : 1200,0,1200,900)
        return row[fields[role]]
    }
    function record(action,index,argument) {
        const row=node(index)
        if (row) host.appendRequest({action:action,ids:row.ids,argument:argument===undefined ? null : argument})
    }
    function requestActivate(index) { record("activate",index) }
    function requestClose(index) { record("close",index) }
    function requestToggleMinimized(index) { record("toggleMinimized",index) }
    function requestToggleMaximized(index) { record("toggleMaximized",index) }
    function requestVirtualDesktops(index,desktops) { record("desktops",index,desktops) }
    function requestActivities(index,activities) { record("activities",index,activities) }
    function requestMove(index) { record("interactiveMove",index) }
    function requestResize(index) { record("interactiveResize",index) }
    function requestNewInstance(index) { record("newInstance",index) }
    function requestOpenUrls(index,urls) { record("openUrls",index,urls) }
    function move(source,target) {
        if (sortMode!==1 || source<0 || target<0 || source>=rows.length || target>=rows.length || source===target) return false
        const ordered=rows.slice(), moved=ordered.splice(source,1)[0]
        ordered.splice(target,0,moved)
        const visible=ordered.reduce((all,row)=>all.concat(row.children || [row]),[])
        host.windows=visible.concat(host.windows.filter(window=>!visible.some(item=>item.ids[0]===window.ids[0])))
        host.appendRequest({action:"reorder",source:source,target:target})
        return true
    }
}
