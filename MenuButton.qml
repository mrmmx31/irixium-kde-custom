/*
    SPDX-FileCopyrightText: 2012 Martin Gräßlin <mgraesslin@kde.org>

    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import org.kde.kwin.decoration
import org.kde.kirigami 2.20 as Kirigami

Item {
    id: menuButton
    property int buttonType: DecorationOptions.DecorationButtonMenu
    property bool hovered: false
    property bool pressed: false
    property bool toggled: false
    // IRIXIUM_CONTROLES_V3: only the Irixium menu uses this artwork/interaction.
    readonly property bool isIrixium: typeof auroraeTheme !== "undefined"
        && /\/Irixium\/decoration(?:\.svgz?)?$/.test(String(auroraeTheme.decorationPath))
    // Preserve the existing KWin preference, including double-click-to-close.
    // This update changes the artwork, not the user's window-menu click policy.
    property bool closeOnDoubleClick: decorationSettings.closeOnDoubleClickOnMenu
    readonly property bool irixiumDown: isIrixium
        && ((pressed && hovered) || pressFlash.running)
    readonly property bool irixiumActive: decoration.client.active

    Item {
        id: irixiumFace
        anchors.fill: parent
        visible: menuButton.isIrixium
        clip: true
        readonly property real edge: Math.max(1, Math.round(Math.min(width, height) / 22))
        readonly property bool lit: menuButton.hovered || menuButton.irixiumDown
        readonly property color dark: menuButton.irixiumActive
            ? (menuButton.irixiumDown ? "#36342a" : "#5b5746") : "#353535"
        readonly property color light: menuButton.irixiumActive
            ? (menuButton.irixiumDown ? "#e7e7df" : "#d3d0c0") : "#dadada"
        Rectangle {
            anchors.fill: parent
            visible: irixiumFace.lit
            color: menuButton.irixiumActive
                ? (menuButton.irixiumDown ? "#8e8771" : "#a19a7a")
                : (menuButton.irixiumDown ? "#777777" : "#8d8d8d")
        }
        // Recessed bevel, like the other Irixium button states. No new hit area.
        Rectangle {
            width: parent.width; height: irixiumFace.edge
            visible: irixiumFace.lit
            color: irixiumFace.dark
        }
        Rectangle {
            width: irixiumFace.edge; height: parent.height
            visible: irixiumFace.lit
            color: irixiumFace.dark
        }
        Rectangle {
            x: irixiumFace.edge; y: parent.height - height
            width: parent.width - irixiumFace.edge; height: irixiumFace.edge
            visible: irixiumFace.lit
            color: irixiumFace.light
        }
        Rectangle {
            x: parent.width - width; y: irixiumFace.edge
            width: irixiumFace.edge; height: parent.height - 2 * irixiumFace.edge
            visible: irixiumFace.lit
            color: irixiumFace.light
        }
        Image {
            // Shift the symbol only; do not move the button or the v2 separators.
            x: menuButton.irixiumDown ? irixiumFace.edge : 0
            y: menuButton.irixiumDown ? irixiumFace.edge : 0
            width: parent.width
            height: parent.height
            source: "file:///usr/share/kwin/aurorae/Irixium/applications.png"
            fillMode: Image.Stretch
            smooth: false
        }
    }
    // Brief visual feedback for very quick clicks; this does not delay the menu.
    Timer {
        id: pressFlash
        interval: 120
        repeat: false
    }
    Kirigami.Icon {
        anchors.fill: parent
        // Some clients/themes expose no window icon; keep the menu button
        // visible instead of leaving an empty slot for non-Irixium themes.
        source: decoration.client.icon || "application-x-executable"
        visible: !menuButton.isIrixium
    }
    DecorationOptions {
        id: options
        deco: decoration
    }
    Timer {
        id: timer
        interval: options.mousePressAndHoldInterval
        repeat: false
        onTriggered: decoration.requestShowWindowMenu()
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        onEntered: menuButton.hovered = true
        onPressed: {
            parent.pressed = true;
            if (menuButton.isIrixium) {
                menuButton.hovered = true;
                pressFlash.restart();
            }
            // we need a timer to figure out whether there is a double click in progress or not
            // if we have a "normal" click we want to open the context menu. This would eat our
            // second click of the double click. To properly get the double click we have to wait
            // the double click delay to ensure that it was only a single click.
            if (timer.running) {
                timer.stop();
            } else if (menuButton.closeOnDoubleClick) {
                timer.start();
            }
        }
        onReleased: {
            parent.pressed = false;
            timer.stop();
        }
        onCanceled: {
            menuButton.pressed = false;
            menuButton.hovered = false;
            timer.stop();
            pressFlash.stop();
        }
        onExited: {
            menuButton.hovered = false;
            pressFlash.stop();
            if (!parent.pressed) {
                return;
            }
            if (timer.running) {
                timer.stop();
            }
            parent.pressed = false;
        }
        onClicked: (mouse) => {
            // for right clicks we show the menu instantly
            // and if the option is disabled we always show menu directly
            if (!menuButton.closeOnDoubleClick || mouse.button == Qt.RightButton) {
                decoration.requestShowWindowMenu();
                timer.stop();
            }
        }
        onDoubleClicked: {
            if (menuButton.closeOnDoubleClick) {
                decoration.requestClose();
            }
        }
    }
}
