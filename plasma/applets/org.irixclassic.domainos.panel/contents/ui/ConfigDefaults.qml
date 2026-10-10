// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.plasmoid
import "ConfigUtils.js" as Utils

KCM.SimpleKCM {
    id: page
    objectName: "domainosDefaultsConfigPage"

    // Plasma stages cfg_* properties in the current configuration page. The
    // native Apply/Discard flow owns saving; this page never writes the applet.
    // Keep these names equal to main.xml, including future schema additions.
    property var cfg_configurationSchemaVersion: undefined
    property var cfg_timeZones: undefined
    property var cfg_calendarPlugins: undefined
    property var cfg_instrumentMetric: undefined
    property var cfg_networkInterface: undefined
    property var cfg_customSensorId: undefined
    property var cfg_customSecondarySensorId: undefined
    property var cfg_instrumentSampleInterval: undefined
    property var cfg_instrumentHistoryLength: undefined
    property var cfg_mailClient: undefined
    property var cfg_mailCountsEnabled: undefined
    property var cfg_terminalCommand: undefined
    property var cfg_tasksOnlyCurrentDesktop: undefined
    property var cfg_tasksOnlyCurrentScreen: undefined
    property var cfg_tasksOnlyCurrentActivity: undefined
    property var cfg_tasksGroupingMode: undefined
    property var cfg_tasksOnlyGroupWhenFull: undefined
    property var cfg_tasksSortMode: undefined
    property var cfg_middleClickAction: undefined
    property var cfg_wheelEnabled: undefined
    property var cfg_iconboxWheelActivates: undefined
    property var cfg_wheelSkipMinimized: undefined
    property var cfg_interactiveMute: undefined
    property var cfg_highlightWindows: undefined
    property var cfg_unhideOnAttention: undefined
    property var cfg_iconboxWindowThumbnails: undefined
    property var cfg_iconboxHintsEnabled: undefined
    property var cfg_barHintsEnabled: undefined
    property var cfg_tasksFilterMode: undefined
    property var cfg_tasksAutomaticThreshold: undefined
    property var cfg_tasksGroupingAppIdBlacklist: undefined
    property var cfg_tasksGroupingLauncherUrlBlacklist: undefined
    property var cfg_pinnedApplications: undefined
    property var cfg_applicationsMenuStyle: undefined
    property var cfg_showIconsRootLevel: undefined
    property var cfg_alignResultsToBottom: undefined
    property var cfg_pagerWheelActivates: undefined
    property var cfg_pagerCurrentScreen: undefined
    property var cfg_trayVisibleItems: undefined
    property var cfg_trayHiddenItems: undefined
    property var cfg_trayOrder: undefined
    property var cfg_trayIncludeHiddenInOverflow: undefined
    property var cfg_trayOverflowMode: undefined
    property var cfg_keepActivityLight: undefined
    property var cfg_activityLightMilliseconds: undefined

    readonly property var defaultValues: Utils.categoryDefaults(page, Plasmoid.configuration)
    readonly property bool hasCustomValues: defaultValues.ok && defaultValues.keys.some(key =>
        JSON.stringify(page["cfg_" + key]) !== JSON.stringify(defaultValues.values[key]))
    property string resetStatus: ""

    function resetAll() {
        const result = Utils.resetCategory(page, Plasmoid.configuration)
        resetStatus = result.ok ? qsTr("Padrões preparados. Aplicar confirma; Descartar mantém as preferências salvas.")
            : qsTr("Os padrões deste painel não estão disponíveis.")
        return result
    }

    Kirigami.FormLayout {
        QQC.Label {
            text: qsTr("Restaura as preferências de todas as categorias desta instância aos padrões originais.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Label {
            text: qsTr("A lista de aplicativos fixados e os comandos personalizados voltam aos padrões ao Aplicar. Inclui também filtros, agrupamento, dicas e organização da bandeja.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Label {
            text: qsTr("Afeta apenas este painel. Os demais painéis, as áreas de trabalho e as preferências de outros usuários permanecem como estão.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Button {
            objectName: "domainosResetAllDefaults"
            text: qsTr("Restaurar todos os padrões")
            icon.name: "edit-undo"
            enabled: page.hasCustomValues
            onClicked: page.resetAll()
        }
        QQC.Label {
            text: !page.defaultValues.ok ? qsTr("Abra as preferências pela própria instância do painel para acessar seus padrões.")
                : page.resetStatus.length ? page.resetStatus
                : !page.hasCustomValues ? qsTr("Todas as preferências deste painel já estão nos padrões.")
                : qsTr("A restauração só será salva ao clicar em Aplicar. Você pode revisar ou descartar a alteração antes de confirmar.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
    }
}
