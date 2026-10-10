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
    property alias cfg_keepActivityLight: keepLight.checked
    property alias cfg_activityLightMilliseconds: duration.value
    property alias cfg_barHintsEnabled: barHints.checked

    footer: DomainOSCategoryDefaults {
        targetPage: page
        configuration: Plasmoid.configuration
    }

    Kirigami.FormLayout {
        QQC.CheckBox {
            id:barHints
            objectName:"domainosBarHintsEnabled"
            text:qsTr("Mostrar dicas ao passar o mouse nos botões da barra")
            checked:false
            Kirigami.FormData.label:qsTr("Dicas da barra:")
        }
        QQC.Label {
            text:qsTr("Desligadas por padrão. A Iconbox tem sua própria opção para títulos, listas de grupos, miniaturas ou nenhuma dica.")
            wrapMode:Text.Wrap;Layout.fillWidth:true
        }
        QQC.Label {
            text: qsTr("A lente pisca a cada 500 ms durante pedidos pendentes e inicializações informadas pelo KDE. O cursor de espera segue o tema de cursores escolhido. Os botões respondem imediatamente.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.CheckBox {
            id: keepLight
            text: qsTr("Manter a luz acesa depois da conclusão")
            Kirigami.FormData.label: qsTr("Lente de atividade:")
        }
        QQC.SpinBox {
            id: duration
            objectName: "domainosActivityDuration"
            from: 0; to: 60000; value: 1000; stepSize: 100; editable: true
            enabled: keepLight.checked
            Kirigami.FormData.label: qsTr("Tempo adicional (ms):")
        }
        QQC.Label {
            text: qsTr("Esse tempo só posterga apagar a luz. Não atrasa o comando, o clique ou o desenho do relevo. 1000 ms é o valor técnico inicial; a permanência está desligada por padrão.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Label {
            text: qsTr("As preferências desta janela pertencem a esta instância do painel e a este usuário. Aplicar salva as alterações; Descartar mantém o que estava salvo. Os padrões não redefinem preferências de outros applets.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
    }
}
