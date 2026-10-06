// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Qt Quick runtime tests with a simulated PreviewItem contract. Not native KWin.
import QtQuick
import QtTest
import "../../package/contents/ui"
import "../../package/contents/ui/Geometry.js" as Geometry

TestCase {
    id: test
    name: "IrixClassicPreview"
    when: windowShown
    width: 620
    height: 420
    QtObject { id: decorationToken }
    QtObject { id: otherToken }
    Item {
        id: hostItem
        property QtObject decoration: decorationToken
        property color windowColor: "#c1c1c1"
        property bool drawBackground: false
    }
    Item { id: offscreenHost }
    PreviewBackground {
        id: fill
        previewHost: hostItem
        expectedDecoration: decorationToken
        metrics: Geometry.metrics(300,1,false)
        frameHeight: 180
    }
    function init() {
        hostItem.decoration=decorationToken;
        hostItem.windowColor="#c1c1c1";
        hostItem.drawBackground=false;
        fill.previewHost=hostItem;
        fill.expectedDecoration=decorationToken;
        fill.metrics=Geometry.metrics(300,1,false);
        fill.frameHeight=180;
        fill.shaded=false;
    }
    function test_preview_creates_opaque_fill() {
        tryCompare(fill,"active",true);
        tryVerify(function(){return fill.item!==null;});
        compare(fill.item.color,Qt.rgba(193/255,193/255,193/255,1));
        compare(fill.x,8);compare(fill.y,32);compare(fill.width,284);compare(fill.height,140);
    }
    function test_real_host_has_no_rectangle() {
        fill.previewHost=offscreenHost;
        tryCompare(fill,"active",false);compare(fill.item,null);
    }
    function test_null_parent_at_creation_is_safe() {
        fill.previewHost=null;
        tryCompare(fill,"active",false);compare(fill.item,null);
    }
    function test_wrong_decoration_is_rejected() {
        hostItem.decoration=otherToken;
        tryCompare(fill,"active",false);compare(fill.item,null);
    }
    function test_native_background_wins() {
        hostItem.drawBackground=true;
        tryCompare(fill,"active",false);compare(fill.item,null);
        hostItem.drawBackground=false;
        tryCompare(fill,"active",true);tryVerify(function(){return fill.item!==null;});
    }
    function test_palette_changes_are_reflected() {
        tryVerify(function(){return fill.item!==null;});
        hostItem.windowColor="#282828";
        tryCompare(fill.item,"color",Qt.rgba(40/255,40/255,40/255,1));
    }
    function test_only_thumbnail_is_forced_opaque() {
        hostItem.windowColor=Qt.rgba(0.2,0.3,0.4,0.25);
        tryVerify(function(){return fill.item!==null;});
        compare(fill.item.color.a,1);
        // QColor can quantize an alpha component to 16 bits.
        verify(Math.abs(hostItem.windowColor.a-0.25)<0.001);
    }
    function test_reparenting_removes_then_restores_fill() {
        fill.previewHost=offscreenHost;
        tryCompare(fill,"active",false);compare(fill.item,null);
        fill.previewHost=hostItem;
        tryCompare(fill,"active",true);tryVerify(function(){return fill.item!==null;});
    }
    function test_resize_respects_client_boundary() {
        fill.metrics=Geometry.metrics(440,2,false);fill.frameHeight=280;
        compare(fill.x,16);compare(fill.y,64);compare(fill.width,408);compare(fill.height,200);
    }
    function test_maximized_uses_no_outer_border() {
        fill.metrics=Geometry.metrics(300,1,true);
        compare(fill.x,0);compare(fill.y,24);compare(fill.width,300);compare(fill.height,156);
    }
    function test_shaded_and_tiny_have_no_fill() {
        fill.shaded=true;tryCompare(fill,"active",false);compare(fill.item,null);
        fill.shaded=false;fill.frameHeight=10;
        tryCompare(fill,"active",false);compare(fill.item,null);
    }
    function test_visual_item_does_not_handle_input() {
        compare(fill.enabled,false);
        compare(hostItem.drawBackground,false); // no writes to native host
    }
}
