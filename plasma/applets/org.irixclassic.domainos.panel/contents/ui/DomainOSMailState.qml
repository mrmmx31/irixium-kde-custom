// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.private.taskmanager as NativeTasks
import org.kde.plasma.workspace.dbus as DBus
import org.kde.plasma.plasma5support as P5Support

Item {
    id: mailSource
    visible: false
    enabled: false
    property string desktopId: ""
    property string defaultDesktopId: ""
    property string metadataCommand: ""
    property var metadataSource: null
    property bool metadataDirty: false
    property bool initialized: false
    readonly property string effectiveDesktopId: desktopId || defaultDesktopId
    readonly property bool supportedClient: ["thunderbird.desktop", "org.mozilla.Thunderbird.desktop"].indexOf(effectiveDesktopId) >= 0
    readonly property bool available: enabled && supportedClient && host.registered
        && !!nativeProvider.item && nativeProvider.item.launcher.countVisible
        && Number.isInteger(nativeProvider.item.launcher.count) && nativeProvider.item.launcher.count >= 0
    readonly property var unreadCount: available ? nativeProvider.item.launcher.count : null
    readonly property string statusText: !enabled ? qsTr("Message counts are disabled in this panel's preferences")
        : !supportedClient ? qsTr("Unread counts require the optional Thunderbird integration")
        : !available ? qsTr("Thunderbird unread-count source is unavailable")
        : qsTr("Thunderbird: %1 unread messages in physical folders").arg(unreadCount)

    // This is independent of SmartLauncher backend cleanup, which is not wired
    // to sender loss in KDE 6.3.6. A lost native host immediately hides old data.
    DBus.DBusServiceWatcher {
        id: host
        busType: DBus.BusType.Session
        watchedService: "org.irixclassic.DomainOS.Thunderbird"
    }
    Loader {
        id: nativeProvider
        active: mailSource.enabled && mailSource.supportedClient
        sourceComponent: Item {
            readonly property QtObject launcher: NativeTasks.SmartLauncherItem {
                launcherUrl: "applications:org.irixclassic.domainos.thunderbird.counts.desktop"
            }
        }
    }
    function quote(value) { return "'" + String(value).replace(/'/g, "'\"'\"'") + "'" }
    function refreshDefaultClient() {
        if (!enabled || desktopId) return
        // The global MIME choice may have changed since panel startup. Hide the
        // old client's badge until this explicit user request is resolved.
        defaultDesktopId = ""
        if (metadataCommand) { metadataDirty = true; return }
        readDefaultClient()
    }
    function readDefaultClient() {
        if (!initialized || !enabled || desktopId || metadataCommand) return
        const path = decodeURIComponent(Qt.resolvedUrl("../code/commands.py").toString().replace(/^file:\/\//, ""))
        metadataCommand = "/usr/bin/python3 " + quote(path) + " " + quote(JSON.stringify({
            action:"mail-clients",requestNonce:"mail-source-"+Date.now().toString(36)+"-"+Math.random().toString(36).slice(2)}))
        const command = metadataCommand
        const provider = metadataSource || metadata
        try { provider.connectSource(command) }
        catch (error) {
            if (metadataCommand !== command) return // A synchronous result already released it.
            metadataCommand = ""; metadataDirty = false; defaultDesktopId = ""
            try { provider.disconnectSource(command) }
            catch (cleanupError) { console.warn("DomainOS mail metadata cleanup failed") }
            console.warn("DomainOS default mail metadata is unavailable")
        }
    }
    function handleMetadataResult(command, data) {
        if (command !== metadataCommand) return
        metadataCommand = ""
        try { (metadataSource || metadata).disconnectSource(command) }
        catch (error) { console.warn("DomainOS mail metadata cleanup failed") }
        // One pending explicit click coalesces into one fresh metadata request.
        // This is not a retry of a failed request or a periodic query.
        if (metadataDirty) {
            metadataDirty = false
            readDefaultClient()
            return
        }
        try {
            const result = JSON.parse(data.stdout)
            if (result.ok !== true || typeof result.defaultClient !== "string") throw new Error("Invalid metadata")
            if (enabled && !desktopId) defaultDesktopId = result.defaultClient
        } catch (error) {
            defaultDesktopId = ""
            console.warn("DomainOS default mail metadata could not be read")
        }
    }
    Component.onCompleted: { initialized = true; readDefaultClient() }
    onEnabledChanged: if (enabled) readDefaultClient()
    onDesktopIdChanged: {
        defaultDesktopId = ""
        metadataDirty = false
        readDefaultClient()
    }
    P5Support.DataSource {
        id: metadata
        engine: "executable"
        connectedSources: []
        onNewData: (command, data) => mailSource.handleMetadataResult(command, data)
    }
}
