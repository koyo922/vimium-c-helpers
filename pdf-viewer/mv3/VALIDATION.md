# Validation / 验收记录

## Real-browser evidence / 实机证据

The initial local build was installed in Chrome 155 on macOS on 2026-10-19,
with the Chrome Web Store Vimium C 2.12.2 backend. Tests were driven through the
actual browser UI, not inferred from a successful build. The public recipe uses
the same PDF.js commit/frontend snapshot and CSP fix, plus defensive response
validation, bilingual connection messages, and original-PDF URL handling.
The latter publication changes have automated coverage; the whole public build
has not yet been installed across additional browser/OS combinations.

| Target | Observed result |
|---|---|
| https://www.python.org/doc/ | `G` reached footer; `gg`, counted `j/k` moved between top/lower content; `f` showed yellow hints; `/Beginner` found 3 |
| https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf | Loaded 14 pages; `G`: 14, `gg`: 1, `20j`: 2, `20k`: 1; `f` showed viewer-control hints; `/JavaScript`: 11 at that rendering state |
| A downloaded local copy of the same public PDF | File URL automatically opened in the viewer; same navigation passed; user's custom full-page `d/u` mapping moved 1 → 2 → 1; hints visible; `/JavaScript`: 32 at that rendering state |
| PDF.js document search (`Cmd+F`) | 42 matches for JavaScript in the same document |

VimDF 0.6.1 was also enabled in the test environment and intercepted PDF URLs
first; disabling that competing reader resolved the routing conflict.
The CSP fix was verified against an actual console error blocking Vimium's
inline stylesheet, then by the appearance of hints and the search HUD.
No private documents, browser storage, profile data or personal screenshots are
included in this repository.

## Automated checks / 自动检查

```sh
python3 -m unittest discover -s pdf-viewer/mv3/tests -v
```

The test executes the **real patched upstream injector** under a minimal Node VM
browser API harness. It verifies local resource loading, denial feedback, and
rejection of version/build mismatch, missing/malformed script lists and unexpected
script origins. Packaging tests cover MV3 input, hint CSS, retained script CSP,
telemetry import removal and refusing to overwrite existing output.
These are protocol/package tests, not a substitute for browser interaction.

## Not yet verified / 尚未验证

- Other OSes/Chromium versions, Edge, Firefox or a different Vimium C build.
- Incognito, embedded PDFs, authenticated/POST-only downloads, expiring URLs.
- PDF presentation-mode scroll hooks and PDF-specific Vimium marks from the old
  custom fork; this build does **not** port those hooks or claim feature parity.
- Full-document search via `/`: intentionally unsupported by ordinary Vimium DOM
  search; use PDF.js `Cmd+F` / `Ctrl+F` instead.
- OCR for image-only PDFs; no OCR engine is added.
- Chrome Web Store acceptance or publication. Only upstream maintainers can
  decide whether/how to merge, publish or update the official listing.

中文：本记录区分已安装本地版的实机结果、公开构建代码的自动检查与未验证场景；
“构建成功”不等于商店已发布，也不等于所有 PDF 服务或旧版功能均兼容。
