// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    anchors.fill: parent
    color: Kirigami.Theme.backgroundColor
    Text {
        anchors.centerIn: parent
        text: "GNU/LINUX\nDomain/OS SR10.4"
        color: Kirigami.Theme.textColor
        font.family: "Nimbus Sans"
        font.pointSize: 18
        horizontalAlignment: Text.AlignHCenter
    }
}
