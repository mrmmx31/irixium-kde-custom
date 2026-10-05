// SPDX-License-Identifier: GPL-3.0-or-later
const assert = require('assert');
const {render, painter, pixels} = require('./render.js');
let cases = 0;
for (const s of [1, 2, 3]) for (const active of [true, false]) for (const max of [true, false]) {
  for (const [w,h] of [[100,80],[321,199],[591,540],[1920,1080]]) {
    const out = render(w*s,h*s,s,active,max);
    const expectedPalette = painter.palette(active);
    assert(out.rectangles.length > 0);
    for (const [x,y,ww,hh,color] of out.rectangles) {
      assert([x,y,ww,hh].every(Number.isInteger));
      assert(ww > 0 && hh > 0 && x >= 0 && y >= 0);
      assert(x+ww <= w*s && y+hh <= h*s);
      assert(expectedPalette.includes(color));
      if(max) assert(y+hh <= 24*s);
    }
    cases++;
  }
}
for (const kind of ['menu','minimize','maximize']) {
  const size = {menu:[17,5],minimize:[5,5],maximize:[15,17]}[kind];
  assert.strictEqual(pixels.glyphs[kind][0].length,size[0]);
  assert.strictEqual(pixels.glyphs[kind].length,size[1]);
  for (const active of [true,false]) for (const max of [true,false]) {
    for (const state of ['hover','down','disabled']) {
      const out=render(591,540,1,active,max,
        state==='hover'?kind:'',state==='down'?kind:'',state==='disabled'?kind:'');
      assert(out.rectangles.every(r=>r.slice(0,4).every(Number.isFinite)));
      assert(out.rectangles.every(r=>painter.palette(active).includes(r[4])));
      cases++;
    }
  }
}
const normal=painter.geometry(591,1,false), maximized=painter.geometry(591,1,true);
for (const k of ['menu','minimize','maximize']) {
  assert.strictEqual(normal[k].y-maximized[k].y,8);
  assert.strictEqual(normal[k].h,maximized[k].h);
}
assert.strictEqual(normal.caption.x,44);
assert.strictEqual(normal.border,8);
assert.strictEqual(normal.top,32);
assert.strictEqual(maximized.top,24);
console.log(`${cases} cenários de desenho + dimensões dos símbolos e geometria: OK.`);
console.log('Motor: Node.js / Context2D gravador. NÃO é teste do runtime Qt Quick/KWin.');
