// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.plasma.configuration
import org.kde.plasma.plasmoid
import org.kde.plasma.workspace.calendar as PlasmaCalendar

ConfigModel {
    id: configModel
    ConfigCategory { name: qsTr("Relógio e calendário"); icon: "preferences-system-time"; source: "ConfigInstruments.qml" }
    ConfigCategory { name: qsTr("Monitor e gr_osview"); icon: "utilities-system-monitor"; source: "ConfigMonitor.qml" }
    ConfigCategory { name: qsTr("Correio e comandos"); icon: "utilities-terminal"; source: "ConfigCommands.qml" }
    ConfigCategory { name: qsTr("Iconbox"); icon: "preferences-system-windows"; source: "ConfigIconbox.qml" }
    ConfigCategory { name: qsTr("Aplicativos fixados"); icon: "applications-other"; source: "ConfigApplications.qml" }
    ConfigCategory { name: qsTr("Pager"); icon: "preferences-desktop-virtual"; source: "ConfigPager.qml" }
    ConfigCategory { name: qsTr("Bandeja e notificações"); icon: "preferences-desktop-notification"; source: "ConfigTray.qml" }
    ConfigCategory { name: qsTr("Interação e atividade"); icon: "preferences-system-power-management"; source: "ConfigActivity.qml" }
    ConfigCategory { name: qsTr("Padrões do painel"); icon: "edit-undo"; source: "ConfigDefaults.qml" }

    // Use each selected provider's own KDE configuration UI. Enabling a source
    // is separate from choosing its holiday regions or connected calendars.
    readonly property PlasmaCalendar.EventPluginsManager eventPluginsManager: PlasmaCalendar.EventPluginsManager {
        Component.onCompleted: populateEnabledPluginsList(Plasmoid.configuration.calendarPlugins)
    }
    readonly property Instantiator eventPluginCategories: Instantiator {
        model: configModel.eventPluginsManager.model
        delegate: ConfigCategory {
            required property string display
            required property string decoration
            required property string configUi
            required property string pluginId
            name: display
            icon: decoration
            source: configUi
            includeMargins: false
            visible: configUi.length > 0 && Plasmoid.configuration.calendarPlugins.indexOf(pluginId) >= 0
        }
        onObjectAdded: (index, object) => configModel.appendCategory(object)
        onObjectRemoved: (index, object) => configModel.removeCategory(object)
    }
}
