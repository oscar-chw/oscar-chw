"""Offline profile checks; these catch known regressions, not every factual error."""

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        self.targets.extend(
            value for key, value in attrs if key in {"src", "href"} and value
        )


def references(text):
    parser = References()
    parser.feed(text)
    return parser.targets + re.findall(r"\]\(([^)]+)\)", text)


def claim_errors(text):
    """Only exact withdrawn claim classes; no inference of truth from a clean scan."""
    rules = {
        "IMC participation is not a ranked-finisher denominator":
            r"904(?:th)?\s*(?:of|/|out of)\s*18,?803|top\s*(?:4\.81|5)\s*%",
        "Old harness score needs new evidence": r"\b39\s*/\s*45\b",
        "Replay ratio is not end-to-end platform speed":
            r"2\.3\d*\s*[×x].{0,70}end.to.end|end.to.end.{0,70}2\.3\d*\s*[×x]",
        "Private predecessor links are not showcase links":
            r"https://github\.com/(?:oscar-chw|hihihhi)/(?:asof-research|streaming-reconciliation)(?:[/)#\s]|$)",
    }
    return [
        reason for reason, pattern in rules.items() if re.search(pattern, text, re.I)
    ]


def missing_local_references(text, root):
    missing = []
    for target in references(text):
        parsed = urlsplit(target.strip("<>"))
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        if not (root / unquote(parsed.path)).is_file():
            missing.append(target)
    return missing


class Profile(unittest.TestCase):
    def setUp(self):
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_profile_has_no_known_withdrawn_claims(self):
        self.assertEqual(claim_errors(self.readme), [])

    def test_claim_checker_rejects_each_known_regression(self):
        for broken in (
            "904th of 18,803", "904 / 18803", "Top 4.81%", "top 5%",
            "Guard: 39/45", "2.30× faster end-to-end from Python",
            "end-to-end platform speed: 2.301816x",
            "[old](https://github.com/oscar-chw/asof-research)",
            "https://github.com/oscar-chw/streaming-reconciliation/",
        ):
            with self.subTest(broken=broken):
                self.assertTrue(claim_errors(broken))

    def test_claim_checker_accepts_scoped_counterexamples(self):
        for sound in (
            "904th globally, 18th in Hong Kong; 18,803 teams joined.",
            "2.30× through Python including conversion; loading excluded.",
            "The project does not establish end-to-end platform speed.",
            "12 readers, 5 writers in a synthetic concurrency fixture.",
            "https://github.com/oscar-chw/qts-platform-demo",
        ):
            with self.subTest(sound=sound):
                self.assertEqual(claim_errors(sound), [])

    def test_header_labels_the_fixture_and_calendar_period(self):
        header = self.readme.split("# Oscar Choi", 1)[0]
        self.assertIn("calendar month", header)
        self.assertIn("synthetic concurrency fixture", header)
        self.assertNotRegex(header, r"\b0 lost\b")

    def test_readme_local_references_resolve(self):
        self.assertEqual(missing_local_references(self.readme, ROOT), [])

    def test_missing_reference_is_detected_in_html_and_markdown(self):
        for text in ('<img src="assets/missing.png">', '[missing](missing.md#part)'):
            with self.subTest(text=text):
                self.assertEqual(len(missing_local_references(text, ROOT)), 1)

    def test_reference_parser_accepts_links_and_fragments(self):
        text = '<a href="https://example.com">link</a> [part](#part)'
        self.assertEqual(missing_local_references(text, ROOT), [])
        self.assertEqual(references(text), ["https://example.com", "#part"])

    def test_header_is_svg_and_portrait_is_gif(self):
        self.assertEqual(ET.parse(ROOT / "assets/header.svg").getroot().tag,
                         "{http://www.w3.org/2000/svg}svg")
        self.assertIn((ROOT / "assets/fourier_portrait.gif").read_bytes()[:6],
                      (b"GIF87a", b"GIF89a"))

    def test_proposed_settings_are_complete_and_have_no_withdrawn_claims(self):
        settings = json.loads((ROOT / "profile-settings.json").read_text())
        self.assertEqual(urlsplit(settings["website"]).scheme, "https")
        self.assertTrue(1 <= len(settings["pins"]) <= 6)
        self.assertEqual(len(settings["pins"]), len(set(settings["pins"])))
        self.assertTrue(settings["repositories"])
        for repo in settings["pins"]:
            self.assertIn(repo, settings["repositories"])
        for repo, fields in settings["repositories"].items():
            with self.subTest(repo=repo):
                self.assertRegex(repo, r"^oscar-chw/[A-Za-z0-9_.-]+$")
                self.assertTrue(0 < len(fields["description"]) <= 350)
                self.assertEqual(claim_errors(fields["description"]), [])
                self.assertTrue(3 <= len(fields["topics"]) <= 20)
                for topic in fields["topics"]:
                    self.assertRegex(topic, r"^[a-z0-9][a-z0-9-]{0,49}$")


if __name__ == "__main__":
    unittest.main()
