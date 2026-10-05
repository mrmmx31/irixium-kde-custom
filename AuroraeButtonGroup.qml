/*
    SPDX-FileCopyrightText: 2012 Martin Gräßlin <mgraesslin@kde.org>

    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import org.kde.kwin.decoration

Item {
    function createButtons() {
        var component = Qt.createComponent("AuroraeButton.qml");
        if (auroraeTheme.buttonSpacing === 0 && buttons.length > 0) {
            createDivider("leadingDivider");
        }
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
            if (auroraeTheme.buttonSpacing === 0 && i < buttons.length - 1) {
                createDivider("divider" + i);
            }
        }
        if (auroraeTheme.buttonSpacing === 0 && buttons.length > 0) {
            createDivider("trailingDivider");
        }
    }
    function createDivider(name) {
        Qt.createQmlObject("import QtQuick 2.0; Rectangle { width: 1; height: auroraeTheme.buttonHeight * auroraeTheme.buttonSizeFactor; color: \"#292929\" }",
            groupRow, name);
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
}
