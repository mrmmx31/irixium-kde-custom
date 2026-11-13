// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM
import org.kde.plasma.plasmoid
import org.kde.plasma.private.digitalclock as Clock
import org.kde.plasma.workspace.calendar as Calendar
import "ConfigUtils.js" as ConfigUtils

KCM.SimpleKCM {
    id: page
    objectName: "domainosClockConfigPage"
    property alias cfg_timeZones: timeZones.selectedTimeZones
    property var cfg_calendarPlugins: []
    readonly property int availableCalendarProviders: providers.model.rowCount()
    readonly property int selectedCalendarProviders: ConfigUtils.copy(cfg_calendarPlugins).length
    readonly property string calendarSelectionStatus: selectedCalendarProviders > 0
        ? qsTr("%1 fonte(s) selecionada(s). Aplicar habilita a agenda neste painel.").arg(selectedCalendarProviders)
        : qsTr("Nenhuma fonte selecionada: o painel mostra o calendário sem eventos.")

    function selectCalendarProvider(pluginId, selected) {
        const chosen = ConfigUtils.copy(cfg_calendarPlugins);
        const index = chosen.indexOf(pluginId);
        if (selected && index < 0) chosen.push(pluginId);
        else if (!selected && index >= 0) chosen.splice(index, 1);
        cfg_calendarPlugins = chosen;
    }

    Clock.TimeZoneModel { id: timeZones }
    Clock.TimeZoneFilterProxy {
        id: availableZones
        sourceModel: timeZones
        filterString: zoneSearch.text
    }
    // Enumerate provider metadata only. Enabling plugins here would access event
    // sources before the user applies the choice; that belongs to the calendar.
    Calendar.EventPluginsManager { id: providers; enabledPlugins: [] }

    footer: DomainOSCategoryDefaults {
        targetPage: page
        configuration: Plasmoid.configuration
    }

    Kirigami.FormLayout {
        QQC.Label {
            text: qsTr("O relógio usa a hora real da sessão. A data segue o idioma e o formato regional do KDE. Não há alteração do fuso do sistema nem de contas nesta página.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.TextField {
            id: zoneSearch
            objectName: "domainosTimeZoneSearch"
            placeholderText: qsTr("Pesquisar cidade ou fuso")
            Kirigami.FormData.label: qsTr("Fusos consultados:")
            Layout.fillWidth: true
        }
        QQC.ScrollView {
            id: zoneScroll
            Layout.fillWidth: true; Layout.preferredWidth: 460; Layout.preferredHeight: 230
            implicitHeight: 230
            clip: true
            ListView {
                id: zones
                width: zoneScroll.availableWidth; height: zoneScroll.availableHeight
                clip: true
                model: availableZones
                delegate: QQC.CheckDelegate {
                    required property var model
                    objectName: "domainosTimeZoneChoice_" + model.timeZoneId
                    width: zones.width
                    text: model.isLocalTimeZone ? qsTr("Local — seguir a sessão") : model.city + " · " + model.timeZoneId
                    checked: model.checked
                    onToggled: model.checked = checked
                }
            }
        }
        QQC.Label {
            text: qsTr("O botão do relógio consulta estes fusos. O calendário continua no botão da data.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        ColumnLayout {
            Kirigami.FormData.label: qsTr("Fontes de agenda:")
            Layout.fillWidth: true
            Repeater {
                model: providers.model
                delegate: QQC.CheckBox {
                    required property var model
                    objectName: "domainosCalendarProviderChoice_"+model.pluginId
                    text: model.display
                    checked: ConfigUtils.copy(page.cfg_calendarPlugins).indexOf(model.pluginId) >= 0
                    onToggled: page.selectCalendarProvider(model.pluginId, checked)
                }
            }
            QQC.Label {
                visible: page.availableCalendarProviders === 0
                text: qsTr("Nenhum provedor de eventos instalado. O calendário mensal continua disponível.")
                wrapMode: Text.Wrap; Layout.fillWidth: true
            }
        }
        QQC.Label {
            objectName: "domainosCalendarSelectionStatus"
            text: page.calendarSelectionStatus
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        QQC.Label {
            text: qsTr("Marque as fontes de agenda e aplique. As páginas das fontes escolhidas permitem selecionar regiões de feriados ou calendários existentes do KDE PIM. Não há criação de conta nem importação de eventos ao selecionar uma fonte.")
            wrapMode: Text.Wrap; Layout.fillWidth: true
        }
    }
}
