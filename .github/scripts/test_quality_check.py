import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import quality_check as Q


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class Numbering(unittest.TestCase):
    def test_headings_folders_and_link_text_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a = _write(root, "1-starter/README.md", "# Stage 1 Starter\n\n## How to work Level 1\n")
            b = _write(root, "2-intermediate/individual/12-jargon-level-2/README.md", "# Glossary\n")
            c = _write(root, "notes.md", "See [Level 3 Systems Glossary](x.md).\nLevel 4 starts here.\n"
                                          "Layer 2 and Phase 1 of a rollout are ordinary prose and pass.\n## Order 4\n")
            v = Q.check_numbering([a, b, c], root)
        self.assertEqual(len([x for x in v if "heading" in x]), 2)     # "How to work Level 1", "Order 4"
        self.assertEqual(len([x for x in v if "folder" in x]), 1)
        self.assertEqual(len([x for x in v if "link text" in x]), 1)
        self.assertEqual(len([x for x in v if "prose" in x]), 1)       # only Level N counts in prose

    def test_provenance_and_history_are_exempt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a = _write(root, "3-expert/README.md", "# Stage 3 Expert\n\nFormerly Level 3 Advanced and Level 4 Professional.\n")
            b = _write(root, "history/LEVELS-4-5-COMPLETION-SUMMARY.md", "# Levels 4 and 5\n## Level 4\n")
            self.assertEqual(Q.check_numbering([a, b], root), [])

    def test_broken_link_inside_history_is_exempt(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            h = _write(root, "history/old.md", "[x](moved/away.md)\n")
            a = _write(root, "a.md", "[x](moved/away.md)\n")
            self.assertEqual(Q.check_links([h], root), [])
            self.assertEqual(len(Q.check_links([a], root)), 1)


class Domain(unittest.TestCase):
    def test_groundwork_links_fail_and_playbook_links_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a = _write(root, "a.md", "[x](https://groundwork.adamabdalla.com/guide/identity.html)\n")
            b = _write(root, "b.md", "[x](https://playbook.adamabdalla.com/1-starter/)\n")
            h = _write(root, "history/old.md", "https://groundwork.adamabdalla.com\n")
            v = Q.check_stale_domain([a, b, h], root)
        self.assertEqual(len(v), 1)
        self.assertIn("a.md", v[0])

    def test_playbook_domain_is_allowlisted_for_brand_scan(self):
        self.assertIsNotNone(Q.URL_ALLOWLIST_RE.search("https://playbook.adamabdalla.com/x"))


if __name__ == "__main__":
    unittest.main()
