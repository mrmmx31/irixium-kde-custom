// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "../applets/org.irixclassic.domainos.panel/contents/ui" as DomainOS

DomainOSTasksPreview {
    id: host
    width:610;height:500
    legacyInterface:false
    property alias iconbox:box
    function uiState() { return JSON.stringify({firstVisible:box.firstVisible,previous:box.canPrevious,next:box.canNext,
        group:box.groupPopupVisible,operations:box.operationsMenuVisible,operationsOpened:box.operationsOpened,
        selected:controller.selectedKeys,requests:requests,layouts:layouts,errors:box.lastError,
        menu:box.basicContextMenu.visible}) }
    function closeMenus() { box.basicContextMenu.close();box.batchContextMenu.close() }
    function runUiBatch(action) { return box.batch(action) }
    function resetUi() {
        box.basicContextMenu.close();box.batchContextMenu.close()
        controller.finishGroupSelection(false);controller.clearSelection()
        requests=[];layouts=[];box.lastError=""
        seed()
    }
    function seedMany() {
        seed()
        for (let id=10;id<=17;++id) addWindow(id,"app"+id)
    }
    function seedManyGroups() {
        seed()
        const original=windows[0],result=[]
        for (let index=0;index<18;++index) {
            const row=JSON.parse(JSON.stringify(original))
            row.ids=[100+index];row.pid=700+index;row.appId="pagegroup"+Math.floor(index/2)
            row.title="Page group "+Math.floor(index/2)+" member "+index;row.active=false
            result.push(row)
        }
        windows=result;box.firstVisible=0
    }
    function disableGeometry() { controller.geometryBackend=null }
    DomainOS.DomainOSPalette { id:palette;followSystem:false }
    DomainOS.DomainOSIconbox {
        id:box
        x:8;y:340;width:594;height:150
        controller:host.controller
        colorPalette:palette
        nativeMenusEnabled:false
    }
}
