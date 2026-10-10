// SPDX-FileCopyrightText: 2026 IRIX Classic contributors
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQml
import QtQuick.Controls as Controls
Controls.ScrollBar {
 id: bar
 property bool skinEnabled: true
 property QtObject colorPalette: null
 DomainOSPalette { id: fallbackPalette }
 readonly property QtObject domainosPalette: colorPalette || fallbackPalette
 property var nativeGeometry: null
 property var geometryComponent: null
 readonly property bool geometryAvailable: nativeGeometry !== null
 function initializeGeometry() {
  if (nativeGeometry) return
  geometryComponent = Qt.createComponent(Qt.resolvedUrl("DomainOSNativeScrollGeometry.qml"))
  // Source checkouts do not contain the compiled optional helper. Retain the
  // desktop graphics/input silently whenever its local component is unavailable.
  if (geometryComponent.status === Component.Ready)
   nativeGeometry = geometryComponent.createObject(bar)
 }
 Component.onCompleted: initializeGeometry()
 readonly property var graphics: {
  const found=[]
  if (background) for (let item of background.children)
   if (item.elementType !== undefined && item.elementType === "scrollbar" && typeof item.subControlRect === "function") found.push(item)
  return found
 }
 readonly property var nativeStyle: {
  for (let item of graphics) if (item.grooveRect !== undefined && typeof item.computeRects === "function") return item
  return null
 }
 readonly property var geometryInput: nativeStyle ? ({width:nativeStyle.width,height:nativeStyle.height,horizontal:bar.horizontal,mirrored:bar.mirrored,minimum:nativeStyle.minimum,maximum:nativeStyle.maximum,value:nativeStyle.value,paintMargins:nativeStyle.paintMargins,textureWidth:nativeStyle.textureWidth,textureHeight:nativeStyle.textureHeight,enabled:bar.enabled,styleName:nativeStyle.styleName}) : ({})
 readonly property var geometryResult: nativeGeometry ? nativeGeometry.evaluate(geometryInput) : ({valid:false})
 function qr(r) {return r?Qt.rect(r.x,r.y,r.width,r.height):Qt.rect(0,0,0,0)}
 readonly property var rects: ({up:qr(geometryResult.up),down:qr(geometryResult.down),handle:qr(geometryResult.handle),groove:qr(geometryResult.groove)})
 readonly property bool usable: graphics.length === 2 && nativeStyle !== null && geometryResult.valid
  && [rects.up,rects.down].every(r => r.width >= 8 && r.height >= 8)
  && rects.groove.x === nativeStyle.grooveRect.x && rects.groove.y === nativeStyle.grooveRect.y
  && rects.groove.width === nativeStyle.grooveRect.width && rects.groove.height === nativeStyle.grooveRect.height
 Item {
  id: skin; parent:bar.background;anchors.fill:parent;z:2
  visible:bar.skinEnabled&&bar.usable&&bar.interactive
  // Cover the native paint; preserve its visible/opacity/state bindings so
  // StyleItem keeps its QStyleOption current for the SDK's own hit-testing.
  // This layer accepts no input. MouseArea, padding, policy and the existing
  // arrow-repeat Timer remain entirely owned by the desktop style.
  Rectangle { anchors.fill: parent; color: bar.domainosPalette.background }
  Bevel {x:bar.rects.groove.x;y:bar.rects.groove.y;width:bar.rects.groove.width;height:bar.rects.groove.height;paletteOverride:bar.domainosPalette;thickness:1;simpleRelief:true;sunken:true;face:bar.domainosPalette.recessed}
  Repeater {
   model:["up","down","handle"]
   delegate:Bevel {
    required property string modelData
    readonly property rect nativeRect:bar.rects[modelData]
    x:nativeRect.x;y:nativeRect.y;width:nativeRect.width;height:nativeRect.height
    paletteOverride:bar.domainosPalette;thickness:2;simpleRelief:true
    sunken:bar.nativeStyle&&bar.nativeStyle.sunken&&bar.nativeStyle.activeControl===modelData
    face:bar.domainosPalette.background
    Item {
     anchors.centerIn: parent
     width: 7; height: 4
     rotation: bar.horizontal ? -90 : 0
     visible: parent.modelData !== "handle"
     readonly property string direction: parent.modelData
     readonly property bool held: parent.sunken
     Repeater {
      model: 4
      delegate: Rectangle {
       required property int index
       width: 1 + index*2; height: 1; color: bar.domainosPalette.black
       x: Math.floor((parent.width-width)/2) + (parent.held ? 1 : 0)
       y: (parent.direction === "up" ? index : 3-index) + (parent.held ? 1 : 0)
      }
     }
    }
   }
  }
 }
}
