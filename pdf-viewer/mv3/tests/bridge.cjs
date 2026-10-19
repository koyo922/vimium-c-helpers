const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(process.argv[2], 'utf8');
function run(url) {
  let box; const events = {};
  const context = {location: new URL(url), URLSearchParams,
    chrome: {runtime: {id: 'test-local-id'}},
    document: {getElementById: () => box,
      createElement: () => ({style: {}, setAttribute() {}, remove() {box = undefined;}}),
      body: {append(value) {box = value;}}},
    window: {VApi: {}, addEventListener(name, fn) {events[name] = fn;}}};
  vm.runInNewContext(source, context);
  context.window.VimiumInjector.callback(-1, 'denied');
  assert.match(box.textContent, /test-local-id/);
  assert.match(box.textContent, /尚未连接/);
  events['vimium-version-mismatch']();
  assert.match(box.textContent, /version mismatch/);
  context.window.VimiumInjector.callback(2);
  assert.equal(box, undefined);
  return context.window.VApi.u();
}
assert.equal(run('chrome-extension://local/https://example.com/a.pdf?token=abc#page=3'), 'https://example.com/a.pdf?token=abc');
assert.equal(run('chrome-extension://local/https://example.com/a.pdf?file=wrong&token=abc'), 'https://example.com/a.pdf?file=wrong&token=abc');
assert.equal(run('chrome-extension://local/file:///tmp/a%20b.pdf#page=2'), 'file:///tmp/a%20b.pdf');
assert.equal(run('chrome-extension://local/content/web/viewer.html?file=https%3A%2F%2Fexample.com%2Fa.pdf%3Fx%3D1'), 'https://example.com/a.pdf?x=1');
assert.equal(run('chrome-extension://local/content/web/viewer.html'), 'chrome-extension://local/content/web/viewer.html');
console.log('Bridge URL and connection-status behavior passed');
