// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// The same layout tests installed imports and exact/temporarily patched files.
import QtQuick
import QtQuick.Controls
import "ArrowProbe.js" as Probe
Rectangle {
    id: win
    width: 700; height: 430
    color: "#c1c1c1"
    property string probeName: "vertical"
    property string probeArrow: "up"
    property real queryX: -1
    property real queryY: -1
    property int sampleTick: 0
    property string diagnostic: "{}"
    property var lastPress: null
    property int pressSerial: 0

    function bar(which) { return which==="vertical" ? vbar:hbar; }
    function bounds(b) {
        const p=b.mapToItem(null,0,0);
        return {x:p.x,y:p.y,width:b.width,height:b.height};
    }
    function styleFor(b) {
        let list=[]; Probe.collect(b.background,list);return Probe.choose(list);
    }
    function hitAt(b,s,x,y) {
        if (!s) return "unavailable";
        const p=s.mapFromItem(b,x,y);
        return s.hitTest(Math.floor(p.x),Math.floor(p.y));
    }
    function resetProbe() {
        area.cancelFlick();
        area.contentX=(area.contentWidth-area.width)*0.45;
        area.contentY=(area.contentHeight-area.height)*0.45;
        lastPress=null; queryX=-1; queryY=-1;
    }
    function recordPress(which,mouse) {
        const b=bar(which),s=styleFor(b);
        const p=b.mapFromItem(b.background,mouse.x,mouse.y);
        ++pressSerial;
        // Observation only: do not change accepted, activeControl or sunken.
        lastPress={bar:which,hit:hitAt(b,s,p.x,p.y),button:mouse.button,
            x:p.x,y:p.y,serial:pressSerial};
    }
    function refreshProbe() {
        const b=bar(probeName),s=styleFor(b),other=bar(probeName==="vertical" ? "horizontal":"vertical");
        let list=[]; Probe.collect(b.background,list);
        const vertical=b.orientation===Qt.Vertical;
        const local=s ? Probe.scan(vertical?b.height:b.width,(vertical?b.width:b.height)/2,
            vertical,function(x,y){return hitAt(b,s,x,y);},probeArrow):null;
        let target=null;
        if (local) {
            const scene=b.mapToItem(null,local.x,local.y);
            const point={x:Math.round(scene.x),y:Math.round(scene.y)};
            const actual=b.mapFromItem(null,queryX<0?point.x:queryX,queryY<0?point.y:queryY);
            const sampledPoint=queryX<0?point:{x:queryX,y:queryY};
            target={x:point.x,y:point.y,localX:local.x,localY:local.y,
                first:local.first,last:local.last,hit:hitAt(b,s,actual.x,actual.y),
                clear:Probe.clearTarget(sampledPoint,bounds(b),bounds(other)),
                bounds:vertical?{x:bounds(b).x,y:bounds(b).y+local.first,width:b.width,height:local.last-local.first+1}
                    :{x:bounds(b).x+local.first,y:bounds(b).y,width:local.last-local.first+1,height:b.height}};
        }
        let visibleSunken=false;
        for (let i=0;i<list.length;++i)
            if(list[i].visible && list[i].opacity>0.01 && list[i].sunken) visibleSunken=true;
        diagnostic=JSON.stringify({position:b.position,value:b.position,
            contentX:area.contentX,contentY:area.contentY,pressed:b.pressed,
            "sunken":visibleSunken,mousePressed:b.background?b.background.pressed:false,
            mouseAreaPressed:b.background?b.background.pressed:false,
            mouseAreaButtons:b.background?b.background.pressedButtons:0,
            activeControl:s?s.activeControl:"unavailable",target:target,
            ownBounds:bounds(b),otherBounds:bounds(other),
            lastPress:lastPress,styleItems:list.map(s=>({sunken:s.sunken,active:s.activeControl,
                opacity:s.opacity,visible:s.visible})),width:b.width,height:b.height});
    }
    onSampleTickChanged: refreshProbe()
    Text { x:12;y:12;color:"black";text:"Ensaio de setas — posição, destinatário e pressão separados" }
    Text { x:12;y:36;color:"black";text:"Dados artificiais. Somente esta janela recebe os eventos do ensaio." }
    Item {
        id: stage
        x:12;y:68;width:win.width-24;height:win.height-116
        Flickable {
            id:area; objectName:"probeArea"
            x:0;y:0;width:stage.width-vbar.width;height:stage.height-hbar.height
            contentWidth:1400;contentHeight:2400;clip:true
            Rectangle { width:1400;height:2400;color:"#efefef" }
            Repeater { model:90
                Text { required property int index; x:8;y:index*24;text:"Linha artificial "+index;color:"black" }
            }
            // Explicit parent and extents keep the two arrow cells out of the shared corner.
            ScrollBar.vertical: ScrollBar { // PROBE_BAR_TYPE
                id:vbar;objectName:"vertical";parent:stage
                x:area.width;y:0;width:implicitWidth;height:area.height
                orientation:Qt.Vertical;policy:ScrollBar.AlwaysOn
            }
            ScrollBar.horizontal: ScrollBar { // PROBE_BAR_TYPE
                id:hbar;objectName:"horizontal";parent:stage
                x:0;y:area.height;width:area.width;height:implicitHeight
                orientation:Qt.Horizontal;policy:ScrollBar.AlwaysOn
            }
        }
        Rectangle { x:area.width;y:area.height;width:vbar.width;height:hbar.height;color:"#c1c1c1" }
    }
    Connections { target:vbar.background;ignoreUnknownSignals:true
        function onPressed(mouse) { win.recordPress("vertical",mouse); }
    }
    Connections { target:hbar.background;ignoreUnknownSignals:true
        function onPressed(mouse) { win.recordPress("horizontal",mouse); }
    }
    Text { x:12;y:win.height-30;color:"black"
        text:"x="+Math.round(area.contentX)+"  y="+Math.round(area.contentY)+"  Pressões observadas: "+win.pressSerial }
    Component.onCompleted: resetProbe()
}
