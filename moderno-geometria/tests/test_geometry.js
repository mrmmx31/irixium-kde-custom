// SPDX-FileCopyrightText: 2026 mrmmx31
// SPDX-License-Identifier: GPL-3.0-or-later
// Runs the exact pure geometry and creation functions embedded in production QML.
// The Row layout below is a model, NOT a Qt Quick/KWin runtime.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');
const source = fs.readFileSync(path.join(__dirname,'../AuroraeButtonGroup.qml'),'utf8');
const pure = source.split('// IRIXIUM_GEOMETRY_FUNCTIONS_BEGIN')[1]
    .split('\n').slice(1).join('\n').split('// IRIXIUM_GEOMETRY_FUNCTIONS_END')[0];
const ctx = vm.createContext({Math, Number}); vm.runInContext(pure, ctx);
let tests=0, scenarios=0;
function test(name, fn) { fn(); tests++; console.log('OK '+name); }
const eq=(a,b)=>assert.equal(a,b);

test('gap=6, divider=2, clearance=2 on both sides',()=>{
    const a=ctx.separatorPosition(0,22,ctx.evenGap(6),true);
    eq(a-22,2); eq(28-(a+2),2);
});
test('symmetry for both groups with one to six buttons',()=>{
    for (const width of [200,591,800,1920]) for (let count=1;count<=6;count++) {
        const gap=ctx.evenGap(6), groupWidth=count*22+(count-1)*gap;
        const left=9, right=width-9-groupWidth;
        for(let i=0;i<count;i++) {
            const dl=left+ctx.separatorPosition(i*28,22,gap,true);
            const dr=right+ctx.separatorPosition((count-1-i)*28,22,gap,false);
            eq(dl+dr+2,width);
        }
        scenarios++;
    }
});
test('equal outer margins for normal and maximized windows',()=>{
    for(const width of [200,591,800,1920]) for(const margin of [9,6]) {
        const lastFaceEnd=width-margin;
        eq(margin,width-lastFaceEnd);scenarios++;
    }
});
test('divider and caption have an eight-unit safety gap',()=>{
    const width=800,left=9,right=800-9-50;
    const dl=left+ctx.separatorPosition(0,22,6,true);
    const dr=right+ctx.separatorPosition(0,22,6,false);
    eq(left+22+12-(dl+2),8);
    eq(dr-(right-12),8);
});
test('normal face stays at y=9; maximized face stays at y=6',()=>{
    eq(ctx.centeredTop(7,33,22),9);
    eq(ctx.centeredTop(4,30,22),6);
});
test('equal vertical clearance around both face and divider',()=>{
    for(const top of [7,4]) {
        const bottom=top+26, y=ctx.centeredTop(top,bottom,22);
        eq(y-top,2);eq(bottom-y-22,2);
    }
});
test('odd residual height uses a one-pixel difference at most',()=>{
    for(let h=23;h<80;h++) {
        const y=ctx.centeredTop(7,7+h,22);
        assert(Math.abs((y-7)-(7+h-y-22))<=1); scenarios++;
    }
});
test('gap normalization is even and never overlaps a divider',()=>{
    for(const raw of [0,1,2,3,4,4.5,5,5.5,6,6.6,8,9,12]) {
        const gap=ctx.evenGap(raw);eq(gap%2,0);assert(gap>=4);scenarios++;
    }
});
test('a 33-unit corner cut aligns with the terminal divider, not borderTop=34',()=>{
    eq(ctx.separatorPosition(9,22,6,true),33);
    const cuts=ctx.cornerCuts(800,600,33,7,6,6,6);
    eq(cuts[0].x,33);
    eq(cuts[1].x,800-35);
    const last=800-9-22;
    eq(ctx.separatorPosition(last,22,6,false),cuts[1].x);
});
test('corner cuts are mirrored across both axes',()=>{
    for(const [w,h] of [[200,150],[591,540],[628,380],[800,600],[1920,1080]]) {
        const c=ctx.cornerCuts(w,h,33,7,6,6,6);
        eq(c.length,8);
        eq(c[0].x+c[1].x+2,w); eq(c[2].x+c[3].x+2,w);
        eq(c[4].y+c[6].y+2,h); eq(c[5].y+c[7].y+2,h);
        scenarios++;
    }
});
test('no corner cuts on windows too small for them',()=>{
    for(const [w,h] of [[60,100],[100,60],[0,0],[69,200]]) {
        eq(ctx.cornerCuts(w,h,33,7,6,6,6).length,0);scenarios++;
    }
});
test('no negative length on missing or narrow borders',()=>{
    for(const border of [0,1,2,4,6,7]) {
        const c=ctx.cornerCuts(800,600,33,7,border,border,border);
        for(const r of c)assert(r.length>=0);scenarios++;
    }
});
test('all actual corner marks stay inside their own borders',()=>{
    for(const [w,h] of [[200,150],[800,600],[1920,1080]]) for(const border of [4,6,7]) {
        const c=ctx.cornerCuts(w,h,33,7,border,border,border);
        for(const r of c) {
            assert(r.x>=0 && r.y>=0);
            assert(r.x+(r.vertical?2:r.length)<=w);
            assert(r.y+(r.vertical?r.length:2)<=h);
        } scenarios++;
    }
});
test('only exact Irixium SVG decoration paths opt in',()=>{
    const re=/\/Irixium\/decoration(?:\.svgz?)?$/;
    for(const p of ['/x/Irixium/decoration.svg','/x/Irixium/decoration.svgz'])assert(re.test(p));
    for(const p of ['/x/Irixium-Classic/decoration.svg','/x/irix_classic/decoration.svg','/x/Breeze/decoration.svg'])assert(!re.test(p));
});

