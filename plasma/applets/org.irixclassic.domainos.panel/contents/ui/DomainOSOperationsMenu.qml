// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls

// Own popup for the fixed local operations. All rows are measured before
// opening; native per-window context menus keep their existing providers.
Controls.Popup {
    id: menu
    objectName: "domainosSelectionOperations"
    required property var iconbox
    property string title: qsTr("Janelas selecionadas")
    property Item anchorItem: null
    property int currentIndex: -1
    property string lastError: ""
    readonly property QtObject colors: iconbox.domainosPalette
    readonly property var items: [heading, pin, firstSeparator, columns, rows,
        mosaic, collect, secondSeparator, maximize, minimize]
    readonly property int count: items.length
    readonly property real naturalContentWidth: items.reduce((width, item) =>
        Math.max(width, item.implicitWidth), 0)
    readonly property real naturalContentHeight: {
        // All ten fixed rows exist even while the popup is hidden. Item.visible
        // is effective visibility here, so filtering on it would measure zero.
        return items.reduce((height, item) => height + item.implicitHeight, 0)
            + Math.max(0, items.length - 1) * menuRows.spacing
    }
    readonly property real maximumWidth: Math.max(1, (anchorItem ? anchorItem.Screen.width : 400) - 8)
    readonly property real maximumHeight: Math.max(1, (anchorItem ? anchorItem.Screen.height : 600) - 8)
    readonly property real preferredWidth: Math.max(1, Math.min(maximumWidth,
        Math.ceil(naturalContentWidth + leftPadding + rightPadding)))
    readonly property real preferredHeight: Math.max(1, Math.min(maximumHeight,
        naturalContentHeight + topPadding + bottomPadding))
    implicitWidth: preferredWidth
    implicitHeight: preferredHeight
    popupType: Controls.Popup.Window
    focus: true
    enter: null
    exit: null
    padding: 8
    leftInset: 0
    rightInset: 0
    topInset: 0
    bottomInset: 0
    closePolicy: Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutsideParent
    signal commandRequested(string command)
    signal pinRequested()
    signal failure(string message)

    DomainOSPopupPlacement {
        id: placement
        popup: menu
        popupAnchor: menu.anchorItem
        positionAnchor: menu.anchorItem
    }

    function itemAt(index) { return index >= 0 && index < count ? items[index] : null }
    function reportFailure(message) { lastError = message; failure(message); return false }
    function prepareForAnchor(anchor) {
        if (!anchor || !anchor.Window.window)
            return reportFailure(qsTr("Não foi possível localizar a janela do painel para abrir as operações."))
        if (!iconbox || !iconbox.menuSelection.length
                || !iconbox.menuSelection.every(iconbox.checkTarget))
            return reportFailure(qsTr("A seleção mudou antes de abrir as operações."))
        anchorItem = anchor
        parent = anchor
        menuRows.forceLayout()
        // As in the existing member picker, reset the public natural size
        // before open(): a former native-window resize must not win this frame.
        width = preferredWidth
        width = undefined
        height = preferredHeight
        height = undefined
        placement.positionPopup()
        lastError = ""
        return width > 0 && height > 0
    }
    function openAt(anchor) {
        if (visible || opened)
            return reportFailure(qsTr("O menu de operações já está aberto."))
        if (!prepareForAnchor(anchor)) return false
        open()
        return true // accepted for opening; onOpened reports the actual map.
    }
    function enabledAction(index) {
        const item = itemAt(index)
        return !!item && item.operation !== undefined && item.operation.length > 0
            && item.enabled
    }
    function focusAction(index, reason) {
        if (!enabledAction(index)) return false
        currentIndex = index
        const item = itemAt(index)
        item.forceActiveFocus(reason === undefined ? Qt.TabFocusReason : reason)
        // Keep the keyboard-selected row inside the bounded viewport.
        const view = scroller.contentItem
        if (view && view.contentY !== undefined) {
            const top = item.y, bottom = top + item.height
            const viewport = scroller.availableHeight
            const desired = top < view.contentY ? top
                : bottom > view.contentY + viewport ? bottom - viewport : view.contentY
            view.contentY = Math.max(0, Math.min(desired,
                Math.max(0, scroller.contentHeight - viewport)))
        }
        return true
    }
    function moveFocus(direction) {
        let index = currentIndex
        if (index < 0) index = direction > 0 ? -1 : 0
        for (let step = 0; step < count; ++step) {
            index = (index + direction + count) % count
            if (focusAction(index)) return true
        }
        currentIndex = -1
        return false
    }
    function endFocus(last) {
        for (let step = 0; step < count; ++step) {
            const index = last ? count - 1 - step : step
            if (focusAction(index)) return true
        }
        return false
    }
    function invoke(operation) {
        const index = items.findIndex(item => item.operation === operation)
        if (!enabledAction(index) || !iconbox.menuSelection.every(iconbox.checkTarget))
            return reportFailure(qsTr("Essa operação não está mais disponível para a seleção."))
        // Close the UI before dispatch, preserving the exact checked snapshot.
        close()
        if (operation === "pin") pinRequested()
        else commandRequested(operation)
        return true
    }
    Connections {
        target: menu
        function onOpened() { menu.currentIndex = -1; menu.moveFocus(1) }
        function onClosed() { menu.currentIndex = -1 }
    }
    background: Bevel {
        paletteOverride: menu.colors
        face: menu.colors.background
        light: menu.colors.highlight
        dark: menu.colors.dark
        texture: Qt.resolvedUrl("../images/metal-weave.svg")
    }
    contentItem: Controls.ScrollView {
        id: scroller
        objectName: "domainosOperationsScrollView"
        Accessible.role: Accessible.PopupMenu
        Accessible.name: menu.title
        contentWidth: availableWidth
        contentHeight: menu.naturalContentHeight
        clip: true
        Controls.ScrollBar.horizontal: DomainOSViewScrollBar {
            scrollView: scroller
            colorPalette: menu.colors
            policy: Controls.ScrollBar.AlwaysOff
        }
        Controls.ScrollBar.vertical: DomainOSViewScrollBar {
            scrollView: scroller
            colorPalette: menu.colors
            policy: scroller.contentHeight > scroller.availableHeight
                ? Controls.ScrollBar.AlwaysOn : Controls.ScrollBar.AlwaysOff
        }
        Keys.priority: Keys.BeforeItem
        Keys.onPressed: event => {
            if (event.key === Qt.Key_Down) menu.moveFocus(1)
            else if (event.key === Qt.Key_Up) menu.moveFocus(-1)
            else if (event.key === Qt.Key_Home) menu.endFocus(false)
            else if (event.key === Qt.Key_End) menu.endFocus(true)
            else if (event.key === Qt.Key_Tab) menu.moveFocus(event.modifiers & Qt.ShiftModifier ? -1 : 1)
            else if (event.key === Qt.Key_Backtab) menu.moveFocus(-1)
            else if (event.key === Qt.Key_Escape) menu.close()
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) {
                const row = menu.itemAt(menu.currentIndex)
                if (row && menu.enabledAction(menu.currentIndex)) menu.invoke(row.operation)
            } else { event.accepted = false; return }
            event.accepted = true
        }
        Column {
            id: menuRows
            width: scroller.availableWidth
            spacing: 2
            Text {
                id: heading
                width: parent.width
                height: implicitHeight
                text: menu.iconbox.menuSelection.length === 1 ? qsTr("1 janela selecionada")
                    : qsTr("%1 janelas selecionadas").arg(menu.iconbox.menuSelection.length)
                color: menu.colors.text
                font: menu.font
                topPadding: 4
                bottomPadding: 4
                leftPadding: 8
                rightPadding: 8
                renderType: Text.NativeRendering
                Accessible.role: Accessible.StaticText
            }
            OperationRow {
                id: pin
                objectName: "domainosTemporaryPinSelection"
                operation: "pin"
                text: qsTr("Fixar janelas temporariamente na Iconbox")
                enabled: menu.iconbox.menuSelection.length > 0 && !!menu.iconbox.controller
                    && menu.iconbox.menuSelection.some(window =>
                        !menu.iconbox.controller.temporaryPinned(window.key, window.pid))
            }
            Separator { id: firstSeparator }
            OperationRow {
                id: columns; objectName: "domainosBatchColumns"; operation: "columns"
                text: qsTr("Dispor em colunas, lado a lado")
                enabled: menu.iconbox.geometryReady(menu.iconbox.menuSelection)
            }
            OperationRow {
                id: rows; objectName: "domainosBatchRows"; operation: "rows"
                text: qsTr("Dispor em linhas, uma sobre a outra")
                enabled: menu.iconbox.geometryReady(menu.iconbox.menuSelection)
            }
            OperationRow {
                id: mosaic; objectName: "domainosBatchMosaic"; operation: "mosaic"
                text: qsTr("Dispor em mosaico")
                enabled: menu.iconbox.geometryReady(menu.iconbox.menuSelection)
            }
            OperationRow {
                id: collect; objectName: "domainosBatchCollect"; operation: "collect"
                text: qsTr("Reunir no desktop e monitor atuais")
                enabled: menu.iconbox.geometryReady(menu.iconbox.menuSelection, "collect")
            }
            Separator { id: secondSeparator }
            OperationRow {
                id: maximize; objectName: "domainosBatchMaximize"; operation: "maximize"
                text: qsTr("Maximizar selecionadas")
                enabled: menu.iconbox.geometryReady(menu.iconbox.menuSelection, "maximize")
            }
            OperationRow {
                id: minimize; objectName: "domainosBatchMinimize"; operation: "minimize"
                text: qsTr("Minimizar selecionadas")
                enabled: menu.iconbox.geometryReady(menu.iconbox.menuSelection, "minimize")
            }
        }
    }

    component Separator: Item {
        width: menuRows.width
        implicitWidth: 16
        implicitHeight: 2
        height: implicitHeight
        Rectangle { width: parent.width; height: 1; color: menu.colors.dark }
        Rectangle { y: 1; width: parent.width; height: 1; color: menu.colors.highlight }
    }
    component OperationRow: Controls.AbstractButton {
        id: row
        required property string operation
        readonly property bool emphasized: hovered || activeFocus
        width: menuRows.width
        implicitWidth: label.implicitWidth + leftPadding + rightPadding
        implicitHeight: label.implicitHeight + topPadding + bottomPadding
        height: implicitHeight
        leftPadding: 8
        rightPadding: 8
        topPadding: 4
        bottomPadding: 4
        font: menu.font
        hoverEnabled: true
        activeFocusOnTab: true
        Accessible.role: Accessible.MenuItem
        Accessible.name: text
        onClicked: menu.invoke(operation)
        onHoveredChanged: if (hovered && enabled) menu.currentIndex = menu.items.indexOf(row)
        contentItem: Text {
            id: label
            text: row.text
            font: row.font
            elide: Text.ElideRight
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            color: row.emphasized && row.enabled ? menu.colors.white : menu.colors.text
            opacity: row.enabled ? 1 : 0.6
        }
        background: Bevel {
            paletteOverride: menu.colors
            face: row.emphasized && row.enabled ? menu.colors.blue : menu.colors.background
            light: menu.colors.highlight
            dark: menu.colors.dark
            thickness: 1
            simpleRelief: true
            sunken: row.down
            visible: row.emphasized || row.down
        }
    }
}
