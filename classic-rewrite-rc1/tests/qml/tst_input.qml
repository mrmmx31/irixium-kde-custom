// SPDX-License-Identifier: GPL-3.0-or-later
// These are REAL QtTest tests when run via testar.sh --qml. They are not
// reported as passed by Node/Python. They do not load KWin's native popup.
import QtQuick
import QtTest
import "../../package/contents/ui"
TestCase {
    id: test
    name: "IrixClassicInput"
    when: windowShown
    width: 700; height: 250
    ButtonInput { id: button; x:20; y:20; width:26; height:24; kind:"minimize" }
    Surface {
        id: smoke
        x:100; y:100; width:591; height:100
        caption:"IRIX Classic — carregamento de Surface"
    }
    SignalSpy { id: activation; target:button; signalName:"activate" }
    SignalSpy { id: closing; target:button; signalName:"closeRequested" }
    function init() {
        button.cancelGesture();button.kind="minimize";button.available=true;
        button.menuOnPress=true;button.closeOnDouble=false;
        mouseMove(test,650,50);activation.clear();closing.clear();
    }
    function cleanup() { mouseRelease(test,650,50,Qt.LeftButton);button.cancelGesture(); }
    function test_hover_inert() {
        mouseMove(button,10,10);compare(button.down,false);compare(activation.count,0);
    }
    function test_release_activates_once() {
        mousePress(button,10,10,Qt.LeftButton);compare(button.down,true);compare(activation.count,0);
        mouseRelease(button,10,10,Qt.LeftButton);compare(button.down,false);compare(activation.count,1);
    }
    function test_leave_cancels() {
        mousePress(button,10,10,Qt.LeftButton);mouseMove(test,650,50);compare(button.down,false);
        mouseRelease(test,650,50,Qt.LeftButton);compare(activation.count,0);
    }
    function test_reenter_restores_pressed_state() {
        mousePress(button,10,10,Qt.LeftButton);mouseMove(test,650,50);
        mouseMove(button,10,10);compare(button.down,true);
        mouseRelease(button,10,10,Qt.LeftButton);compare(activation.count,1);
    }
    function test_disabled_still_consumes_without_action() {
        button.available=false;mouseClick(button,10,10,Qt.LeftButton);
        compare(button.down,false);compare(activation.count,0);
    }
    function test_disable_during_gesture_cancels() {
        mousePress(button,10,10,Qt.LeftButton);button.available=false;
        button.available=true;mouseRelease(button,10,10,Qt.LeftButton);
        compare(button.down,false);compare(activation.count,0);
    }
    function test_menu_on_press_not_release() {
        button.kind="menu";mousePress(button,10,10,Qt.LeftButton);compare(activation.count,1);
        mouseRelease(button,10,10,Qt.LeftButton);compare(activation.count,1);
    }
    function test_local_menu_fallback() {
        button.kind="menu";button.menuOnPress=false;
        mousePress(button,10,10,Qt.LeftButton);compare(activation.count,0);
        mouseRelease(button,10,10,Qt.LeftButton);compare(activation.count,1);
    }
    function test_hidden_control_cancels() {
        mousePress(button,10,10,Qt.LeftButton);button.visible=false;
        compare(button.down,false);button.visible=true;
        mouseRelease(button,10,10,Qt.LeftButton);compare(activation.count,0);
    }
    function test_runtime_surface_loads() {
        compare(smoke.metrics.top,32);compare(smoke.metrics.border,8);
        smoke.maximizedWindow=true;compare(smoke.metrics.top,24);
        smoke.maximizedWindow=false;smoke.maximizeAllowed=false;
        wait(50);smoke.maximizeAllowed=true;
    }
}
