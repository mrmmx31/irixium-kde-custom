// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Runs the production JS, not a second implementation of the detection rules.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ui = path.join(__dirname, '../package/contents/ui');
function load(name) {
    const scope = {};
    vm.createContext(scope);
    vm.runInContext(fs.readFileSync(path.join(ui, name), 'utf8').replace(/^\.pragma library\s*$/m, ''), scope);
    return scope;
}
const p = load('PreviewSupport.js');
const g = load('Geometry.js');
let count = 0;
function test(name, body) {
    body(); ++count; console.log('PASS', name);
}
function plain(v) { return JSON.parse(JSON.stringify(v)); }
const deco = {}, other = {};
const host = {drawBackground: false, windowColor: '#c1c1c1', decoration: deco};
test('null host is not a preview', () => assert.equal(p.isPreviewHost(null, deco), false));
test('undefined host is not a preview', () => assert.equal(p.isPreviewHost(undefined, deco), false));
test('real offscreen Item is not a preview', () => assert.equal(p.isPreviewHost({width: 600, height: 400}, deco), false));
test('missing decoration identity is rejected', () => assert.equal(p.isPreviewHost(host, null), false));
test('different decoration identity is rejected', () => assert.equal(p.isPreviewHost(host, other), false));
test('null decoration in host is rejected', () => assert.equal(p.isPreviewHost({...host, decoration: null}, deco), false));
test('background property must be boolean', () => assert.equal(p.isPreviewHost({...host, drawBackground: 'false'}, deco), false));
test('absent color is rejected', () => assert.equal(p.isPreviewHost({...host, windowColor: undefined}, deco), false));
test('null color is rejected', () => assert.equal(p.isPreviewHost({...host, windowColor: null}, deco), false));
test('contract and identity enable preview mode', () => assert.equal(p.isPreviewHost(host, deco), true));
test('suppressed native background needs a fill', () => assert.equal(p.needsFill(host, deco), true));
test('native drawing suppresses the extra fill', () => assert.equal(p.needsFill({...host, drawBackground: true}, deco), false));
test('initial native draw true then Aurorae disables it', () => {
    const h={...host, drawBackground:true}; assert.equal(p.needsFill(h,deco),false);
    h.drawBackground=false; assert.equal(p.needsFill(h,deco),true);
});
test('caption alone never enables painting', () => assert.equal(p.needsFill({caption:'IRIX Classic',width:260,height:160},deco),false));
test('window palette may differ from the title palette', () => assert.equal(p.needsFill({...host,windowColor:'#101010'},deco),true));
test('detection has no host mutation', () => {
    const h = Object.freeze({...host}); p.needsFill(h,deco); assert.deepEqual(h,host);
});
test('normal client geometry', () => assert.deepEqual(plain(p.clientRect(g.metrics(600,1,false),300,false)),{x:8,y:32,w:584,h:260}));
test('maximized client geometry', () => assert.deepEqual(plain(p.clientRect(g.metrics(600,1,true),300,false)),{x:0,y:24,w:600,h:276}));
test('shaded windows have no fake content', () => assert.equal(p.clientRect(g.metrics(600,1,false),300,true).h,0));
test('missing geometry is empty', () => assert.deepEqual(plain(p.clientRect(null,300,false)),{x:0,y:0,w:0,h:0}));
test('undersized dimensions cannot become negative', () => {
    const r=p.clientRect(g.metrics(3,1,false),4,false); assert.equal(r.w,0); assert.equal(r.h,0);
});
let scenarios=0;
for (const scale of [1,2,3]) for (const max of [false,true])
for (const width of [0,12,300,800]) for (const height of [0,20,160,900]) {
    const m=g.metrics(width,scale,max), r=p.clientRect(m,height,false);
    assert.equal(r.x,m.border);assert.equal(r.y,m.top);
    assert.ok(r.w>=0&&r.h>=0);
    if (r.w>0) assert.equal(r.x+r.w,m.width-m.border);
    if (r.h>0) assert.equal(r.y+r.h,height-m.border);
    assert.equal(p.clientRect(m,height,true).h,0);
    ++scenarios;
}
console.log(`${count} preview contract tests and ${scenarios} geometry scenarios passed.`);
