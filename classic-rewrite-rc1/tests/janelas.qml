// SPDX-License-Identifier: GPL-3.0-or-later
// Real client windows; the ACTIVE KWin decoration supplies their title bars.
import QtQuick
import QtQuick.Window
QtObject {
    property var normal: Window {
        visible: true; width: 560; height: 230
        title: "IRIX Classic — janela redimensionável"
        flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint
            | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
        Text {
            anchors.fill: parent; anchors.margins: 20; wrapMode: Text.WordWrap
            text: "Teste a decoração selecionada no KDE.\n\nPressione e segure; saia do botão; volte e solte. Teste minimizar, maximizar/restaurar, o menu e sua preferência de duplo clique.\n\nA janela de tamanho fixo deve indicar maximização indisponível."
        }
        onClosing: { fixed.visible=false; Qt.quit(); }
    }
    property var fixed: Window {
        visible: true; width: 390; height: 160
        minimumWidth:390; maximumWidth:390; minimumHeight:160; maximumHeight:160
        title: "IRIX Classic — tamanho fixo"
        flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint
            | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint
        Text {
            anchors.fill: parent; anchors.margins: 20; wrapMode: Text.WordWrap
            text: "Esta janela não solicita o botão de maximizar e fixa seu tamanho.\n\nConfira o desenho indisponível e se clicar nele deixa de executar a ação."
        }
    }
}
