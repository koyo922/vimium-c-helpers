# Manifest V3 PDF viewer for Vimium C

[中文说明](README.zh-CN.md) · [Validation and limitations](VALIDATION.md)

This **unofficial, locally loadable compatibility build** restores Vimium C in a
modern PDF.js Chromium viewer. It uses the existing Vimium C extension's mappings
and backend for remote and local PDFs. It is a build recipe and reviewable bridge,
not a claim that the original Chrome Web Store listing has been updated.

## Why a new build path?

The older viewer linked by this repository uses Manifest V2, a persistent
background page and blocking webRequest APIs. Merely changing the manifest
number does not migrate those features. This recipe uses Mozilla's existing MV3
Chromium implementation and ports the Vimium integration instead.

MV3 also prevents executing another extension's scripts. The viewer therefore
packages a **fixed, checksum-verified Vimium C frontend snapshot** locally and
connects to the installed Vimium C backend using its external extension protocol.
The expected version/build must match before the frontend is loaded.

| Component | Pinned source |
|---|---|
| PDF.js | [v6.4.299](https://github.com/mozilla/pdf.js/releases/tag/v6.4.299), commit `d0991a0d53f3bb3a7307e3b83f279c1d117aafb3` |
| Vimium C frontend | Chrome Web Store 2.12.2, build `9e78033`, extension `hfjbmagddngcpeloejdejnfgbamkjaeg` |
| Integration | `build.py`, `bridge.js`, `tests/` in this directory |

## Build

Requires Python **3.12+**, Node.js **22** and npm. No browser profile or credentials
are read by the build. The work directory must be new and may consume several
hundred MB; the output directory must also be new.

```sh
python3 pdf-viewer/mv3/build.py \
  --work-dir /absolute/path/to/new-pdfjs-build-work \
  --output /absolute/path/to/pdf-viewer-mv3
python3 -m unittest discover -s pdf-viewer/mv3/tests -v
```

The script downloads the pinned PDF.js commit, runs `npm ci --ignore-scripts` and
its `gulp chromium` build, then adds the bridge. Keep the output directory while
installed; the temporary work directory can be removed after a successful build.
`BUILD_INFO.json` and `SHA256SUMS.json` record provenance and output checksums.
This pins source/dependencies, not a promise of byte-identical output across OSes
or Node/npm versions. PDF.js source archives have no Git history, so the internal
engine label can be `6.4.0`; `BUILD_INFO.json` identifies the actual source commit.

For integration-only iteration, use `--pdfjs-dir /path/to/pdfjs/build/chromium`
instead of `--work-dir`. The caller is responsible for supplying the pinned build.

## Install

1. Install/retain the Chrome Web Store version of Vimium C **2.12.2**.
2. In `chrome://extensions`, enable Developer mode and load the output directory
   with **Load unpacked**. Record the new viewer's extension ID.
3. In Vimium C options, append that ID under **Trusted external extensions**
   (受信任的其它扩展), then save. Keep the existing entries.
4. Enable **Allow access to file URLs** on the viewer for local PDFs.
5. If another PDF extension intercepts links first, disable that conflicting
   reader. Reopen the PDF from its original URL.

The extension ID depends on the unpacked installation path; do not copy another
person's ID. This recipe does not impersonate the original store extension or
install/update an extension automatically.

## Use

| Keys | Behavior |
|---|---|
| `j` / `k` | Scroll down/up; counts such as `20j` work |
| `gg` / `G` | Jump to the beginning/end |
| `f` | Show hints for links and viewer controls |
| `/` | Vimium search over **currently rendered text**, not necessarily the entire PDF |
| `Cmd+F` (macOS), `Ctrl+F` | PDF.js document search, including pages not yet rendered |

Existing Vimium mappings are inherited; `d`/`u` behavior follows the user's
configuration. The local validation used custom full-page mappings, not a change
to Vimium's default mappings.

## Permissions and boundaries

- PDF.js's MV3 permissions and host access are retained for PDF response
  recognition, redirects, document fetching and navigation. Local-file access
  requires the browser toggle above. These permissions have broad website access.
- Executable scripts remain packaged locally. Script CSP stays at upstream
  `self` + `wasm-unsafe-eval`; no remote-code/eval bypass is introduced.
- Only style CSP adds `unsafe-inline`, because Vimium generates hint/HUD styles.
- The upstream background telemetry module is not imported by this local build.
  No upload service is added; remote PDFs are requested from their origin.
- Version/build mismatch stops Vimium injection with a visible message; PDF
  viewing remains available. A Vimium C update requires a reviewed snapshot update.
- See [VALIDATION.md](VALIDATION.md) for tested and untested scenarios. This is
  **not full feature parity** with the old custom PDF.js fork.

## Maintenance and contribution

To refresh the Vimium frontend, obtain the official extension, copy **only** the
four files listed in `vendor/vimium-c/snapshot.json`, preserve its license and
update the version/build/checksums after reviewing the external protocol and
injector patch. Never copy browser settings, storage, cookies or a whole profile.
Run the tests and real-browser checks before shipping a new compatibility build.
The ~108 KB vendored JS snapshot is needed for MV3's local-script requirement;
the multi-megabyte generated PDF.js build is deliberately not checked into Git.

To remove the viewer, uninstall it in Chrome and remove its ID from Vimium C's
trusted-extension list. The original Vimium C extension and mappings stay intact.

## Licenses

The integration follows this repository's MIT license. PDF.js retains Apache-2.0.
The Vimium C snapshot includes its upstream Apache-2.0 / historical MIT notices in
[`vendor/vimium-c/LICENSE.txt`](vendor/vimium-c/LICENSE.txt); modified injector
output preserves that accompanying license. `snapshot.json` records original
file hashes. Changes to the injector are confined to the version/source guard and
local resource URL mapping in `build.py`.
