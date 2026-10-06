// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

QtObject {
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: false
    property bool titleBold: true
    // Legacy literals retained so older appearance files can be imported.
    // main.qml defines the current menu policy; these do not disable its double-click.
    property bool menuDoubleClickClosesWindow: false
    property bool menuOpensOnPress: true
}
