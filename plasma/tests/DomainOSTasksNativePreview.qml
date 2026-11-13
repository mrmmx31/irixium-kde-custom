// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "../applets/org.irixclassic.domainos.panel/contents/ui" as DomainOS

Item {
    property alias controller: tasks
    function state() { return JSON.stringify({rows:tasks.taskRows,windows:tasks.windowRows,
        windowCount:tasks.windowCount,selected:tasks.selectedKeys,desktop:tasks.currentDesktopId}) }
    function action(key,action) { return JSON.stringify(tasks.requestAction(key,action)) }
    function choose(key,modifiers) { return tasks.selectTask(key,modifiers) }
    DomainOS.DomainOSTasks {
        id: tasks
        onlyCurrentActivity:false
        onlyCurrentDesktop:false
        onlyCurrentScreen:false
        groupingMode:0
    }
}
