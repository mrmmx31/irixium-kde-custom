// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

QtObject {
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: false
    property bool titleBold: true
    // This is deliberately local to the package. A single menu click opens
    // the actions menu immediately instead of waiting for double-click input.
    property bool menuDoubleClickClosesWindow: false
    property bool menuOpensOnPress: true
}
