// SPDX-License-Identifier: GPL-3.0-or-later
// Recorder for the real painting functions; NOT a Qt Quick renderer.
const fs=require('fs'), path=require('path'), vm=require('vm');
const ui=path.join(__dirname,'../package/contents/ui');
function load(file,extra={}) {
  const text=fs.readFileSync(path.join(ui,file),'utf8').replace(/^\.(?:pragma|import).*$/mg,'');
  const c={Math,Number,...extra}; vm.createContext(c); vm.runInContext(text,c,{filename:file}); return c;
}
const pixels=load('Pixels.js'), geometry=load('Geometry.js');
const painter=load('Artwork.js',{Pixels:pixels,Geometry:geometry});
function render(w=591,h=540,s=1,active=true,max=false,hover='',down='',disabled='') {
  let ox=0,oy=0;const stack=[],cmds=[];
  const ctx={fillStyle:'#000000',
    save(){stack.push([ox,oy,this.fillStyle]);},
    restore(){[ox,oy,this.fillStyle]=stack.pop();},
    translate(x,y){ox+=x;oy+=y;},
    fillRect(x,y,w,h){
      if (![x,y,w,h].every(Number.isFinite)||w<0||h<0)throw Error('invalid rectangle');
      cmds.push([x+ox,y+oy,w,h,this.fillStyle]);
    }};
  const state={};for (const k of ['menu','minimize','maximize'])state[k]={enabled:k!==disabled,down:k===down};
  painter.paintDecoration(ctx,w,h,s,active,max,state);
  if(stack.length)throw Error('unbalanced context');
  return {width:w,height:h,rectangles:cmds,geometry:geometry.metrics(w,s,max)};
}
module.exports={load,render,pixels,painter,geometry};
if(require.main===module){const a=process.argv.slice(2);process.stdout.write(JSON.stringify(render(
  Number(a[0]||591),Number(a[1]||540),Number(a[2]||1),a[3]!=='inactive',a[4]==='max',a[5]||'',a[6]||'',a[7]||'')));}
