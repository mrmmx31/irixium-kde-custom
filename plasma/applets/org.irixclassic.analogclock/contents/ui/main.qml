/*
    SPDX-FileCopyrightText: 2012 Viranch Mehta <viranch.mehta@gmail.com>
    SPDX-FileCopyrightText: 2012 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2013 David Edmundson <davidedmundson@kde.org>

    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick 2.15
import QtQuick.Layouts 1.1

import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.core as PlasmaCore
import org.kde.ksvg 1.0 as KSvg
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.plasma5support 2.0 as P5Support
import org.kde.kirigami 2.20 as Kirigami

import org.kde.plasma.workspace.calendar 2.0 as PlasmaCalendar

PlasmoidItem {
    id: analogclock

    width: Kirigami.Units.gridUnit * 15
    height: Kirigami.Units.gridUnit * 15

    readonly property string currentTime: Qt.locale().toString(dataSource.data["Local"]["DateTime"], Qt.locale().timeFormat(Locale.LongFormat))
    readonly property string currentDate: Qt.locale().toString(dataSource.data["Local"]["DateTime"], Qt.locale().dateFormat(Locale.LongFormat).replace(/(^dddd.?\s)|(,?\sdddd$)/, ""))

    property int hours
    property int minutes
    property int seconds
    property bool showSecondsHand: Plasmoid.configuration.showSecondHand
    property bool showTimezone: Plasmoid.configuration.showTimezoneString
    property int tzOffset

    Plasmoid.backgroundHints: "NoBackground";
    preferredRepresentation: compactRepresentation

    toolTipMainText: Qt.locale().toString(dataSource.data["Local"]["DateTime"],"dddd")
    toolTipSubText: `${currentTime}\n${currentDate}`


    function dateTimeChanged() {
        var currentTZOffset = dataSource.data["Local"]["Offset"] / 60;
        if (currentTZOffset !== tzOffset) {
            tzOffset = currentTZOffset;
            Date.timeZoneUpdated(); // inform the QML JS engine about TZ change
        }
    }

    P5Support.DataSource {
        id: dataSource
        engine: "time"
        connectedSources: "Local"
        interval: showSecondsHand || (analogclock.compactRepresentationItem && analogclock.compactRepresentationItem.containsMouse) ? 1000 : 30000
        onDataChanged: {
            var date = new Date(data["Local"]["DateTime"]);
            hours = date.getHours();
            minutes = date.getMinutes();
            seconds = date.getSeconds();
        }
        Component.onCompleted: {
            dataChanged();
        }
    }

    compactRepresentation: MouseArea {
        id: representation
        objectName: "classicClock"

        readonly property int pressOffset: pressed ? 1 : 0

        KSvg.FrameSvgItem {
            id: clockSocket
            objectName: "classicClockSocket"
            anchors.fill: parent
            imagePath: "widgets/instrument"
            prefix: representation.pressed ? "pressed" : "normal"
        }

        KSvg.FrameSvgItem {
            id: clockWell
            objectName: "classicClockWell"
            anchors {
                fill: parent
                leftMargin: clockSocket.margins.left
                rightMargin: clockSocket.margins.right
                topMargin: clockSocket.margins.top
                bottomMargin: clockSocket.margins.bottom
            }
            imagePath: "widgets/instrument-well"
            prefix: ["normal", ""]
        }

        Layout.minimumWidth: Plasmoid.formFactor !== PlasmaCore.Types.Vertical ? representation.height : Kirigami.Units.gridUnit
        Layout.minimumHeight: Plasmoid.formFactor === PlasmaCore.Types.Vertical ? representation.width : Kirigami.Units.gridUnit

        property bool wasExpanded

        activeFocusOnTab: true
        hoverEnabled: true

        Accessible.name: Plasmoid.title
        Accessible.description: i18nc("@info:tooltip", "Current time is %1; Current date is %2", analogclock.currentTime, analogclock.currentDate)
        Accessible.role: Accessible.Button

        onPressed: wasExpanded = analogclock.expanded
        onClicked: analogclock.expanded = !wasExpanded

        KSvg.Svg {
            id: clockSvg

            property double naturalHorizontalHandShadowOffset: estimateHorizontalHandShadowOffset()
            property double naturalVerticalHandShadowOffset: estimateVerticalHandShadowOffset()

            imagePath: "widgets/clock"
            function estimateHorizontalHandShadowOffset() {
                var id = "hint-hands-shadow-offset-to-west";
                if (hasElement(id)) {
                    return -elementSize(id).width;
                }
                id = "hint-hands-shadows-offset-to-east";
                if (hasElement(id)) {
                    return elementSize(id).width;
                }
                return 0;
            }
            function estimateVerticalHandShadowOffset() {
                var id = "hint-hands-shadow-offset-to-north";
                if (hasElement(id)) {
                    return -elementSize(id).height;
                }
                id = "hint-hands-shadow-offset-to-south";
                if (hasElement(id)) {
                    return elementSize(id).height;
                }
                return 0;
            }

            onRepaintNeeded: {
                naturalHorizontalHandShadowOffset = estimateHorizontalHandShadowOffset();
                naturalVerticalHandShadowOffset = estimateVerticalHandShadowOffset();
            }
        }

        Item {
            id: clockContent
            objectName: "classicClockContent"
            x: clockWell.x + clockWell.margins.left + representation.pressOffset
            y: clockWell.y + clockWell.margins.top + representation.pressOffset
            width: Math.max(1, clockWell.width - clockWell.margins.left - clockWell.margins.right)
            height: Math.max(1, clockWell.height - clockWell.margins.top - clockWell.margins.bottom)

            Item {
                id: clock

                anchors {
                    top: parent.top
                    bottom: showTimezone ? timezoneBg.top : parent.bottom
                    bottomMargin: showTimezone ? 2 : 0
                    horizontalCenter: parent.horizontalCenter
                }
                width: parent.width

                readonly property double svgScale: face.width / face.naturalSize.width
                readonly property double horizontalShadowOffset:
                    Math.round(clockSvg.naturalHorizontalHandShadowOffset * svgScale) + Math.round(clockSvg.naturalHorizontalHandShadowOffset * svgScale) % 2
                readonly property double verticalShadowOffset:
                    Math.round(clockSvg.naturalVerticalHandShadowOffset * svgScale) + Math.round(clockSvg.naturalVerticalHandShadowOffset * svgScale) % 2

                KSvg.SvgItem {
                    id: face
                    anchors.centerIn: parent
                    width: Math.min(parent.width, parent.height)
                    height: Math.min(parent.width, parent.height)
                    svg: clockSvg
                    elementId: "ClockFace"
                }

                Hand {
                    elementId: "HourHandShadow"
                    rotationCenterHintId: "hint-hourhandshadow-rotation-center-offset"
                    horizontalRotationOffset: clock.horizontalShadowOffset
                    verticalRotationOffset: clock.verticalShadowOffset
                    rotation: 180 + hours * 30 + (minutes/2)
                    svgScale: clock.svgScale

                }
                Hand {
                    elementId: "HourHand"
                    rotationCenterHintId: "hint-hourhand-rotation-center-offset"
                    rotation: 180 + hours * 30 + (minutes/2)
                    svgScale: clock.svgScale
                }

                Hand {
                    elementId: "MinuteHandShadow"
                    rotationCenterHintId: "hint-minutehandshadow-rotation-center-offset"
                    horizontalRotationOffset: clock.horizontalShadowOffset
                    verticalRotationOffset: clock.verticalShadowOffset
                    rotation: 180 + minutes * 6
                    svgScale: clock.svgScale
                }
                Hand {
                    elementId: "MinuteHand"
                    rotationCenterHintId: "hint-minutehand-rotation-center-offset"
                    rotation: 180 + minutes * 6
                    svgScale: clock.svgScale
                }

                Hand {
                    visible: showSecondsHand
                    elementId: "SecondHandShadow"
                    rotationCenterHintId: "hint-secondhandshadow-rotation-center-offset"
                    horizontalRotationOffset: clock.horizontalShadowOffset
                    verticalRotationOffset: clock.verticalShadowOffset
                    rotation: 180 + seconds * 6
                    svgScale: clock.svgScale
                }
                Hand {
                    visible: showSecondsHand
                    elementId: "SecondHand"
                    rotationCenterHintId: "hint-secondhand-rotation-center-offset"
                    rotation: 180 + seconds * 6
                    svgScale: clock.svgScale
                }

                KSvg.SvgItem {
                    id: center
                    anchors.centerIn: clock
                    width: naturalSize.width * clock.svgScale
                    height: naturalSize.height * clock.svgScale
                    svg: clockSvg
                    elementId: "HandCenterScrew"
                    z: 1000
                }

                KSvg.SvgItem {
                    anchors.fill: face
                    width: naturalSize.width * clock.svgScale
                    height: naturalSize.height * clock.svgScale
                    svg: clockSvg
                    elementId: "Glass"
                }
            }

            KSvg.FrameSvgItem {
                id: timezoneBg

                anchors {
                    horizontalCenter: parent.horizontalCenter
                    bottom: parent.bottom
                    bottomMargin: 0
                }
                width: Math.min(parent.width, timezoneText.implicitWidth + margins.right + margins.left)
                height: timezoneText.implicitHeight + margins.top + margins.bottom
                visible: showTimezone

                imagePath: "widgets/instrument-well"
                prefix: ["normal", ""]

                PlasmaComponents.Label {
                    id: timezoneText
                    x: timezoneBg.margins.left
                    y: timezoneBg.margins.top
                    width: Math.max(1, timezoneBg.width - timezoneBg.margins.left - timezoneBg.margins.right)
                    elide: Text.ElideRight
                    text: dataSource.data["Local"]["Timezone"]
                    textFormat: Text.PlainText
                }
            }
        }
    }

    fullRepresentation: PlasmaCalendar.MonthView {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 22
        Layout.maximumWidth: Kirigami.Units.gridUnit * 80
        Layout.minimumHeight: Kirigami.Units.gridUnit * 22
        Layout.maximumHeight: Kirigami.Units.gridUnit * 40

        readonly property var appletInterface: analogclock

        today: dataSource.data["Local"]["DateTime"]
    }

    Component.onCompleted: {
        tzOffset = new Date().getTimezoneOffset();
        dataSource.onDataChanged.connect(dateTimeChanged);
    }
}
