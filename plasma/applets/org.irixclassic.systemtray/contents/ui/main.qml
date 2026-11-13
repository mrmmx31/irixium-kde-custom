/*
    SPDX-FileCopyrightText: 2016 Marco Martin <mart@kde.org>
    SPDX-FileCopyrightText: 2026 mrmmx31

    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick 2.1
import QtQuick.Layouts 1.1
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid 2.0
import org.kde.ksvg 1.0 as KSvg

// The upstream C++ applet owns the real tray containment. The Classic
// package changes only its presentation, retaining upstream tray behavior.
PlasmoidItem {
    id: root

    readonly property int frameInset: 4
    readonly property int wellInset: 2
    readonly property int contentInset: frameInset + wellInset
    property ContainmentItem internalSystray

    Layout.minimumWidth: internalSystray ? internalSystray.Layout.minimumWidth + 2 * contentInset : 0
    Layout.minimumHeight: internalSystray ? internalSystray.Layout.minimumHeight + 2 * contentInset : 0
    Layout.preferredWidth: Layout.minimumWidth
    Layout.preferredHeight: Layout.minimumHeight

    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.status: internalSystray ? internalSystray.plasmoid.status : PlasmaCore.Types.UnknownStatus

    KSvg.FrameSvgItem {
        objectName: "classicTrayHousing"
        anchors.fill: parent
        imagePath: "widgets/instrument"
        prefix: "normal"
    }

    KSvg.FrameSvgItem {
        objectName: "classicTrayWell"
        anchors.fill: parent
        anchors.margins: root.frameInset
        imagePath: "widgets/instrument-well"
    }

    // Synchronize state between the upstream tray and the wrapping applet.
    onExpandedChanged: {
        if (internalSystray) {
            internalSystray.expanded = root.expanded;
        }
    }
    Connections {
        target: internalSystray
        function onExpandedChanged() {
            root.expanded = internalSystray.expanded;
        }
    }

    function attachTray() {
        root.internalSystray = Plasmoid.internalSystray;
        if (!root.internalSystray) {
            return;
        }
        root.internalSystray.parent = root;
        root.internalSystray.anchors.fill = root;
        root.internalSystray.anchors.margins = root.contentInset;
    }

    Component.onCompleted: attachTray()

    Connections {
        target: Plasmoid
        function onInternalSystrayChanged() {
            root.attachTray();
        }
    }
}
