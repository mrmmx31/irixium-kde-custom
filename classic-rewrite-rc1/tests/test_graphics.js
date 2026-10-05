// SPDX-License-Identifier: GPL-3.0-or-later
const assert=require('assert'),fs=require('fs'),path=require('path'),crypto=require('crypto');
const {render,painter,pixels,geometry}=require('./render');let n=0;
for(const s of [1,2,3])for(const active of [true,false])for(const max of [true,false])
 for(const [w,h]of [[100,80],[321,199],[591,540],[1920,1080]]){
  const r=render(w*s,h*s,s,active,max);for(const [x,y,ww,hh,c]of r.rectangles){
   assert([x,y,ww,hh].every(Number.isInteger));assert(ww>0&&hh>0&&x>=0&&y>=0);
   assert(x+ww<=w*s&&y+hh<=h*s);assert(painter.palette(active).includes(c));if(max)assert(y+hh<=24*s);
  }n++;
 }
for(const w of [8,25,41,42,50,65,66,89,90,91,92,99]){
 const g=geometry.metrics(w,1,false),names=['menu','minimize','maximize'].filter(k=>g[k].visible);
 for(let i=0;i<names.length;i++)for(let j=i+1;j<names.length;j++){
  const a=g[names[i]],b=g[names[j]];assert(a.x+a.w<=b.x||b.x+b.w<=a.x);
 }
 for(const h of [24,32,36,60])for(const [x,y,ww,hh]of render(w,h).rectangles){assert(x>=0&&y>=0&&x+ww<=w&&y+hh<=h);}
 n++;
}
for(const k of ['menu','minimize','maximize']){
 for(const active of [true,false])for(const max of [true,false]){
  const a=render(591,540,1,active,max),b=render(591,540,1,active,max,k);
  assert.deepEqual(a.rectangles,b.rectangles); // hover makes NO painting difference
  assert.notDeepEqual(a.rectangles,render(591,540,1,active,max,'',k).rectangles);
  const disabled=painter.disabledGlyph(k);assert(disabled.join('').indexOf('1')<0);
  assert.equal(disabled.length,pixels.glyphs[k].length);assert.equal(disabled[0].length,pixels.glyphs[k][0].length);
  n++;
 }
}
const baseline=JSON.parse(fs.readFileSync(path.join(__dirname,'baseline.json')));
for(const c of baseline.cases){const r=render(...c.args),sum=crypto.createHash('sha256').update(JSON.stringify(r.rectangles)).digest('hex');assert.equal(sum,c.rectangles_sha256);n++;}
console.log(`${n} cenários gráficos: OK; ${baseline.cases.length} sequências de repouso preservadas.`);
console.log('Gravador Context2D; não substitui Qt Quick ou KWin.');
