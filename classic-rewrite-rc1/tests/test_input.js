// SPDX-License-Identifier: GPL-3.0-or-later
const assert=require('assert');const {load}=require('./render');const input=load('InputState.js');
const keys={left:1,right:2,middle:4};let count=0;
function test(name,fn){fn();count++;console.log('OK',name);}
function controller(kind='minimize',available=true,menuOnPress=true,closeOnDouble=false){
 let state=input.idle(), actions=[];const policy={kind,available,menuOnPress,closeOnDouble};
 return {policy,actions,get down(){return input.depressed(state,policy.available);},
 send(type,button=1,inside=true){const r=input.step(state,{type,button,inside},policy,keys);state=r.state;
 if(r.action)actions.push([r.action,r.button]);return r;}};
}
test('hover has no visual pressure or action',()=>{const c=controller();c.send('move');assert(!c.down);assert.equal(c.actions.length,0);});
test('minimize acts exactly once on release',()=>{const c=controller();c.send('press');assert(c.down);assert.equal(c.actions.length,0);c.send('release');assert(!c.down);assert.equal(c.actions.length,1);c.send('release');assert.equal(c.actions.length,1);});
test('leave-release cancels',()=>{const c=controller();c.send('press');c.send('move',0,false);assert(!c.down);c.send('release',1,false);assert.equal(c.actions.length,0);});
test('leave-reenter-release acts',()=>{const c=controller();c.send('press');c.send('move',0,false);c.send('move',0,true);assert(c.down);c.send('release');assert.equal(c.actions.length,1);});
test('grab cancellation resets without action',()=>{const c=controller();c.send('press');c.send('cancel');assert(!c.down);c.send('release');assert.equal(c.actions.length,0);});
test('disabled never acts',()=>{const c=controller('minimize',false);for(const e of ['press','release','accessible','double'])c.send(e);assert(!c.down);assert.equal(c.actions.length,0);});
test('disable-reenable in gesture cannot restore stale press',()=>{const c=controller();c.send('press');c.policy.available=false;c.send('cancel');c.policy.available=true;c.send('release');assert.equal(c.actions.length,0);});
test('menu opens on press only once',()=>{const c=controller('menu');c.send('press');assert.equal(c.actions.length,1);c.send('release');assert.equal(c.actions.length,1);});
test('menu cancellation cannot issue a second popup on release',()=>{const c=controller('menu');c.send('press');c.send('cancel');c.send('release');assert.equal(c.actions.length,1);assert(!c.down);});
test('menu release mode is an explicit local fallback',()=>{const c=controller('menu',true,false);c.send('press');assert.equal(c.actions.length,0);c.send('release');assert.equal(c.actions.length,1);});
test('close only with opt-in preference and left menu double-click',()=>{for(const enabled of [false,true])for(const k of ['menu','minimize','maximize']){const c=controller(k,true,true,enabled);c.send('double');assert.equal(c.actions.length,enabled&&k==='menu'?1:0);}});
test('right menu double-click cannot close',()=>{const c=controller('menu',true,true,true);c.send('double',2);assert.equal(c.actions.length,0);});
test('left/right/middle maximize preserved',()=>{for(const b of [1,2,4]){const c=controller('maximize');c.send('press',b);c.send('release',b);assert.deepEqual(c.actions,[['activate',b]]);}});
test('minimize ignores non-left buttons',()=>{for(const b of [2,4]){const c=controller();c.send('press',b);c.send('release',b);assert.equal(c.actions.length,0);}});
test('mismatched release does not trigger or discard original press',()=>{const c=controller('maximize');c.send('press',1);c.send('press',2);c.send('release',2);assert(c.down);assert.equal(c.actions.length,0);c.send('release',1);assert.equal(c.actions.length,1);});
test('accessibility activation is capability-checked',()=>{for(const k of ['menu','minimize','maximize']){const c=controller(k);c.send('accessible');assert.deepEqual(c.actions,[['activate',1]]);}});
test('press outside and unsolicited release are inert',()=>{const c=controller();c.send('press',1,false);c.send('release');assert.equal(c.actions.length,0);});
test('unknown kind is rejected',()=>{const c=controller('oops');c.send('press');c.send('release');c.send('accessible');assert.equal(c.actions.length,0);});
console.log(`${count} testes de máquina de estados: OK (Node.js, não eventos Qt/KWin).`);
