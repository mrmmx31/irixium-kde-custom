#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Native QtQuick5/6 KDE controls in the coordinated private Xephyr namespace.

The QML and artificial text data are written only inside the disposable HOME.
Controls inherit the KDE platform palette/font. No custom painting or CSS is used.
"""
from pathlib import Path
import argparse
import importlib
import importlib.util
import json
import os
import re
import sys

from qt6_demo import private_guards, selection


QML_SOURCE = r'''
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import org.kde.kirigami 2.0 as Kirigami

ApplicationWindow {
    id: window
    objectName: "privateQtQuick__MAJOR__Window"
    width: 660
    height: 560
    visible: true
    title: "DomainOS SR10.4 — QtQuick__MAJOR__ / KDE"
    property int selectedRow: -1
    property var coordinateDisabledHintTarget: null
    property bool coordinateDisabledHintReady: false
    readonly property var disabledHintTargets: [disabledButton, disabledCheckBox,
        disabledSwitch, disabledCombo, disabledSpin, disabledText, disabledSlider]
    property int tooltipRolePopupCount: 0
    property string lastTooltipRoleSnapshot: "{}"
    property var tooltipRoleWatchers: []
    property var tooltipRoleWatchedControls: []
    Rectangle {
        id: tooltipRolePaletteProbe
        visible: true
        opacity: 0
        x: -1
        y: -1
        width: 1
        height: 1
        Kirigami.Theme.colorSet: Kirigami.Theme.Tooltip
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.backgroundColor
    }
    Text {
        id: tooltipRoleTextProbe
        visible: true
        opacity: 0
        x: -1
        y: -1
        width: 1
        height: 1
        Kirigami.Theme.colorSet: Kirigami.Theme.Tooltip
        Kirigami.Theme.inherit: false
        color: Kirigami.Theme.textColor
    }
    readonly property string nativeTooltipPalette: JSON.stringify({
        roleBackground: tooltipRolePaletteProbe.color.toString(),
        roleForeground: tooltipRoleTextProbe.color.toString(),
        popupBackground: pressButton.ToolTip.toolTip.background.color.toString(),
        popupForeground: pressButton.ToolTip.toolTip.contentItem.children[0].color.toString(),
        adaptedPopups: tooltipRolePopupCount
    })
    function applyTooltipRole(control) {
        if (__MAJOR__ === 6 && control && control.ToolTip.text) {
            var popup = control.ToolTip.toolTip
            if (popup) {
                try {
                    popup.Kirigami.Theme.colorSet = Kirigami.Theme.Tooltip
                    popup.Kirigami.Theme.inherit = false
                    if (popup.contentItem) {
                        popup.contentItem.Kirigami.Theme.colorSet = Kirigami.Theme.Tooltip
                        popup.contentItem.Kirigami.Theme.inherit = false
                    }
                    if (popup.background) {
                        popup.background.Kirigami.Theme.colorSet = Kirigami.Theme.Tooltip
                        popup.background.Kirigami.Theme.inherit = false
                    }
                    ++window.tooltipRolePopupCount
                    window.lastTooltipRoleSnapshot = JSON.stringify({
                        name: control.objectName,
                        text: control.ToolTip.text,
                        colorSet: String(popup.Kirigami.Theme.colorSet),
                        background: popup.background.color.toString(),
                        foreground: popup.contentItem.children[0].color.toString()
                    })
                } catch (error) {
                    console.warn("Could not apply the KDE Tooltip role:", error)
                }
            }
        }
    }
    Component {
        id: tooltipRoleWatcherComponent
        Connections {
            property var ownerControl: null
            target: ownerControl ? ownerControl.ToolTip.toolTip : null
            function onVisibleChanged() {
                if (target && target.visible)
                    window.applyTooltipRole(ownerControl)
            }
        }
    }
    function watchTooltipRole(control) {
        if (__MAJOR__ !== 6 || !control || !control.ToolTip || !control.ToolTip.text
                || tooltipRoleWatchedControls.indexOf(control) >= 0)
            return
        var watcher = tooltipRoleWatcherComponent.createObject(window, {"ownerControl": control})
        if (watcher) {
            tooltipRoleWatchedControls.push(control)
            tooltipRoleWatchers.push(watcher)
        }
    }
    function watchExistingTooltipRoles(item) {
        if (!item)
            return
        watchTooltipRole(item)
        for (var i = 0; i < item.children.length; ++i)
            watchExistingTooltipRoles(item.children[i])
    }
    function installTooltipRoleWatchers() {
        if (__MAJOR__ !== 6)
            return
        watchExistingTooltipRoles(contentItem)
        // ScrollBar is an attached control; include both table and ScrollView
        // bars explicitly in case the QtQuick style omits them from children.
    }
    function visibleInCurrentPage(item) {
        var ancestor = item
        while (ancestor) {
            if (!ancestor.visible || ancestor.opacity <= 0)
                return false
            if (ancestor === contentItem)
                return true
            ancestor = ancestor.parent
        }
        return false
    }
    function trackDisabledControlHint(position) {
        var next = null
        for (var i = 0; i < disabledHintTargets.length; ++i) {
            var target = disabledHintTargets[i]
            if (!visibleInCurrentPage(target) || target.enabled)
                continue
            var local = target.mapFromItem(contentItem, position.x, position.y)
            if (local.x >= 0 && local.y >= 0 &&
                    local.x < target.width && local.y < target.height) {
                next = target
                break
            }
        }
        if (next !== coordinateDisabledHintTarget) {
            coordinateDisabledHintTarget = next
            coordinateDisabledHintReady = false
        }
    }
    Timer {
        interval: 750
        repeat: false
        running: __MAJOR__ === 5 && window.coordinateDisabledHintTarget !== null &&
                 !window.coordinateDisabledHintReady
        onTriggered: window.coordinateDisabledHintReady = true
    }
    ToolTip {
        id: coordinateDisabledTooltip
        parent: Overlay.overlay
        visible: __MAJOR__ === 5 && window.coordinateDisabledHintReady &&
                 window.coordinateDisabledHintTarget !== null
        delay: 0
        timeout: 6000
        text: window.coordinateDisabledHintTarget ?
              window.coordinateDisabledHintTarget.ToolTip.text : ""
        readonly property point ownerOrigin: window.coordinateDisabledHintTarget ?
            window.coordinateDisabledHintTarget.mapToItem(Overlay.overlay, 0, 0) : Qt.point(0, 0)
        x: window.coordinateDisabledHintTarget ?
           Math.max(8, Math.min(ownerOrigin.x +
               (window.coordinateDisabledHintTarget.width - width) / 2,
               Overlay.overlay.width - width - 8)) : 0
        y: window.coordinateDisabledHintTarget ?
           (ownerOrigin.y >= height + 8 ? ownerOrigin.y - height - 8 :
            ownerOrigin.y + window.coordinateDisabledHintTarget.height + 8) : 0
    }
    function menuHint(caption) {
        switch (caption) {
        case "Record activation": return "Registra a ativação da ação de exemplo; não inicia aplicações."
        case "Checkable action": return "Marca ou desmarca esta opção do menu nativo."
        case "Unavailable action": return "Ação desabilitada: mostra o estado sem executar uma operação."
        case "Submenu": return "Abre o submenu com uma ação de exemplo."
        case "Native submenu item": return "Ação de exemplo do submenu nativo."
        case "Close only this gallery": return "Fecha somente esta galeria privada, sem encerrar a sessão."
        default: return "Ação do menu desta galeria privada: " + caption + "."
        }
    }
    function collectHints(item) {
        var result = []
        function walk(control) {
            if (control.ToolTip.text)
                result.push({name: control.objectName, text: control.ToolTip.text})
            for (var i = 0; i < control.children.length; ++i)
                walk(control.children[i])
        }
        walk(item)
        return JSON.stringify(result)
    }
    readonly property string nativeHints: collectHints(contentItem)
    readonly property var nativePressTip: pressButton.ToolTip.toolTip
    readonly property var nativeDisabledHintTip: coordinateDisabledTooltip
    property var nativeTableCellHintControl: null
    property var nativeTableVerticalBar: null
    property var nativeTableHorizontalBar: null
    property var nativeScrollViewVerticalBar: null
    property var nativeScrollViewHorizontalBar: null
    readonly property var nativeMenu: galleryMenu
    signal actionRecorded(string action, string detail)
    function log(action, detail) {
        statusLabel.text = action + ": " + detail
        actionRecorded(action, String(detail))
    }
    Component.onCompleted: Qt.callLater(window.installTooltipRoleWatchers)
    readonly property string nativePalettes: JSON.stringify({
        normalButton: {button: String(pressButton.palette.button),
                       buttonText: String(pressButton.palette.buttonText),
                       window: String(pressButton.palette.window),
                       highlight: String(pressButton.palette.highlight)},
        disabledButton: {button: String(disabledButton.palette.button),
                         buttonText: String(disabledButton.palette.buttonText),
                         window: String(disabledButton.palette.window),
                         highlight: String(disabledButton.palette.highlight)}
    })
    readonly property string nativeFont: pressButton.font.family + ";" + pressButton.font.pointSize
    menuBar: MenuBar {
        Menu {
            id: galleryMenu
            title: "Native menu"
            delegate: MenuItem {
                id: nativeMenuRow
                hoverEnabled: true
                ToolTip.visible: hovered
                ToolTip.delay: 750
                ToolTip.timeout: -1
                ToolTip.text: window.menuHint(text)
                readonly property string rowHintPalette: {
                    const tip = ToolTip.toolTip
                    if (!tip)
                        return "{}"
                    try {
                        return JSON.stringify({background: tip.background.color.toString(),
                            foreground: tip.contentItem.children[0].color.toString()})
                    } catch (error) {
                        return "{}"
                    }
                }
                Connections {
                    target: nativeMenuRow.ToolTip.toolTip
                    function onVisibleChanged() {
                        if (target.visible)
                            window.applyTooltipRole(nativeMenuRow)
                    }
                }
                readonly property bool rowHintVisible: ToolTip.visible
                readonly property string rowHintText: ToolTip.text
                readonly property string rowHintRect: {
                    const tip = ToolTip.toolTip
                    if (!tip || !tip.parent)
                        return "{}"
                    const p = tip.parent.mapToGlobal(tip.x, tip.y)
                    return JSON.stringify({x: p.x, y: p.y, width: tip.width, height: tip.height})
                }
                onHoveredChanged: {
                    if (hovered) {
                        const tip = ToolTip.toolTip
                        tip.x = width + 8
                        tip.y = (height - tip.implicitHeight) / 2
                    }
                }
            }
            Action { text: "Record activation"; onTriggered: window.log("menu", "activated") }
            Action { text: "Checkable action"; checkable: true; checked: true }
            Action { text: "Unavailable action"; enabled: false }
            MenuSeparator {}
            Menu {
                id: gallerySubmenu
                title: "Submenu"
                delegate: MenuItem {
                    id: nativeSubmenuRow
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.delay: 750
                    ToolTip.timeout: -1
                    ToolTip.text: window.menuHint(text)
                    Connections {
                        target: nativeSubmenuRow.ToolTip.toolTip
                        function onVisibleChanged() {
                            if (target.visible)
                                window.applyTooltipRole(nativeSubmenuRow)
                        }
                    }
                }
                Action { text: "Native submenu item" }
            }
            Action { text: "Close only this gallery"; onTriggered: window.close() }
        }
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        Label {
            text: "REAL QtQuick__MAJOR__ controls | " + runtimeDescription
            Layout.fillWidth: true
            elide: Text.ElideRight
        }
        TabBar {
            id: pages
            objectName: "qtquick__MAJOR___tabs"
            Layout.fillWidth: true
            TabButton { objectName: "qtquick__MAJOR___controlsTab"; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Escolha esta página de controles; os valores das demais páginas são preservados.";  text: "Controls" }
            TabButton { objectName: "qtquick__MAJOR___tableTab"; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Escolha esta página de controles; os valores das demais páginas são preservados.";  text: "Table" }
            TabButton { objectName: "qtquick__MAJOR___scrollTab"; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Escolha esta página de controles; os valores das demais páginas são preservados.";  text: "Scroll" }
        }
        StackLayout {
            currentIndex: pages.currentIndex
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                id: controlsPage
                HoverHandler {
                    enabled: __MAJOR__ === 5
                    onPointChanged: {
                        const position = window.contentItem.mapFromItem(controlsPage,
                                                                         point.position.x,
                                                                         point.position.y)
                        window.trackDisabledControlHint(position)
                    }
                    onHoveredChanged: {
                        if (!hovered) {
                            window.coordinateDisabledHintTarget = null
                            window.coordinateDisabledHintReady = false
                        }
                    }
                }
                GroupBox {
                    title: "Native buttons and selection"
                    Layout.fillWidth: true
                    RowLayout {
                        id: disabledButtonRow
                        HoverHandler {
                            enabled: __MAJOR__ === 5
                            onPointChanged: {
                                const position = window.contentItem.mapFromItem(disabledButtonRow,
                                                                                 point.position.x,
                                                                                 point.position.y)
                                window.trackDisabledControlHint(position)
                            }
                            onHoveredChanged: {
                                if (!hovered && window.coordinateDisabledHintTarget === disabledButton) {
                                    window.coordinateDisabledHintTarget = null
                                    window.coordinateDisabledHintReady = false
                                }
                            }
                        }
                        Button { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Botão da amostra: pressione para observar o relevo e solte para acionar.";
                            id: pressButton
                            objectName: "qtquick__MAJOR___pressButton"
                            text: "Press and release"
                            onClicked: window.log("button", "clicked")
                        }
                        Button { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Botão alternável: clique para ligar ou desligar o estado da amostra.";  text: "Latched"; checkable: true; checked: true }
                        Button { hoverEnabled: true; ToolTip.timeout: 6000; ToolTip.text: "Botão desabilitado: mostra o relevo deste estado sem executar uma ação.";
                            id: disabledButton
                            objectName: "qtquick__MAJOR___disabledButton"
                            text: "Disabled"
                            ToolTip.visible: hovered
                            ToolTip.delay: 750
                            enabled: false
                        }
                    }
                }
                RowLayout {
                    CheckBox { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Escolha independente: clique para marcar ou desmarcar; não altera o projeto.";  text: "Off" }
                    CheckBox { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Escolha independente: clique para marcar ou desmarcar; não altera o projeto.";  text: "Checked"; checked: true }
                    CheckBox { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Escolha independente com estado misto; clique para alternar na amostra, sem alterar o projeto.";  text: "Mixed"; tristate: true; checkState: Qt.PartiallyChecked }
                    CheckBox { id: disabledCheckBox; objectName: "qtquick__MAJOR___disabledCheckBox"; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Opção desabilitada: mostra o estado marcado sem permitir alteração.";  text: "Disabled"; checked: true; enabled: false }
                }
                RowLayout {
                    RadioButton { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Opção exclusiva do grupo: selecionar esta opção desmarca a outra.";  text: "Radio A"; checked: true }
                    RadioButton { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Opção exclusiva do grupo: selecionar esta opção desmarca a outra.";  text: "Radio B" }
                    Switch { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Interruptor nativo: clique para ligar ou desligar o estado da amostra; não altera o projeto.";
                        objectName: "qtquick__MAJOR___switch"
                        text: "Native switch"
                        onToggled: window.log("switch", checked)
                    }
                    Switch { id: disabledSwitch; objectName: "qtquick__MAJOR___disabledSwitch"; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Interruptor desabilitado: mostra o estado ligado sem permitir alteração.";  text: "Disabled"; checked: true; enabled: false }
                }
                GridLayout {
                    columns: 2
                    Layout.fillWidth: true
                    Label { text: "Combo" }
                    ComboBox { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Escolha uma opção da amostra; não altera o esquema do desktop.";
                        objectName: "qtquick__MAJOR___combo"
                        model: ["First option", "Second option", "Third option"]
                        Layout.fillWidth: true
                        onActivated: window.log("combo", currentText)
                    }
                    Label { text: "Disabled combo" }
                    ComboBox { id: disabledCombo; objectName: "qtquick__MAJOR___disabledCombo"; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Lista desabilitada: mostra o estado indisponível sem permitir escolher uma opção.";  model: ["Unavailable"]; enabled: false; Layout.fillWidth: true }
                    Label { text: "Spin box" }
                    SpinBox { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Valor da amostra, sem unidade: de " + from + " a " + to + ", passo " + stepSize + ". Use as setas ou edite; não altera medidas do tema em px.";
                        objectName: "qtquick__MAJOR___spin"
                        from: -99; to: 999; value: 42; editable: true
                        onValueModified: window.log("spin", value)
                    }
                    Label { text: "Disabled spin" }
                    SpinBox { id: disabledSpin; objectName: "qtquick__MAJOR___disabledSpin"; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Campo numérico desabilitado: mostra o valor da amostra sem permitir edição.";  value: 42; enabled: false }
                    Label { text: "Text" }
                    TextField { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Entrada nativa de uma linha: selecione ou edite o texto da amostra; não altera o projeto.";  text: "Editable native TextField"; Layout.fillWidth: true }
                    Label { text: "Disabled text" }
                    TextField { id: disabledText; objectName: "qtquick__MAJOR___disabledText"; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Campo de texto desabilitado: mostra o conteúdo sem permitir edição.";  text: "Unavailable"; enabled: false; Layout.fillWidth: true }
                }
                RowLayout {
                    Label { text: "Slider" }
                    Slider { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Escala da amostra, sem unidade: de " + from + " a " + to + ". Arraste o cursor; não altera o tema.";
                        id: slider
                        objectName: "qtquick__MAJOR___slider"
                        from: 0; to: 100; value: 43
                        Layout.fillWidth: true
                        onMoved: window.log("slider", value)
                    }
                    Slider { id: disabledSlider; objectName: "qtquick__MAJOR___disabledSlider"; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Escala desabilitada: mostra o valor da amostra sem permitir ajuste.";  value: 0.43; enabled: false }
                }
                ProgressBar {
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.delay: 750
                    ToolTip.timeout: 6000
                    ToolTip.text: "Indicador do valor da escala na amostra; não mede uma tarefa em execução."
                    from: 0; to: 100; value: slider.value; Layout.fillWidth: true
                }
                Item { Layout.fillHeight: true }
            }
            Frame {
                ColumnLayout {
                    anchors.fill: parent
                    RowLayout {
                        Repeater {
                            model: ["Item", "State", "Value"]
                            Label { text: modelData; Layout.fillWidth: true }
                        }
                    }
                    TableView {
                        id: table
                        objectName: "qtquick__MAJOR___table"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: galleryTableModel
                        columnSpacing: 1
                        rowSpacing: 1
                        delegate: ItemDelegate {
                            id: tableCellHint
                            objectName: "qtquick__MAJOR___tableCellHint"
                            Component.onCompleted: {
                                if (!window.nativeTableCellHintControl) {
                                    window.nativeTableCellHintControl = tableCellHint
                                }
                            }
                            hoverEnabled: true
                            ToolTip.visible: hovered
                            ToolTip.delay: 750
                            ToolTip.timeout: 6000
                            ToolTip.text: "Célula da tabela: clique para selecionar esta linha de dados artificiais."
                            Connections {
                                target: tableCellHint.ToolTip.toolTip
                                function onVisibleChanged() {
                                    if (target.visible)
                                        window.applyTooltipRole(tableCellHint)
                                }
                            }
                            implicitWidth: 230
                            implicitHeight: 32
                            text: display
                            highlighted: row === window.selectedRow
                            onClicked: {
                                window.selectedRow = row
                                window.log("table cell", row + "," + column)
                            }
                        }
                        ScrollBar.vertical: ScrollBar { id: tableVerticalScrollBar; objectName: "qtquick__MAJOR___tableVertical"; Component.onCompleted: window.nativeTableVerticalBar = tableVerticalScrollBar; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Barra nativa: arraste o cursor para percorrer o conteúdo da amostra.";  policy: ScrollBar.AlwaysOn }
                        ScrollBar.horizontal: ScrollBar { id: tableHorizontalScrollBar; objectName: "qtquick__MAJOR___tableHorizontal"; Component.onCompleted: window.nativeTableHorizontalBar = tableHorizontalScrollBar; hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Barra nativa: arraste o cursor para percorrer o conteúdo da amostra.";  policy: ScrollBar.AlwaysOn }
                        Connections {
                            target: tableVerticalScrollBar
                            function onHoveredChanged() {
                                if (tableVerticalScrollBar.hovered)
                                    window.applyTooltipRole(tableVerticalScrollBar)
                            }
                        }
                        Connections {
                            target: tableHorizontalScrollBar
                            function onHoveredChanged() {
                                if (tableHorizontalScrollBar.hovered)
                                    window.applyTooltipRole(tableHorizontalScrollBar)
                            }
                        }
                        Connections {
                            target: tableVerticalScrollBar.ToolTip.toolTip
                            function onVisibleChanged() {
                                if (target.visible)
                                    window.applyTooltipRole(tableVerticalScrollBar)
                            }
                        }
                        Connections {
                            target: tableHorizontalScrollBar.ToolTip.toolTip
                            function onVisibleChanged() {
                                if (target.visible)
                                    window.applyTooltipRole(tableHorizontalScrollBar)
                            }
                        }
                    }
                }
            }
            ScrollView {
                objectName: "qtquick__MAJOR___scrollView"
                clip: true
                ScrollBar.vertical: ScrollBar {
                    id: scrollViewVerticalBar
                    objectName: "qtquick__MAJOR___scrollViewVertical"
                    Component.onCompleted: {
                        window.nativeScrollViewVerticalBar = scrollViewVerticalBar
                    }
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.delay: 750
                    ToolTip.timeout: 6000
                    ToolTip.text: "Barra vertical nativa: arraste o cursor para percorrer o conteúdo da amostra."
                    policy: ScrollBar.AlwaysOn
                }
                ScrollBar.horizontal: ScrollBar {
                    id: scrollViewHorizontalBar
                    objectName: "qtquick__MAJOR___scrollViewHorizontal"
                    Component.onCompleted: {
                        window.nativeScrollViewHorizontalBar = scrollViewHorizontalBar
                    }
                    hoverEnabled: true
                    ToolTip.visible: hovered
                    ToolTip.delay: 750
                    ToolTip.timeout: 6000
                    ToolTip.text: "Barra horizontal nativa: arraste o cursor para percorrer o conteúdo da amostra."
                    policy: ScrollBar.AlwaysOn
                }
                Connections {
                    target: scrollViewVerticalBar
                    function onHoveredChanged() {
                        if (scrollViewVerticalBar.hovered)
                            window.applyTooltipRole(scrollViewVerticalBar)
                    }
                }
                Connections {
                    target: scrollViewHorizontalBar
                    function onHoveredChanged() {
                        if (scrollViewHorizontalBar.hovered)
                            window.applyTooltipRole(scrollViewHorizontalBar)
                    }
                }
                Connections {
                    target: scrollViewVerticalBar.ToolTip.toolTip
                    function onVisibleChanged() {
                        if (target.visible)
                            window.applyTooltipRole(scrollViewVerticalBar)
                    }
                }
                Connections {
                    target: scrollViewHorizontalBar.ToolTip.toolTip
                    function onVisibleChanged() {
                        if (target.visible)
                            window.applyTooltipRole(scrollViewHorizontalBar)
                    }
                }
                TextArea { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Editor nativo de várias linhas: selecione, copie ou edite a amostra; não modifica arquivos pessoais.";
                    objectName: "qtquick__MAJOR___textArea"
                    text: artificialText
                    wrapMode: TextEdit.NoWrap
                    selectByMouse: true
                }
            }
        }
        RowLayout {
            Label {
                id: statusLabel
                text: "Artificial data only; controls inherit the private KDE scheme."
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            Button { hoverEnabled: true; ToolTip.visible: hovered; ToolTip.delay: 750; ToolTip.timeout: 6000; ToolTip.text: "Salva a captura e o JSON desta janela no perfil privado; não instala o tema."; text: "Save window proof"; onClicked: window.log("capture", "requested") }
        }
    }
}
'''


def binding_inventory(major):
    """Locate binding modules without initializing Qt or contacting a display."""
    required = ('QtCore', 'QtGui', 'QtWidgets', 'QtQml', 'QtQuick')
    modules = {}
    for name in required:
        qualified = f'PyQt{major}.{name}'
        try:
            found = importlib.util.find_spec(qualified)
        except (ImportError, ValueError):
            found = None
        modules[qualified] = found.origin if found else None
    return {'toolkit': f'QtQuick{major}', 'qtMajor': major,
            'status': 'ready' if all(modules.values()) else 'unavailable',
            'modules': modules, 'gui_started': False, 'qt_initialized': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qt-major', type=int, choices=(5, 6), default=6)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--guard-only', action='store_true')
    parser.add_argument('--verificar-only', action='store_true', help='Inspect bindings only; never initialize Qt')
    args = parser.parse_args(argv)
    if args.verificar_only:
        inventory = binding_inventory(args.qt_major)
        print(json.dumps(inventory, sort_keys=True))
        return 0 if inventory['status'] == 'ready' else 3
    guards = private_guards()  # Before all Qt imports/application initialization.
    output = (args.output or Path('/home/domainos-test') / f'qtquick{args.qt_major}-proof').resolve()
    if not output.is_relative_to(Path('/home/domainos-test')):
        raise RuntimeError('Proof output must remain inside fake HOME')
    if args.guard_only:
        print(json.dumps(guards, sort_keys=True))
        return 0
    inventory = binding_inventory(args.qt_major)
    if inventory['status'] != 'ready':
        raise RuntimeError(f'QtQuick{args.qt_major} bindings unavailable: ' +
                           ', '.join(name for name, path in inventory['modules'].items() if not path))
    # Native Controls style selection is process-local and precedes Qt initialization.
    # It is not a QApplication style/palette override or custom component drawing.
    os.environ['QT_QUICK_CONTROLS_STYLE'] = 'org.kde.desktop'
    if args.qt_major == 6:
        from PyQt6.QtCore import (Qt, QObject, QModelIndex, QAbstractTableModel,
                                 QTimer, QUrl, QT_VERSION_STR, PYQT_VERSION_STR, qVersion)
        from PyQt6.QtGui import QPalette
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickWindow
    else:
        from PyQt5.QtCore import (Qt, QObject, QModelIndex, QAbstractTableModel,
                                 QTimer, QUrl, QT_VERSION_STR, PYQT_VERSION_STR, qVersion)
        from PyQt5.QtGui import QPalette
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtQml import QQmlApplicationEngine
        from PyQt5.QtQuick import QQuickWindow
    try:
        quick_style_api = importlib.import_module(f'PyQt{args.qt_major}.QtQuickControls2').QQuickStyle
    except ImportError:
        quick_style_api = None  # Optional diagnostic binding, not a rendering dependency.
    display_role = int(Qt.ItemDataRole.DisplayRole)

    class ArtificialTable(QAbstractTableModel):
        def rowCount(self, parent=QModelIndex()):
            return 0 if parent.isValid() else 60

        def columnCount(self, parent=QModelIndex()):
            return 0 if parent.isValid() else 3

        def data(self, index, role=display_role):
            if index.isValid() and role == display_role:
                return (f'Object {index.row() + 1}', 'Available', str(index.row() * 3))[index.column()]
            return None

        def roleNames(self):
            return {display_role: b'display'}

    app = QApplication(sys.argv[:1])
    app.setApplicationName(f'DomainOS Theme Preview — QtQuick{args.qt_major}')
    app.setDesktopFileName(f'org.irixclassic.preview.qtquick{args.qt_major}')
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o700)
    data_path = output / 'artificial-scroll-text.txt'
    data_path.write_text(('Native QtQuick ScrollView and TextArea: artificial content only. ' * 4 + '\n') * 45)
    data_path.chmod(0o600)
    qml_path = output / 'gallery.qml'
    qml_source = QML_SOURCE.replace('__MAJOR__', str(args.qt_major))
    if args.qt_major == 5:
        # QtQuick5's installed Kirigami module does not expose the attached
        # Theme object used by the QtQuick6 tooltip-role diagnostic.
        qml_source = qml_source.replace('import org.kde.kirigami 2.0 as Kirigami\n', '')
        qml_source = re.sub(r'    Rectangle \{\n        id: tooltipRolePaletteProbe.*?\n    \}\n', '', qml_source, count=1, flags=re.S)
        qml_source = re.sub(r'    Text \{\n        id: tooltipRoleTextProbe.*?\n    \}\n', '', qml_source, count=1, flags=re.S)
        qml_source = re.sub(r'    readonly property string nativeTooltipPalette: JSON.stringify\(\{.*?\n    \}\)\n', '', qml_source, count=1, flags=re.S)
    qml_path.write_text(qml_source)
    qml_path.chmod(0o600)
    record = {'scope': 'Owned bwrap/Xephyr preview only; native KDE QtQuick controls',
              'guards': guards, 'qtMajor': args.qt_major, 'qtVersion': QT_VERSION_STR,
              'qtRuntimeVersion': qVersion(), 'pyqtVersion': PYQT_VERSION_STR,
              'qmlSource': str(qml_path), 'dataSource': str(data_path),
              'actions': [], 'qmlWarnings': [], 'customDrawing': False,
              'paletteOverride': False, 'fontOverride': False}
    engine = QQmlApplicationEngine()
    engine.warnings.connect(lambda messages: record['qmlWarnings'].extend(str(message.toString()) for message in messages))
    model = ArtificialTable(engine)
    engine.rootContext().setContextProperty('galleryTableModel', model)
    engine.rootContext().setContextProperty('artificialText', data_path.read_text())
    engine.rootContext().setContextProperty('runtimeDescription', f'Qt {qVersion()} | org.kde.desktop')
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    roots = engine.rootObjects()
    if len(roots) != 1 or not isinstance(roots[0], QQuickWindow):
        raise RuntimeError('Native QtQuick gallery failed to load: ' + '; '.join(record['qmlWarnings']))
    window = roots[0]

    def qml_sources():
        sources = set()
        for node in (window, *window.findChildren(QObject)):
            context = engine.contextForObject(node)
            if context and not context.baseUrl().isEmpty():
                sources.add(context.baseUrl().toString())
        return sorted(sources)

    def save_proof(screenshot=False):
        palette = app.palette()
        groups = {'active': QPalette.ColorGroup.Active, 'inactive': QPalette.ColorGroup.Inactive,
                  'disabled': QPalette.ColorGroup.Disabled}
        roles = ('Window', 'WindowText', 'Base', 'Text', 'Button', 'ButtonText', 'Highlight', 'HighlightedText')
        sources = qml_sources()
        record.update(platform=app.platformName(), platformTheme=os.environ.get('QT_QPA_PLATFORMTHEME'),
                      quickStyle={'requested': os.environ['QT_QUICK_CONTROLS_STYLE'],
                                  'name': quick_style_api.name() if quick_style_api else None,
                                  'nameApiAvailable': quick_style_api is not None,
                                  'kdeDesktopQmlObserved': any('/org/kde/desktop/' in path or
                                                              '/org.kde.desktop/' in path for path in sources)},
                      loadedQmlContexts=sources,
                      nativeHints=json.loads(window.property('nativeHints')),
                      tooltipPalette=(json.loads(window.property('nativeTooltipPalette'))
                                      if args.qt_major == 6 else None),
                      widgetStyle={'objectName': app.style().objectName(), 'className': app.style().metaObject().className()},
                      font=app.font().toString(), nativeControlFont=window.property('nativeFont'),
                      selections=selection(),
                      palette={group: {role: palette.color(value, getattr(QPalette.ColorRole, role)).name()
                                       for role in roles} for group, value in groups.items()},
                      nativeControlPalettes=json.loads(window.property('nativePalettes')),
                      window={'objectName': window.objectName(), 'width': window.width(), 'height': window.height(),
                              'x': window.x(), 'y': window.y()},
                      apiLimits=['QtQuick ScrollBar has no native Motif arrow buttons.',
                                 'TableView uses native ItemDelegate cells, not historical TreeView geometry.'])
        if screenshot and window.isVisible():
            path = output / f'qtquick{args.qt_major}.png'
            record['screenshotSaved'] = window.grabWindow().save(str(path), 'PNG')
            record['screenshot'] = str(path)
        target = output / 'RESULTADO.json'
        target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
        target.chmod(0o600)

    def action_recorded(action, detail):
        record['actions'].append({'action': action, 'detail': detail})
        save_proof(action == 'capture')

    window.actionRecorded.connect(action_recorded)
    app.aboutToQuit.connect(lambda: save_proof(False))
    save_proof(False)
    # QA snapshot of this private window only; it never delays an interactive action.
    QTimer.singleShot(1000, lambda: save_proof(True))
    return app.exec()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, ImportError) as error:
        print('Private QtQuick demo refused: ' + str(error), file=sys.stderr)
        sys.exit(2)
