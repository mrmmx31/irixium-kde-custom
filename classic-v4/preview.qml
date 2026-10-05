// SPDX-License-Identifier: GPL-3.0-or-later
// Pure Qt Quick preview: it does not change KWin or create a fake terminal session.
import QtQuick
import QtQuick.Window
import "kwin/decorations/irixium_irix_classic_v4/contents/ui"
Window {
    visible: true
    width: 780; height: 430
    color: "#4e7298"
    title: "Prévia técnica — IRIX Classic v4"
    Rectangle {
        x: 48; y: 72; width: 684; height: 302
        color: "#c1c1c1"
    }
    ClassicSurface {
        x: 40; y: 40; width: 700; height: 342
        caption: "IRIX Classic — prévia, não é uma captura do KWin"
        onMenuActivated: activeWindow = !activeWindow
        onMinimizeActivated: caption = "Pequeno quadrado: minimizar"
        onMaximizeActivated: maximizedWindow = !maximizedWindow
    }
}
