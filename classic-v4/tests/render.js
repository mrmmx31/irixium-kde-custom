// SPDX-License-Identifier: GPL-3.0-or-later
// Executes the actual paint functions. A recording Context2D is NOT Qt Quick.
const fs = require('fs'), path = require('path'), vm = require('vm');
const ui = path.join(__dirname, '../kwin/decorations/irixium_irix_classic_v4/contents/ui');
function load(file, extra = {}) {
  const code = fs.readFileSync(path.join(ui, file), 'utf8').replace(/^\.(?:pragma|import).*$/mg, '');
  const context = {Math, Number, ...extra}; vm.createContext(context);
  vm.runInContext(code, context, {filename: file}); return context;
}
const pixels = load('Pixels.js');
const painter = load('Painter.js', {Pixels: pixels});
function render(w=591,h=540,s=1,active=true,max=false,hover='',down='',disabled='') {
  const cmds = []; let offX=0, offY=0;
  const ctx = {fillStyle: '#000000', fillRect(x,y,w,h) {
    if (![x,y,w,h].every(Number.isFinite) || w < 0 || h < 0) throw Error('invalid rectangle');
    cmds.push([x+offX,y+offY,w,h,this.fillStyle]);
  }};
  painter.paintFrame(ctx,w,h,s,active,max);
  const g=painter.geometry(w,s,max);
  for (const kind of ['menu','minimize','maximize']) {
    if (kind==='minimize' && w<90*s || kind==='maximize' && w<66*s) continue;
    const b=g[kind]; offX=b.x;offY=b.y;
    painter.paintButton(ctx,kind,b.w,b.h,s,active,kind===hover,kind===down,kind!==disabled);
  }
  return {width:w,height:h,rectangles:cmds,geometry:g};
}
module.exports = {render,painter,pixels};
if (require.main === module) {
 const args=process.argv.slice(2); const data=render(Number(args[0]||591),Number(args[1]||540),Number(args[2]||1),args[3]!=='inactive',args[4]==='max',args[5]||'',args[6]||'',args[7]||'');
 process.stdout.write(JSON.stringify(data));
}
