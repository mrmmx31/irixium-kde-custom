// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.ksvg 1.0 as KSvg
import "Rendering.js" as Rendering

Item {
    id: control
    property string kind: "menu"
    property url artwork
    property string label: ""
    property bool available: true
    property bool activeWindow: true
    // The menu uses the same isolated double-click state machine as Classic.
    property bool menuOnPress: true
    property bool closeOnDouble: true
    property bool pressed: false
    property bool hovered: pointer.containsMouse
    readonly property bool rasterArtwork: Rendering.isRaster(artwork)
    readonly property var stateCandidates: Rendering.buttonCandidates(
        activeWindow, available, pressed, hovered)
    readonly property string renderedElement: rasterArtwork ? "png" : vector.elementId
    readonly property bool artworkValid: rasterArtwork ? menuBitmap.status === Image.Ready
        : (atlasRevision >= 0 && stateAtlas.hasElement(vector.elementId))
    // hasElement() is a method, not a notifying QML property. Re-evaluate
    // after the atlas loads, even when pointer/window state has not changed.
    property int atlasRevision: 0
    Connections {
        target: stateAtlas
        function onRepaintNeeded() { control.atlasRevision++; }
    }
    signal activate(int mouseButton)
    signal closeRequested()

    Accessible.role: Accessible.Button
    Accessible.name: control.label
    Accessible.description: control.available ? "" : "Indisponível para esta janela"

    // This is the only ordinary Image: applications.png is one 22x22 bitmap,
    // unlike the 66x66 SVG atlases. No system/shared-theme reference is used.
    Image {
        id: menuBitmap
        anchors.centerIn: parent
        width: Math.min(control.width, implicitWidth)
        height: Math.min(control.height, implicitHeight)
        visible: control.rasterArtwork
        source: control.rasterArtwork ? control.artwork : ""
        fillMode: Image.PreserveAspectFit
        smooth: false
        opacity: control.available ? (control.activeWindow ? 1.0 : 0.85) : 0.45
    }
    KSvg.Svg {
        id: stateAtlas
        imagePath: control.rasterArtwork ? "" : Rendering.localPath(control.artwork)
        multipleImages: true
    }
    KSvg.SvgItem {
        id: vector
        objectName: "irixiumModernStateElement"
        anchors.fill: parent
        visible: !control.rasterArtwork
        svg: stateAtlas
        elementId: {
            control.atlasRevision;
            stateAtlas.imagePath;
            return Rendering.pickElement(stateAtlas, control.stateCandidates);
        }
        smooth: false
        // Preserve real disabled states; fade only if an older atlas lacks them.
        opacity: !control.available && elementId.indexOf("deactivated") !== 0 ? 0.45 : 1.0
    }
    // The bitmap has no pressed variant. Retain local press feedback for this
    // one control only; SVG controls use their actual pressed layers above.
    Item {
        anchors.fill: parent
        visible: control.rasterArtwork && control.pressed && control.available
        Rectangle { anchors.fill: parent; color: "#403d31"; opacity: 0.12 }
        Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: "#403d31" }
        Rectangle { anchors.left: parent.left; width: 1; height: parent.height; color: "#403d31" }
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#ded7bc" }
        Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: "#ded7bc" }
    }
    ButtonInput {
        anchors.fill: parent
        visible: control.kind === "menu"
        kind: "menu"
        label: control.label
        available: control.available
        menuOnPress: control.menuOnPress
        closeOnDouble: control.closeOnDouble
        onDownChanged: control.pressed = down
        onActivate: (button) => control.activate(button)
        onCloseRequested: control.closeRequested()
    }
    MouseArea {
        id: pointer
        anchors.fill: parent
        enabled: control.available && control.kind !== "menu"
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onPressed: (mouse) => {
            control.pressed = true;
            if (control.kind === "menu")
                control.activate(mouse.button);
        }
        onReleased: control.pressed = false
        onCanceled: control.pressed = false
        onClicked: (mouse) => {
            if (control.kind !== "menu")
                control.activate(mouse.button);
        }
    }
    onAvailableChanged: {
        if (!available)
            pressed = false;
    }
}
