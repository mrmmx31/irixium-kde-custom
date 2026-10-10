// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls

// Plasma's standard subtitle is limited to eight lines. Groups need every
// member, including wrapped long titles; this optional hint contains only text.
Controls.ScrollView {
    id: view
    property string groupTitle: ""
    property var windows: []
    property QtObject colorPalette: null
    DomainOSPalette { id: fallbackPalette }
    readonly property QtObject domainosPalette: colorPalette || fallbackPalette
    property real hintWidth: 480
    property real maximumHeight: 480
    implicitWidth: hintWidth
    implicitHeight: Math.min(column.implicitHeight + topPadding + bottomPadding, maximumHeight)
    contentWidth: availableWidth
    clip: true; padding: 8
    Controls.ScrollBar.horizontal:DomainOSViewScrollBar {
        scrollView:view
        colorPalette:view.domainosPalette;policy:Controls.ScrollBar.AlwaysOff
    }
    Controls.ScrollBar.vertical:DomainOSViewScrollBar {
        scrollView:view
        colorPalette:view.domainosPalette
        policy:column.implicitHeight>view.availableHeight
            ? Controls.ScrollBar.AlwaysOn : Controls.ScrollBar.AlwaysOff
    }
    background: Bevel { paletteOverride: view.domainosPalette; thickness: 1; simpleRelief: true }
    Column {
        id: column
        width: view.availableWidth
        spacing: 6
        Text {
            width: parent.width
            text: view.groupTitle
            color: view.domainosPalette.text
            font.family: "Nimbus Sans"; font.pixelSize: 14; font.bold: true
            textFormat: Text.PlainText; wrapMode: Text.Wrap; renderType: Text.NativeRendering
        }
        Repeater {
            model: view.windows
            delegate: Text {
                objectName: "domainosWindowHintTitle"
                required property int index
                required property var modelData
                width: column.width
                text: (index + 1) + ". " + modelData.title
                color: view.domainosPalette.text
                font.family: "Nimbus Sans"; font.pixelSize: 13
                textFormat: Text.PlainText; wrapMode: Text.Wrap; renderType: Text.NativeRendering
            }
        }
    }
}
