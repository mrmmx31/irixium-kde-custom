/*
    SPDX-FileCopyrightText: 2012 Martin Gräßlin <mgraesslin@kde.org>

    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import org.kde.kwin.decoration

Item {
    function createButtons() {
        var component = Qt.createComponent("AuroraeButton.qml");
        for (var i=0; i<buttons.length; i++) {
            if (buttons[i] == DecorationOptions.DecorationButtonExplicitSpacer) {
                Qt.createQmlObject("import QtQuick 2.0; Item { width: auroraeTheme.explicitButtonSpacer * auroraeTheme.buttonSizeFactor; height: auroraeTheme.buttonHeight * auroraeTheme.buttonSizeFactor }",
                    groupRow, "explicitSpacer" + buttons + i);
            } else if (buttons[i] == DecorationOptions.DecorationButtonMenu) {
                Qt.createQmlObject("import QtQuick 2.0; MenuButton { width: auroraeTheme.buttonWidthMenu * auroraeTheme.buttonSizeFactor; height: auroraeTheme.buttonHeight * auroraeTheme.buttonSizeFactor }",
                    groupRow, "menuButton" + buttons + i);
            } else if (buttons[i] == DecorationOptions.DecorationButtonApplicationMenu) {
                Qt.createQmlObject("import QtQuick 2.0; AppMenuButton { width: auroraeTheme.buttonWidthAppMenu * auroraeTheme.buttonSizeFactor; height: auroraeTheme.buttonHeight * auroraeTheme.buttonSizeFactor }",
                    groupRow, "appMenuButton" + buttons + i);
            } else if (buttons[i] == DecorationOptions.DecorationButtonMaximizeRestore) {
                var maximizeComponent = Qt.createComponent("AuroraeMaximizeButton.qml");
                maximizeComponent.createObject(groupRow);
            } else {
                component.createObject(groupRow, {buttonType: buttons[i]});
            }
        }
    }
    id: group
    property var buttons
    property bool animate: false

    Row {
        id: groupRow
        spacing: auroraeTheme.buttonSpacing * auroraeTheme.buttonSizeFactor
    }
    onButtonsChanged: {
        for (var i = 0; i < groupRow.children.length; i++) {
            groupRow.children[i].destroy();
        }
        createButtons();
    }
    anchors {
        top: root.top
        topMargin: (decoration.client.maximized ? auroraeTheme.titleEdgeTopMaximized + auroraeTheme.buttonMarginTopMaximized : auroraeTheme.titleEdgeTop + root.padding.top + auroraeTheme.buttonMarginTop)
    }

    // IRIXIUM_DIVISORIAS_BEGIN v2
    // Keep the button group above the later inner-border SVG layers.
    // Outside Irixium, retain the original stacking order.
    z: irixiumOverlay.isIrixium ? 1 : 0

    // Decorative only: no input handlers, no changes to button geometry.
    // Keep the direct child at 0 x 0: aurorae.qml uses childrenRect.width.
    Item {
        id: irixiumOverlay
        width: 0
        height: 0
        clip: false
        visible: isIrixium

        readonly property bool isIrixium: typeof auroraeTheme !== "undefined"
            && /\/Irixium\/decoration(?:\.svgz?)?$/.test(String(auroraeTheme.decorationPath))
        readonly property bool isMaximized: decoration.client.maximized
        readonly property bool isActive: decoration.client.active
        readonly property bool isLeftGroup: typeof leftButtonGroup !== "undefined"
            ? group === leftButtonGroup
            : group.x + groupRow.width / 2 < root.width / 2
        // This is the artwork's outer band, not a minimum KWin border size.
        readonly property real artworkBand: 7
        readonly property real titleTop: isMaximized ? 0 : root.padding.top + artworkBand
        readonly property real titleBottom: isMaximized
            ? root.maximizedBorders.top : root.padding.top + root.borders.top
        readonly property color grooveDark: isActive ? "#5b5746" : "#565656"
        readonly property color grooveLight: isActive ? "#dad7ca" : "#dadada"

        Repeater {
            model: groupRow.children
            delegate: Item {
                property var sourceButton: modelData
                // The outer AuroraeMaximizeButton is an Item WITHOUT buttonType.
                // Use the configured entry, not a property of its implementation.
                // Invisible help buttons and explicit spacers are still excluded.
                readonly property bool isButtonEntry: index < group.buttons.length
                    && group.buttons[index] !== DecorationOptions.DecorationButtonExplicitSpacer
                visible: isButtonEntry
                    && sourceButton !== null && sourceButton !== undefined
                    && sourceButton.visible && sourceButton.width > 0 && sourceButton.height > 0
                x: sourceButton ? Math.round(sourceButton.x + (irixiumOverlay.isLeftGroup
                    ? sourceButton.width + groupRow.spacing / 2 - 1
                    : -groupRow.spacing / 2 - 1)) : 0
                y: irixiumOverlay.titleTop - group.y
                width: 2
                height: Math.max(0, irixiumOverlay.titleBottom - irixiumOverlay.titleTop - 1)
                Rectangle {
                    x: 0
                    width: 1
                    height: parent.height
                    color: irixiumOverlay.grooveDark
                    antialiasing: false
                }
                Rectangle {
                    x: 1
                    width: 1
                    height: parent.height
                    color: irixiumOverlay.grooveLight
                    antialiasing: false
                }
            }
        }

        // Only the left group draws the eight corner cuts. Each edge uses
        // its own REAL border width. BorderSize=Normal clamps 7 to 6 in Aurorae.
        // Missing/narrow edges suppress their own marks, not the entire frame.
        Item {
            id: irixiumCornerMarks
            x: -group.x + root.padding.left
            y: -group.y + root.padding.top
            width: Math.max(0, root.width - root.padding.left - root.padding.right)
            height: Math.max(0, root.height - root.padding.top - root.padding.bottom)
            readonly property real span: Math.max(22, Math.round(root.borders.top))
            readonly property real topBand: Math.max(0, Math.min(irixiumOverlay.artworkBand, Math.floor(root.borders.top)))
            readonly property real leftBand: Math.max(0, Math.min(irixiumOverlay.artworkBand, Math.floor(root.borders.left)))
            readonly property real rightBand: Math.max(0, Math.min(irixiumOverlay.artworkBand, Math.floor(root.borders.right)))
            readonly property real bottomBand: Math.max(0, Math.min(irixiumOverlay.artworkBand, Math.floor(root.borders.bottom)))
            visible: irixiumOverlay.isLeftGroup && !irixiumOverlay.isMaximized
                && width >= 2 * span + 4 && height >= 2 * span + 4

            Repeater {
                model: [
                    {px: irixiumCornerMarks.span, py: 1, vertical: true,
                     length: Math.max(0, irixiumCornerMarks.topBand - 2)},
                    {px: irixiumCornerMarks.width - irixiumCornerMarks.span - 2, py: 1, vertical: true,
                     length: Math.max(0, irixiumCornerMarks.topBand - 2)},
                    {px: irixiumCornerMarks.span, py: irixiumCornerMarks.height - irixiumCornerMarks.bottomBand + 1, vertical: true,
                     length: Math.max(0, irixiumCornerMarks.bottomBand - 2)},
                    {px: irixiumCornerMarks.width - irixiumCornerMarks.span - 2, py: irixiumCornerMarks.height - irixiumCornerMarks.bottomBand + 1, vertical: true,
                     length: Math.max(0, irixiumCornerMarks.bottomBand - 2)},
                    {px: 1, py: irixiumCornerMarks.span, vertical: false,
                     length: Math.max(0, irixiumCornerMarks.leftBand - 2)},
                    {px: irixiumCornerMarks.width - irixiumCornerMarks.rightBand + 1, py: irixiumCornerMarks.span, vertical: false,
                     length: Math.max(0, irixiumCornerMarks.rightBand - 2)},
                    {px: 1, py: irixiumCornerMarks.height - irixiumCornerMarks.span - 2, vertical: false,
                     length: Math.max(0, irixiumCornerMarks.leftBand - 2)},
                    {px: irixiumCornerMarks.width - irixiumCornerMarks.rightBand + 1, py: irixiumCornerMarks.height - irixiumCornerMarks.span - 2, vertical: false,
                     length: Math.max(0, irixiumCornerMarks.rightBand - 2)}
                ]
                delegate: Item {
                    property var groove: modelData
                    x: groove.px
                    y: groove.py
                    width: groove.vertical ? 2 : groove.length
                    height: groove.vertical ? groove.length : 2
                    visible: groove.length > 0
                    Rectangle {
                        width: parent.groove.vertical ? 1 : parent.width
                        height: parent.groove.vertical ? parent.height : 1
                        color: irixiumOverlay.grooveDark
                        antialiasing: false
                    }
                    Rectangle {
                        x: parent.groove.vertical ? 1 : 0
                        y: parent.groove.vertical ? 0 : 1
                        width: parent.groove.vertical ? 1 : parent.width
                        height: parent.groove.vertical ? parent.height : 1
                        color: irixiumOverlay.grooveLight
                        antialiasing: false
                    }
                }
            }
        }
    }
    // IRIXIUM_DIVISORIAS_END
}
