// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-FileCopyrightText: 2017 Marco Martin <mart@kde.org>
// SPDX-FileCopyrightText: 2017 The Qt Company Ltd.
// SPDX-FileCopyrightText: 2023 ivan tkachenko <ratijas@kde.org>
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls as Controls

// Replacing the desktop ScrollView's inline bar replaces its positioning
// bindings too. Keep the installed SDK's public geometry/active contract;
// DomainOSScrollBar still owns only paint, and desktop input remains intact.
// Geometry bindings derive from qqc2-desktop-style 6.13.0 ScrollView.qml,
// selected under its GPL-2.0-or-later licensing alternative.
DomainOSScrollBar {
    required property var scrollView
    parent: scrollView
    z: 1
    x: horizontal ? scrollView.leftPadding
        : scrollView.mirrored
            ? (scrollView.background?.visible ? (scrollView.background.leftPadding ?? 0) : 0)
            : scrollView.width - width
                - (scrollView.background?.visible ? (scrollView.background.rightPadding ?? 0) : 0)
    y: horizontal ? scrollView.height - height
        - (scrollView.background?.visible ? (scrollView.background.bottomPadding ?? 0) : 0)
        : scrollView.topPadding
    width: horizontal ? scrollView.availableWidth : implicitWidth
    height: horizontal ? implicitHeight : scrollView.availableHeight
    active: horizontal ? scrollView.Controls.ScrollBar.vertical.active
        : scrollView.Controls.ScrollBar.horizontal.active
}
