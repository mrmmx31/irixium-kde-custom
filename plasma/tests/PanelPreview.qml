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

    KSvg.FrameSvgItem {
        id: panel
        objectName: "panelHousing"
        width: parent.width
        height: 64
        imagePath: artworkRoot + "/widgets/panel-background.svg"
        RowLayout {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 4
            // Same location and compact launch group as the Classic layout.
            KSvg.FrameSvgItem {
                Layout.preferredWidth: 236
                Layout.fillHeight: true
                imagePath: artworkRoot + "/widgets/button.svg"
                prefix: "normal"
                Row {
                    anchors.centerIn: parent
                    spacing: 2
                    Repeater {
                        model: [
                            {name: "computer", caption: "Applications"},
                            {name: "internet-web-browser", caption: "Web"},
                            {name: "system-file-manager", caption: "Files"},
                            {name: "utilities-terminal", caption: "Console"}
                        ]
                        // Surrounding launchers are schematic native controls;
                        // their actual applet models are tested in Plasma hosts.
                        delegate: PC.ToolButton {
                            required property var modelData
                            width: 55
                            height: 48
                            icon.name: modelData.name
                            icon.width: 32
                            icon.height: 32
                            Accessible.name: modelData.caption
                        }
                    }
                }
            }
            KSvg.FrameSvgItem {
                objectName: "previewIconboxHousing"
                Layout.fillWidth: true
                Layout.fillHeight: true
                imagePath: artworkRoot + "/widgets/iconbox.svg"
                Rectangle {
                    objectName: "previewIconboxHeading"
                    x: 3
                    y: 3
                    width: parent.width - 6
                    height: 8
                    color: "#aaa9a2"
                    clip: true
                    Rectangle {
                        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                        height: 1
                        color: "#41413b"
                    }
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
            KSvg.FrameSvgItem {
                Layout.preferredWidth: 134
                Layout.fillHeight: true
                imagePath: artworkRoot + "/widgets/button.svg"
                prefix: "normal"
                Row {
                    anchors.centerIn: parent
                    spacing: 4
                    Repeater {
                        model: 2
                        delegate: KSvg.FrameSvgItem {
                            required property int index
                            width: 57
                            height: 42
                            imagePath: artworkRoot + "/widgets/pager.svg"
                            prefix: index === 0 ? "active" : "normal"
                            Rectangle {
                                x: 8; y: 9; width: 29; height: 18
                                color: index === 0 ? "#789c9c" : "#aaa9a2"
                                border.color: "#41413b"
                            }
                            Rectangle { x: 26; y: 19; width: 23; height: 14; color: "#c1c1c1"; border.color: "#41413b" }
                        }
                    }
                }
            }
            KSvg.FrameSvgItem {
                Layout.preferredWidth: 198
                Layout.fillHeight: true
                imagePath: artworkRoot + "/widgets/button.svg"
                prefix: "normal"
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
            KSvg.FrameSvgItem {
                Layout.preferredWidth: 64
                Layout.fillHeight: true
                imagePath: artworkRoot + "/widgets/button.svg"
                prefix: "normal"
                // Schematic clock face only; production uses the actual clock applet.
                Rectangle {
                    anchors.centerIn: parent
                    width: 42; height: 42
                    radius: 21
                    color: "#e5e5da"
                    border.color: "#41413b"
                    Repeater {
                        model: 12
                        delegate: Rectangle {
                            required property int index
                            width: 1; height: 3
                            x: 20 + 16 * Math.sin(index * Math.PI / 6)
                            y: 20 - 16 * Math.cos(index * Math.PI / 6)
                            color: "#41413b"
                        }
                    }
                    Rectangle { x: 20; y: 8; width: 2; height: 15; color: "#41413b" }
                    Rectangle { x: 20; y: 20; width: 11; height: 2; color: "#41413b" }
                }
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
