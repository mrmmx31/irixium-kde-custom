// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
QtObject {
    // Local to this decoration; the installer never changes the monitor scale.
    property int pixelScale: 1
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: true
    property bool titleBold: true
    // CDE-like mouse-down request. false is a local release/click fallback.
    // No claim that KWin's native popup reproduces all dtwm grabs.
    property bool menuOpensOnPress: true
}
