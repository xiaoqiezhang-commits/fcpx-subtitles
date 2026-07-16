import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_fcpxml.py"
VALIDATE = ROOT / "scripts" / "validate_fcpxml.py"


def run(*args):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )


class SkillContractTests(unittest.TestCase):
    def test_skill_requires_project_preflight_and_fixed_editorial_rules(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for required in (
            "font family",
            "font size",
            "frame size",
            "frame rate",
            "one line",
            "separate Chinese and English",
            "actual audio",
            "reference script",
            "apostrophes",
            "adjacent repetition",
        ):
            self.assertIn(required, text)


class GeneratorTests(unittest.TestCase):
    def make_valid_input(self, folder):
        path = Path(folder) / "segments.tsv"
        path.write_text(
            "start|end|en|zh\n"
            "00:00:00.000|00:00:02.000|We listen to our customers|我们倾听用户的声音\n"
            "00:00:02.000|00:00:04.520|That's why the product keeps improving|这就是产品不断进步的原因\n",
            encoding="utf-8",
        )
        return path

    def build_valid(self, folder):
        source = self.make_valid_input(folder)
        result = run(
            BUILD,
            "--input", source,
            "--output-dir", folder,
            "--name", "Interview",
            "--width", "1920",
            "--height", "1080",
            "--fps", "25",
            "--font-family", "PingFang SC",
            "--font-face", "Regular",
            "--font-size", "54",
            "--languages", "zh,en",
            "--position-zh", "0 -410",
            "--position-en", "0 -410",
            "--adjust-en", "0 -8.5",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(folder) / "Interview-中文.fcpxml", Path(folder) / "Interview-English.fcpxml"

    def test_generates_separate_single_line_bilingual_fcpxml(self):
        with tempfile.TemporaryDirectory() as folder:
            zh, en = self.build_valid(folder)
            self.assertTrue(zh.exists())
            self.assertTrue(en.exists())
            zh_root = ET.parse(zh).getroot()
            en_root = ET.parse(en).getroot()
            for root in (zh_root, en_root):
                self.assertEqual(root.tag, "fcpxml")
                titles = root.findall(".//title")
                self.assertEqual(len(titles), 2)
                self.assertTrue(all("\n" not in (t.findtext("text/text-style") or "") for t in titles))
            zh_times = [(t.get("offset"), t.get("duration")) for t in zh_root.findall(".//title")]
            en_times = [(t.get("offset"), t.get("duration")) for t in en_root.findall(".//title")]
            self.assertEqual(zh_times, en_times)
            self.assertEqual(en_root.find(".//title/adjust-transform").get("position"), "0 -8.5")
            self.assertIsNone(zh_root.find(".//title/adjust-transform"))

    def test_rejects_multiline_cards(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "bad.tsv"
            source.write_text(
                'start|end|en|zh\n00:00:00.000|00:00:02.000|First line\\nSecond line|第一行\n',
                encoding="utf-8",
            )
            result = run(
                BUILD, "--input", source, "--output-dir", folder, "--name", "Bad",
                "--width", "1920", "--height", "1080", "--fps", "25",
                "--font-family", "PingFang SC", "--font-face", "Regular",
                "--font-size", "54", "--languages", "zh,en",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("one line", result.stderr)

    def test_validator_detects_adjacent_repeated_prefix(self):
        with tempfile.TemporaryDirectory() as folder:
            zh, en = self.build_valid(folder)
            tree = ET.parse(en)
            cards = tree.getroot().findall(".//title/text/text-style")
            cards[0].text = "In the final review"
            cards[1].text = "In the final review we found a different result"
            tree.write(en, encoding="utf-8", xml_declaration=True)
            result = run(VALIDATE, "--zh", zh, "--en", en)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("adjacent repetition", result.stderr)

    def test_validator_passes_valid_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            zh, en = self.build_valid(folder)
            result = run(
                VALIDATE, "--zh", zh, "--en", en,
                "--width", "1920", "--height", "1080", "--fps", "25",
                "--font-family", "PingFang SC", "--font-face", "Regular", "--font-size", "54",
                "--position-zh", "0 -410", "--position-en", "0 -410",
                "--adjust-en", "0 -8.5",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
