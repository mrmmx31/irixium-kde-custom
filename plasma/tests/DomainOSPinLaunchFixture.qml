// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import "../../../org.irixclassic.domainos.panel/contents/ui" as Panel
PlasmoidItem {
    id:host
    preferredRepresentation:fullRepresentation
    fullRepresentation:Item {
        id:fixture;objectName:"domainosPinLaunchFixture"
        Layout.minimumWidth:500;Layout.minimumHeight:120
        Layout.preferredWidth:500;Layout.preferredHeight:120
        property string desktopId:"org.irixclassic.domainos.pin.launch.test.desktop"
        property var immediate:({})
        property var reports:[]
        function state() {
            return JSON.stringify({pins:runtime.applications.pins,pinInfo:runtime.applications.pinInfo(0),
                popupVisible:runtime.applications.popupVisible,drawer:runtime.applications.drawer,
                report:runtime.commands.lastReport,reports:reports,jobs:runtime.commands.jobs,
                activity:{sequence:runtime.activity.sequence,pending:runtime.activity.pendingCount,
                    lit:runtime.activity.lit,tailLit:runtime.activity.tailLit,
                    keepLightAfterCompletion:runtime.activity.keepLightAfterCompletion,
                    lastReport:runtime.activity.lastReport},immediate:immediate,
                windows:runtime.tasks.windowRows,launchers:runtime.tasks.tasksModel ? runtime.tasks.tasksModel.launcherList : []})
        }
        function showDrawer() { runtime.applications.showDrawer(anchor);return runtime.applications.popupVisible }
        function launchPin() {
            const accepted=runtime.applications.launchPin(0)
            immediate={accepted:accepted,pins:runtime.applications.pins.slice(),
                pending:runtime.activity.pendingCount,lit:runtime.activity.lit,
                sequence:runtime.activity.sequence,jobs:Object.assign({},runtime.commands.jobs)}
            return accepted
        }
        Rectangle { anchors.fill:parent;color:"#7894a7" }
        Item { id:anchor;x:10;y:80;width:120;height:30 }
        Panel.DomainOSPalette { id:colors;followSystem:false }
        Panel.DomainOSRuntime {
            id:runtime;hostItem:host;colorPalette:colors
            screenGeometry:Qt.rect(0,0,1100,700);availableGeometry:screenGeometry
            instanceId:"private-pin-launch-directed"
            settings:({pinnedApplications:[fixture.desktopId],tasksOnlyCurrentDesktop:false,
                tasksOnlyCurrentActivity:false,tasksOnlyCurrentScreen:false,tasksGroupingMode:0})
        }
        Connections {
            target:runtime.commands
            function onReported(report) { fixture.reports=fixture.reports.concat([report]) }
        }
    }
}
