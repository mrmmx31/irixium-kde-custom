// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Observe the INSTALLED style, never a patched copy of ScrollBar.qml.
import QtQuick
import QtQuick.Controls
ApplicationWindow {
    id: win
    visible: true
    width: 620; height: 380
    title: "Diagnóstico de setas — Qt Quick instalado"
    property string probeName: "vertical"
    property int sampleTick: 0
    property string diagnostic: { sampleTick; return inspect(probeName) }
    function resetProbe() { area.contentX = 360; area.contentY = 900; }
    function collectStyles(item, output) {
        if (!item) return;
        if (item.elementType !== undefined && item.elementType === "scrollbar"
                && typeof item.hitTest === "function") output.push(item);
        if (item.children) for (let i = 0; i < item.children.length; ++i)
            collectStyles(item.children[i], output);
    }
    function arrowRect(style, bar, target) {
        // KQuickStyleItem 6.13 exposes page/handle rectangles, NOT up/down
        // rectangles for scrollbars. Use its native hitTest, not guessed metrics.
        const vertical = bar.orientation === Qt.Vertical;
        const length = Math.min(2048, Math.floor(vertical ? bar.height : bar.width));
        const cross = Math.floor((vertical ? bar.width : bar.height) / 2);
        let start = -1, end = -1;
        for (let i = 0; i < length; ++i) {
            const hit = vertical ? style.hitTest(cross, i) : style.hitTest(i, cross);
            if (hit === target) { if (start < 0) start = i; end = i; }
            else if (start >= 0) break; // one contiguous arrow segment
        }
        if (start < 0) return null;
        return vertical ? {x:0, y:start, width:bar.width, height:end-start+1}
                        : {x:start, y:0, width:end-start+1, height:bar.height};
    }
    function inspect(which) {
        const b = which === "vertical" ? vbar : hbar;
        let styles = []; collectStyles(b.background, styles);
        let chosen = styles.length ? styles[0] : null;
        for (let i = 0; i < styles.length; ++i) {
            if (styles[i].activeControl !== "none" && styles[i].opacity > 0) {
                chosen = styles[i]; break;
            }
        }
        const origin = b.mapToItem(win.contentItem, 0, 0);
        return JSON.stringify({
            value:b.position, contentX:area.contentX, contentY:area.contentY,
            pressed:b.pressed, enabled:b.enabled, size:b.size,
            x:origin.x, y:origin.y, width:b.width, height:b.height,
            up:chosen ? arrowRect(chosen,b,"up") : null,
            down:chosen ? arrowRect(chosen,b,"down") : null,
            styleItems:styles.map(s => ({sunken:s.sunken, active:s.activeControl,
                opacity:s.opacity, visible:s.visible})),
            mouseAreaPressed:b.background ? b.background.pressed : null,
            mouseAreaButtons:b.background ? b.background.pressedButtons : null
        });
    }
    Column {
        anchors.fill: parent; anchors.margins: 12; spacing: 8
        Label { text: "Clique nas setas. Observe o movimento e o relevo separadamente." }
        Label { text: "Flickable: x="+Math.round(area.contentX)+"  y="+Math.round(area.contentY) }
        Flickable {
            id: area; objectName: "probeArea"
            width: parent.width; height: 282
            contentWidth: 1400; contentHeight: 2400
            contentX: 360; contentY: 900
            clip: true
            Rectangle { width:1400; height:2400; color:win.palette.base }
            Repeater {
                model: 100
                Label {
                    required property int index
                    x: 12; y: index * 24
                    text: "Linha " + index + " — conteúdo artificial para diagnóstico; nenhum dado pessoal."
                }
            }
            ScrollBar.vertical: ScrollBar { id:vbar; objectName:"vertical"; policy:ScrollBar.AlwaysOn }
            ScrollBar.horizontal: ScrollBar { id:hbar; objectName:"horizontal"; policy:ScrollBar.AlwaysOn }
        }
        Button { text:"Restaurar posição central"; onClicked:win.resetProbe() }
    }
}
