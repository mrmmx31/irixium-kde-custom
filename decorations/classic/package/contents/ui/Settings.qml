// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
QtObject {
    // Local to this decoration; the installer never changes the monitor scale.
    property int pixelScale: 1
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: true
    property bool titleBold: true
    // Legacy literals retained so older appearance files can be imported.
    // main.qml defines the current menu policy; these do not disable its double-click.
    property bool menuDoubleClickClosesWindow: false
    property bool menuOpensOnPress: true
}
