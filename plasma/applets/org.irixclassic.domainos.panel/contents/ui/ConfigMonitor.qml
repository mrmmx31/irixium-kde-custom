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
    property string cfg_instrumentMetric: "network"
    property alias cfg_networkInterface: network.text
    property alias cfg_customSensorId: primarySensor.text
    property alias cfg_customSecondarySensorId: secondarySensor.text
    property alias cfg_instrumentSampleInterval: interval.value
    property alias cfg_instrumentHistoryLength: samples.value
    readonly property var metrics: ["network", "cpu", "memory", "disk", "custom"]

    footer: DomainOSCategoryDefaults {
        targetPage: page
        configuration: Plasmoid.configuration
    }

    Kirigami.FormLayout {
        QQC.ComboBox {
            Layout.fillWidth: true
            model: [qsTr("Rede: recepção e envio"), qsTr("CPU"), qsTr("Memória"), qsTr("Disco"), qsTr("Sensores escolhidos")]
            currentIndex: Math.max(0, page.metrics.indexOf(page.cfg_instrumentMetric))
            onActivated: index => page.cfg_instrumentMetric = page.metrics[index]
            Kirigami.FormData.label: qsTr("Objeto medido:")
        }
        QQC.TextField {
            id: network
            text: "all"
            enabled: page.cfg_instrumentMetric === "network"
            placeholderText: qsTr("all ou identificador da interface, por exemplo enp3s0")
            Kirigami.FormData.label: qsTr("Interface de rede:")
            Layout.fillWidth: true
        }
        QQC.TextField {
            id: primarySensor
            enabled: page.cfg_instrumentMetric === "custom"
            placeholderText: qsTr("Identificador real do sensor do KSystemStats")
            Kirigami.FormData.label: qsTr("Sensor principal:")
            Layout.fillWidth: true
        }
        QQC.TextField {
            id: secondarySensor
            enabled: page.cfg_instrumentMetric === "custom"
            placeholderText: qsTr("Opcional, com a mesma unidade do principal")
            Kirigami.FormData.label: qsTr("Segundo sensor:")
            Layout.fillWidth: true
        }
        QQC.Label {
            text: qsTr("Sensores ausentes aparecem como indisponíveis; um valor de zero não substitui uma fonte ausente. O quadro gr_osview identifica os sensores, unidades e escala reais.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.SpinBox {
            id: interval
            from: 1000; to: 60000; value: 1000; stepSize: 250; editable: true
            Kirigami.FormData.label: qsTr("Intervalo de amostragem (ms):")
        }
        QQC.SpinBox {
            id: samples
            from: 10; to: 1000; value: 60; editable: true
            Kirigami.FormData.label: qsTr("Amostras do histórico:")
        }
        QQC.Label {
            text: qsTr("1000 ms e 60 amostras são valores técnicos iniciais. A assinatura de sensores limita a amostragem; não acrescenta um timer ao clique ou ao redimensionamento. Clicar no gráfico abre o gr_osview já existente.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
    }
}
