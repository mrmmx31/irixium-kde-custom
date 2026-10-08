/* SPDX-License-Identifier: GPL-3.0-or-later */
import QtQuick
import QtQuick.Window
import org.kde.ksvg as KSvg
import org.kde.plasma.components as PC

Window {
    width: 1000
    height: 296
    visible: true
    color: "#263f4d"
    title: "DomainOS — isolated native resource verification"
    Component.onCompleted: KSvg.ImageSet.imageSetName = "IrixClassicDomainOS"

    KSvg.FrameSvgItem {
        objectName: "housing"
        x: 0; y: 0; width: 1000; height: 296
        imagePath: artworkRoot + "/widgets/panel-background.svg"
        smooth: false
    }
    KSvg.FrameSvgItem {
        objectName: "smallHousing"
        x: 12; y: 12; width: 120; height: 52
        imagePath: artworkRoot + "/widgets/panel-background.svg"
        smooth: false
    }
    KSvg.FrameSvgItem {
        objectName: "wideHousing"
        x: 144; y: 12; width: 240; height: 52
        imagePath: artworkRoot + "/widgets/panel-background.svg"
        smooth: false
    }
    Repeater {
        model: ["normal", "pressed", "focus"]
        delegate: KSvg.FrameSvgItem {
            required property int index
            required property string modelData
            objectName: "button_" + modelData
            x: 12 + index * 132; y: 76; width: 120; height: 42
            imagePath: artworkRoot + "/widgets/button.svg"
            prefix: modelData
            smooth: false
            Text {
                anchors.centerIn: parent
                text: parent.modelData
                color: "#102b37"
                font.family: "monospace"
                font.pixelSize: 12
            }
        }
    }
    KSvg.FrameSvgItem {
        x: 408; y: 12; width: 188; height: 106
        imagePath: artworkRoot + "/widgets/instrument.svg"
        prefix: "normal"
        smooth: false
        KSvg.SvgItem {
            anchors.centerIn: parent
            width: 64; height: 64
            imagePath: artworkRoot + "/widgets/clock.svg"
            elementId: "ClockFace"
        }
    }
    KSvg.FrameSvgItem {
        objectName: "commandRail"
        x: 12; y: 136; width: 584; height: 28
        imagePath: artworkRoot + "/widgets/command-rail.svg"
        smooth: false
    }
    KSvg.FrameSvgItem {
        x: 12; y: 180; width: 584; height: 94
        imagePath: artworkRoot + "/widgets/iconbox.svg"
        smooth: false
        KSvg.FrameSvgItem {
            x: 5; y: 5; width: parent.width-10; height: 16
            imagePath: artworkRoot + "/widgets/iconbox.svg"
            prefix: "heading"
            smooth: false
        }
        Text {
            x: 12; y: 34
            text: "Opaque blue-gray Iconbox field"
            color: "#ecffff"
            font.family: "monospace"
            font.pixelSize: 12
        }
    }
    Repeater {
        model: ["normal", "active"]
        delegate: Item {
            required property int index
            required property string modelData
            objectName: "pager_" + modelData
            x: 620+index*176; y: 12; width: 160; height: 120
            Rectangle { anchors.fill: parent; color: "#263f4d" }
            Rectangle { x: 12; y: 16; width: 96; height: 50; color: "#b98976" }
            Rectangle { x: 76; y: 78; width: 66; height: 30; color: "#3296c4" }
            KSvg.FrameSvgItem {
                anchors.fill: parent
                imagePath: artworkRoot + "/widgets/pager.svg"
                prefix: parent.modelData
                smooth: false
            }
        }
    }
    PC.Switch {
        objectName: "nativeSwitch"
        x: 620; y: 160
        text: "Native DomainOS switch"
        checked: true
    }
    PC.Slider {
        objectName: "nativeSlider"
        x: 620; y: 212; width: 300
        value: 0.65
    }
}
