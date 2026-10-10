// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
QtObject {
    property int pixelScale: 1
    // Swiss 742 bold is named by the SR10.4 VUE manual. This installed-family
    // substitute is kept explicit; no proprietary font is bundled.
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 12
    property bool titleItalic: false
    property bool titleBold: true
}
