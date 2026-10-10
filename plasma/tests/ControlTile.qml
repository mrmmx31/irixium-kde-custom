/* SPDX-License-Identifier: GPL-3.0-or-later */
import QtQuick
import QtQuick.Templates as T
import org.kde.ksvg as KSvg
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import "../applets/org.irixclassic.iconbox/contents/ui/code/tools.js" as TaskTools

// Gallery control. Artwork and prefix selection come from the production
// Classic package; real task activation is tested separately in plasmashell.
T.Button {
    id: control
    implicitWidth: 74
    implicitHeight: 42
    padding: 0
    checkable: true
    hoverEnabled: true
    property string iconName: "utilities-terminal"
    property string baseState: "normal"
    property int activationCount: 0
    readonly property int captionHeight: 14
    readonly property int iconSize: 24
    readonly property int wellSize: iconSize + 4
    readonly property string effectiveState: checked ? "focus" : baseState
    readonly property string usedPrefix: iconFrame.usedPrefix
    onClicked: activationCount += 1

    background: Item {
        // Match the production panel delegate: only the icon has a square
        // frame; the caption is its own strip, not part of a raised button.
        KSvg.FrameSvgItem {
            id: iconFrame
            objectName: control.objectName + "Frame"
            width: control.wellSize
            height: control.wellSize
            anchors.horizontalCenter: parent.horizontalCenter
            imagePath: artworkRoot + "/widgets/task-icon.svg"
            prefix: control.down
                ? TaskTools.taskPrefixPressed(control.effectiveState, PlasmaCore.Types.BottomEdge)
                : (control.hovered
                    ? TaskTools.taskPrefixHovered(control.effectiveState, PlasmaCore.Types.BottomEdge)
                    : TaskTools.taskPrefix(control.effectiveState, PlasmaCore.Types.BottomEdge))
        }
        Rectangle {
            objectName: control.objectName + "CaptionStrip"
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 4; rightMargin: 4 }
            height: control.captionHeight
            color: control.down || control.effectiveState === "focus" ? "#637f7f"
                : control.effectiveState === "attention" ? "#aaa27a"
                : control.effectiveState === "minimized" ? "#aaa9a2"
                : control.hovered ? "#adc9c7" : "#9ebfbf"
            Rectangle {
                anchors { left: parent.left; right: parent.right; top: parent.top }
                height: 1
                color: control.down || control.effectiveState === "focus" ? "#41413b" : "#bfd3d0"
            }
            Rectangle {
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                height: 1
                color: control.down || control.effectiveState === "focus" ? "#bfd3d0" : "#789292"
            }
        }
    }
    contentItem: Item {
        Kirigami.Icon {
            width: control.iconSize
            height: control.iconSize
            anchors.horizontalCenter: parent.horizontalCenter
            y: 2 + (control.down ? 1 : 0)
            source: control.iconName
            active: false
        }
        Text {
            objectName: control.objectName + "Caption"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 5 + (control.down ? 1 : 0)
            anchors.rightMargin: 5 - (control.down ? 1 : 0)
            anchors.bottomMargin: control.down ? -1 : 0
            height: control.captionHeight
            text: control.text
            color: control.down || control.effectiveState === "focus" ? "#f4f4e9" : "#000000"
            font: Qt.font({
                family: Kirigami.Theme.smallFont.family,
                styleName: Kirigami.Theme.smallFont.styleName,
                weight: Kirigami.Theme.smallFont.weight,
                italic: Kirigami.Theme.smallFont.italic,
                pixelSize: 10,
            })
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
    }
}
