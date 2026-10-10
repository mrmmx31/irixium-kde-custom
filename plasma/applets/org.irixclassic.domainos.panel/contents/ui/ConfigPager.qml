// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.plasmoid

KCM.SimpleKCM {
    id: page
    property alias cfg_pagerWheelActivates: wheel.checked
    property alias cfg_pagerCurrentScreen: screen.checked

    footer: DomainOSCategoryDefaults {
        targetPage: page
        configuration: Plasmoid.configuration
    }

    Kirigami.FormLayout {
        QQC.CheckBox {
            id: wheel
            text: qsTr("A roda também ativa a área de trabalho percorrida")
            Kirigami.FormData.label: qsTr("Navegação:")
        }
        QQC.Label {
            text: qsTr("Desligado: a roda percorre os cartões sem trocar a área ativa. Setas permitem alcançar todas as áreas; os dois cartões desenhados não limitam a quantidade de áreas reais.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.CheckBox {
            id: screen
            text: qsTr("Mostrar nas miniaturas somente janelas desta tela")
            Kirigami.FormData.label: qsTr("Miniaturas:")
        }
        QQC.Label {
            text: qsTr("Os cartões representam a geometria das janelas, sem capturar seu conteúdo. O arraste de janelas entre miniaturas foi adiado.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Label {
            text: qsTr("Criar, remover e renomear áreas são comandos explícitos no menu de contexto do Pager. Afetam as áreas reais desta sessão KDE e mantêm pelo menos uma área. Aplicar estas preferências não cria áreas nem modifica seus nomes.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
            Kirigami.FormData.label: qsTr("Áreas e nomes:")
        }
    }
}
