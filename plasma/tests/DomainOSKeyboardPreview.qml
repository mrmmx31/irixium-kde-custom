// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "../applets/org.irixclassic.domainos.panel/contents/ui" as DomainOS

DomainOSIconboxPreview {
    id: host
    property int instrumentClicks:0
    property int instrumentCancels:0
    Item {
        x:8;y:200;width:83;height:75
        readonly property QtObject domainosPalette:palette
        DomainOS.DomainOSPalette { id:palette;followSystem:false }
        DomainOS.PanelButton {
            objectName:"domainosKeyboardInstrument"
            anchors.fill:parent
            label:"Keyboard instrument"
            onClicked:host.instrumentClicks++
            onPointerCancelled:host.instrumentCancels++
        }
    }
}
