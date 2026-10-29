import unittest
from .voice_pass import rewrite_line, rewrite_text

D = "—"


class Patterns(unittest.TestCase):
    def test_heading(self):
        self.assertEqual(rewrite_line(f"# 07 {D} Agents & MCP"), "# 07: Agents & MCP")

    def test_heading_with_link_keeps_url(self):
        self.assertEqual(rewrite_line(f"## [07 {D} Agents](07-agents.md)"), "## [07: Agents](07-agents.md)")

    def test_link_list_bullet(self):
        self.assertEqual(rewrite_line(f"- [a.md](a.md) {D} the setup script"), "- [a.md](a.md): the setup script")

    def test_bold_term_bullet(self):
        self.assertEqual(rewrite_line(f"- **HITL** {D} earn autonomy"), "- **HITL.** Earn autonomy")

    def test_placeholder(self):
        self.assertEqual(rewrite_line(f"- [NAME] {D} [role]"), "- [NAME]: [role]")

    def test_numbered_bullet(self):
        self.assertEqual(rewrite_line(f"2. HITL before autonomous {D} earn autonomy"), "2. HITL before autonomous: earn autonomy")

    def test_prose_and_double_dash_untouched(self):
        prose = f"Guess when data is available {D} ask for it."
        self.assertEqual(rewrite_line(prose), prose)
        self.assertEqual(rewrite_line(f"# A {D} B {D} C"), f"# A {D} B {D} C")


class Fences(unittest.TestCase):
    def test_fenced_lines_untouched_and_counts(self):
        text, counts = rewrite_text(f"# A {D} B\n```\n# C {D} D\n```\n")
        self.assertEqual(text, f"# A: B\n```\n# C {D} D\n```\n")
        self.assertEqual(counts["heading"], 1)


if __name__ == "__main__":
    unittest.main()
