// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
QtObject {
    // Local to this decoration; the installer never changes the monitor scale.
    property int pixelScale: 1
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: true
    property bool titleBold: true
    // Theme-local historical behavior. Does not rewrite the KDE global preference.
    // true: double left click requests Close, when the client permits it.
    property bool menuDoubleClickClosesWindow: true
    // Used for right click, and for left click when double-click Close is disabled.
    // With Close enabled, a single left click waits for Qt's double-click interval.
    property bool menuOpensOnPress: true
}
