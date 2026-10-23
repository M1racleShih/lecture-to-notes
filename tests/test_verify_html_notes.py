import contextlib
import io
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from scripts.verify_html_notes import verify

ROOT = Path(__file__).resolve().parents[1]

def png(width=1, height=1):
    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xffffffff)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    data = zlib.compress((b"\x00" + b"\xff\xff\xff" * width) * height)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", data) + chunk(b"IEND", b"")

class HTMLGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        profile = dict(mode="conceptual-talk", audience="first reader",
                       central_question="What changes?", reader_outcome="Explain the mechanism",
                       visual_teaching_atoms=0, formula_teaching_atoms=0)
        for name, value in {
            "metadata.json": {"duration": 600},
            "lecture_profile.json": profile,
            "bands.json": {"height": 720, "crop_bottom": 0},
            "layout.json": {"width": 1280, "height": 720, "composite": False, "panels": []},
        }.items():
            (self.root / name).write_text(json.dumps(value))
        (self.root / "cover.jpg").write_bytes(png())
        for name in ("audio.srt", "audio_corrected.srt"):
            (self.root / name).write_text("1\n00:00:00,000 --> 00:00:10,000\n教学内容\n")
        (self.root / "figure_manifest.tsv").write_text("figure\tframe\tstart\tend\ttopic\tpanel\n")
        (self.root / "figure_verification.txt").write_text("Synthetic spoken-lecture fixture: no source figures.\n")
        (self.root / "browser_verification.txt").write_text("Unit-test fixture only; browser behavior is tested separately.\n")
        (self.root / "teaching_atoms.tsv").write_text("atom\tstatus\tevidence\n机制\tok\t#mechanism\n")
        (self.root / "numerical_claims.tsv").write_text("claim\tvalue\tsource_time\tin_notes\n")
        self.prose = "讲义解释变化的前提并保留证据，读者可以核对适用条件。" * 150
        self.write()

    def write(self, extra="", head=""):
        (self.root / "notes.html").write_text(
            '<!doctype html><html lang="zh"><head><title>Lecture</title>'+head+
            '</head><body><h1>讲义</h1><img class="cover" src="cover.jpg" alt="原封面">'
            '<main><h2 id="mechanism">为什么发生变化</h2><p>'+self.prose+'</p>'+extra+
            '</main></body></html>', encoding="utf-8")

    def gate(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            report = verify(self.root, **kwargs)
        return report.ok, output.getvalue()

    def claim(self, value="40%"):
        (self.root / "numerical_claims.tsv").write_text(
            "claim\tvalue\tsource_time\tin_notes\n降幅\t"+value+"\t00:02\t\n")

    def test_html_does_not_require_tex_or_pdf(self):
        ok, log = self.gate()
        self.assertTrue(ok, log)
        self.assertFalse((self.root / "notes.tex").exists())
        self.assertIn("OVERALL PASS", log)

    def test_claim_is_checked_against_article_and_written(self):
        self.claim()
        self.write("<p>视频报告占比降低 40%。</p>")
        ok, log = self.gate(write_claims=True)
        self.assertTrue(ok, log)
        self.assertIn("\tyes\n", (self.root / "numerical_claims.tsv").read_text())

    def test_css_scripts_templates_and_hidden_text_cannot_discharge_a_claim(self):
        self.claim()
        for fragment in (
            "<script>const count=40;</script>",
            "<style>p{width:40px}</style>",
            "<template><p>40%</p></template>",
            "<p hidden>40%</p>",
            '<div aria-hidden="true"><p>40%</p></div>',
            '<div style="display:none"><p>40%</p></div>',
        ):
            with self.subTest(fragment=fragment):
                self.write(fragment)
                ok, log = self.gate()
                self.assertFalse(ok)
                self.assertIn("FAIL all numerical claims", log)

    def test_hidden_padding_cannot_pass_density(self):
        self.prose = "正文"
        self.write("<template>"+"讲"*4000+"</template><div hidden>"+"讲"*4000+"</div>")
        ok, log = self.gate()
        self.assertFalse(ok)
        self.assertIn("FAIL source-fit density", log)

    def test_missing_or_network_asset_is_rejected(self):
        for resource in ('<img src="missing.png" alt="图">', '<script src="https://example.com/runtime.js"></script>'):
            self.write(resource)
            ok, log = self.gate()
            self.assertFalse(ok)
            self.assertIn("FAIL referenced image/style/script assets", log)

    def test_traversal_asset_is_rejected(self):
        self.write('<img src="../outside.png" alt="图">')
        ok, log = self.gate()
        self.assertFalse(ok)
        self.assertIn("FAIL referenced", log)

    def test_duplicate_ids_and_missing_anchors_fail(self):
        self.write('<h3 id="mechanism">重复</h3><a href="#missing">跳转</a>')
        ok, log = self.gate()
        self.assertFalse(ok)
        self.assertIn("FAIL unique", log)
        self.assertIn("FAIL source links", log)

    def test_caption_must_match_manifest_time_and_link(self):
        figures = self.root / "figures"
        figures.mkdir()
        (figures / "example.png").write_bytes(png(1280, 720))
        (self.root / "figure_manifest.tsv").write_text(
            "figure\tframe\tstart\tend\ttopic\tpanel\n"
            "example.png\tframes/one.png\t00:02:15\t00:02:20\t机制\tmain\n")
        valid = ('<figure data-source-start="00:02:15" data-source-end="00:02:20">'
                 '<img src="figures/example.png" alt="机制图"><figcaption>机制 '
                 '<a href="https://example.com/video?t=135">02:15–02:20</a></figcaption></figure>')
        self.write(valid)
        ok, log = self.gate()
        self.assertTrue(ok, log)
        self.write(valid.replace("02:15–02:20", "02:15–02:21"))
        ok, log = self.gate()
        self.assertFalse(ok)
        self.assertIn("FAIL example.png visible caption", log)

    def test_installed_html_assets_and_imports_work_without_tex(self):
        with tempfile.TemporaryDirectory() as target:
            subprocess.run(["bash", str(ROOT / "scripts/install_skill.sh"), target], check=True, capture_output=True)
            installed = Path(target) / "lecture-to-notes"
            self.assertTrue((installed / "assets/notes-template.html").is_file())
            self.assertTrue((installed / "references/html-lectures.md").is_file())
            result = subprocess.run([sys.executable, str(installed / "assets/verify_html_notes.py"), "--help"],
                                    cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--write-claims", result.stdout)

if __name__ == "__main__":
    unittest.main()
