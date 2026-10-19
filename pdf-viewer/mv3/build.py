#!/usr/bin/env python3
"""Build a Manifest V3 PDF.js viewer with a version-matched Vimium C bridge.

Requires Python >= 3.12, Node.js 22 and npm. Executable JavaScript is packaged
locally; this does not modify the user's installed Vimium C extension/profile.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

HERE = Path(__file__).resolve().parent
PDFJS_COMMIT = "d0991a0d53f3bb3a7307e3b83f279c1d117aafb3"  # v6.4.299
PDFJS_VERSION = "6.4.299"
VENDOR = HERE / "vendor" / "vimium-c"


def snapshot():
    lock = json.loads((VENDOR / "snapshot.json").read_text())
    for name, expected in lock["sha256"].items():
        actual = hashlib.sha256((VENDOR / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Vimium snapshot checksum mismatch: {name}")
    return lock


def patched_injector():
    lock = snapshot()
    script = (VENDOR / "lib/injector.js").read_text()
    # Keep the upstream injector/handshake. MV3 cannot execute a sibling
    # extension's scripts, so resolve only the audited snapshot's filenames.
    replacements = {
        "function n(t,n){": "function n(t,n){" + (
            'if(t&&(t.version!==VERSION||typeof t.h!=="string"||'
            '!t.h.endsWith(BUILD)||!Array.isArray(t.s)||t.s.length===0||'
            '!t.s.every(x=>typeof x==="string"&&'
            '/^chrome-extension:\\/\\/EXTID\\/content\\/'
            '(vimium-c|extend_click_vc|injected_end)\\.js$/.test(x))))'
            '{window.dispatchEvent(new Event("vimium-version-mismatch"));return;}'
        ).replace("VERSION", json.dumps(lock["version"]))
         .replace("BUILD", json.dumps(lock["build"]))
         .replace("EXTID", lock["extension_id"]),
        "for(let e of t.s){": (
            'for(let e of t.s){e=chrome.runtime.getURL("vimium/"+'
            'e.split("/").pop());'
        ),
    }
    for before, after in replacements.items():
        if script.count(before) != 1:
            raise ValueError("Upstream injector changed: re-audit the patch")
        script = script.replace(before, after)
    return script


def build_pdfjs(work):
    # Never reuse or delete caller-owned source trees.
    work.mkdir(parents=True, exist_ok=False)
    archive = work / "pdfjs.tar.gz"
    url = f"https://api.github.com/repos/mozilla/pdf.js/tarball/{PDFJS_COMMIT}"
    req = urllib.request.Request(url, headers={"User-Agent": "vimium-c-helpers-mv3"})
    with urllib.request.urlopen(req, timeout=60) as response, archive.open("wb") as dest:
        shutil.copyfileobj(response, dest)
    with tarfile.open(archive) as bundle:
        bundle.extractall(work, filter="data")
    sources = [p for p in work.iterdir() if p.is_dir()]
    if len(sources) != 1:
        raise ValueError("Expected one PDF.js source directory")
    source = sources[0]
    subprocess.run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=source, check=True)
    subprocess.run(["npx", "--no-install", "gulp", "chromium"], cwd=source, check=True)
    # A source archive has no Git history, so PDF.js labels it 6.4.0.
    # Preserve that generated engine label; record exact source provenance below.
    return source / "build/chromium"


def assemble(pdfjs, output):
    lock = snapshot()
    manifest = json.loads((pdfjs / "manifest.json").read_text())
    if manifest.get("manifest_version") != 3:
        raise ValueError("Expected a compiled PDF.js Manifest V3 Chromium build")
    if output.exists():
        raise FileExistsError("Output exists; choose a new directory (no automatic overwrite)")
    viewer_source = (pdfjs / "content/web/viewer.html").read_text()
    if "style-src 'self';" not in viewer_source or "</head>" not in viewer_source:
        raise ValueError("PDF.js viewer CSP/markup changed: re-audit integration")
    injector = patched_injector()
    shutil.copytree(pdfjs, output)
    manifest.update(
        name="PDF Viewer for Vimium C — MV3 Local",
        version="6.4.299.1",
        description="PDF.js viewer with Vimium C 2.12.2 shortcuts. Unofficial MV3 compatibility build.",
    )
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    vendor = output / "vimium"
    vendor.mkdir()
    for path in (VENDOR / "content").glob("*.js"):
        shutil.copy2(path, vendor / path.name)
    shutil.copy2(VENDOR / "LICENSE.txt", vendor / "LICENSE.txt")
    shutil.copy2(HERE / "bridge.js", vendor / "bridge.js")
    shutil.copy2(HERE.parents[1] / "LICENSE.txt", vendor / "INTEGRATION-LICENSE.txt")
    (vendor / "injector.js").write_text(injector)
    # Vimium's dynamic hint/HUD styles need inline CSS. The script policy is
    # intentionally unchanged: self + wasm-unsafe-eval (upstream PDF.js).
    viewer_source = viewer_source.replace("style-src 'self';", "style-src 'self' 'unsafe-inline';")
    viewer_source = viewer_source.replace("</head>",
        '<script src="../../vimium/bridge.js" defer></script>\n'
        '<script src="../../vimium/injector.js" '
        f'data-extension-id="{lock["extension_id"]}" defer></script>\n</head>')
    (output / "content/web/viewer.html").write_text(viewer_source)
    background = output / "background.js"
    source = background.read_text()
    if ',\n  "telemetry.js"' not in source:
        raise ValueError("PDF.js background changed: review telemetry integration")
    background.write_text(source.replace(',\n  "telemetry.js"', ''))
    (output / "BUILD_INFO.json").write_text(json.dumps({
        "pdfjs_source_version": PDFJS_VERSION, "pdfjs_source_commit": PDFJS_COMMIT,
        "vimium_version": lock["version"], "vimium_build": lock["build"],
        "unofficial": True,
    }, indent=2) + "\n")
    checksums = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "SHA256SUMS.json").write_text(json.dumps(checksums, indent=2) + "\n")
    print(f"Built {output}. Load this directory unpacked, then add its ID to Vimium C's trusted extensions.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--work-dir", type=Path, help="NEW temporary directory for downloading/building pinned PDF.js")
    group.add_argument("--pdfjs-dir", type=Path, help="Already compiled PDF.js Chromium directory (for local iteration)")
    parser.add_argument("--output", type=Path, required=True, help="NEW directory to install/retain")
    args = parser.parse_args()
    snapshot()  # Fail before network/build work if vendored inputs were altered.
    if args.output.exists():
        parser.error("--output must not already exist")
    pdfjs = args.pdfjs_dir or build_pdfjs(args.work_dir.resolve())
    assemble(pdfjs, args.output.resolve())


if __name__ == "__main__":
    main()
