// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls

DomainOSButton {
    id:button
    required property var ordering
    required property string favoriteId
    required property string favoriteTitle
    required property int direction
    property var pressedRequest:null
    Layout.minimumWidth:28;Layout.preferredWidth:28;Layout.maximumWidth:28
    Layout.minimumHeight:28;Layout.preferredHeight:28;Layout.maximumHeight:28
    padding:2;icon.name:direction<0 ? "go-up" : "go-down";icon.width:16;icon.height:16
    Accessible.name:direction<0 ? qsTr("Mover %1 para cima").arg(favoriteTitle)
        : qsTr("Mover %1 para baixo").arg(favoriteTitle)
    Controls.ToolTip.visible:hovered
    Controls.ToolTip.delay:Qt.styleHints.mousePressAndHoldInterval
    Controls.ToolTip.text:Accessible.name
    onPressed:pressedRequest=ordering.capture(favoriteId,direction)
    onCanceled:pressedRequest=null
    onClicked: {
        const request=pressedRequest
        pressedRequest=null
        ordering.move(request)
    }
}
