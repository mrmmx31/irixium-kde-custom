// SPDX-License-Identifier: GPL-3.0-or-later
// Thunderbird 140 ESR: folder metadata only, never messenger.messages.*.
"use strict";
const HOST = "org.irixclassic.domainos.thunderbird";
let port = null;
let running = false;
let dirty = false;
let connected = false;

function publish(available, unreadCount) {
    if (!port || !connected) return;
    try {
        // Neither identifiers, folder names, account identities nor messages
        // cross the native port. Unknown never masquerades as zero.
        port.postMessage({schema: 1, type: "counts", available,
            unreadCount: available ? unreadCount : null});
    } catch (error) {
        connected = false;
        const failedPort = port;
        port = null;
        // Release the persistent native source even when posting throws before
        // its ordinary disconnect event. That event may run synchronously.
        if (failedPort) {
            try { failedPort.disconnect(); }
            catch (disconnectError) { console.warn("DomainOS unread-count port could not be closed"); }
        }
        console.warn("DomainOS unread-count connection is unavailable");
    }
}

async function aggregate() {
    const folders = await messenger.folders.query({isRoot: false, isVirtual: false,
        isUnified: false, isTag: false});
    // A profile without a physical message folder has no configured source.
    if (!folders.length) return {available: false, unreadCount: null};
    let unreadCount = 0;
    for (const folder of folders) {
        const info = await messenger.folders.getFolderInfo(folder.id);
        const count = info.unreadMessageCount;
        if (!Number.isInteger(count) || count < 0) return {available: false, unreadCount: null};
        unreadCount += count;
        if (!Number.isSafeInteger(unreadCount) || unreadCount > 2147483646)
            return {available: false, unreadCount: null};
    }
    return {available: true, unreadCount};
}

async function refresh() {
    dirty = true;
    if (running || !connected) return;
    running = true;
    try {
        while (dirty && connected) {
            dirty = false;
            try {
                const state = await aggregate();
                publish(state.available, state.unreadCount);
            } catch (error) {
                // Do not log the API exception: it can contain a folder path.
                publish(false, null);
                console.warn("DomainOS unread count could not be obtained");
            }
        }
    } finally { running = false; }
}

function connect() {
    try {
        port = messenger.runtime.connectNative(HOST);
        connected = true;
        port.onDisconnect.addListener(() => {
            connected = false;
            port = null;
            // No reconnect timer or automatic restart. Re-enable/reload this
            // extension explicitly after repairing its local host registration.
            console.warn("DomainOS unread-count host disconnected");
        });
        port.onMessage.addListener(message => {
            if (message && message.ok === false) {
                connected = false;
                const rejectedPort = port;
                port = null;
                if (rejectedPort) {
                    try { rejectedPort.disconnect(); }
                    catch (disconnectError) { console.warn("DomainOS unread-count port could not be closed"); }
                }
                console.warn("DomainOS unread-count host rejected the request");
            }
        });
        refresh();
    } catch (error) {
        connected = false;
        port = null;
        console.warn("DomainOS unread-count host could not be started");
    }
}

// These notifications are already collapsed by Thunderbird for count bursts.
// Coalescing in flight prevents simultaneous reads; there is no periodic poll.
messenger.folders.onFolderInfoChanged.addListener(refresh);
messenger.folders.onCreated.addListener(refresh);
messenger.folders.onDeleted.addListener(refresh);
messenger.folders.onRenamed.addListener(refresh);
messenger.folders.onMoved.addListener(refresh);
messenger.folders.onUpdated.addListener(refresh);
messenger.accounts.onCreated.addListener(refresh);
messenger.accounts.onDeleted.addListener(refresh);
connect();
