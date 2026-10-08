// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Values preserved from upstream/Irixiumrc; defaults follow KDE Aurorae.
import QtQuick

QtObject {
    property int borderSize: 3
    property real buttonSizeFactor: 1.0
    property real logicalScale: 1.0
    readonly property int borderLeft: Math.round(7 * logicalScale)
    readonly property int borderRight: Math.round(7 * logicalScale)
    readonly property int borderBottom: Math.round(7 * logicalScale)
    readonly property int titleEdgeTop: Math.round(7 * logicalScale)
    readonly property int titleEdgeBottom: Math.round(1 * logicalScale)
    readonly property int titleEdgeLeft: Math.round(9 * logicalScale)
    readonly property int titleEdgeRight: Math.round(9 * logicalScale)
    readonly property int titleEdgeTopMaximized: Math.round(4 * logicalScale)
    readonly property int titleEdgeBottomMaximized: Math.round(4 * logicalScale)
    readonly property int titleEdgeLeftMaximized: Math.round(6 * logicalScale)
    readonly property int titleEdgeRightMaximized: Math.round(6 * logicalScale)
    readonly property int titleBorderLeft: Math.round(12 * logicalScale)
    readonly property int titleBorderRight: Math.round(12 * logicalScale)
    readonly property int titleHeight: Math.round(26 * logicalScale)
    readonly property int buttonWidth: Math.round(22 * logicalScale)
    readonly property int buttonHeight: Math.round(22 * logicalScale)
    readonly property int buttonSpacing: Math.round(6 * logicalScale)
    readonly property int buttonMarginTop: Math.round(2 * logicalScale)
    readonly property int buttonMarginTopMaximized: Math.round(2 * logicalScale)
    readonly property int paddingLeft: Math.round(0 * logicalScale)
    readonly property int paddingRight: Math.round(0 * logicalScale)
    readonly property int paddingTop: Math.round(0 * logicalScale)
    readonly property int paddingBottom: Math.round(0 * logicalScale)
    readonly property int buttonWidthMinimize: Math.round(22 * logicalScale)
    readonly property int buttonWidthMaximizeRestore: Math.round(22 * logicalScale)
    readonly property int buttonWidthMenu: Math.round(22 * logicalScale)
    readonly property color activeTextColor: "#000000"
    readonly property color inactiveTextColor: "#000000"
}
