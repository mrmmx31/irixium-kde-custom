// SPDX-License-Identifier: GPL-3.0-or-later
const assert=require('assert');const {load}=require('./render');const input=load('InputState.js');
const keys={left:1,right:2,middle:4};let count=0;
function test(name,fn){fn();count++;console.log('OK',name);}
function controller(kind='minimize',available=true,menuOnPress=true,closeOnDouble=false){
 let state=input.idle(), actions=[];const policy={kind,available,menuOnPress,closeOnDouble};
 return {policy,actions,get down(){return input.depressed(state,policy.available);},get waiting(){return !!state.waiting;},
 send(type,button=1,inside=true){const r=input.step(state,{type,button,inside},policy,keys);state=r.state;
 if(r.action)actions.push([r.action,r.button]);return r;}};
}
test('hover has no visual pressure or action',()=>{const c=controller();c.send('move');assert(!c.down);assert.equal(c.actions.length,0);});
test('minimize acts immediately on press exactly once',()=>{const c=controller();c.send('press');assert(!c.down);assert.deepEqual(c.actions,[['activate',1]]);c.send('release');assert.deepEqual(c.actions,[['activate',1]]);});
test('minimize does not wait for release after press',()=>{const c=controller();c.send('press');c.send('move',0,false);c.send('release',1,false);assert.deepEqual(c.actions,[['activate',1]]);});
test('maximize acts immediately for all supported buttons',()=>{for(const b of [1,2,4]){const c=controller('maximize');c.send('press',b);assert.deepEqual(c.actions,[['activate',b]]);c.send('release',b);assert.deepEqual(c.actions,[['activate',b]]);}});
test('grab cancellation cannot repeat an immediate action',()=>{const c=controller();c.send('press');c.send('cancel');assert(!c.down);c.send('release');assert.deepEqual(c.actions,[['activate',1]]);});
test('disabled never acts',()=>{const c=controller('minimize',false);for(const e of ['press','release','accessible','double'])c.send(e);assert(!c.down);assert.equal(c.actions.length,0);});
test('disable-reenable cannot repeat an immediate action',()=>{const c=controller();c.send('press');c.policy.available=false;c.send('cancel');c.policy.available=true;c.send('release');assert.deepEqual(c.actions,[['activate',1]]);});
test('menu opens on press only once',()=>{const c=controller('menu');c.send('press');assert.equal(c.actions.length,1);c.send('release');assert.equal(c.actions.length,1);});
test('menu cancellation cannot issue a second popup on release',()=>{const c=controller('menu');c.send('press');c.send('cancel');c.send('release');assert.equal(c.actions.length,1);assert(!c.down);});
test('menu release mode is an explicit local fallback',()=>{const c=controller('menu',true,false);c.send('press');assert.equal(c.actions.length,0);c.send('release');assert.equal(c.actions.length,1);});
test('close only with opt-in preference and left menu double-click',()=>{for(const enabled of [false,true])for(const k of ['menu','minimize','maximize']){const c=controller(k,true,true,enabled);c.send('press');c.send('release');c.actions.length=0;c.send('double');assert.equal(c.actions.length,enabled&&k==='menu'?1:0);}});
test('right menu double-click cannot close',()=>{const c=controller('menu',true,true,true);c.send('double',2);assert.equal(c.actions.length,0);});
test('left/right/middle maximize preserved',()=>{for(const b of [1,2,4]){const c=controller('maximize');c.send('press',b);c.send('release',b);assert.deepEqual(c.actions,[['activate',b]]);}});
test('minimize ignores non-left buttons',()=>{for(const b of [2,4]){const c=controller();c.send('press',b);c.send('release',b);assert.equal(c.actions.length,0);}});
test('each supported maximize press acts once',()=>{const c=controller('maximize');c.send('press',1);c.send('press',2);c.send('release',2);assert(!c.down);assert.deepEqual(c.actions,[['activate',1],['activate',2]]);c.send('release',1);assert.deepEqual(c.actions,[['activate',1],['activate',2]]);});
test('accessibility activation is capability-checked',()=>{for(const k of ['menu','minimize','maximize']){const c=controller(k);c.send('accessible');assert.deepEqual(c.actions,[['activate',1]]);}});
test('press outside and unsolicited release are inert',()=>{const c=controller();c.send('press',1,false);c.send('release');assert.equal(c.actions.length,0);});
test('unknown kind is rejected',()=>{const c=controller('oops');c.send('press');c.send('release');c.send('accessible');assert.equal(c.actions.length,0);});

