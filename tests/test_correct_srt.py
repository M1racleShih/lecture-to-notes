import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "correct_srt.py"


class CorrectSrtCliTests(unittest.TestCase):
    def run_correction(self, source: Path, output: Path | None = None):
        glossary = source.parent / "glossary.json"
        glossary.write_text(json.dumps({"刻石": "刻蚀"}), encoding="utf-8")
        command = [sys.executable, str(SCRIPT), str(source), "-g", str(glossary)]
        if output is not None:
            command += ["-o", str(output)]
        return subprocess.run(command, capture_output=True, text=True, encoding="utf-8")

    def test_empty_or_non_srt_input_does_not_overwrite_files(self):
        for content in (b"", b"not an SRT transcript\n"):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "audio.srt"
                source.write_bytes(content)
                result = self.run_correction(source)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(source.read_bytes(), content)

    def test_tolerates_empty_whisper_cues_and_applies_glossary(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "audio.srt"
            content = (
                "1\n00:00:00,000 --> 00:00:01,000\n刻石工艺\n\n"
                "2\n00:00:01,500 --> 00:00:01,500\n\n"
                "3\n00:00:02,000 --> 00:00:03,000\n正常文本\n"
            )
            source.write_text(content, encoding="utf-8")
            result = self.run_correction(source)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = (
                "1\n00:00:00,000 --> 00:00:01,000\n刻蚀工艺\n\n"
                "3\n00:00:02,000 --> 00:00:03,000\n正常文本\n"
            )
            self.assertEqual(source.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
