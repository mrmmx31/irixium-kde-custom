// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import "ConfigUtils.js" as ConfigUtils

QQC.Control {
    id: reset
    property QtObject targetPage: null
    property var configuration: null
    property bool resetAllowed: true
    property string statusText: ""
    readonly property var availableDefaults: ConfigUtils.categoryDefaults(targetPage, configuration)
    readonly property bool hasCustomValues: availableDefaults.ok && availableDefaults.keys.some(
        key => JSON.stringify(targetPage["cfg_" + key]) !== JSON.stringify(availableDefaults.values[key]))
    signal resetPrepared()
    padding: 6
    implicitHeight: contentItem.implicitHeight + topPadding + bottomPadding

    function prepareDefaults() {
        if (!resetAllowed) return false;
        const result = ConfigUtils.resetCategory(targetPage, configuration);
        statusText = result.ok
            ? qsTr("Padrões desta categoria preparados. Aplicar salva; Descartar mantém as preferências anteriores.")
            : qsTr("Os padrões nativos desta categoria não estão disponíveis.");
        if (result.ok) resetPrepared();
        return result.ok;
    }

    contentItem: ColumnLayout {
        QQC.Button {
            objectName: "domainosResetCategory"
            text: qsTr("Restaurar esta categoria")
            enabled: reset.resetAllowed && reset.hasCustomValues
            onClicked: reset.prepareDefaults()
        }
        QQC.Label {
            text: reset.statusText.length > 0 ? reset.statusText
                : qsTr("Usa os padrões desta categoria somente nesta instância do painel. Aplicar salva; Descartar mantém o que estava salvo.")
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
    }
}
