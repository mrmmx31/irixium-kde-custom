// SPDX-License-Identifier: GPL-2.0-or-later
// Execute the actual QML JavaScript handlers with mocks. This is NOT a Qt Quick test.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const test = require('node:test');
const qml = fs.readFileSync(path.join(__dirname, '../MenuButton.qml'), 'utf8');
function block(name) {
    const start = qml.indexOf(name + ':');
    assert(start >= 0, name);
    const open = qml.indexOf('{', start);
    let depth = 1, i = open + 1;
    for (; depth && i < qml.length; ++i) {
        if (qml[i] === '{') ++depth;
        if (qml[i] === '}') --depth;
    }
    assert.equal(depth, 0);
    return qml.slice(open + 1, i - 1);
}
const args = ['menuButton', 'parent', 'timer', 'pressFlash', 'decoration', 'Qt', 'mouse'];
const handlers = Object.fromEntries(['onPressed','onReleased','onCanceled','onExited','onClicked','onDoubleClicked']
    .map(name => [name, new Function(...args, block(name))]));
const isIrixiumSource = qml.match(/readonly property bool isIrixium: ([\s\S]*?)\n    \/\//)[1].trim();
const detect = new Function('auroraeTheme', 'return (' + isIrixiumSource + ')');
const closeSource = qml.match(/property bool closeOnDoubleClick: (.+)/)[1];
const closePolicy = new Function('isIrixium','decorationSettings','return (' + closeSource + ')');
const downSource = qml.match(/readonly property bool irixiumDown: ([\s\S]*?)\n    readonly property/)[1];
const down = new Function('isIrixium','pressed','hovered','pressFlash','return (' + downSource + ')');
function setup(irix=true, preference=false) {
    const menuButton = {isIrixium:irix, pressed:false, hovered:false};
    Object.defineProperty(menuButton,'closeOnDoubleClick',{get:()=>closePolicy(irix,{closeOnDoubleClickOnMenu:preference})});
    const timer = {running:false,start(){this.running=true;},stop(){this.running=false;}};
    const pressFlash = {running:false,restart(){this.running=true;},stop(){this.running=false;}};
    const calls = {menu:0,close:0};
    const decoration = {requestShowWindowMenu(){++calls.menu;},requestClose(){++calls.close;}};
    const Qt = {LeftButton:1,RightButton:2};
    return {menuButton,timer,pressFlash,calls,
        fire(name,button=1){ handlers[name](menuButton,menuButton,timer,pressFlash,decoration,Qt,{button}); },
        down(){return down(irix,menuButton.pressed,menuButton.hovered,pressFlash);} };
}
test('recognizes Irixium svg and svgz',()=>{
    assert.equal(detect({decorationPath:'/home/u/.local/share/aurorae/themes/Irixium/decoration.svg'}),true);
    assert.equal(detect({decorationPath:'/usr/share/aurorae/themes/Irixium/decoration.svgz'}),true);
});
test('does not style similarly named or unrelated themes',()=>{
    for(const p of ['/theme/IrixiumOther/decoration.svg','/theme/Other/decoration.svg','/Irixium/other.svg'])
        assert.equal(detect({decorationPath:p}),false);
    assert.equal(detect(undefined),false);
});
test('hover events are enabled and update the visual flag',()=>{
    assert(qml.includes('hoverEnabled: true'));
    const line=qml.match(/onEntered: (.+)/)[1];
    const menuButton={hovered:false}; new Function('menuButton',line)(menuButton);
    assert.equal(menuButton.hovered,true);
});
test('press depresses Irixium and starts visual feedback',()=>{
    const s=setup(); s.fire('onPressed'); assert(s.down()); assert(s.pressFlash.running); assert(!s.timer.running);
});
test('quick release retains the short flash, which can expire',()=>{
    const s=setup(); s.fire('onPressed'); s.fire('onReleased'); assert(s.down());
    s.pressFlash.stop(); assert(!s.down());
});
test('holding remains depressed after flash expiry',()=>{
    const s=setup(); s.fire('onPressed'); s.pressFlash.stop(); assert(s.down());
    s.fire('onReleased'); assert(!s.down());
});
test('canceled press clears flags and timers',()=>{
    const s=setup(); s.fire('onPressed'); s.fire('onCanceled');
    assert(!s.down()); assert(!s.menuButton.pressed); assert(!s.menuButton.hovered); assert(!s.pressFlash.running);
});
test('leaving the button clears the press',()=>{
    const s=setup(); s.fire('onPressed'); s.fire('onExited'); assert(!s.down()); assert(!s.menuButton.pressed);
});
test('single left click opens menu without closing or delay',()=>{
    const s=setup(); s.fire('onPressed'); s.fire('onReleased'); s.fire('onClicked');
    assert.equal(s.calls.menu,1); assert.equal(s.calls.close,0);
});
test('right click opens menu',()=>{
    const s=setup(); s.fire('onPressed',2); s.fire('onReleased',2); s.fire('onClicked',2);
    assert.equal(s.calls.menu,1); assert.equal(s.calls.close,0);
});
test('Irixium also preserves the existing double-click preference',()=>{
    for(const pref of [true,false]) { const s=setup(true,pref); s.fire('onDoubleClicked'); assert.equal(s.calls.close,pref ? 1 : 0); }
});
test('other-theme double-click preference remains honored',()=>{
    const s=setup(false,true); s.fire('onDoubleClicked'); assert.equal(s.calls.close,1);
    const t=setup(false,false); t.fire('onDoubleClicked'); assert.equal(t.calls.close,0);
});
test('other themes never activate Irixium press visuals',()=>{
    const s=setup(false); s.fire('onPressed'); assert(!s.pressFlash.running); assert(!s.down());
});
test('original icon is still used outside Irixium',()=>{
    assert(qml.includes('source: decoration.client.icon'));
    assert(qml.includes('visible: !menuButton.isIrixium'));
});
