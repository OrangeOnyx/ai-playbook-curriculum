import tempfile
import unittest
from pathlib import Path
from .fold_to_stages import (STAGE_OF_LEVEL, new_module_dir, new_file_path, rewrite_text, plan_moves)


class ModuleMapping(unittest.TestCase):
    def test_levels_map_to_stage_folders(self):
        self.assertEqual(STAGE_OF_LEVEL["level-1-essentials"], "1-starter")
        self.assertEqual(STAGE_OF_LEVEL["level-3-advanced"], "3-expert")
        self.assertEqual(STAGE_OF_LEVEL["level-4-professional"], "3-expert")
        self.assertEqual(STAGE_OF_LEVEL["level-5-frontier"], "4-frontier-operator")

    def test_advanced_modules_keep_their_numbers(self):
        self.assertEqual(new_module_dir("level-3-advanced/individual/01-shipping-to-production"),
                         "3-expert/individual/01-shipping-to-production")
        self.assertEqual(new_module_dir("level-3-advanced/company/10-continuous-learning-org"),
                         "3-expert/company/10-continuous-learning-org")

    def test_professional_modules_are_offset(self):
        self.assertEqual(new_module_dir("level-4-professional/individual/01-leading-ai-teams"),
                         "3-expert/individual/15-leading-ai-teams")
        self.assertEqual(new_module_dir("level-4-professional/individual/11-teaching-and-writing"),
                         "3-expert/individual/25-teaching-and-writing")
        self.assertEqual(new_module_dir("level-4-professional/company/01-applied-research-team"),
                         "3-expert/company/11-applied-research-team")
        self.assertEqual(new_module_dir("level-4-professional/company/08-partnership-strategy"),
                         "3-expert/company/18-partnership-strategy")

    def test_jargon_folders_lose_the_level_word(self):
        self.assertEqual(new_module_dir("level-2-intermediate/individual/12-jargon-level-2"),
                         "2-intermediate/individual/12-jargon-stage-2")
        self.assertEqual(new_module_dir("level-3-advanced/individual/14-jargon-level-3"),
                         "3-expert/individual/14-jargon-stage-3")
        self.assertEqual(new_module_dir("level-4-professional/individual/12-jargon-level-4"),
                         "3-expert/individual/26-jargon-stage-3-continued")
        self.assertEqual(new_module_dir("level-5-frontier/individual/10-jargon-level-5"),
                         "4-frontier-operator/individual/10-jargon-stage-4")

    def test_eli10_collision_and_history_files(self):
        self.assertEqual(new_file_path("level-4-professional/eli10/what-is-a-model-card-eli10.md"),
                         "3-expert/eli10/what-is-a-model-card-for-your-own-model-eli10.md")
        self.assertEqual(new_file_path("level-3-advanced/eli10/what-is-a-model-card-eli10.md"),
                         "3-expert/eli10/what-is-a-model-card-eli10.md")
        self.assertEqual(new_file_path("level-4-professional/README.md"),
                         "history/level-4-professional-README.md")
        self.assertEqual(new_file_path("LEVEL-MAP.md"), "STAGE-MAP.md")
        self.assertEqual(new_file_path("GROUNDWORK-AND-FLUENCY.md"), "PLAYBOOK-AND-CURRICULUM.md")
        self.assertEqual(new_file_path("LEVELS-4-5-COMPLETION-SUMMARY.md"),
                         "history/LEVELS-4-5-COMPLETION-SUMMARY.md")
        self.assertEqual(new_file_path("shared/graphics/hero-level-4.png"), "shared/graphics/stage-3.svg")
        self.assertEqual(new_file_path("level-1-essentials/individual/01-foundation/README.md"),
                         "1-starter/individual/01-foundation/README.md")