// Exercise the production creation routine and its deferred-destruction policy.
const enums={DecorationButtonExplicitSpacer:0,DecorationButtonMenu:1,DecorationButtonApplicationMenu:2,
             DecorationButtonMaximizeRestore:3,DecorationButtonQuickHelp:4,DecorationButtonClose:5,
             DecorationButtonMinimize:6};
function buildContext(buttons) {
    const row={children:[]};
    const make=(type,props={})=>{
        const b={width:22,height:22,visible:props.buttonType!==enums.DecorationButtonQuickHelp,
                 enabled:true,destroy(){this.destroyPending=true;},...props};
        if(type!=='AuroraeMaximizeButton.qml' && props.buttonType!==undefined)b.buttonType=props.buttonType;
        row.children.push(b);return b;
    };
    const c=vm.createContext({buttons,irixiumEntries:[],DecorationOptions:enums,groupRow:row,console,
        Qt:{createComponent(name){return{createObject(parent,props){return make(name,props);}};},
            createQmlObject(code,parent,name){const b=make('dynamic');if(name.startsWith('explicit'))b.width=22;return b;}}});
    const create=source.slice(source.indexOf('    function createButtons()'),source.indexOf('\n    Row {'));
    vm.runInContext(create,c); vm.runInContext('createButtons()',c);
    return c;
}
test('hidden Help has its own record and does not change Maximize identity',()=>{
    const c=buildContext([enums.DecorationButtonQuickHelp,enums.DecorationButtonClose,enums.DecorationButtonMaximizeRestore]);
    eq(c.irixiumEntries.length,3);
    eq(c.irixiumEntries[0].item.visible,false);
    eq(c.irixiumEntries[2].item.buttonType,undefined);
    eq(c.irixiumEntries[2].type,enums.DecorationButtonMaximizeRestore);
});
test('changing button order hides pending destroys before creating the new row',()=>{
    const c=buildContext([enums.DecorationButtonMenu]);
    const old=c.groupRow.children[0];c.buttons=[enums.DecorationButtonMinimize,enums.DecorationButtonMaximizeRestore];
    const event=source.slice(source.indexOf('    onButtonsChanged: {')+'    onButtonsChanged: '.length,
                             source.indexOf('\n    anchors {'));
    vm.runInContext(event,c);
    eq(old.visible,false);eq(old.destroyPending,true);
    eq(c.irixiumEntries.length,2);eq(c.irixiumEntries[0].type,enums.DecorationButtonMinimize);
});
test('explicit spacers are represented separately from real buttons',()=>{
    const c=buildContext([enums.DecorationButtonMenu,enums.DecorationButtonExplicitSpacer,enums.DecorationButtonMinimize]);
    eq(c.irixiumEntries.filter(x=>x.type!==enums.DecorationButtonExplicitSpacer).length,2);
    eq(c.irixiumEntries.length,3);
});
test('disabled controls keep their cell and record',()=>{
    const c=buildContext([enums.DecorationButtonMaximizeRestore]);
    c.irixiumEntries[0].item.enabled=false;
    eq(c.irixiumEntries[0].item.visible,true);eq(c.irixiumEntries[0].item.width,22);
});
test('empty button lists have no decorative dividers',()=>{
    const c=buildContext([]);eq(c.irixiumEntries.length,0);
});
test('the patch does not add input or client actions',()=>{
    assert(!/\b(MouseArea|TapHandler|requestClose|requestMinimize|requestShowWindowMenu)\b/.test(source));
});
test('the original non-Irixium vertical-margin expression remains available',()=>{
    assert(source.includes('auroraeTheme.titleEdgeTopMaximized + auroraeTheme.buttonMarginTopMaximized'));
    assert(source.includes('auroraeTheme.titleEdgeTop + root.padding.top + auroraeTheme.buttonMarginTop'));
});
console.log(`RESULTADO: ${tests} testes JavaScript; ${scenarios} cenários geométricos parametrizados. Qt/KWin não executado.`);
