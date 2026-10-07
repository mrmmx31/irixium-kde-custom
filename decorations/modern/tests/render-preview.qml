// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "../package/contents/ui" as Modern

Rectangle {
    id: gallery
    width: 900
    height: 510
    color: "#e6e6e6"
    property int calls: 0
    property string lastAction: "Sem ações de KWin: esta janela é somente uma prévia."
    function registerAction(name) { calls++; lastAction = name + " — " + calls; }
    Text { x: 16; y: 8; text: "Irixium Moderno — renderização do pacote independente"; color: "black" }
    Modern.Surface {
        id: activeFrame
        objectName: "previewActive"
        x: 16; y: 40; width: 868; height: 128
        caption: "Ativa: atlas SVG recortado por estado, não reduzido inteiro"
        onMenuRequested: gallery.registerAction("Menu de ações")
        onMinimizeRequested: gallery.registerAction("Minimizar")
        onMaximizeRequested: gallery.registerAction("Maximizar")
        onCloseRequested: gallery.registerAction("Fechar (somente prévia)")
        Rectangle { x: 7; y: 34; width: parent.width - 14; height: parent.height - 41; color: "#c0c0c0"
            Text { anchors.centerIn: parent; text: "Área de cliente ilustrativa; passe o mouse e pressione os botões."; color: "black" }
        }
    }
    Modern.Surface {
        id: inactiveFrame
        objectName: "previewInactive"
        x: 16; y: 182; width: 868; height: 128
        activeWindow: false
        caption: "Inativa: estados e cores da arte existente"
        Rectangle { x: 7; y: 34; width: parent.width - 14; height: parent.height - 41; color: "#c0c0c0" }
    }
    Modern.Surface {
        id: maxFrame
        objectName: "previewMaximized"
        x: 16; y: 324; width: 868; height: 58
        maximizedWindow: true
        caption: "Maximizada: mesma ordem minimizar / maximizar-restaurar"
        Rectangle { x: 0; y: 34; width: parent.width; height: 24; color: "#c0c0c0" }
    }
    Modern.Surface {
        id: disabledFrame
        objectName: "previewDisabled"
        x: 16; y: 397; width: 868; height: 72
        minimizeAllowed: false; maximizeAllowed: false; closeOnDouble: false
        caption: "Ações indisponíveis: camadas deactivated do SVG"
        Rectangle { x: 7; y: 34; width: parent.width - 14; height: parent.height - 41; color: "#c0c0c0" }
    }
    Text { x: 16; y: 486; text: gallery.lastAction; color: "black" }
}
