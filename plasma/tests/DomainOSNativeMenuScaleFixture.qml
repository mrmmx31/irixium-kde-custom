// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel

PlasmoidItem {
    id: host
    preferredRepresentation: fullRepresentation
    fullRepresentation: Item {
        id: fixture
        objectName: "domainosNativeMenuScaleFixture"
        Layout.minimumWidth: 594; Layout.minimumHeight: 150
        Layout.preferredWidth: 594; Layout.preferredHeight: 150
        function target() {
            return tasks.taskRows.find(row => row.group
                && row.members.some(window => window.title.startsWith("DomainOS menu scale owned ")))
        }
        function configureScale(value) { scene.scale = value; return target() ? target().key : "" }
        function snapshot() {
            return JSON.stringify({target: target(), error: box.lastError,
                scale: scene.scale, native: !!box.nativeMenuBridge && !!box.nativeMenuBridge.openedMenu})
        }
        Panel.DomainOSPalette { id: colors; followSystem: false }
        Panel.DomainOSTasks {
            id: tasks
            onlyCurrentDesktop: false; onlyCurrentActivity: false; onlyCurrentScreen: false
            groupingMode: 1; onlyGroupWhenFull: false
        }
        Item {
            id: scene
            width: parent.width / scale; height: parent.height / scale
            scale: 0.5; transformOrigin: Item.TopLeft
            Panel.DomainOSIconbox {
                id: box
                anchors.fill: parent
                controller: tasks; colorPalette: colors; hostItem: host
                nativeMenusEnabled: true; hintsEnabled: false; thumbnailsEnabled: false
            }
        }
    }
}
