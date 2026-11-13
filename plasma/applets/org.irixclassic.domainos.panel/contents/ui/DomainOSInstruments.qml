// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasma5support as P5Support
import org.kde.plasma.workspace.calendar as PlasmaCalendar
import org.kde.ksysguard.sensors as Sensors
import org.kde.ksysguard.formatter as SensorFormatter
import "../../../org.irixclassic.grosview/contents/ui" as ExistingMonitor

// Native data and popup controller. The approved panel supplies its existing
// four faces; loading this controller does not add a second drawing or panel.
Item {
    id: instruments
    objectName: "domainosLiveInstruments"
    property QtObject domainosPalette: fallbackPalette
    DomainOSPalette { id: fallbackPalette }
    property bool monitoringEnabled: true
    property int popupLocation: PlasmaCore.Types.BottomEdge
    property var timeZones: ["Local", "UTC"]
    // Only explicitly selected calendar providers are ever activated.
    property var calendarPlugins: []
    // A connected provider supplies aggregate state. Neither an installed mail
    // client nor a missing source means zero unread messages.
    property QtObject mailStateProvider: null
    property string metric: "network"
    property string networkInterface: "all"
    property string customSensorId: ""
    property string customSecondarySensorId: ""
    property int sampleInterval: 1000
    readonly property int effectiveSampleInterval: Math.max(1000,sampleInterval)
    property int historyLength: 60
    property real observedPeak: 0
    property var primaryHistory: []
    property var secondaryHistory: []
    property var primarySampleTimes: []
    property var secondarySampleTimes: []
    signal mailRequested()

    readonly property var localTimeData: clockSource.data["Local"] || ({})
    readonly property bool timeAvailable: monitoringEnabled
        && localTimeData["DateTime"] !== undefined
        && Number.isFinite(new Date(localTimeData["DateTime"]).getTime())
    readonly property date currentDateTime: timeAvailable
        ? new Date(localTimeData["DateTime"]) : new Date(NaN)
    readonly property int clockHour: timeAvailable ? currentDateTime.getHours() : 0
    readonly property int clockMinute: timeAvailable ? currentDateTime.getMinutes() : 0
    readonly property int clockSecond: timeAvailable ? currentDateTime.getSeconds() : 0
    readonly property real hourAngle: clockHour*30+clockMinute/2
    readonly property real minuteAngle: clockMinute*6+clockSecond/10
    readonly property string fullDateText: timeAvailable
        ? Qt.formatDate(currentDateTime, Qt.locale(), Locale.LongFormat) : qsTr("Time unavailable")
    readonly property string timeText: timeAvailable
        ? Qt.formatTime(currentDateTime, Qt.locale(), Locale.LongFormat) : "—"
    readonly property string dateText: timeAvailable
        ? compactDate(currentDateTime)+"\n"+Qt.formatDate(currentDateTime, "ddd") : "—"
    readonly property string localeName: Qt.locale().name
    readonly property string localTimezone: localTimeData["Timezone"] || ""
    readonly property string primarySensorId: sensorIdentifiers()[0]
    readonly property string secondarySensorId: sensorIdentifiers()[1]
    readonly property bool primaryAvailable: sensorAvailable(primarySensor)
    readonly property bool secondaryAvailable: secondarySensorId.length > 0 && sensorAvailable(secondarySensor)
    readonly property int primaryUnit: primarySensor.unit
    readonly property int secondaryUnit: secondarySensor.unit
    // A shared graph accepts the same native unit only. Different unit scales
    // are not silently converted or represented as comparable fractions.
    readonly property bool unitsCompatible: !secondarySensorId.length || primaryUnit === secondaryUnit
    readonly property bool metricAvailable: primaryAvailable
        && (!secondarySensorId.length || secondaryAvailable) && unitsCompatible
    readonly property var primaryValue: primaryAvailable ? Number(primarySensor.value) : null
    readonly property var secondaryValue: secondaryAvailable ? Number(secondarySensor.value) : null
    readonly property string primaryText: primaryAvailable ? primarySensor.formattedValue : "—"
    readonly property string secondaryText: secondaryAvailable ? secondarySensor.formattedValue : "—"
    readonly property var scaleMaximum: metricAvailable
        ? (metric === "cpu" || metric === "memory" ? 100 : observedPeak) : null
    readonly property string scaleText: metricAvailable && scaleMaximum > 0
        ? SensorFormatter.Formatter.formatValue(scaleMaximum,primarySensor.unit) : "—"
    readonly property var primaryFraction: metricAvailable
        ? (scaleMaximum > 0 ? Math.min(1,Math.max(0,primaryValue/scaleMaximum)) : 0) : null
    readonly property var secondaryFraction: metricAvailable && secondaryAvailable
        ? (scaleMaximum > 0 ? Math.min(1,Math.max(0,secondaryValue/scaleMaximum)) : 0) : null
    readonly property string metricStatus: metricAvailable ? qsTr("Live system measurements")
        : primaryAvailable && secondaryAvailable && !unitsCompatible
            ? qsTr("Measurement unavailable: sensor units differ. Select matching units or remove the secondary sensor.")
            : qsTr("Measurement unavailable")
    readonly property string metricScope: metric === "network"
        ? (networkInterface === "all" ? qsTr("All network interfaces · receive / send") : qsTr("%1 · receive / send").arg(networkInterface))
        : metric === "disk" ? qsTr("All disks · read / write")
        : metric === "cpu" ? qsTr("CPU usage") : metric === "memory" ? qsTr("Physical memory usage")
        : customSensorId+(customSecondarySensorId.length ? " / "+customSecondarySensorId : "")
    readonly property bool clockPopupVisible: clockPopup.visible
    readonly property bool calendarPopupVisible: calendarPopup.visible
    readonly property bool monitorPopupVisible: monitorPopup.visible
    // The native model and enabledPlugins share pluginsChanged. Keep metadata
    // IDs separate so loading a selected provider cannot invalidate its own
    // enabledPlugins binding through the model's notification.
    property var _availableCalendarPluginIds: []
    readonly property var availableCalendarPlugins: _availableCalendarPluginIds
    function refreshCalendarPluginMetadata() {
        const model = eventPlugins.model
        const result = []
        for (let row = 0; row < model.rowCount(); row++) result.push(model.get(row,"pluginId"))
        if (result.length !== _availableCalendarPluginIds.length
            || result.some((plugin,index) => plugin !== _availableCalendarPluginIds[index]))
            _availableCalendarPluginIds = result
    }
    Component.onCompleted: refreshCalendarPluginMetadata()
    readonly property var activeCalendarPlugins: calendarPlugins.filter(plugin => availableCalendarPlugins.indexOf(plugin) >= 0)
    readonly property bool agendaConfigured: activeCalendarPlugins.length > 0
    readonly property bool agendaProvidersUnavailable: calendarPlugins.length > 0 && !agendaConfigured
    readonly property bool mailStateAvailable: mailStateProvider !== null
        && mailStateProvider.available === true
        && typeof mailStateProvider.unreadCount === "number"
        && Number.isInteger(mailStateProvider.unreadCount) && mailStateProvider.unreadCount >= 0
    readonly property var mailUnreadCount: mailStateAvailable ? mailStateProvider.unreadCount : null
    readonly property string mailStatusText: mailStateProvider !== null && mailStateProvider.statusText
        ? mailStateProvider.statusText : qsTr("Contagem de correio indisponível")

    function compactDate(date, locale) {
        // Keep the locale's day/month order and separators. The full localized
        // date is available in the calendar and the instrument's tooltip.
        const region = locale || Qt.locale()
        let format = region.dateFormat(Locale.ShortFormat)
        format = format.replace(/^[yY]{2,4}([./\s-])*/, "")
            .replace(/([./\s-])*[yY]{2,4}$/, "")
        return region.toString(date, format)
    }
    function sensorIdentifiers() {
        if (metric === "network") {
            const device = networkInterface.length ? networkInterface : "all"
            return ["network/"+device+"/download", "network/"+device+"/upload"]
        }
        if (metric === "disk") return ["disk/all/read", "disk/all/write"]
        if (metric === "cpu") return ["cpu/all/usage", ""]
        if (metric === "memory") return ["memory/physical/usedPercent", ""]
        return [customSensorId, customSecondarySensorId]
    }
    function sensorAvailable(sensor) {
        return monitoringEnabled && sensor.enabled && sensor.sensorId.length > 0
            && sensor.hasCurrentValue
            && sensor.status === Sensors.Sensor.Ready
            && sensor.value !== undefined && sensor.value !== null
            && Number.isFinite(Number(sensor.value)) && Number(sensor.value) >= 0
    }
    function recordSample(sensor, secondary) {
        // Read both native sources here: derived availability bindings may not
        // yet have updated during valueChanged dispatch.
        if (!sensorAvailable(sensor) || !sensorAvailable(primarySensor)
            || primarySensor.sensorId !== primarySensorId
            || (secondarySensorId.length && (!sensorAvailable(secondarySensor)
                || secondarySensor.sensorId !== secondarySensorId
                || primarySensor.unit !== secondarySensor.unit))) return
        // Use the signal source, not a derived binding which may still hold the
        // preceding value during native valueChanged signal dispatch.
        const value = Number(sensor.value)
        if (metric !== "cpu" && metric !== "memory") observedPeak = Math.max(observedPeak,value)
        const values = (secondary ? secondaryHistory : primaryHistory).slice()
        const times = (secondary ? secondarySampleTimes : primarySampleTimes).slice()
        values.push(value); times.push(Date.now())
        const count = Math.max(2,Math.min(3600,historyLength))
        while (values.length > count) { values.shift(); times.shift() }
        if (secondary) { secondaryHistory = values; secondarySampleTimes = times }
        else { primaryHistory = values; primarySampleTimes = times }
    }
    function resetMeasurements() {
        observedPeak = 0
        primaryHistory = []; secondaryHistory = []
        primarySampleTimes = []; secondarySampleTimes = []
    }
    function timeForZone(zone) {
        const data = clockSource.data[zone]
        if (!data || !data["DateTime"]) return "—"
        const date = new Date(data["DateTime"])
        const offset = Number(data["Offset"])
        if (!Number.isFinite(date.getTime()) || !Number.isFinite(offset)) return "—"
        const corrected = new Date(date.getTime()+date.getTimezoneOffset()*60000+offset*1000)
        // The corrected Date still carries the process's local zone. Printing
        // its Qt "t" token would wrongly label a UTC clock with that local zone.
        const format = Qt.locale().timeFormat(Locale.LongFormat).replace(/\s*t{1,4}/g, "").trim()
        const abbreviation = data["Timezone Abbreviation"] || data["Timezone"] || zone
        return Qt.formatTime(corrected, format)+" "+abbreviation
    }
    function closePopups() { clockPopup.visible = false; calendarPopup.visible = false; monitorPopup.visible = false }
    DomainOSPopupToggle { id: clockToggle; showing: clockPopup.visible }
    DomainOSPopupToggle { id: calendarToggle; showing: calendarPopup.visible }
    DomainOSPopupToggle { id: monitorToggle; showing: monitorPopup.visible }
    function showClock(anchor) {
        const show = clockToggle.shouldOpen(anchor)
        closePopups(); clockPopup.visualParent = anchor; clockPopup.visible = show
    }
    function showCalendar(anchor) {
        const show = calendarToggle.shouldOpen(anchor)
        closePopups(); calendarPopup.visualParent = anchor
        if (timeAvailable) monthView.resetToToday()
        calendarPopup.visible = show
    }
    function showMonitor(anchor) {
        const show = monitorToggle.shouldOpen(anchor)
        closePopups(); monitorPopup.visualParent = anchor; monitorPopup.visible = show
    }
    function requestMail() { mailRequested() }
    function sensorSnapshot() {
        return {metric:metric, scope:metricScope, primarySensorId:primarySensorId,
            secondarySensorId:secondarySensorId, available:metricAvailable,
            unitsCompatible:unitsCompatible,statusText:metricStatus,
            primary:{status:primarySensor.status,available:primaryAvailable,value:primaryValue,
                formattedValue:primaryText,unit:primarySensor.unit,interval:primarySensor.updateInterval,
                rateLimitMilliseconds:primarySensor.updateRateLimit},
            secondary:{status:secondarySensor.status,available:secondaryAvailable,value:secondaryValue,
                formattedValue:secondaryText,unit:secondarySensor.unit,interval:secondarySensor.updateInterval,
                rateLimitMilliseconds:secondarySensor.updateRateLimit},
            scaleMaximum:scaleMaximum,primaryFraction:primaryFraction,secondaryFraction:secondaryFraction,
            primaryHistory:primaryHistory,secondaryHistory:secondaryHistory,
            scaleText:scaleText,primaryName:primarySensor.name,secondaryName:secondarySensor.name,
            primarySampleTimes:primarySampleTimes,secondarySampleTimes:secondarySampleTimes,
            samplingLimitMilliseconds:effectiveSampleInterval,
            requestedSamplingLimitMilliseconds:sampleInterval,
            clockIntervalMilliseconds:clockSource.interval,historySampleLimit:historyLength}
    }
    onPrimarySensorIdChanged: resetMeasurements()
    onSecondarySensorIdChanged: resetMeasurements()
    onPrimaryUnitChanged: resetMeasurements()
    onSecondaryUnitChanged: resetMeasurements()
    onMetricAvailableChanged: if (!metricAvailable) resetMeasurements()
    onMonitoringEnabledChanged: if (!monitoringEnabled) closePopups()

    P5Support.DataSource {
        id: clockSource
        objectName: "domainosTimeSource"
        engine: "time"
        connectedSources: instruments.monitoringEnabled
            ? ["Local"].concat(instruments.timeZones.filter(zone => zone !== "Local")) : []
        // The monitor's sampling preference must not slow the clock/fuses.
        interval: 1000
        onDataChanged: {
            const data = clockSource.data["Local"]
            if (data && data["Offset"] !== undefined) Date.timeZoneUpdated()
        }
    }
    Sensors.Sensor {
        id: primarySensor
        objectName: "domainosPrimarySensor"
        property int lastValueStatus: -1
        property bool hasCurrentValue: false
        sensorId: instruments.primarySensorId
        enabled: instruments.monitoringEnabled && sensorId.length > 0
        updateRateLimit: instruments.effectiveSampleInterval
        onSensorIdChanged: { lastValueStatus = -1; hasCurrentValue = false }
        onEnabledChanged: if (!enabled) hasCurrentValue = false
        onValueChanged: {
            // libksysguard forwards statusChanged to valueChanged and retains
            // the previous ID's value. A status transition is not a sample.
            if (status !== lastValueStatus) {
                lastValueStatus = status; hasCurrentValue = false; return
            }
            hasCurrentValue = status === Sensors.Sensor.Ready
            instruments.recordSample(primarySensor,false)
        }
    }
    Sensors.Sensor {
        id: secondarySensor
        objectName: "domainosSecondarySensor"
        property int lastValueStatus: -1
        property bool hasCurrentValue: false
        sensorId: instruments.secondarySensorId
        enabled: instruments.monitoringEnabled && sensorId.length > 0
        updateRateLimit: instruments.effectiveSampleInterval
        onSensorIdChanged: { lastValueStatus = -1; hasCurrentValue = false }
        onEnabledChanged: if (!enabled) hasCurrentValue = false
        onValueChanged: {
            if (status !== lastValueStatus) {
                lastValueStatus = status; hasCurrentValue = false; return
            }
            hasCurrentValue = status === Sensors.Sensor.Ready
            instruments.recordSample(secondarySensor,true)
        }
    }

    PlasmaCore.Dialog {
        id: clockPopup
        objectName: "domainosTimePopup"
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowDoesNotAcceptFocus
        location: instruments.popupLocation
        hideOnWindowDeactivate: true
        mainItem: Bevel {
            id: timeContent
            objectName: "domainosTimePopupContent"
            DomainOSControlPalette { target: timeContent }
            property QtObject domainosPalette: instruments.domainosPalette
            width: 390; height: 75+zoneRows.implicitHeight
            thickness: 2; face: instruments.domainosPalette.background
            Column {
                anchors.fill: parent; anchors.margins: 12; spacing: 8
                PlasmaComponents.Label { text: instruments.timeText; font.bold: true; font.pixelSize: 22 }
                Column {
                    id: zoneRows
                    spacing: 7
                    Repeater {
                        model: ["Local"].concat(instruments.timeZones.filter(zone => zone !== "Local"))
                        PlasmaComponents.Label {
                            required property string modelData
                            objectName: "domainosTimezone_"+modelData
                            text: (modelData === "Local" ? instruments.localTimezone || qsTr("Local") : modelData)
                                +"  "+instruments.timeForZone(modelData)
                            textFormat: Text.PlainText
                        }
                    }
                }
            }
        }
    }
    PlasmaCore.Dialog {
        id: calendarPopup
        objectName: "domainosCalendarPopup"
        type: PlasmaCore.Dialog.PopupMenu
        location: instruments.popupLocation
        hideOnWindowDeactivate: true
        mainItem: Bevel {
            id: calendarContent
            objectName: "domainosCalendarPopupContent"
            DomainOSControlPalette { target: calendarContent }
            property QtObject domainosPalette: instruments.domainosPalette
            width: instruments.agendaConfigured ? 700 : 390
            height: 420
            thickness: 2; face: instruments.domainosPalette.background
            RowLayout {
                anchors.fill: parent; anchors.margins: 12; spacing: 12
                ColumnLayout {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    PlasmaComponents.Label { text: instruments.fullDateText; Layout.fillWidth: true; wrapMode: Text.Wrap }
                    PlasmaComponents.Label {
                        visible: instruments.agendaProvidersUnavailable
                        text: qsTr("Configured calendar providers are unavailable")
                        Layout.fillWidth: true; wrapMode: Text.Wrap
                    }
                    PlasmaComponents.Label {
                        objectName: "domainosCalendarNoSource"
                        visible: instruments.calendarPlugins.length === 0
                        text: qsTr("Agenda sem fontes selecionadas. Escolha Fontes de agenda nas preferências do painel para mostrar os eventos.")
                        Layout.fillWidth: true; wrapMode: Text.Wrap
                    }
                    PlasmaCalendar.MonthView {
                        id: monthView
                        objectName: "domainosMonthView"
                        Layout.fillWidth: true; Layout.fillHeight: true
                        today: instruments.timeAvailable ? instruments.currentDateTime : new Date()
                        eventPluginsManager: eventPlugins
                        onCurrentDateChanged: agenda.updateEvents()
                    }
                }
                ColumnLayout {
                    id: agenda
                    objectName: "domainosAgenda"
                    visible: instruments.agendaConfigured
                    Layout.preferredWidth: 280; Layout.fillHeight: true
                    function updateEvents() {
                        events.model = instruments.agendaConfigured
                            ? monthView.daysModel.eventsForDate(monthView.currentDate) : []
                    }
                    PlasmaComponents.Label { text: qsTr("Events"); font.bold: true }
                    ListView {
                        id: events
                        objectName: "domainosAgendaEvents"
                        Layout.fillWidth: true; Layout.fillHeight: true
                        clip: true; model: []
                        delegate: PlasmaComponents.Label {
                            required property var modelData
                            width: ListView.view.width
                            text: (modelData.isAllDay ? "" : Qt.formatTime(modelData.startDateTime,Qt.locale(),Locale.ShortFormat)+"  ")+modelData.title
                            textFormat: Text.PlainText; wrapMode: Text.Wrap
                            bottomPadding: 10
                        }
                    }
                    PlasmaComponents.Label {
                        visible: events.count === 0
                        text: qsTr("No events supplied for this day")
                        Layout.fillWidth: true; wrapMode: Text.Wrap
                    }
                }
            }
        }
    }
    PlasmaCalendar.EventPluginsManager {
        id: eventPlugins
        objectName: "domainosCalendarProviders"
        // The model enumerates installed provider metadata, never accounts.
        // Absent providers are not passed to the native loader as if available.
        enabledPlugins: instruments.calendarPopupVisible ? instruments.activeCalendarPlugins : []
    }
    Connections {
        target: eventPlugins
        function onPluginsChanged() { instruments.refreshCalendarPluginMetadata() }
    }
    Connections {
        target: monthView.daysModel
        function onAgendaUpdated(updatedDate) {
            if (updatedDate.toDateString() === monthView.currentDate.toDateString()) agenda.updateEvents()
        }
    }
    PlasmaCore.Dialog {
        id: monitorPopup
        objectName: "domainosMonitorPopup"
        type: PlasmaCore.Dialog.PopupMenu
        flags: Qt.WindowDoesNotAcceptFocus
        location: instruments.popupLocation
        hideOnWindowDeactivate: true
        mainItem: Bevel {
            id: monitorContent
            objectName: "domainosMonitorPopupContent"
            DomainOSControlPalette { target: monitorContent }
            property QtObject domainosPalette: instruments.domainosPalette
            width: 430; height: 305
            thickness: 2; face: instruments.domainosPalette.background
            ColumnLayout {
                anchors.fill: parent; anchors.margins: 12; spacing: 5
                PlasmaComponents.Label { text: instruments.metricScope; Layout.fillWidth: true; wrapMode: Text.Wrap }
                PlasmaComponents.Label {
                    text: instruments.primaryText+(instruments.secondarySensorId.length ? " / "+instruments.secondaryText : "")
                        +" · "+instruments.metricStatus
                    Layout.fillWidth: true; wrapMode: Text.Wrap
                }
                Loader {
                    objectName: "domainosGrosviewLoader"
                    active: instruments.monitorPopupVisible
                    Layout.fillWidth: true; Layout.fillHeight: true
                    sourceComponent: ExistingMonitor.Grosview { objectName: "domainosExistingGrosview" }
                }
                PlasmaComponents.Label {
                    text: qsTr("%1 ms · up to %2 samples · scale: %3")
                        .arg(instruments.effectiveSampleInterval).arg(instruments.historyLength)
                        .arg(instruments.scaleText)
                    Layout.fillWidth: true; wrapMode: Text.Wrap
                }
            }
        }
    }
}
