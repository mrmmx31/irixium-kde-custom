// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kwin.private.kdecoration as KDec

Rectangle {
    id: gallery
    width: 1000; height: 630
    color: "#e6e6e6"
    property bool windowActive: true
    property bool windowMaximized: false
    property bool decorationsReady: false
    function updateClients() {
        decorationsReady = !!modern.client && !!legacy.client && !!current.client;
        if (!decorationsReady) return;
        var items = [modern, legacy, current];
        var labels = ["Irixium Moderno", "Irixium 1.3 (Aurorae)", "Irixium 4.1 (Aurorae)"];
        for (var i = 0; i < items.length; i++) {
            items[i].client.caption = labels[i];
            items[i].client.active = windowActive;
            items[i].client.maximizedHorizontally = windowMaximized;
            items[i].client.maximizedVertically = windowMaximized;
        }
    }
    onWindowActiveChanged: updateClients()
    onWindowMaximizedChanged: updateClients()
    Component.onCompleted: updateClients()
    KDec.Bridge { id: modernBridge; plugin: "org.kde.kwin.aurorae"; theme: "irixium_modern" }
    KDec.Settings { id: modernSettings; bridge: modernBridge.bridge }
    KDec.Decoration {
        id: modern; objectName: "nativeModern"
        x: 16; y: 16; width: 968; height: 180
        bridge: modernBridge.bridge; settings: modernSettings
        windowColor: "#c0c0c0"
    }
    KDec.Bridge { id: legacyBridge; plugin: "org.kde.kwin.aurorae"; theme: "irixium_modern_13" }
    KDec.Settings { id: legacySettings; bridge: legacyBridge.bridge }
    KDec.Decoration {
        id: legacy; objectName: "nativeLegacy"
        x: 16; y: 216; width: 968; height: 180
        bridge: legacyBridge.bridge; settings: legacySettings
        windowColor: "#c0c0c0"
    }
    KDec.Bridge { id: currentBridge; plugin: "org.kde.kwin.aurorae"; theme: "irixium_modern_41" }
    KDec.Settings { id: currentSettings; bridge: currentBridge.bridge }
    KDec.Decoration {
        id: current; objectName: "nativeCurrent"
        x: 16; y: 416; width: 968; height: 190
        bridge: currentBridge.bridge; settings: currentSettings
        windowColor: "#c0c0c0"
    }
}
