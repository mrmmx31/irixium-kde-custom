// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls
import org.kde.plasma.core as PlasmaCore

// P04 candidate: KDE-owned native window with our measured Motif panel.
// Not installed until lifecycle, positioning and real-session checks pass.
PlasmaCore.Dialog {
    id: menu
    objectName: "domainosSelectionOperations"
    required property var iconbox
    title: qsTr("Operações das janelas selecionadas")
    property font font: Qt.application.font
    readonly property bool opened: visible
    property rect invocationRect: Qt.rect(0, 0, 0, 0)
    property real heightLimit: maximumHeight
    property Item anchorItem: null
    // A stable child survives the chooser closing. Native Wayland placement
    // uses this button-sized anchor rather than the entire Iconbox.
    property Item placementAnchor: Item { parent: menu.anchorItem; visible: false }
    property int currentIndex: -1
    property string lastError: ""
    readonly property QtObject colors: iconbox.domainosPalette
    readonly property var items: [heading, pin, firstSeparator, columns, rows,
        mosaic, collect, secondSeparator, maximize, restore, minimize]
    readonly property int count: items.length
    readonly property real naturalContentWidth: items.reduce((width, item) =>
        Math.max(width, item.implicitWidth), 0)
    readonly property real naturalContentHeight: {
        // All eleven fixed rows exist even while the popup is hidden. Item.visible
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
    type: PlasmaCore.Dialog.PopupMenu
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    location: PlasmaCore.Types.BottomEdge
    backgroundHints: PlasmaCore.Dialog.NoBackground
    hideOnWindowDeactivate: true
    property real leftPadding: 8
    property real rightPadding: 8
    property real topPadding: 8
    property real bottomPadding: 8
    signal aboutToShow()
    signal openedPanel()
    signal closed()
    signal commandRequested(string command)
    signal pinRequested()
    signal failure(string message)

    function positionPanel() {
        if (!anchorItem) return
        const screen = anchorItem.Screen
        const left = screen.virtualX + 4, top = screen.virtualY + 4
        const right = screen.virtualX + screen.width - 4
        const bottom = screen.virtualY + screen.height - 4
        const above = Math.max(0, invocationRect.y - top - 4)
        const below = Math.max(0, bottom - invocationRect.y - invocationRect.height - 4)
        const useAbove = above >= preferredHeight || above >= below
        heightLimit = Math.max(1, useAbove ? above : below)
        x = Math.max(left, Math.min(invocationRect.x, right - preferredWidth))
        const desired = useAbove ? invocationRect.y - mainItem.height - 4
            : invocationRect.y + invocationRect.height + 4
        y = Math.max(top, Math.min(desired, bottom - mainItem.height))
    }
    function open() {
        aboutToShow()
        visible = true
        positionPanel()
        requestActivate()
        focusAction(currentIndex)
    }
    onActiveChanged: {
        if (active && visible) focusAction(currentIndex)
    }
    onVisibleChanged: {
        if (visible) {
            currentIndex = -1
            moveFocus(1)
            openedPanel()
            // A Plasma Dialog is mapped asynchronously on some X11 window
            // managers. Repeat activation after the native window exists so
            // its first focused row receives keyboard navigation.
            Qt.callLater(()=>{
                if (!visible) return
                requestActivate()
                focusAction(currentIndex)
            })
        } else {
            currentIndex = -1
            closed()
        }
    }
    function itemAt(index) { return index >= 0 && index < count ? items[index] : null }
    function reportFailure(message) { lastError = message; failure(message); return false }
    function prepareForAnchor(anchor, sourceRect) {
        if (!anchor || !anchor.Window.window)
            return reportFailure(qsTr("Não foi possível localizar a janela do painel para abrir as operações."))
        if (!iconbox || !iconbox.menuSelection.length
                || !iconbox.menuSelection.every(iconbox.checkTarget))
            return reportFailure(qsTr("A seleção mudou antes de abrir as operações."))
        anchorItem = anchor
        const origin = anchor.mapToGlobal(0, 0)
        const extent = anchor.mapToGlobal(anchor.width, anchor.height)
        if (sourceRect && (![sourceRect.x,sourceRect.y,sourceRect.width,sourceRect.height].every(Number.isFinite)
                || sourceRect.width <= 0 || sourceRect.height <= 0))
            return reportFailure(qsTr("A área do botão de operações é inválida."))
        invocationRect = sourceRect || Qt.rect(origin.x, origin.y, extent.x-origin.x, extent.y-origin.y)
        const localOrigin=anchor.mapFromGlobal(invocationRect.x,invocationRect.y)
        const localEnd=anchor.mapFromGlobal(invocationRect.x+invocationRect.width,invocationRect.y+invocationRect.height)
        placementAnchor.x=localOrigin.x;placementAnchor.y=localOrigin.y
        placementAnchor.width=localEnd.x-localOrigin.x;placementAnchor.height=localEnd.y-localOrigin.y
        visualParent=placementAnchor
        menuRows.forceLayout()
        positionPanel()
        lastError = ""
        return mainItem.width > 0 && mainItem.height > 0
    }
    function openAt(anchor, sourceRect) {
        if (visible || opened)
            return reportFailure(qsTr("O menu de operações já está aberto."))
        if (!prepareForAnchor(anchor, sourceRect)) return false
        open()
        return true // accepted for opening; openedPanel reports visibility.
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
    function handleKey(event) {
        if (event.key === Qt.Key_Down) moveFocus(1)
        else if (event.key === Qt.Key_Up) moveFocus(-1)
        else if (event.key === Qt.Key_Home) endFocus(false)
        else if (event.key === Qt.Key_End) endFocus(true)
        else if (event.key === Qt.Key_Tab) moveFocus(event.modifiers & Qt.ShiftModifier ? -1 : 1)
        else if (event.key === Qt.Key_Backtab) moveFocus(-1)
        else if (event.key === Qt.Key_Escape) close()
        else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) {
            const row = itemAt(currentIndex)
            if (row && enabledAction(currentIndex)) invoke(row.operation)
        } else { event.accepted = false; return false }
        event.accepted = true
        return true
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
    mainItem: FocusScope {
        focus: true
        width: menu.preferredWidth
        height: Math.min(menu.preferredHeight, menu.heightLimit)
        Bevel {
        anchors.fill: parent
        paletteOverride: menu.colors
        face: menu.colors.background
        light: menu.colors.highlight
        dark: menu.colors.dark
    }
    Controls.ScrollView {
        anchors.fill: parent
        anchors.leftMargin: menu.leftPadding
        anchors.rightMargin: menu.rightPadding
        anchors.topMargin: menu.topPadding
        anchors.bottomMargin: menu.bottomPadding
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
        Keys.onPressed: event => menu.handleKey(event)
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
                id: restore; objectName: "domainosBatchRestore"; operation: "restore"
                text: qsTr("Restaurar selecionadas")
                helpText: qsTr("Remove minimização e maximização, traz todo o conjunto selecionado à frente e deixa a última janela selecionada ativa, sem alterar manualmente sua posição.")
                enabled: menu.iconbox.geometryReady(menu.iconbox.menuSelection, "restore")
            }
            OperationRow {
                id: minimize; objectName: "domainosBatchMinimize"; operation: "minimize"
                text: qsTr("Minimizar selecionadas")
                enabled: menu.iconbox.geometryReady(menu.iconbox.menuSelection, "minimize")
            }
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
        property string helpText: ""
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
        Accessible.description: helpText
        Controls.ToolTip.visible: hovered && helpText.length > 0
        Controls.ToolTip.delay: 700
        Controls.ToolTip.text: helpText
        Keys.priority: Keys.BeforeItem
        Keys.onPressed: event => menu.handleKey(event)
        onClicked: menu.invoke(operation)
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
