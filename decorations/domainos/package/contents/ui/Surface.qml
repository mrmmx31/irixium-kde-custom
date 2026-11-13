// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import "Geometry.js" as Geometry
import "Palette.js" as Palette
Item {
    id: surface
    property bool activeWindow: true
    property bool maximizedWindow: false
    property bool resizeAllowed: true
    property bool minimizeAllowed: true
    property bool maximizeAllowed: true
    property bool menuOnPress: false
    property bool closeOnDouble: true
    property string caption: ""
    property int pixelScale: 1
    property string titleFamily: "Nimbus Sans"
    property int titlePixels: 12
    property bool titleItalic: false
    property bool titleBold: true
    readonly property var metrics: Geometry.metrics(width,pixelScale,maximizedWindow,
        resizeAllowed,minimizeAllowed,maximizeAllowed)
    // Defaults reproduce the screenshot in standalone reference tests.
    // The actual decoration binds face/caption to KWin's current color roles.
    property color faceColor: activeWindow ? "#fe8282" : "#7acac5"
    property color captionColor: "#ffffff"
    readonly property color referenceFace: activeWindow ? "#fe8282" : "#7acac5"
    readonly property color lightColor: Palette.tone(faceColor,referenceFace,
        activeWindow ? Qt.color("#ffc8c8") : Qt.color("#c5e8e6"))
    readonly property color darkColor: Palette.tone(faceColor,referenceFace,
        activeWindow ? Qt.color("#864545") : Qt.color("#406b68"))
    property alias titleItem: titleRegion
    signal menuRequested(int mouseButton)
    signal closeRequested()
    signal minimizeRequested()
    signal maximizeRequested(int mouseButton)
    clip: true
    function cancelGestures() {
        if (menuInput) menuInput.cancelGesture();
        if (minimizeInput) minimizeInput.cancelGesture();
        if (maximizeInput) maximizeInput.cancelGesture();
    }
    // Activating an inactive window must preserve the first menu click.
    onMaximizedWindowChanged: cancelGestures()
    onResizeAllowedChanged: cancelGestures()
    onPixelScaleChanged: cancelGestures()
    onWidthChanged: cancelGestures()
    onHeightChanged: cancelGestures()
    Frame {
        width:surface.width/surface.metrics.scale
        height:surface.height/surface.metrics.scale
        scale:surface.metrics.scale
        transformOrigin:Item.TopLeft
        activeWindow:surface.activeWindow
        maximizedWindow:surface.maximizedWindow
        resizeAllowed:surface.resizeAllowed
        face:surface.faceColor; light:surface.lightColor; dark:surface.darkColor
    }
    component Glyph: Item {
        id: glyph
        property string kind
        property bool down: false
        property bool allowed: true
        readonly property int unit: surface.metrics.scale
        readonly property int glyphWidth: (kind === "minimize" ? 4 : 12)*unit
        readonly property int glyphHeight: (kind === "menu" ? 4 : (kind === "minimize" ? 4 : 12))*unit
        anchors.fill:parent
        Relief {
            width:parent.width
            height:parent.height-(surface.maximizedWindow ? 0 : glyph.unit)
            lineWidth:glyph.unit
            face:surface.faceColor; light:surface.lightColor; dark:surface.darkColor
            down:glyph.down
        }
        Relief {
            x:Math.floor((parent.width-glyph.glyphWidth)/2)+(glyph.down ? glyph.unit : 0)
            y:Math.floor((parent.height-glyph.glyphHeight)/2)+(glyph.down ? glyph.unit : 0)
            width:glyph.glyphWidth; height:glyph.glyphHeight
            lineWidth:glyph.unit
            face:surface.faceColor; light:surface.lightColor; dark:surface.darkColor
            opacity:glyph.allowed ? 1 : 0.45
        }
    }
    Item {
        id:titleRegion
        x:surface.metrics.menu.x; y:surface.metrics.menu.y
        width:Math.max(0,surface.width-2*x); height:20*surface.metrics.scale
    }
    Relief {
        id:captionRelief
        objectName:"domainosTitleRelief"
        x:surface.metrics.caption.x; y:surface.metrics.caption.y
        width:surface.metrics.caption.w
        height:surface.metrics.caption.h-(surface.maximizedWindow ? 0 : surface.metrics.scale)
        lineWidth:surface.metrics.scale
        face:surface.faceColor; light:surface.lightColor; dark:surface.darkColor
        down:titlePress.active
        // Observe the pointer passively: KWin still owns moving the window
        // and the configured titlebar double-click action.
        PointHandler {
            id:titlePress
            objectName:"domainosTitlePress"
            acceptedButtons:Qt.LeftButton
            target:null
        }
    }
    Text {
        objectName:"domainosCaption"
        x:surface.metrics.caption.x+surface.metrics.scale
        y:surface.metrics.caption.y
        width:Math.max(0,surface.metrics.caption.w-2*surface.metrics.scale)
        height:surface.metrics.caption.h-surface.metrics.scale
        text:surface.caption
        textFormat:Text.PlainText
        color:surface.captionColor
        font.family:surface.titleFamily
        font.pixelSize:surface.titlePixels*surface.metrics.scale
        font.bold:surface.titleBold; font.italic:surface.titleItalic
        renderType:Text.NativeRendering
        antialiasing:false
        horizontalAlignment:Text.AlignHCenter
        verticalAlignment:Text.AlignVCenter
        elide:Text.ElideRight
        clip:true
    }
    ButtonInput {
        id:menuInput
        objectName:"domainosMenu"
        Glyph { kind:"menu"; down:menuInput.down; allowed:menuInput.available }
        kind:"menu"; label:"Menu da janela — mais ações"
        menuOnPress:surface.menuOnPress; closeOnDouble:surface.closeOnDouble
        x:surface.metrics.menu.x; y:surface.metrics.menu.y
        width:surface.metrics.menu.w; height:surface.metrics.menu.h
        visible:surface.metrics.menu.visible
        onActivate:(button)=>surface.menuRequested(button)
        onCloseRequested:surface.closeRequested()
    }
    ButtonInput {
        id:minimizeInput
        objectName:"domainosMinimize"
        Glyph { kind:"minimize"; down:minimizeInput.down; allowed:minimizeInput.available }
        kind:"minimize"; label:"Minimizar"
        available:surface.minimizeAllowed
        x:surface.metrics.minimize.x; y:surface.metrics.minimize.y
        width:surface.metrics.minimize.w; height:surface.metrics.minimize.h
        visible:surface.metrics.minimize.visible
        onActivate:surface.minimizeRequested()
    }
    ButtonInput {
        id:maximizeInput
        objectName:"domainosMaximize"
        Glyph { kind:"maximize"; down:maximizeInput.down; allowed:maximizeInput.available }
        kind:"maximize"; label:surface.maximizedWindow ? "Restaurar" : "Maximizar"
        available:surface.maximizeAllowed
        x:surface.metrics.maximize.x; y:surface.metrics.maximize.y
        width:surface.metrics.maximize.w; height:surface.metrics.maximize.h
        visible:surface.metrics.maximize.visible
        onActivate:(button)=>surface.maximizeRequested(button)
    }
}
