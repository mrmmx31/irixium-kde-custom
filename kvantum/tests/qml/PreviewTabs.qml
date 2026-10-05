// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts

Controls.ApplicationWindow {
    width: 760; height: 490; visible: true
    title: "IrixClassic — abas Qt Quick / ensaio manual"
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 12; spacing: 8
        Controls.Label {
            Layout.fillWidth: true; wrapMode: Text.WordWrap
            text: "TabBar/TabButton reais do org.kde.desktop. Compare com a galeria Widgets. A aplicação controla a troca de páginas."
        }
        Controls.TabBar {
            id: bar; Layout.fillWidth: true
            Controls.TabButton { text: "Geral" }
            Controls.TabButton { text: "Detalhes" }
            Controls.TabButton { text: "Indisponível"; enabled: false }
            Controls.TabButton { text: "Avançado" }
        }
        StackLayout {
            Layout.fillWidth: true; Layout.fillHeight: true
            currentIndex: bar.currentIndex
            Controls.Label { text: "Página Geral — sem pintura personalizada." }
            Controls.TextField { text: "Campo na página Detalhes" }
            Controls.Label { text: "Esta página está desativada." }
            Controls.Label { text: "Página Avançado" }
        }
        Controls.Label {
            Layout.fillWidth: true; wrapMode: Text.WordWrap
            text: "Teste clique, Tab, setas e indicação de seleção. A galeria não instala tema nem modifica arquivos KDE."
        }
    }
}
