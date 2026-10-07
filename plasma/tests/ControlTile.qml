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
    implicitWidth: 94
    implicitHeight: 56
    checkable: true
    hoverEnabled: true
    property string iconName: "utilities-terminal"
    property string baseState: "normal"
    property int activationCount: 0
    readonly property string effectiveState: checked ? "focus" : baseState
    readonly property string usedPrefix: surface.usedPrefix
    onClicked: activationCount += 1

    background: KSvg.FrameSvgItem {
        id: surface
        objectName: control.objectName + "Frame"
        imagePath: artworkRoot + "/widgets/tasks.svg"
        prefix: control.down
            ? TaskTools.taskPrefixPressed(control.effectiveState, PlasmaCore.Types.BottomEdge)
            : (control.hovered
                ? TaskTools.taskPrefixHovered(control.effectiveState, PlasmaCore.Types.BottomEdge)
                : TaskTools.taskPrefix(control.effectiveState, PlasmaCore.Types.BottomEdge))
    }
    contentItem: Item {
        Kirigami.Icon {
            width: 32
            height: 32
            anchors.horizontalCenter: parent.horizontalCenter
            y: 4 + (control.down ? 1 : 0)
            source: control.iconName
        }
        Text {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 5
            anchors.rightMargin: 5
            anchors.bottomMargin: control.down ? 3 : 4
            text: control.text
            color: "#000000"
            font.pixelSize: 11
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
    }
}
