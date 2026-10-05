// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts

QQC.ApplicationWindow {
    width: 930; height: 690; visible: true
    title: "IrixClassic — bloco 7 / Qt Quick do KDE"
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 12; spacing: 8
        QQC.Label { text: "Controles nativos de org.kde.desktop. Nenhuma configuração global é alterada."; wrapMode: Text.Wrap }
        QQC.Label { text: "A geometria QML é própria: não é uma captura histórica nem garantia de equivalência com Widgets."; wrapMode: Text.Wrap }
        RowLayout {
            Layout.fillWidth: true
            QQC.Slider { id: value; from: 0; to: 100; value: 45; Layout.fillWidth: true }
            QQC.Label { text: Math.round(value.value) }
            QQC.Slider { from: 0; to: 100; value: 65; enabled: false }
        }
        QQC.ProgressBar { from: 0; to: 100; value: value.value; Layout.fillWidth: true }
        QQC.ProgressBar { indeterminate: true; Layout.fillWidth: true }
        QQC.ProgressBar { value: 0.55; enabled: false; Layout.fillWidth: true }
        QQC.SplitView {
            Layout.fillWidth: true; Layout.fillHeight: true
            orientation: Qt.Horizontal
            QQC.ScrollView {
                SplitView.preferredWidth: 250
                ColumnLayout {
                    Repeater {
                        model: 16
                        QQC.ItemDelegate { required property int index; text: "Item " + (index+1)
                            enabled: index !== 4; checkable: true; checked: index===1; Layout.fillWidth: true }
                    }
                }
            }
            QQC.TextArea { text: "Painel de texto nativo.\nArraste o divisor e teste o foco com Tab.\n\n"
                                + "Área de conteúdo sem repintura pelo tema.\n".repeat(28)
                           wrapMode: TextEdit.Wrap; SplitView.fillWidth: true }
        }
        RowLayout {
            QQC.Dial { value: 0.4 }
            QQC.Dial { value: 0.7; enabled: false }
            QQC.Button {
                text: "Tooltip"
                QQC.ToolTip.visible: hovered
                QQC.ToolTip.text: "Dica nativa do Qt Quick; o componente decide a apresentação."
            }
        }
    }
}
