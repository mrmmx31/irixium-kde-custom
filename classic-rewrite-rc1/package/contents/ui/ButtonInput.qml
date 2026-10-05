// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "InputState.js" as InputState
Item {
    id: control
    property string kind: "menu"
    property bool available: true
    property bool menuOnPress: true
    property bool closeOnDouble: false
    property string label: ""
    property var gesture: InputState.idle()
    readonly property bool down: InputState.depressed(gesture, available && visible && enabled)
    readonly property var keys: ({left:Qt.LeftButton, right:Qt.RightButton, middle:Qt.MiddleButton})
    signal activate(int mouseButton)
    signal closeRequested()
    function inside(x,y) { return x >= 0 && y >= 0 && x < width && y < height; }
    function send(type,button,isInside) {
        var result = InputState.step(gesture, {type:type,button:button,inside:isInside},
            {kind:kind,available:available && visible && enabled,
             menuOnPress:menuOnPress,closeOnDouble:closeOnDouble},keys);
        // Reset before invoking native code, which may cancel input or destroy us.
        gesture = result.state;
        if (result.action === "activate") activate(result.button);
        else if (result.action === "close") closeRequested();
    }
    function cancelGesture() { gesture = InputState.idle(); }
    onAvailableChanged: cancelGesture()
    onVisibleChanged: cancelGesture()
    onEnabledChanged: cancelGesture()
    onKindChanged: cancelGesture()
    onWidthChanged: cancelGesture()
    onHeightChanged: cancelGesture()
    // A disabled accessible proxy still describes the unavailable operation.
    // The sibling MouseArea consumes its clicks so they do not fall through to
    // KWin's title-bar actions. Artwork and control availability are independent.
    Item {
        anchors.fill: parent
        enabled: control.available
        Accessible.role: Accessible.Button
        Accessible.name: control.label
        Accessible.description: control.available ? "" : "Indisponível para esta janela"
        Accessible.onPressAction: control.send("accessible",Qt.LeftButton,true)
    }
    MouseArea {
        id: mouseArea
        objectName: "irixButtonMouseArea"
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: control.kind === "maximize"
            ? Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
            : (control.kind === "menu" ? Qt.LeftButton | Qt.RightButton : Qt.LeftButton)
        onPressed: (mouse) => control.send("press",mouse.button,control.inside(mouse.x,mouse.y))
        onReleased: (mouse) => control.send("release",mouse.button,control.inside(mouse.x,mouse.y))
        onPositionChanged: (mouse) => control.send("move",0,control.inside(mouse.x,mouse.y))
        onEntered: control.send("move",0,true)
        onExited: control.send("move",0,false)
        onCanceled: control.cancelGesture()
        onDoubleClicked: (mouse) => {
            if (control.kind === "menu" && control.closeOnDouble && control.available
                    && mouse.button === Qt.LeftButton) {
                control.send("double",mouse.button,true);
            } else {
                // Qt then emits the second press/release normally; don't swallow it.
                mouse.accepted = false;
            }
        }
    }
}
