"use strict";
(() => {
  function status(message) {
    let box = document.getElementById('vimium-connection-status');
    if (!box) {
      box = document.createElement('div');
      box.id = 'vimium-connection-status';
      box.style.cssText = 'position:fixed;bottom:8px;right:8px;z-index:100000;padding:8px 12px;background:#fff3cd;color:#222;border-radius:6px;font:13px sans-serif;max-width:480px';
      box.setAttribute('role', 'status');
      document.body.append(box);
    }
    box.textContent = message;
  }
  window.VimiumInjector = { callback(code, reason) {
    if (code === 2) {
      const box = document.getElementById('vimium-connection-status');
      if (box) box.remove();
      if (window.VApi) {
        window.VApi.u = () => {
          const routed = location.pathname.slice(1);
          // PDF.js rewrites the path to the original URL; its query is then
          // the PDF query, even if it contains a parameter named file.
          if (/^(https?:|file:)\/\//.test(routed)) return routed + location.search;
          return new URLSearchParams(location.search).get('file') || location.href;
        };
      }
    } else if (code === -1) {
      status('Vimium C not connected / 尚未连接：add this ID to trusted extensions / 加入受信任扩展：' + chrome.runtime.id + '; reload / 刷新。' + (reason || ''));
    }
  }};
  window.addEventListener('vimium-version-mismatch', () => status('Vimium C version mismatch / 版本不匹配：rebuild the local bridge / 请更新兼容包。PDF viewing remains available / PDF 阅读仍可用。'));
})();
