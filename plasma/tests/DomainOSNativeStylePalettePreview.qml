// SPDX-License-Identifier: GPL-3.0-or-later
// Private native rendering fixture: all labels/data below are synthetic.
import QtQuick
import QtQuick.Window
import QtQuick.Templates as T
import org.kde.ksvg as KSvg
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC
import org.kde.plasma.extras as PlasmaExtras
import org.kde.kirigami as Kirigami

Window {
    id: root
    width: 960
    height: 660
    visible: true
    title: "DomainOS native popup color verification — synthetic data"
    SystemPalette { id: palette }
    color: palette.window
    Component.onCompleted: KSvg.ImageSet.imageSetName = "IrixClassicDomainOS"
    readonly property color headerThemeBackground: volumeHeader.Kirigami.Theme.backgroundColor
    readonly property color footerThemeBackground: volumeFooter.Kirigami.Theme.backgroundColor
    readonly property color headerThemeText: volumeHeader.Kirigami.Theme.textColor
    readonly property color footerThemeText: volumeFooter.Kirigami.Theme.textColor
    readonly property color bodyThemeBackground: popup.Kirigami.Theme.backgroundColor
    readonly property color selectedThemeBackground: Kirigami.Theme.highlightColor
    readonly property bool actualHeaderVisible: volumeHeader.background.visible
    readonly property bool actualFooterVisible: volumeFooter.background.visible
    Item {
        id: popup
        x: 12; y: 12; width: 444; height: 272
        // A deliberately very different enclosing role detects native scopes
        // leaking into the actual Header/Window PlasmoidHeading components.
        Kirigami.Theme.inherit: false
        Kirigami.Theme.colorSet: Kirigami.Theme.Complementary
        KSvg.FrameSvgItem { anchors.fill: parent; imagePath: "dialogs/background" }
        PlasmaExtras.PlasmoidHeading {
            id: volumeHeader
            objectName: "nativeVolumeHeader"
            x: 8; y: 8; width: 428; height: 48
            position: T.ToolBar.Header
            PC.Label { text: "Audio Volume — synthetic header" }
        }
        PC.Slider { objectName: "nativeVolumeSlider"; x: 20; y: 76; width: 404; value: .65 }
        PC.Switch { objectName: "nativeVolumeSwitch"; x: 20; y: 126; checked: true; text: "Synthetic switch" }
        PC.Button { objectName: "nativeVolumeButton"; x: 20; y: 176; text: "Synthetic control" }
        PlasmaExtras.PlasmoidHeading {
            id: volumeFooter
            objectName: "nativeVolumeFooter"
            x: 8; y: 216; width: 428; height: 48
            position: T.ToolBar.Footer
            PC.Label { text: "Audio Volume — synthetic footer" }
        }
    }
    Item {
        x: 480; y: 12; width: 468; height: 272
        Kirigami.Theme.inherit: false
        Kirigami.Theme.colorSet: Kirigami.Theme.Window
        KSvg.FrameSvgItem { anchors.fill: parent; imagePath: "dialogs/background" }
        PlasmaExtras.PlasmoidHeading {
            objectName: "nativeNotificationsHeader"
            x: 8; y: 8; width: 452; height: 48
            position: T.ToolBar.Header
            PC.Label { text: "Notifications — synthetic header" }
        }
        PC.Label { x: 20; y: 88; text: "This fixture reads no notifications or accounts." }
        PC.Button { x: 20; y: 128; text: "Synthetic action" }
        PlasmaExtras.PlasmoidHeading {
            objectName: "nativeNotificationsFooter"
            x: 8; y: 216; width: 452; height: 48
            position: T.ToolBar.Footer
            PC.Label { text: "Notifications — synthetic footer" }
        }
    }
    Repeater {
        model: [
            {name:"button", path:"widgets/button", prefix:"normal", role:"ButtonBackground"},
            {name:"lineedit", path:"widgets/lineedit", prefix:"base", role:"ViewBackground"},
            {name:"sliderHighlight", path:"widgets/slider", prefix:"groove-highlight", role:"Highlight"},
            {name:"switchActive", path:"widgets/switch", prefix:"active", role:"Highlight"},
            {name:"rawHeader", path:"widgets/plasmoidheading", prefix:"header", role:"HeaderBackground"},
            {name:"rawFooter", path:"widgets/plasmoidheading", prefix:"footer", role:"Background"},
            {name:"tooltip", path:"widgets/tooltip", prefix:"", role:"TooltipBackground"},
            {name:"viewSelected", path:"widgets/viewitem", prefix:"selected", role:"Highlight"},
            {name:"panel", path:"widgets/panel-background", prefix:"", role:"Background"}
        ]
        delegate: Item {
            required property int index
            required property var modelData
            x: 12+(index%3)*316; y: 314+Math.floor(index/3)*110
            width: 300; height: 94
            PC.Label { text: modelData.name+" — "+modelData.role }
            KSvg.FrameSvgItem {
                objectName: "nativeFrame_"+modelData.name
                x: 0; y: 26; width: 300; height: 64
                imagePath: modelData.path
                prefix: modelData.prefix
                smooth: false
            }
        }
    }
}