class MovePlanOrdering(unittest.TestCase):
    def test_whole_folder_move_precedes_rename_file_moves_into_its_stage(self):
        # A RENAME_FILE move that lands inside a stage directory (e.g. 3-expert/eli10/...)
        # must not run before the whole-folder move that creates that stage directory by
        # renaming a level directory (e.g. level-3-advanced -> 3-expert): mkdir-ing the
        # stage directory early makes `git mv level-3-advanced 3-expert` nest instead of
        # rename.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "level-3-advanced").mkdir()
            (root / "level-4-professional" / "eli10").mkdir(parents=True)
            (root / "level-4-professional" / "eli10" / "what-is-a-model-card-eli10.md").write_text("x")
            moves = plan_moves(root)
            whole_folder_idx = moves.index(("level-3-advanced", "3-expert"))
            model_card_idx = moves.index((
                "level-4-professional/eli10/what-is-a-model-card-eli10.md",
                "3-expert/eli10/what-is-a-model-card-for-your-own-model-eli10.md"))
            self.assertLess(whole_folder_idx, model_card_idx)


class TextRewrite(unittest.TestCase):
    PM = {"level-4-professional/individual/01-leading-ai-teams": "3-expert/individual/15-leading-ai-teams",
          "level-4-professional": "3-expert", "level-1-essentials": "1-starter",
          "level-3-advanced": "3-expert",
          "shared/graphics/hero-level-3.png": "shared/graphics/stage-3.svg"}

    def test_single_level_words(self):
        out, _ = rewrite_text("Level 1 exit criteria met. See Level 4 and Level 5.", self.PM, False)
        self.assertEqual(out, "Stage 1 exit criteria met. See Stage 3 and Stage 4.")

    def test_lowercase_level_prose_forms(self):
        out, _ = rewrite_text("legacy level-3+ module READMEs", self.PM, False)
        self.assertEqual(out, "legacy Stage 3 and up module READMEs")
        out, _ = rewrite_text("For each level-3 module README; see level-3-advanced/x", self.PM, False)
        self.assertEqual(out, "For each Stage 3 module README; see 3-expert/x")

    def test_ranges_before_singles(self):
        out, _ = rewrite_text("Any Level 1–3 concept; Levels 4-5 are ahead; Level 3+ buys you time.", self.PM, False)
        self.assertEqual(out, "Any Stages 1 to 3 concept; Stages 3 and 4 are ahead; Stage 3 and up buys you time.")
        out, _ = rewrite_text("Levels 1 and much of Level 2 need no code.", self.PM, False)
        self.assertEqual(out, "Stage 1 and much of Stage 2 need no code.")

    def test_paths_longest_first(self):
        out, _ = rewrite_text("[x](../../level-4-professional/individual/01-leading-ai-teams/README.md) and `level-1-essentials/00-start-here/`",
                              self.PM, False)
        self.assertEqual(out, "[x](../../3-expert/individual/15-leading-ai-teams/README.md) and `1-starter/00-start-here/`")

    def test_sibling_module_links_inside_level_4(self):
        out, _ = rewrite_text("see [teams](../01-leading-ai-teams/README.md)", self.PM, True)
        self.assertEqual(out, "see [teams](../15-leading-ai-teams/README.md)")
        out, _ = rewrite_text("see [teams](../01-leading-ai-teams/README.md)", self.PM, False)
        self.assertEqual(out, "see [teams](../01-leading-ai-teams/README.md)")

    def test_program_names_and_domain(self):
        out, hits = rewrite_text("The Groundwork Curriculum is part of Groundwork: https://groundwork.adamabdalla.com/guide/identity.html", self.PM, False)
        self.assertTrue(out.startswith("The AI Playbook Curriculum is part of "))
        self.assertIn("https://playbook.adamabdalla.com/1-starter/1-1-know-me/", out)
        self.assertEqual(hits, ["Groundwork"])

    def test_hero_image_and_alt(self):
        out, _ = rewrite_text("![Level 3](../shared/graphics/hero-level-3.png)", self.PM, False)
        self.assertEqual(out, "![Stage 3](../shared/graphics/stage-3.svg)")

    def test_five_levels_phrase(self):
        out, _ = rewrite_text("A five-level path. Five levels, two tracks.", self.PM, False)
        self.assertEqual(out, "A four-stage path. Four stages, two tracks.")


if __name__ == "__main__":
    unittest.main()
