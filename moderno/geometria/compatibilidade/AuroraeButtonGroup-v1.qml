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

    // IRIXIUM_DIVISORIAS_BEGIN v1
    // Decorative only: no MouseArea, no changes to button sizes or margins.
    // Keep this container at 0 x 0: the caller uses group.childrenRect.width.
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
        // Only the left group draws the frame marks, including when it is empty.
        readonly property bool isLeftGroup: group.x + groupRow.width / 2 < root.width / 2
        // The existing Irixium SVG has a seven-logical-pixel outer frame.
        readonly property real frameBand: 7
        readonly property real titleTop: isMaximized ? 0 : root.padding.top + frameBand
        readonly property real titleBottom: isMaximized
            ? root.maximizedBorders.top : root.padding.top + root.borders.top
        readonly property color grooveDark: isActive ? "#5b5746" : "#565656"
        readonly property color grooveLight: isActive ? "#dad7ca" : "#dadada"

        // A separator follows each visible button of the left group, or
        // precedes each visible button of the right group. Explicit spacers
        // are not buttons. The actual Row determines positions and gaps.
        Repeater {
            model: groupRow.children
            delegate: Item {
                property var sourceButton: modelData
                visible: sourceButton !== null && sourceButton !== undefined
                    && sourceButton.visible
                    && typeof sourceButton.buttonType !== "undefined"
                    && sourceButton.width > 0
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

        // Eight short grooves split the four resize corners from the straight
        // frame sections. They are overlaid at fixed offsets, not repeated or
        // stretched with a FrameSvg tile. The outermost outline stays intact.
        Item {
            id: irixiumCornerMarks
            x: -group.x + root.padding.left
            y: -group.y + root.padding.top
            width: Math.max(0, root.width - root.padding.left - root.padding.right)
            height: Math.max(0, root.height - root.padding.top - root.padding.bottom)
            readonly property real span: Math.max(22, Math.round(root.borders.top))
            readonly property real band: irixiumOverlay.frameBand
            visible: irixiumOverlay.isLeftGroup && !irixiumOverlay.isMaximized
                && root.borders.left >= band && root.borders.right >= band
                && root.borders.bottom >= band
                && width >= 2 * span + 4 && height >= 2 * span + 4

            Repeater {
                model: [
                    {px: irixiumCornerMarks.span, py: 1, vertical: true},
                    {px: irixiumCornerMarks.width - irixiumCornerMarks.span - 2, py: 1, vertical: true},
                    {px: irixiumCornerMarks.span, py: irixiumCornerMarks.height - irixiumCornerMarks.band + 1, vertical: true},
                    {px: irixiumCornerMarks.width - irixiumCornerMarks.span - 2, py: irixiumCornerMarks.height - irixiumCornerMarks.band + 1, vertical: true},
                    {px: 1, py: irixiumCornerMarks.span, vertical: false},
                    {px: irixiumCornerMarks.width - irixiumCornerMarks.band + 1, py: irixiumCornerMarks.span, vertical: false},
                    {px: 1, py: irixiumCornerMarks.height - irixiumCornerMarks.span - 2, vertical: false},
                    {px: irixiumCornerMarks.width - irixiumCornerMarks.band + 1, py: irixiumCornerMarks.height - irixiumCornerMarks.span - 2, vertical: false}
                ]
                delegate: Item {
                    property var groove: modelData
                    x: groove.px
                    y: groove.py
                    width: groove.vertical ? 2 : irixiumCornerMarks.band - 2
                    height: groove.vertical ? irixiumCornerMarks.band - 2 : 2
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
