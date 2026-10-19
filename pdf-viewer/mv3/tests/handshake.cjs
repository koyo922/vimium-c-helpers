const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = readFileSync(process.argv[2],'utf8');
assert.ok(process.argv[2], 'pass the generated injector path');
const host='hfjbmagddngcpeloejdejnfgbamkjaeg';
function run(response) {
  const loaded=[], events=[], callbacks=[], timers=[];
  class HTMLHtmlElement {}
  const script={src:'chrome-extension://local/vimium/injector.js', dataset:{extensionId:host,vimiumHooks:'false'},parentElement:{insertBefore(s){loaded.push(s.src)}}};
  const context={console, HTMLHtmlElement, location:{host:'local'}, setTimeout(fn){timers.push(fn)}, Event:class {constructor(type){this.type=type}},
    chrome:{runtime:{id:'local',getManifest:()=>({manifest_version:3}), getURL:p=>'chrome-extension://local/'+p,sendMessage(id,msg,cb){assert.equal(id,host);cb(response)}}},
    document:{currentScript:script,readyState:'complete', documentElement:new HTMLHtmlElement(),contains:()=>true,createElement:()=>({})},
    requestIdleCallback:fn=>fn(), VimiumInjector:{callback:(...args)=>callbacks.push(args)},
    window:{dispatchEvent:e=>events.push(e.type)}};
  vm.runInNewContext(source,context);
  for(let i=0;i<timers.length && i<10;i++) timers[i]();
  return {loaded,events,callbacks};
}
const good={s:[`chrome-extension://${host}/content/vimium-c.js`],h:':9e78033',version:'2.12.2'};
assert.deepEqual(run(good).loaded,['chrome-extension://local/vimium/vimium-c.js']);
for(const response of [{...good,version:'2.12.3'},{...good,h:':unexpected'},{...good,s:['https://example.com/remote.js']},{...good,s:[]},{...good,s:null},{...good,h:null},{...good,s:[null]}]) {
  const r=run(response);assert.equal(r.loaded.length,0);assert.deepEqual(r.events,['vimium-version-mismatch']);
}
const denied=run(false); assert.equal(denied.loaded.length,0);assert.equal(denied.callbacks[0][0],-1);
console.log('PASS: matching frontend loads locally; version/build mismatch and unexpected source blocked; allowlist denial reported.');
