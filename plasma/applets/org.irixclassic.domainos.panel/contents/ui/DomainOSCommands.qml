// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.private.sessions as Sessions

Item {
    id: commands
    property var settings: ({})
    property var palette
    property var activity
    property var jobs: ({})
    property var lastReport: ({})
    property var executableSource: executable
    // Executable DataEngine sources are shared by applet instances. Make every
    // user request a distinct source, including simultaneous identical clicks.
    readonly property string instanceNonce: Date.now().toString(36) + "-" + Math.random().toString(36).slice(2)
    signal reported(var report)
    signal localHelpRequested(var anchor)
    signal closeLocalHelpRequested()
    property bool localHelpVisible: false
    readonly property var sessionCapabilities: ({
        lock: session.canLock, logout: session.canLogout,
        suspend: session.canSuspend, hibernate: session.canHibernate
    })
    Sessions.SessionManagement { id: session }
    function begin(label) { return activity.begin(label) }
    function finish(token, report) {
        activity.finish(token, report)
        lastReport = report
        reported(report)
    }
    function quote(value) { return "'" + String(value).replace(/'/g, "'\"'\"'") + "'" }
    function launch(action, options = {}) {
        const token = begin(action)
        let command = ""
        let registered = false
        try {
            const request = Object.assign({}, options, {action: action, token: token,
                requestNonce: instanceNonce + "-" + token})
            const path = decodeURIComponent(Qt.resolvedUrl("../code/commands.py").toString().replace(/^file:\/\//, ""))
            command = "python3 " + quote(path) + " " + quote(JSON.stringify(request))
            jobs[command] = token
            registered = true
            executableSource.connectSource(command)
        } catch (error) {
            // A connection may have submitted the action before throwing. Close
            // our bookkeeping without retrying or claiming it did not execute.
            if (!registered || jobs[command] === token) {
                if (registered) { delete jobs[command]; releaseSource(command) }
                finish(token, {ok: false, token: token, action: action,
                    outcome: registered ? "unknown" : "failed",
                    code: registered ? "command-connection-unconfirmed" : "invalid-command-request",
                    detail: registered ? qsTr("Could not confirm the request. Do not repeat it automatically.")
                        : qsTr("Could not prepare the request. No action was submitted.")})
            }
        }
        return token
    }
    function releaseSource(source) {
        try { executableSource.disconnectSource(source); return true }
        catch (error) { console.warn("DomainOS command source cleanup failed"); return false }
    }
    function handleResult(source, data) {
        const token = jobs[source]
        if (token === undefined) return false
        // Remove ownership before disconnecting: even a failing provider cannot
        // finish the same request repeatedly through duplicate data signals.
        delete jobs[source]
        const disconnected = releaseSource(source)
        let result
        try {
            result = JSON.parse(data.stdout)
            if (!result || typeof result !== "object" || result.token !== token || typeof result.ok !== "boolean")
                throw new Error("Mismatched command result")
        } catch (error) {
            result = {ok: false, token: token, outcome: "unknown", code: "invalid-command-result",
                detail: qsTr("The result could not be read. Do not repeat the action automatically.")}
        }
        if (!disconnected) result = Object.assign({}, result, {cleanupFailed: true})
        finish(token, result)
        return true
    }
    function openTerminal() { return launch("terminal", {terminalCommand: settings.terminalCommand || ""}) }
    function openMail() { return launch("mail", {mailClient: settings.mailClient || ""}) }
    function openAppearance() { return launch("appearance") }
    function openApplication(desktopId) { return launch("application", {desktopId: desktopId}) }
    function openXman() {
        return launch("xman", {palette: {background: String(palette.background), foreground: String(palette.text),
                                        selection: String(palette.blue), selectionText: String(palette.white)}})
    }
    function openKdeHelp() { return launch("kde-help") }
    function lock() { return launch("lock") }
    function sleep(kind) {
        if (kind !== "suspend" && kind !== "hibernate") return
        if (!sessionCapabilities[kind]) {
            const token = begin(kind)
            finish(token, {ok: false, outcome: "unavailable", action: kind, detail: qsTr("Session does not offer this action")})
            return token
        }
        return launch(kind)
    }
    property Item helpAnchor: null
    DomainOSPopupPlacement { id: menuPlacement }
    DomainOSPopupToggle { id: sessionToggle; showing: sessionMenu.visible }
    DomainOSPopupToggle { id: helpToggle; showing: helpMenu.visible || commands.localHelpVisible }
    function showSession(anchor) {
        if (!sessionToggle.shouldOpen(anchor)) { sessionMenu.close(); return }
        menuPlacement.showMenu(sessionMenu, anchor)
    }
    function showHelp(anchor) {
        helpAnchor = anchor
        if (!helpToggle.shouldOpen(anchor)) {
            helpMenu.close()
            closeLocalHelpRequested()
            return
        }
        menuPlacement.showMenu(helpMenu, anchor)
    }
    Controls.Menu {
        id: sessionMenu
        objectName: "domainosSessionMenu"
        popupType: Controls.Popup.Window
        closePolicy: Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutsideParent
        enter: null
        exit: null
        Controls.MenuItem {
            text: qsTr("Log out…"); enabled: session.canLogout
            onTriggered: commands.launch("logout-prompt")
        }
        Controls.MenuItem { text: qsTr("Suspend"); enabled: session.canSuspend; onTriggered: commands.sleep("suspend") }
        Controls.MenuItem { text: qsTr("Hibernate"); enabled: session.canHibernate; onTriggered: commands.sleep("hibernate") }
    }
    Controls.Menu {
        id: helpMenu
        objectName: "domainosHelpMenu"
        popupType: Controls.Popup.Window
        closePolicy: Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutsideParent
        enter: null
        exit: null
        Controls.MenuItem { text: qsTr("Irix Classic DomainOS help"); onTriggered: commands.localHelpRequested(commands.helpAnchor) }
        Controls.MenuItem { text: qsTr("Unix manual browser (xman)"); onTriggered: commands.openXman() }
        Controls.MenuItem { text: qsTr("KDE Help"); onTriggered: commands.openKdeHelp() }
    }
    P5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: (source, data) => commands.handleResult(source, data)
    }
}
