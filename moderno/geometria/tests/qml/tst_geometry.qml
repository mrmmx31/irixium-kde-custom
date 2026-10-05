import QtQuick
import QtTest
import org.kde.kwin.decoration
TestCase {
    name: "IrixiumModernGeometry"
    when: windowShown
    width: 800; height: 600
    property var scene
    Component { id: factory; Fixture {} }
    function init() { scene = createTemporaryObject(factory, this); verify(scene !== null); wait(1); }
    function test_normal() {
        tryCompare(scene.leftGroup, "width", 22);
        tryCompare(scene.rightGroup, "width", 50);
        compare(scene.leftGroup.x,9);
        compare(scene.rightGroup.x,741);
        compare(scene.leftGroup.y,9); compare(scene.rightGroup.y,9);
    }
    function test_maximized() {
        scene.client.maximized=true;
        tryCompare(scene.leftGroup,"y",6);
        compare(scene.rightGroup.y,6);
        compare(scene.leftGroup.x,6);compare(scene.rightGroup.x,744);
    }
    function test_hidden_help_identity() {
        compare(scene.rightGroup.irixiumEntries.length,3);
        compare(scene.rightGroup.irixiumEntries[0].item.visible,false);
        compare(scene.rightGroup.irixiumEntries[2].type,DecorationOptions.DecorationButtonMaximizeRestore);
        compare(scene.rightGroup.irixiumEntries[2].item.buttonType,undefined);
    }
    function test_help_becomes_visible() {
        scene.config.helpVisible=true;
        tryCompare(scene.rightGroup,"width",78);
    }
    function test_reorder() {
        scene.rightGroup.buttons=[DecorationOptions.DecorationButtonMinimize,DecorationOptions.DecorationButtonMaximizeRestore];
        tryCompare(scene.rightGroup,"width",50);
        compare(scene.rightGroup.irixiumEntries.length,2);
    }
    function test_spacer() {
        scene.rightGroup.buttons=[DecorationOptions.DecorationButtonMinimize,DecorationOptions.DecorationButtonExplicitSpacer,
                                  DecorationOptions.DecorationButtonMaximizeRestore];
        tryCompare(scene.rightGroup,"width",78);
    }
    function test_active_does_not_change_positions() {
        scene.client.active=false;
        compare(scene.rightGroup.x,741);compare(scene.rightGroup.y,9);
    }
    function test_other_theme_uses_original_spacing() {
        scene.config.buttonSpacing=5;
        tryCompare(scene.rightGroup,"width",50);
        scene.config.decorationPath="/fixture/Breeze/decoration.svg";
        tryCompare(scene.rightGroup,"width",49);
        compare(scene.rightGroup.irixiumLayout,false);
    }
}
