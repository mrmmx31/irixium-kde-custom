// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kwin.private.kdecoration as KDec

Rectangle {
    id: gallery
    width: 1000; height: 660
    color: "#263a4d"
    property bool ready: false
    property bool activeState: true
    property bool maximizedState: false
    function updateClients() {
        ready = !!primary.client && !!secondary.client;
        if (!ready) return;
        primary.client.caption = "Help Index — DomainOS SR10.4";
        primary.client.active = activeState;
        primary.client.maximizedHorizontally = maximizedState;
        primary.client.maximizedVertically = maximizedState;
        secondary.client.caption = "Terminal Window — DomainOS SR10.4";
        secondary.client.active = false;
    }
    onActiveStateChanged: updateClients()
    onMaximizedStateChanged: updateClients()
    Component.onCompleted: updateClients()
    Text {
        x: 16; y: 8
        text: "DOMAINOS SR10.4 · KDecoration3 / Aurorae · referência de 10.4 somente"
        color: "white"; font.pixelSize: 14
    }
    KDec.Bridge { id: primaryBridge; plugin: "org.kde.kwin.aurorae"; theme: "domainos_sr104" }
    KDec.Settings { id: primarySettings; bridge: primaryBridge.bridge }
    KDec.Decoration {
        id: primary; objectName: "nativeDomainOSPrimary"
        x: 16; y: 40; width: 968; height: 280
        bridge: primaryBridge.bridge; settings: primarySettings
        windowColor: "#6688b5"
    }
    KDec.Bridge { id: secondaryBridge; plugin: "org.kde.kwin.aurorae"; theme: "domainos_sr104" }
    KDec.Settings { id: secondarySettings; bridge: secondaryBridge.bridge }
    KDec.Decoration {
        id: secondary; objectName: "nativeDomainOSSecondary"
        x: 16; y: 352; width: 968; height: 280
        bridge: secondaryBridge.bridge; settings: secondarySettings
        windowColor: "#78a0d5"
    }
}
