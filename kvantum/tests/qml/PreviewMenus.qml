// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Native Qt Quick menus from the installed org.kde.desktop module.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ApplicationWindow {
    id: win
    visible: true
    width: 640; height: 360
    title: "IrixClassic — menus Qt Quick do KDE"
    property string lastAction: "Nenhuma ação executada."
    ActionGroup { id: modes; exclusive: true }
    Action { id: textMode; text: "Texto"; checkable: true; checked: true; ActionGroup.group: modes }
    Action { id: imageMode; text: "Imagem"; checkable: true; ActionGroup.group: modes }
    menuBar: MenuBar {
        Menu {
            title: qsTr("&Arquivo")
            Action { text: "&Abrir..."; shortcut: "Ctrl+O"; onTriggered: win.lastAction=text }
            Action { text: "Salvar indisponível"; enabled: false }
            MenuSeparator {}
            Action { text: "Exibir detalhes"; checkable: true; checked: true }
            Menu {
                title: "Formato"
                MenuItem { action: textMode }
                MenuItem { action: imageMode }
            }
            MenuSeparator {}
            Action { text: "Fechar galeria"; onTriggered: win.close() }
        }
        Menu { title: "&Editar"; Action { text: "Exemplo"; onTriggered: win.lastAction=text } }
        Menu { title: "A&juda"; Action { text: "Sobre a galeria" } }
    }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20
        Label { text: "Menu nativo do Qt Quick/KDE com configuração temporária Kvantum."; wrapMode: Text.Wrap; Layout.fillWidth: true }
        Label { text: win.lastAction; Layout.fillWidth: true }
        Button { text: "Abrir popup"; onClicked: popup.open() }
        Menu {
            id: popup
            Action { text: "Ação de teste"; onTriggered: win.lastAction=text }
            MenuSeparator {}
            MenuItem { action: textMode }
            MenuItem { action: imageMode }
            Action { text: "Indisponível"; enabled: false }
        }
        Item { Layout.fillHeight: true }
        Label { text: "Nenhum comando desta janela altera arquivos ou configurações do sistema."; wrapMode: Text.Wrap; Layout.fillWidth: true }
    }
}
