/* SPDX-License-Identifier: GPL-3.0-or-later */
import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import org.kde.ksvg as KSvg
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC

Window {
    id: window
    objectName: "classicPanelPreview"
    width: 1440
    height: previewControls ? 328 : 64
    visible: true
    color: "#c1c1c1"
    title: "IRIX Classic — native Plasma preview"

    KSvg.Svg { id: nativeSwitch; objectName: "nativeSwitchSvg"; imagePath: "widgets/switch" }
    KSvg.Svg { id: nativeSlider; objectName: "nativeSliderSvg"; imagePath: "widgets/slider" }
    KSvg.Svg { id: nativeList; objectName: "nativeListSvg"; imagePath: "widgets/listitem" }
    KSvg.Svg { id: previewClockSvg; imagePath: artworkRoot + "/widgets/clock.svg" }

    component PreviewHand: KSvg.SvgItem {
        id: previewHand
        required property string pivotId
        required property real dialScale
        required property real angle
        svg: previewClockSvg
        readonly property rect pivot: svg.elementRect(pivotId)
        readonly property rect bounds: svg.elementRect(elementId)
        readonly property real pivotX: (pivot.x - bounds.x + pivot.width / 2) * dialScale
        readonly property real pivotY: (pivot.y - bounds.y + pivot.height / 2) * dialScale
        width: naturalSize.width * dialScale
        height: naturalSize.height * dialScale
        x: parent.width / 2 - pivotX
        y: parent.height / 2 - pivotY
        transform: Rotation { angle: previewHand.angle; origin.x: previewHand.pivotX; origin.y: previewHand.pivotY }
    }

    KSvg.FrameSvgItem {
        id: panel
        objectName: "panelHousing"
        width: parent.width
        height: 64
        imagePath: artworkRoot + "/widgets/panel-background.svg"
        smooth: false
        RowLayout {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 4
            // Same location and compact launch group as the Classic layout.
            Item {
                Layout.preferredWidth: 236
                Layout.fillHeight: true
                Row {
                    anchors.centerIn: parent
                    spacing: 4
                    Repeater {
                        model: [
                            {name: "computer", caption: "Applications"},
                            {name: "internet-web-browser", caption: "Web"},
                            {name: "system-file-manager", caption: "Files"},
                            {name: "utilities-terminal", caption: "Console"}
                        ]
                        // Each production launcher owns a separate raised plate.
                        // Actions and configuration use the real applet hosts.
                        delegate: MouseArea {
                            required property var modelData
                            width: 56
                            height: 56
                            hoverEnabled: true
                            activeFocusOnTab: true
                            Accessible.name: modelData.caption
                            Accessible.role: Accessible.Button
                            KSvg.FrameSvgItem {
                                anchors.fill: parent
                                anchors.margins: 2
                                imagePath: artworkRoot + "/widgets/button.svg"
                                prefix: parent.pressed ? "pressed" : (parent.containsMouse ? "hover" : "normal")
                            }
                            Kirigami.Icon {
                                anchors.centerIn: parent
                                anchors.horizontalCenterOffset: parent.pressed ? 1 : 0
                                anchors.verticalCenterOffset: parent.pressed ? 1 : 0
                                width: 32
                                height: 32
                                source: modelData.name
                                active: false
                            }
                        }
                    }
                }
            }
            KSvg.FrameSvgItem {
                objectName: "previewIconboxHousing"
                Layout.fillWidth: true
                Layout.fillHeight: true
                imagePath: artworkRoot + "/widgets/iconbox.svg"
                smooth: false
                KSvg.FrameSvgItem {
                    objectName: "previewIconboxHeading"
                    x: 3
                    y: 3
                    width: parent.width - 6
                    height: 8
                    imagePath: artworkRoot + "/widgets/iconbox.svg"
                    prefix: "heading"
                    smooth: false
                    clip: true
                    Text {
                        anchors { fill: parent; leftMargin: 4; bottomMargin: 1 }
                        text: "Iconbox"
                        font.pixelSize: 8
                        color: "#41413b"
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                Row {
                    x: 3
                    y: 11
                    height: parent.height - 14
                    spacing: 0
                    ControlTile { objectName: "normalTask"; text: "Console"; iconName: "utilities-terminal" }
                    ControlTile { objectName: "activeTask"; text: "Editor"; iconName: "text-editor"; checked: true }
                    ControlTile { objectName: "minimizedTask"; text: "Files"; iconName: "system-file-manager"; baseState: "minimized" }
                    ControlTile { text: "Browser"; iconName: "internet-web-browser" }
                    ControlTile { text: "Settings"; iconName: "preferences-system" }
                }
            }
            Item {
                Layout.preferredWidth: 134
                Layout.fillHeight: true
                Row {
                    anchors.centerIn: parent
                    spacing: 4
                    Repeater {
                        model: 2
                        delegate: Item {
                            required property int index
                            width: 57
                            height: 52
                            // Illustrative windows beneath the frame, matching
                            // the stock pager's actual stacking order.
                            Rectangle {
                                z: 1
                                x: 8; y: 9; width: 29; height: 18
                                color: index === 0 ? "#789c9c" : "#aaa9a2"
                                border.color: "#41413b"
                            }
                            Rectangle { z: 1; x: 26; y: 25; width: 23; height: 14; color: "#aaa9a2"; border.color: "#41413b" }
                            KSvg.FrameSvgItem {
                                anchors.fill: parent
                                z: 2
                                imagePath: artworkRoot + "/widgets/pager.svg"
                                prefix: parent.index === 0 ? "active" : "normal"
                            }
                        }
                    }
                }
            }
            KSvg.FrameSvgItem {
                Layout.preferredWidth: 198
                Layout.fillHeight: true
                imagePath: artworkRoot + "/widgets/instrument.svg"
                prefix: "normal"
                KSvg.FrameSvgItem {
                    anchors.fill: parent
                    anchors.margins: 4
                    imagePath: artworkRoot + "/widgets/instrument-well.svg"
                }
                Row {
                    anchors.centerIn: parent
                    spacing: 3
                    Repeater {
                        model: ["network-wireless", "preferences-system-bluetooth", "audio-volume-high", "battery", "go-up"]
                        delegate: PC.ToolButton {
                            required property string modelData
                            width: 34
                            height: 38
                            icon.name: modelData
                        }
                    }
                }
            }
            Item {
                id: previewClock
                Layout.preferredWidth: 64
                Layout.fillHeight: true
                KSvg.FrameSvgItem {
                    anchors.fill: parent
                    imagePath: artworkRoot + "/widgets/instrument.svg"
                    prefix: previewClockMouse.pressed ? "pressed" : "normal"
                }
                KSvg.FrameSvgItem {
                    anchors.fill: parent
                    anchors.margins: 4
                    imagePath: artworkRoot + "/widgets/instrument-well.svg"
                }
                Item {
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: previewClockMouse.pressed ? 1 : 0
                    anchors.verticalCenterOffset: previewClockMouse.pressed ? 1 : 0
                    width: 42
                    height: 42
                    KSvg.SvgItem {
                        id: previewClockFace
                        anchors.fill: parent
                        svg: previewClockSvg
                        elementId: "ClockFace"
                    }
                    PreviewHand {
                        elementId: "HourHand"
                        pivotId: "hint-hourhand-rotation-center-offset"
                        dialScale: previewClockFace.width / Math.max(1, previewClockFace.naturalSize.width)
                        angle: 180 + 10 * 30 + 10 / 2
                    }
                    PreviewHand {
                        elementId: "MinuteHand"
                        pivotId: "hint-minutehand-rotation-center-offset"
                        dialScale: previewClockFace.width / Math.max(1, previewClockFace.naturalSize.width)
                        angle: 180 + 10 * 6
                    }
                    KSvg.SvgItem {
                        anchors.centerIn: parent
                        width: naturalSize.width * previewClockFace.width / Math.max(1, previewClockFace.naturalSize.width)
                        height: width
                        svg: previewClockSvg
                        elementId: "HandCenterScrew"
                    }
                }
                MouseArea { id: previewClockMouse; anchors.fill: parent }
            }
        }
    }

    Item {
        id: gallery
        visible: previewControls
        x: 16; y: 84
        width: parent.width - 32
        height: 225
        Text { text: "Plasma native controls — gallery only; no network services are called"; color: "#000000"; font.pixelSize: 14 }
        Column {
            x: 0; y: 38; spacing: 18
            PC.Switch { objectName: "wifiSwitch"; text: "Wi-Fi" }
            PC.Switch { objectName: "bluetoothSwitch"; text: "Bluetooth"; checked: true }
            PC.Switch { text: "Unavailable"; checked: true; enabled: false }
        }
        Column {
            x: 260; y: 38; spacing: 16
            Text { text: "Volume / horizontal"; color: "#000000" }
            PC.Slider { objectName: "horizontalSlider"; width: 260; from: 0; to: 100; value: 35 }
            PC.ItemDelegate {
                objectName: "listEntry"
                text: "Network devices"
                width: 260
                height: 40
                onClicked: highlighted = !highlighted
            }
        }
        Column {
            x: 570; y: 38; spacing: 8
            Text { text: "Brightness / vertical"; color: "#000000" }
            PC.Slider { objectName: "verticalSlider"; orientation: Qt.Vertical; height: 130; from: 0; to: 100; value: 65 }
        }
        Column {
            x: 780; y: 38; spacing: 16
            PC.Button { objectName: "commandButton"; text: "Apply" }
            PC.ToolButton { objectName: "trayButton"; icon.name: "network-wireless"; text: "Tray control" }
        }
    }
}
