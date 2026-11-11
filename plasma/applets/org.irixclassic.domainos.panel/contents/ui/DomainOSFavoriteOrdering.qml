// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick

// Order belongs to KAStats, not to a second drawer preference. The source
// client is observed before editing; no favorites are added/removed here.
QtObject {
    id:ordering
    property var model
    required property var readRows
    property var visibleRows:[]
    property string client:""
    property string activity:""
    property int generation:0
    property bool ready:false
    property var pendingMove:null
    readonly property bool busy:pendingMove!==null
    signal failed(string explanation)
    signal moved(var order)

    function ids(items) { return items.map(item=>String(item.favoriteId)) }
    function sameOrder(first,second) { return JSON.stringify(ids(first))===JSON.stringify(ids(second)) }
    function selectClient(value) {
        if (!value || !model || typeof model.initForClient!=="function" || typeof model.moveRow!=="function") {
            failed(qsTr("O provedor KDE não oferece ordenação nativa. A ordem atual foi mantida."))
            return false
        }
        try {
            // Re-read persisted order, including edits made in the KDE menu.
            // initForClient reads it without writing configuration.
            model.initForClient(value)
            client=value
            return true
        } catch (error) {
            failed(qsTr("Não foi possível carregar a ordem compartilhada do KDE."))
            return false
        }
    }
    function capture(favoriteId,direction) {
        if (!ready || busy || (direction!==-1 && direction!==1)) return null
        const index=visibleRows.findIndex(item=>item.favoriteId===favoriteId)
        const neighbor=visibleRows[index+direction]
        if (index<0 || !neighbor) return null
        return {favoriteId:favoriteId,neighborId:neighbor.favoriteId,direction:direction,
            activity:activity,generation:generation,client:client}
    }
    function move(request) {
        if (!ready || busy || !request || request.activity!==activity || request.generation!==generation
                || request.client!==client || (request.direction!==-1 && request.direction!==1)) return false
        const index=visibleRows.findIndex(item=>item.favoriteId===request.favoriteId)
        const neighbor=visibleRows[index+request.direction]
        if (index<0 || !neighbor || neighbor.favoriteId!==request.neighborId) return false
        // A held pointer must never move a replacement row after a reset.
        const rows=readRows()
        if (!sameOrder(rows,visibleRows)) {
            failed(qsTr("A ordem dos favoritos mudou. Reabra a gaveta antes de mover o item."))
            return false
        }
        const expected=ids(rows)
        expected.splice(index,1)
        expected.splice(index+request.direction,0,request.favoriteId)
        try {
            pendingMove={order:expected,activity:activity,generation:generation,client:client}
            model.moveRow(index,index+request.direction)
            // Proxy/delegate bindings settle after moveRow returns. Verify on
            // the next event turn; a synchronous check can see the old rows.
            Qt.callLater(confirmMove)
            return true
        } catch (error) {
            pendingMove=null
            failed(qsTr("Não foi possível mover o favorito no provedor KDE."))
            return false
        }
    }
    function confirmMove() {
        const pending=pendingMove
        pendingMove=null
        if (!pending || pending.activity!==activity || pending.generation!==generation || pending.client!==client) return
        if (JSON.stringify(ids(readRows()))!==JSON.stringify(pending.order)) {
            failed(qsTr("O KDE não confirmou a movimentação. Confira a ordem antes de tentar novamente."))
            return
        }
        moved(pending.order)
    }
}
