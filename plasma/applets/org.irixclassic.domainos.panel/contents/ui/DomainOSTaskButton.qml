// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: button
    implicitWidth:66; implicitHeight:98
    required property var record
    required property QtObject colorPalette
    property bool selected:false
    property bool partiallySelected:false
    property int selectedMembers:0
    property var frozenRecord:null
    property var firstClickRecord:null
    property bool doubleClickDispatched:false
    property bool reorderEnabled:false
    property bool wasDragged:false
    property bool interactiveMute:true
    property var smartLauncherItem:null
    readonly property bool demandsAttention:!!record && (record.group
        ? (record.members || []).some(member=>member.demandsAttention)
        : record.demandsAttention) || !!smartLauncherItem && smartLauncherItem.urgent
    readonly property bool dragActive:pointer.drag.active
    readonly property real dragDistance:pointer.drag.threshold
    readonly property bool pressed:pointer.pressed && pointer.containsMouse
    readonly property bool labelTruncated:taskCaption.truncated
    readonly property bool fullyMinimized: {
        if (!record) return false
        const members=record.group ? (record.members || []) : [record]
        return members.length>0 && members.every(member=>member.minimized===true)
    }
    // Selection survives minimization for batch operations. Its raised relief
    // must still distinguish a minimized window from a restored selected one.
    readonly property bool selectionRelief:selected && !fullyMinimized
    readonly property int pressOffset:pressed ? 2 : 0
    property var audioStreams:[]
    readonly property bool hasAudioStream:audioStreams.length>0
    readonly property bool muted:hasAudioStream && audioStreams.every(stream=>stream.muted)
    readonly property bool playingAudio:hasAudioStream && audioStreams.some(stream=>!stream.corked)
    activeFocusOnTab:true
    signal selectedByPointer(var record,int modifiers)
    signal activatedByPointer(var record)
    signal contextByPointer(var record,var anchor,var options)
    signal middleByPointer(var record)
    signal audioNavigationRequested(var record,int direction)
    signal wheelRequested(int angle,var record)
    signal reorderedByPointer(var record,point position)
    signal keyboardReorderRequested(var record,int direction)
    signal urlsDropped(var record,var urls)
    signal geometryPublicationRequested()
    signal pointerPressed()
    signal pointerCancelled()

    Accessible.role:Accessible.Button
    Accessible.name:record.title+(record.group ? qsTr("; %1 de %2 selecionadas").arg(selectedMembers).arg(record.memberKeys.length) : "")
    Accessible.description:qsTr("Clique escolhe janelas; duplo clique restaura, ativa ou minimiza")
    Accessible.checkable:true
    Accessible.checked:selected
    Accessible.onPressAction:selectedByPointer(record,0)
    Keys.onPressed:event=>{
        if (event.isAutoRepeat) return
        if ([Qt.Key_Left,Qt.Key_Right,Qt.Key_Up,Qt.Key_Down].indexOf(event.key)>=0
                && (event.modifiers & Qt.ControlModifier) && (event.modifiers & Qt.ShiftModifier)) {
            if (reorderEnabled) keyboardReorderRequested(record,event.key===Qt.Key_Left || event.key===Qt.Key_Up ? -1 : 1)
            event.accepted=true
        }
        else if (event.key===Qt.Key_Space) { selectedByPointer(record,event.modifiers);event.accepted=true }
        else if (event.key===Qt.Key_Return || event.key===Qt.Key_Enter) { activatedByPointer(record);event.accepted=true }
        else if (event.key===Qt.Key_Menu) { showContextMenu({});event.accepted=true }
    }

    function showContextMenu(options) { contextByPointer(record,button,options || {}) }
    function toggleMuted() {
        const mute=!muted
        for (const stream of audioStreams) { if (mute) stream.mute();else stream.unmute() }
    }
    onXChanged:geometryPublicationRequested()
    onYChanged:geometryPublicationRequested()
    onWidthChanged:geometryPublicationRequested()
    onHeightChanged:geometryPublicationRequested()
    onRecordChanged:geometryPublicationRequested()
    Component.onCompleted:geometryPublicationRequested()
    // Only this invisible target moves while crossing the platform drag
    // threshold. The approved task geometry stays fixed throughout the gesture.
    Item { id:dragTarget; visible:false }
    Bevel {
        objectName:button.objectName+"Relief"
        anchors.fill:parent
        face:button.colorPalette.recessed
        light:button.colorPalette.highlight; dark:button.colorPalette.dark
        texture:Qt.resolvedUrl("../images/metal-weave.svg")
        sunken:button.pressed || button.selectionRelief
        thickness:4
    }
    Rectangle {
        anchors.fill:parent;anchors.margins:4
        visible:button.activeFocus || button.demandsAttention;color:"transparent"
        border.width:button.demandsAttention ? 2 : 1;border.color:button.colorPalette.focus
    }
    Item {
        x:button.pressOffset;y:button.pressOffset;width:parent.width;height:parent.height
        Kirigami.Icon {
            objectName:button.objectName+"Icon"
            x:2;y:4;width:64;height:64
            source:button.record.icon
            smooth:false
            implicitWidth:64;implicitHeight:64
        }
        Bevel {
            objectName:button.objectName+"Label"
            x:2;y:68;width:62;height:26;thickness:1
            face:button.selected ? button.colorPalette.blue : button.colorPalette.label
            light:button.colorPalette.highlight;dark:button.colorPalette.dark
            sunken:button.selectionRelief
        }
        Text {
            id: taskCaption
            objectName:button.objectName+"LabelText"
            x:2;y:68;width:62;height:26
            text:button.record.title
            font.family:"Nimbus Sans";font.pixelSize:16
            color:button.selected ? button.colorPalette.white : button.colorPalette.text
            horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter
            elide:Text.ElideRight;renderType:Text.NativeRendering;textFormat:Text.PlainText
        }
    }
    MouseArea {
        id:pointer
        anchors.fill:parent
        hoverEnabled:true
        acceptedButtons:Qt.LeftButton|Qt.RightButton|Qt.MiddleButton|Qt.BackButton|Qt.ForwardButton
        drag.target:button.reorderEnabled && pointer.pressedButtons===Qt.LeftButton ? dragTarget : null
        drag.axis:Drag.XAndYAxis
        drag.threshold:Qt.styleHints.startDragDistance
        onWheel:wheel=>button.wheelRequested(wheel.angleDelta.y,button.record)
        onPressed:mouse=>{
            button.frozenRecord=button.record;button.wasDragged=false
            button.doubleClickDispatched=false
            dragTarget.x=0;dragTarget.y=0
            if (mouse.button===Qt.LeftButton) button.pointerPressed()
        }
        onPositionChanged:mouse=>{ if (drag.active) button.wasDragged=true }
        onReleased:mouse=>{
            if (!containsMouse || button.wasDragged) button.pointerCancelled()
            if (button.wasDragged && button.frozenRecord) {
                button.reorderedByPointer(button.frozenRecord,button.mapToItem(button.parent,mouse.x,mouse.y))
                button.frozenRecord=null
            }
        }
        onCanceled:{ button.frozenRecord=null;button.wasDragged=true;button.pointerCancelled() }
        onClicked: mouse => {
            const target=button.frozenRecord
            if (!target || button.wasDragged || button.doubleClickDispatched) return
            if (mouse.button===Qt.RightButton) button.contextByPointer(target,button,{})
            else if (mouse.button===Qt.MiddleButton) button.middleByPointer(target)
            else if (mouse.button===Qt.BackButton || mouse.button===Qt.ForwardButton)
                button.audioNavigationRequested(target,mouse.button===Qt.BackButton ? -1 : 1)
            else {
                button.firstClickRecord=target
                button.selectedByPointer(target,mouse.modifiers)
            }
        }
        onDoubleClicked: mouse => {
            if (mouse.button!==Qt.LeftButton || !button.frozenRecord) return
            button.doubleClickDispatched=true
            const first=button.firstClickRecord, current=button.frozenRecord
            const same=first && first.key===current.key && first.pid===current.pid
            button.activatedByPointer(Object.assign({},current,{doubleClickActive:same ? first.active : current.active}))
            button.firstClickRecord=null
        }
    }
    // Native status overlays occupy the existing icon; no new task cells,
    // layout changes, transitions or delayed input/presentation are introduced.
    Rectangle {
        objectName:button.objectName+"Progress"
        x:4;y:62;width:58;height:4;z:2
        visible:!!button.smartLauncherItem && button.smartLauncherItem.progressVisible
        color:button.colorPalette.dark
        Rectangle {
            width:parent.width*Math.max(0,Math.min(100,button.smartLauncherItem ? button.smartLauncherItem.progress : 0))/100
            height:parent.height;color:button.colorPalette.blue
        }
    }
    Rectangle {
        objectName:button.objectName+"Count"
        x:4;y:6;width:Math.min(38,Math.max(20,countText.implicitWidth+4));height:20;z:2
        visible:!!button.smartLauncherItem && button.smartLauncherItem.countVisible
        color:button.colorPalette.blue;border.width:1;border.color:button.colorPalette.dark
        Text {
            id:countText;anchors.centerIn:parent
            text:button.smartLauncherItem ? String(button.smartLauncherItem.count) : ""
            color:button.colorPalette.white;font.pixelSize:14;font.family:"Nimbus Sans";renderType:Text.NativeRendering
        }
    }
    Item {
        objectName:button.objectName+"Audio"
        x:38;y:6;width:24;height:24;z:3
        visible:button.playingAudio || button.muted
        activeFocusOnTab:visible && button.interactiveMute
        Accessible.role:Accessible.Button
        Accessible.name:button.muted ? qsTr("Reativar áudio de %1").arg(button.record.title) : qsTr("Silenciar %1").arg(button.record.title)
        Accessible.checkable:true;Accessible.checked:button.muted
        Accessible.onPressAction:if (button.interactiveMute) button.toggleMuted()
        Keys.onSpacePressed:if (button.interactiveMute) button.toggleMuted()
        Keys.onReturnPressed:if (button.interactiveMute) button.toggleMuted()
        Bevel { anchors.fill:parent;thickness:1;face:button.colorPalette.label;light:button.colorPalette.highlight;dark:button.colorPalette.dark;sunken:audioPointer.pressed }
        Kirigami.Icon { anchors.fill:parent;anchors.margins:2;source:button.muted ? "audio-volume-muted-symbolic" : "audio-volume-high-symbolic";animated:false }
        MouseArea {
            id:audioPointer;anchors.fill:parent;enabled:button.interactiveMute
            acceptedButtons:Qt.LeftButton;onClicked:button.toggleMuted()
        }
    }
    DropArea {
        anchors.fill:parent
        onEntered:event=>{ if (!event.hasUrls) event.accepted=false }
        onDropped:event=>{
            if (event.hasUrls) { button.urlsDropped(button.record,Array.from(event.urls).map(url=>String(url)));event.acceptProposedAction() }
        }
    }
}