test('left menu press and release never post before double-click classification',()=>{
 for(const menuOnPress of [false,true]){const c=controller('menu',true,menuOnPress,true);
 c.send('press');assert(c.down);assert.equal(c.actions.length,0);
 c.send('release');assert(!c.down);assert(c.waiting);assert.equal(c.actions.length,0);}
});
test('single left click posts exactly once at timeout',()=>{const c=controller('menu',true,true,true);
 c.send('press');c.send('release');c.send('timeout');c.send('timeout');
 assert.deepEqual(c.actions,[['activate',1]]);assert(!c.waiting);assert(!c.down);
});
test('complete native double-click sequence closes without posting any popup',()=>{
 const c=controller('menu',true,true,true);
 for(const e of ['press','release','press','double','release','timeout'])c.send(e);
 assert.deepEqual(c.actions,[['close',1]]);assert(!c.down);assert(!c.waiting);
});
test('double-click without second press signal also works',()=>{const c=controller('menu',true,true,true);
 for(const e of ['press','release','double','release','timeout'])c.send(e);
 assert.deepEqual(c.actions,[['close',1]]);
});
test('unsolicited double-click cannot close',()=>{const c=controller('menu',true,true,true);
 c.send('double');assert.equal(c.actions.length,0);
});
test('second press suspends pending timeout',()=>{const c=controller('menu',true,true,true);
 for(const e of ['press','release','press','timeout'])c.send(e);assert.equal(c.actions.length,0);
 c.send('double');assert.deepEqual(c.actions,[['close',1]]);
});
test('two clicks not recognized as double never close',()=>{const c=controller('menu',true,true,true);
 for(const e of ['press','release','press','release','timeout'])c.send(e);
 assert.deepEqual(c.actions,[['activate',1]]);
});
test('canceled pending click cannot open a popup or close later',()=>{const c=controller('menu',true,true,true);
 for(const e of ['press','release','cancel','timeout','double'])c.send(e);assert.equal(c.actions.length,0);
});
test('leaving during pending click cancels popup',()=>{const c=controller('menu',true,true,true);
 c.send('press');c.send('release');c.send('move',0,false);c.send('timeout');
 c.send('move',0,true);c.send('double');assert.equal(c.actions.length,0);
});
test('left release outside does not schedule popup',()=>{const c=controller('menu',true,true,true);
 c.send('press');c.send('release',1,false);c.send('timeout');assert.equal(c.actions.length,0);
});
test('right click opens immediately and cancels pending left click',()=>{const c=controller('menu',true,true,true);
 c.send('press');c.send('release');c.send('press',2);c.send('release',2);c.send('timeout');
 assert.deepEqual(c.actions,[['activate',2]]);
});
test('long press opens menu once and cannot close afterward',()=>{const c=controller('menu',true,true,true);
 for(const e of ['press','hold','release','double','timeout'])c.send(e);
 assert.deepEqual(c.actions,[['activate',1]]);
});
test('long press outside cannot open',()=>{const c=controller('menu',true,true,true);
 c.send('press');c.send('move',0,false);c.send('hold',1,false);c.send('release',1,false);
 assert.equal(c.actions.length,0);
});
test('disabled and stale timeout cannot act',()=>{const c=controller('menu',true,true,true);
 c.send('press');c.send('release');c.policy.available=false;c.send('timeout');
 c.policy.available=true;c.send('timeout');c.send('double');assert.equal(c.actions.length,0);
});
test('accessibility request cancels pending click and opens once',()=>{const c=controller('menu',true,true,true);
 for(const e of ['press','release','accessible','timeout'])c.send(e);
 assert.deepEqual(c.actions,[['activate',1]]);
});
test('ordinary minimize/maximize ignore menu timeouts and holds',()=>{for(const k of ['minimize','maximize']){
 const c=controller(k,true,true,true);c.send('press');c.send('hold');c.send('timeout');
 assert(!c.down);assert.deepEqual(c.actions,[['activate',1]]);c.send('release');assert.deepEqual(c.actions,[['activate',1]]);
}});
console.log(`${count} testes de máquina de estados: OK (Node.js, não eventos Qt/KWin).`);
