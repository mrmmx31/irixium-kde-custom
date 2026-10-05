// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
QtObject {
    // 1 = original grid. 2 = exact integer enlargement for a high-density screen.
    // The OS display scale remains separate and is never changed by this theme.
    property int pixelScale: 1
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 14
    property bool titleItalic: true
    property bool titleBold: true
    // No proprietary IRIX bitmap fonts are shipped; native font metrics can differ.
}
