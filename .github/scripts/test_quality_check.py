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

    def test_raw_github_bootstrap_url_is_allowlisted_for_brand_scan(self):
        self.assertIsNotNone(Q.URL_ALLOWLIST_RE.search("https://raw.githubusercontent.com/OrangeOnyx/x/master/y.sh"))

    def test_companion_repo_link_text_is_allowlisted_for_brand_scan(self):
        self.assertIsNotNone(Q.URL_ALLOWLIST_RE.search("[`OrangeOnyx/lease-abstractor`](https://github.com/OrangeOnyx/lease-abstractor)"))
        self.assertIsNone(Q.URL_ALLOWLIST_RE.search("built by OrangeOnyx for"))

    def test_brand_scan_allowlist_matches_windows_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = _write(root, "history/x.md", "Orange Ocean\n")
            self.assertEqual(Q.check_brand_names([p], root), [])



class Voice(unittest.TestCase):
    def test_strip_fences_keeps_line_numbers(self):
        t = "a\n```\nx — y\n50%\n```\nb — c\n"
        s = Q.strip_fences(t)
        self.assertEqual(s.count("\n"), t.count("\n"))
        self.assertNotIn("x — y", s)
        self.assertIn("b — c", s)

    def test_em_dash_flagged_outside_fences_and_inside_inline_code(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a = _write(root, "a.md", "plain — dash\n```\nfenced — dash\n```\n`inline — dash`\nen – dash\n")
            h = _write(root, "history/x.md", "old — dash\n")
            v = Q.check_em_dashes([a, h], root)
        self.assertEqual([x.split(":")[1] for x in v], ["1", "5"])

    def test_banned_words_use_site_regex(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a = _write(root, "a.md", "We leverage this.\nA robust plan.\nrobustness is fine\nunlocking is fine\nBest Practices\n")
            v = Q.check_banned_words([a], root)
        self.assertEqual(len(v), 3)
        self.assertIn("banned word 'leverage'", v[0])

    def test_starter_pack_prompts_may_name_the_words_they_forbid(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a = _write(root, "shared/starter-packs/x/README.md", "Never say leverage.\n")
            b = _write(root, "shared/cover-letter/x.md", "We leverage it.\n")
            self.assertEqual(Q.check_banned_words([a], root), [])
            self.assertEqual(len(Q.check_banned_words([b], root)), 1)

    def test_percentages_counted_in_prose_and_tables_not_fences(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a = _write(root, "a.md", "Save 50% here.\n| cell | 95% |\n```\n100%\n```\n")
            v = Q.check_percentages([a], root)
        self.assertEqual(len(v), 2)


if __name__ == "__main__":
    unittest.main()
