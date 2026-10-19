"""Exercise the actual patched upstream injector and the build/CSP boundary."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mv3_build", HERE.parent / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class BridgeTests(unittest.TestCase):
    def test_bridge_behavior(self):
        subprocess.run(["node", str(HERE / "bridge.cjs"), str(HERE.parent / "bridge.js")], check=True)

    def test_real_injector_handshake(self):
        with tempfile.TemporaryDirectory() as temporary:
            injector = Path(temporary) / "injector.js"
            injector.write_text(build.patched_injector())
            subprocess.run(["node", str(HERE / "handshake.cjs"), str(injector)], check=True)

    def test_package_keeps_script_csp_and_enables_hint_css(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "input"
            (pdf / "content/web").mkdir(parents=True)
            (pdf / "manifest.json").write_text(json.dumps({"manifest_version": 3,
                "content_security_policy": {"extension_pages": "script-src 'self' 'wasm-unsafe-eval'; object-src 'self'"}}))
            (pdf / "content/web/viewer.html").write_text(
                "<head><meta content=\"script-src 'self' 'wasm-unsafe-eval'; style-src 'self';\"></head>")
            (pdf / "background.js").write_text('importScripts("pdfHandler.js",\n  "telemetry.js");')
            output = root / "output"
            build.assemble(pdf, output)
            self.assertEqual((output / "vimium/INTEGRATION-LICENSE.txt").read_bytes(), (HERE.parents[2] / "LICENSE.txt").read_bytes())
            page = (output / "content/web/viewer.html").read_text()
            self.assertIn("style-src 'self' 'unsafe-inline';", page)
            self.assertIn("script-src 'self' 'wasm-unsafe-eval';", page)
            self.assertNotIn("script-src 'self' 'unsafe-inline'", page)
            self.assertIn('data-extension-id="hfjbmagddngcpeloejdejnfgbamkjaeg"', page)
            self.assertNotIn('"telemetry.js"', (output / "background.js").read_text())
            subprocess.run(["node", "--check", str(output / "vimium/bridge.js")], check=True)
            with self.assertRaises(FileExistsError):
                build.assemble(pdf, output)

    def test_reject_legacy_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary)
            (pdf / "manifest.json").write_text('{"manifest_version":2}')
            with self.assertRaisesRegex(ValueError, "Manifest V3"):
                build.assemble(pdf, pdf / "output")


if __name__ == "__main__":
    unittest.main()
