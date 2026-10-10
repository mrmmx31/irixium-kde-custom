// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

// Qt 6.8 Popup.Window does not apply the Item popup's edge constraints.
// Its dimensions are physical pixels, even when its button is scaled. Measure
// in screen coordinates, then map only its position through the real launcher.
Item {
    id: placement
    property var popup: null
    property Item popupAnchor: null
    property Item positionAnchor: null
    property bool alignRight: false
    property bool centerOnAnchor: false
    property real gap: 4
    property bool positioning: false
    property var currentMenu: null
    DomainOSControlPalette { target: placement.popup || placement.currentMenu }
    DomainOSControlPalette {
        target: placement.popup ? placement.popup.contentItem
            : placement.currentMenu ? placement.currentMenu.contentItem : null
    }
    DomainOSControlPalette {
        target: placement.popup ? placement.popup.background
            : placement.currentMenu ? placement.currentMenu.background : null
    }
    // Qt gives each submenu another window/content tree as well. Reuse the
    // existing menu objects; only their local color roles need the same scope.
    function subMenus(menu) {
        const result = []
        if (!menu || typeof menu.itemAt !== "function") return result
        for (let index = 0; index < menu.count; ++index) {
            const item = menu.itemAt(index)
            const child = item ? item.subMenu : null
            if (child) result.push(child, ...subMenus(child))
        }
        return result
    }
    Repeater {
        model: placement.subMenus(placement.popup || placement.currentMenu)
        delegate: Item {
            id: submenuScope
            required property var modelData
            visible: false
            DomainOSControlPalette { target: submenuScope.modelData }
            DomainOSControlPalette { target: submenuScope.modelData.contentItem }
            DomainOSControlPalette { target: submenuScope.modelData.background }
        }
    }

    // Dialogs and non-menu popups keep their actual anchor and normal sizing.
    // Map the physical window frame back through that anchor's drawing scale.
    // Layout changes reposition synchronously, without a timer or repaint loop.
    function positionPopup() {
        const anchor = popupAnchor
        if (positioning || !popup || !anchor || !anchor.Window.window) return
        positioning = true
        try {
            if (popup.parent !== anchor) popup.parent = anchor
            const screen = anchor.Screen
            const left = screen.virtualX + 4
            const top = screen.virtualY + 4
            const right = screen.virtualX + screen.width - 4
            const bottom = screen.virtualY + screen.height - 4
            const insetLeft = Math.max(0, -popup.leftInset)
            const insetTop = Math.max(0, -popup.topInset)
            const frameWidth = popup.width + insetLeft + Math.max(0, -popup.rightInset)
            const frameHeight = popup.height + insetTop + Math.max(0, -popup.bottomInset)
            const positionAnchor = placement.positionAnchor || anchor
            const origin = positionAnchor.mapToGlobal(0, 0)
            const end = positionAnchor.mapToGlobal(positionAnchor.width, positionAnchor.height)
            let x = alignRight ? end.x - frameWidth : origin.x
            let y = origin.y - frameHeight - gap
            if (centerOnAnchor) {
                x = (origin.x + end.x - frameWidth) / 2
                y = (origin.y + end.y - frameHeight) / 2
            } else if (y < top) {
                const below = end.y + gap
                if (below + frameHeight <= bottom || bottom - end.y >= origin.y - top)
                    y = below
            }
            x = Math.max(left, Math.min(x, right - frameWidth))
            y = Math.max(top, Math.min(y, bottom - frameHeight))
            const position = anchor.mapFromGlobal(x, y)
            // Qt subtracts window insets in parent coordinates before mapping
            // to global coordinates, including for a scaled parent item.
            popup.x = position.x + insetLeft
            popup.y = position.y + insetTop
        } finally {
            positioning = false
        }
    }
    Connections {
        target: placement.popup
        function onAboutToShow() { placement.positionPopup() }
        function onWidthChanged() { if (placement.popup.visible) placement.positionPopup() }
        function onHeightChanged() { if (placement.popup.visible) placement.positionPopup() }
    }
    function showMenu(menu, anchor, point) {
        if (!anchor || !anchor.Window.window) return
        currentMenu = menu
        // Menu's ListView lays out its delegates lazily. Measure every row
        // before positioning the very first opening, not only later openings.
        if (menu.contentItem && typeof menu.contentItem.forceLayout === "function")
            menu.contentItem.forceLayout()
        // The desktop style's ListView can still report only its first row
        // before showing. The actual menu items already know their natural
        // sizes; include all rows/separators without waiting for a repaint.
        let contentWidth = 0
        let contentHeight = 0
        for (let index = 0; index < menu.count; ++index) {
            const item = menu.itemAt(index)
            if (!item) continue
            contentWidth = Math.max(contentWidth, item.implicitWidth)
            contentHeight += item.implicitHeight
        }
        contentHeight += Math.max(0, menu.count - 1) * (menu.contentItem.spacing || 0)
        const screen = anchor.Screen
        const margin = 4
        const gap = 4
        const left = screen.virtualX + margin
        const top = screen.virtualY + margin
        const right = screen.virtualX + screen.width - margin
        const bottom = screen.virtualY + screen.height - margin
        const origin = point ? anchor.mapToGlobal(point.x, point.y) : anchor.mapToGlobal(0, 0)
        const end = point ? origin : anchor.mapToGlobal(0, anchor.height)
        const insetLeft = Math.max(0, -menu.leftInset)
        const insetTop = Math.max(0, -menu.topInset)
        const insetRight = Math.max(0, -menu.rightInset)
        const insetBottom = Math.max(0, -menu.bottomInset)
        menu.width = Math.min(right - left - insetLeft - insetRight,
            Math.max(menu.implicitBackgroundWidth + menu.leftInset + menu.rightInset,
                     contentWidth + menu.leftPadding + menu.rightPadding))
        menu.height = Math.min(bottom - top - insetTop - insetBottom,
            Math.max(menu.implicitBackgroundHeight + menu.topInset + menu.bottomInset,
                     contentHeight + menu.topPadding + menu.bottomPadding))
        const frameWidth = menu.width + insetLeft + insetRight
        const frameHeight = menu.height + insetTop + insetBottom
        const above = origin.y - frameHeight - gap
        const below = end.y + gap
        let y = above >= top ? above : below
        if (above < top && below + frameHeight > bottom)
            y = origin.y - top > bottom - end.y ? above : below
        const x = Math.max(left, Math.min(origin.x, right - frameWidth))
        y = Math.max(top, Math.min(y, bottom - frameHeight))
        const position = anchor.mapFromGlobal(x, y)
        // The overload with an explicit parent/position preserves Menu's
        // keyboard setup without using the cursor's unchecked position.
        // Retain the real launcher as parent so CloseOnPressOutsideParent can
        // pass its second click to that button instead of dismissing the menu
        // before the button sees the press. Width/height stay physical pixels;
        // insets are subtracted by Qt in the parent's local coordinates.
        menu.popup(anchor, position.x + insetLeft, position.y + insetTop)
    }
}
