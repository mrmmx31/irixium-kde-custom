/*
    SPDX-FileCopyrightText: 2012-2013 Eike Hein <hein@kde.org>
    SPDX-FileCopyrightText: 2026 mrmmx31

    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "code/layoutmetrics.js" as LayoutMetrics

GridLayout {
    property bool animating: false

    rowSpacing: 0
    columnSpacing: 0

    property int animationsRunning: 0
    onAnimationsRunningChanged: {
        animating = animationsRunning > 0;
    }

    readonly property real minimumWidth: children
        .filter(item => item.visible && item.width > 0)
        .reduce((minimumWidth, item) => Math.min(minimumWidth, item.width), Infinity)

    // The Classic icon toolbar has one row (one column on vertical panels).
    readonly property int stripeCount: 1

    readonly property int orthogonalCount: {
        return Math.ceil(tasksModel.count / stripeCount);
    }

    rows: tasks.vertical ? orthogonalCount : stripeCount
    columns: tasks.vertical ? stripeCount : orthogonalCount
}
