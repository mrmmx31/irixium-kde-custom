// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.workspace.dbus as DBus

Item {
    id: operations
    property var activity
    property var pending: ({})
    property var lastReport: ({})
    property var executableSource: executable
    readonly property bool available: service.registered
    readonly property string nonce: Date.now().toString(36)+"-"+Math.random().toString(36).slice(2)
    signal reported(var report)
    DBus.DBusServiceWatcher { id: service; busType: DBus.BusType.Session; watchedService: "org.kde.KWin" }
    function quote(value) { return "'"+String(value).replace(/'/g,"'\"'\"'")+"'" }
    function identity(window) { return {key:window.key,windowIds:Array.from(window.windowIds),pid:window.pid} }
    function launch(request) {
        if (!available) return {state:"unavailable",reason:qsTr("KWin is unavailable in this session")}
        const token=activity.begin("windows-"+request.action)
        let command=""
        let registered=false
        try {
            const submitted=Object.assign({},request,{token:token,nonce:nonce+"-"+token})
            const path=decodeURIComponent(Qt.resolvedUrl("../code/window_ops.py").toString().replace(/^file:\/\//,""))
            // PyQt6 must match the installed KDE libraries (the distribution Python).
            command="/usr/bin/python3 "+quote(path)+" "+quote(JSON.stringify(submitted))
            pending[command]={token:token,action:request.action}
            registered=true
            executableSource.connectSource(command)
        } catch (error) {
            const pendingEntry=pending[command]
            if (!registered || (pendingEntry && pendingEntry.token===token)) {
                if (registered) {delete pending[command];releaseSource(command)}
                const detail=registered?qsTr("Could not confirm the window request. Do not repeat it automatically.")
                    :qsTr("Could not prepare the window request. No action was submitted.")
                finish(token,request.action==="preflight"
                    ? {ok:true,token:token,action:request.action,outcome:"preflight",available:false,
                        geometryAvailable:false,detail:detail,windows:[]}
                    : {ok:false,token:token,action:request.action,outcome:registered?"unknown":"failed",
                        code:registered?"window-connection-unconfirmed":"invalid-window-request",detail:detail})
            }
        }
        // The report channel conveys immediate failure as well as asynchronous
        // results. Keeping this return contract avoids duplicate error dialogs.
        return {state:"requested",token:token}
    }
    function finish(token,report) {
        lastReport=report
        activity.finish(token,report)
        reported(report)
    }
    function releaseSource(source) {
        try {executableSource.disconnectSource(source);return true}
        catch (error) {console.warn("DomainOS window source cleanup failed");return false}
    }
    function handleResult(source,data) {
        const entry=pending[source]
        if (!entry || entry.token===undefined) return false
        const token=entry.token, action=entry.action
        delete pending[source]
        const disconnected=releaseSource(source)
        let report
        try {
            report=JSON.parse(data.stdout)
            if (!report || typeof report!=="object" || report.token!==token || typeof report.ok!=="boolean")
                throw new Error("Mismatched window operation result")
        } catch (error) {
            report={ok:false,token:token,outcome:"unknown",code:"invalid-window-result",
                detail:qsTr("The window result could not be read. Do not repeat the action automatically.")}
        }
        report=Object.assign({action:action},report)
        if (action==="preflight" && !report.ok)
            report={ok:true,token:token,action:action,outcome:"preflight",available:false,
                geometryAvailable:false,detail:report.detail,windows:[],cleanupFailed:report.cleanupFailed}
        if (!disconnected) report=Object.assign({},report,{cleanupFailed:true})
        finish(token,report)
        return true
    }
    function requestLayout(payload) {
        return launch({action:"layout",mode:payload.mode,windows:payload.windows.map(identity),desktopId:payload.desktopId})
    }
    function requestRestore(payload) {
        return launch({action:"restore",windows:payload.windows.map(identity)})
    }
    function requestPreflight(payload) {
        return launch({action:"preflight",windows:payload.windows.map(identity)})
    }
    function requestTerminate(payload) {
        return launch({action:"terminate",window:identity(payload.window),selectedKeys:payload.selectedKeys.slice()})
    }
    P5Support.DataSource {
        id: executable
        engine: "executable"; connectedSources: []
        onNewData: (source,data)=>operations.handleResult(source,data)
    }
}
