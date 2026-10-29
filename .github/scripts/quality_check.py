#!/usr/bin/env python3
"""Quality checks for the AI Fluency Program repo.

Runs eight checks:
  1. Brand-name scan       [ WARN ] - no unapproved company/brand names
  2. Link check            [ FAIL ] - all relative Markdown links resolve
  3. Module coverage       [ WARN ] - files inside a module are linked from
                                     its README
  4. Old numbering         [ FAIL ] - no retired Level/Phase/Layer/Order/
                                     Interview numbering in headings, folder
                                     names, link text, or (Level N only) prose
  5. Stale domain          [ FAIL ] - no links into the retired Groundwork
                                     domain
  6. Em dashes             [ FAIL ] - no U+2014 outside fenced code blocks
  7. Banned words          [ FAIL ] - none of the words the Playbook site's
                                     build rejects (same regex)
  8. Percentage figures    [ WARN ] - count of N% figures in prose may not
                                     grow past PERCENT_BASELINE

Exit code is 0 unless a hard-fail check (link check, old numbering, stale
domain, em dashes, banned words, or percentages above baseline) finds
violations. Pass `--strict` to escalate warnings into hard failures.

Run from the repo root:
    python3 .github/scripts/quality_check.py
    python3 .github/scripts/quality_check.py --strict
    python3 .github/scripts/quality_check.py --all     # print every hit

The script is intentionally dependency-free (stdlib only).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Brand names that should not appear in program content. The list is
# case-sensitive; case-insensitive variants are handled by lowering.
BRAND_TERMS = [
    "Belle Realty",
    "Orange Ocean",
    "On The Blvd",
    "On The Boulevard",
    "OrangeOnyx",
    "Deal Leverage",
]
# Standalone OTB (word boundary) — separate to avoid false-positives inside
# other words.
BRAND_TERMS_STANDALONE = ["OTB"]

# Paths where brand references are acceptable (URLs to companion repos,
# the top-level cover-letter files, this quality-check script itself,
# LICENSE, CONTRIBUTING, and completion history docs).
ALLOWED_PATH_PREFIXES = [
    "shared/cover-letter/",
    ".github/scripts/quality_check.py",
    ".github/pre-commit-checklist.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "history/",
    "PLAYBOOK-AND-CURRICULUM.md",  # names Adam once, deliberately
]

# Directories to skip entirely
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".bak"}

# GitHub URL pattern that mentions OrangeOnyx (companion repo links) is
# always allowed no matter where it appears.
URL_ALLOWLIST_RE = re.compile(
    r"https?://[^\s\)]*(?:github\.com/OrangeOnyx|playbook\.adamabdalla\.com)[^\s\)]*",
    re.IGNORECASE,
)

# Voice gates. The banned-word regex is copied verbatim from the Playbook
# site's build gate (playbook-site/scripts/gates.py, BANNED) so the two
# repositories reject the same words. Keep them identical.
EM_DASH = "\u2014"
BANNED_RE = re.compile(
    r"\bleverage|\bseamless|\bempower|\bunlock\b|\brobust\b|actionable|data-driven|game-changer|synergy|circle back|best practices|dive into|at the end of the day|\bdelve|\belevate\b|testament",
    re.IGNORECASE,
)
PERCENT_RE = re.compile(r"\b\d{1,3}(?:\.\d+)?%")
# Percentage figures in prose are a ratchet, not a ban: the author's own
# thresholds stay as numbers, so the count may hold but never grow.
PERCENT_BASELINE = 46


def iter_markdown_files(root: Path):
    for p in root.rglob("*.md"):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if any(part.endswith(".bak") for part in rel.parts):
            continue
        yield p


def path_is_allowed(rel_path: str) -> bool:
    return any(rel_path.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES)


def check_brand_names(files, root: Path = REPO_ROOT) -> list[str]:
    """Return list of violations as human-readable strings."""
    violations = []
    for p in files:
        rel = str(p.relative_to(root)).replace("\\", "/")
        if path_is_allowed(rel):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        # Strip allow-listed URLs so mentions inside them don't trip us.
        stripped = URL_ALLOWLIST_RE.sub("", text)
        for term in BRAND_TERMS:
            if term in stripped:
                # Count and report first-hit line
                for lineno, line in enumerate(stripped.splitlines(), 1):
                    if term in line:
                        violations.append(f"{rel}:{lineno}: brand term '{term}'")
                        break
        for term in BRAND_TERMS_STANDALONE:
            # Word-boundary match
            for m in re.finditer(rf"\b{re.escape(term)}\b", stripped):
                lineno = stripped.count("\n", 0, m.start()) + 1
                violations.append(f"{rel}:{lineno}: standalone term '{term}'")
                break
    return violations


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

# Fence patterns to strip out before link-checking (so example code doesn't
# trip the checker with placeholder links).
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


def check_links(files, root: Path = REPO_ROOT) -> list[str]:
    """Verify relative Markdown links resolve to existing files.

    history/ is a frozen verbatim record whose links point at moved paths
    by design, so it is exempt.
    """
    violations = []
    for p in files:
        rel = str(p.relative_to(root)).replace("\\", "/")
        if rel.startswith(EXEMPT_PREFIXES):
            continue
        raw = p.read_text(encoding="utf-8", errors="replace")
        # Strip fenced code blocks and inline code before scanning for links,
        # so example markdown inside tutorials doesn't trigger false positives.
        text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", raw))
        for m in LINK_RE.finditer(text):
            target = m.group(1).split("#", 1)[0].strip()
            if not target:
                continue
            # Skip absolute URLs, mailto, anchors, and template placeholders
            if target.startswith(("http://", "https://", "mailto:", "#", "<", "{")):
                continue
            # Skip common template-placeholder targets used inside example
            # code blocks (URL, PATH, TARGET, etc. — all-caps single words)
            if re.fullmatch(r"[A-Z][A-Z_]*", target):
                continue
            # Resolve relative to the file's directory
            resolved = (p.parent / target).resolve()
            if not resolved.exists():
                lineno = text.count("\n", 0, m.start()) + 1
                violations.append(f"{rel}:{lineno}: broken link -> {target}")
    return violations


def check_module_coverage(root: Path) -> list[str]:
    """For each 'module' directory (contains README.md and >1 markdown files),
    every sibling *.md must be referenced from the README (by filename)."""
    violations = []
    for readme in root.rglob("README.md"):
        rel = str(readme.relative_to(root))
        if any(part in SKIP_DIRS for part in Path(rel).parts):
            continue
        module_dir = readme.parent
        peers = [
            p for p in module_dir.iterdir()
            if p.is_file() and p.suffix == ".md" and p.name != "README.md"
        ]
        if len(peers) == 0:
            continue
        readme_text = readme.read_text(encoding="utf-8", errors="replace")
        for peer in peers:
            if peer.name not in readme_text:
                violations.append(
                    f"{rel}: does not reference sibling '{peer.name}'"
                )
    return violations


# Headline positions (headings, folder names, link text) may carry none of the retired
# numbering words. Prose is gated only on the level words: "Phase 1 of a rollout" is
# ordinary lesson text, but "Level 4" can only be the retired numbering.
OLD_NUMBERING = re.compile(r"\b(?:Interview|Order|Layer|Phase|Level)s? [0-9]\b|\blevel-[1-5]\b")
PROSE_NUMBERING = re.compile(r"\bLevels? [1-5]\b|\blevel-[1-5]\b")
HEADING_RE = re.compile(r"^#{1,6} (.*)$")
EXEMPT_PREFIXES = ("history/",)
STALE_DOMAIN = "groundwork.adamabdalla.com"


def check_numbering(files, root: Path = REPO_ROOT) -> list[str]:
    """Four is the only headline number. A line starting with 'Formerly' is provenance
    and exempt; history/ is exempt by path. One violation per line at most."""
    violations = []
    for p in files:
        rel = str(p.relative_to(root)).replace("\\", "/")
        if rel.startswith(EXEMPT_PREFIXES):
            continue
        for part in Path(rel).parts[:-1]:
            if OLD_NUMBERING.search(part.replace("-", " ")) or re.search(r"level-[1-5]", part):
                violations.append(f"{rel}: folder name carries old numbering '{part}'")
                break
        text = p.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.startswith("Formerly"):
                continue
            hm = HEADING_RE.match(line)
            if hm:
                if OLD_NUMBERING.search(hm.group(1)):
                    violations.append(f"{rel}:{lineno}: heading carries old numbering")
                continue
            if any(OLD_NUMBERING.search(lm.group(1)) for lm in re.finditer(r"\[([^\]]+)\]\(", line)):
                violations.append(f"{rel}:{lineno}: link text carries old numbering")
                continue
            if PROSE_NUMBERING.search(line):
                violations.append(f"{rel}:{lineno}: prose carries old numbering")
    return violations


def check_stale_domain(files, root: Path = REPO_ROOT) -> list[str]:
    """A link into the retired Groundwork domain lands on a redirect; it is stale by definition."""
    violations = []
    for p in files:
        rel = str(p.relative_to(root)).replace("\\", "/")
        if rel.startswith(EXEMPT_PREFIXES):
            continue
        for lineno, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if STALE_DOMAIN in line:
                violations.append(f"{rel}:{lineno}: stale domain {STALE_DOMAIN}")
                break
    return violations


def strip_fences(text: str) -> str:
    """Blank every fenced code block, keeping its newlines so line numbers survive."""
    return FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def _prose_lines(p: Path):
    text = strip_fences(p.read_text(encoding="utf-8", errors="replace"))
    return enumerate(text.splitlines(), 1)


def check_em_dashes(files, root: Path = REPO_ROOT) -> list[str]:
    """No em dash (U+2014) anywhere outside a fenced code block."""
    violations = []
    for p in files:
        rel = str(p.relative_to(root)).replace("\\", "/")
        if rel.startswith(EXEMPT_PREFIXES):
            continue
        for lineno, line in _prose_lines(p):
            if EM_DASH in line:
                violations.append(f"{rel}:{lineno}: em dash")
    return violations


# Pasteable prompts under shared/starter-packs/ name the words they forbid;
# that is their job, so they are exempt from the banned-word gate only.
BANNED_WORDS_EXEMPT = EXEMPT_PREFIXES + ("shared/starter-packs/",)


def check_banned_words(files, root: Path = REPO_ROOT) -> list[str]:
    """None of the words the Playbook site's build rejects, one hit per match."""
    violations = []
    for p in files:
        rel = str(p.relative_to(root)).replace("\\", "/")
        if rel.startswith(BANNED_WORDS_EXEMPT):
            continue
        for lineno, line in _prose_lines(p):
            for m in BANNED_RE.finditer(line):
                violations.append(f"{rel}:{lineno}: banned word '{m.group(0)}'")
    return violations


def check_percentages(files, root: Path = REPO_ROOT) -> list[str]:
    """Count lines carrying an N% figure outside fences; tables count as prose."""
    violations = []
    for p in files:
        rel = str(p.relative_to(root)).replace("\\", "/")
        if rel.startswith(EXEMPT_PREFIXES):
            continue
        for lineno, line in _prose_lines(p):
            if PERCENT_RE.search(line):
                violations.append(f"{rel}:{lineno}: percentage figure")
    return violations


# Which categories are hard-fail vs advisory. Broken links, old numbering, and
# the stale domain block CI by default. Brand-name scrubs and module coverage
# are cleanup work that the repo carries; the report tells you what to fix,
# at your own pace.
HARD_FAIL_CATEGORIES = {"broken links", "old numbering", "stale domain", "em dashes", "banned words"}


def main() -> int:
    strict = "--strict" in sys.argv
    cap = None if "--all" in sys.argv else 50
    files = list(iter_markdown_files(REPO_ROOT))
    print(f"-> scanning {len(files)} markdown files under {REPO_ROOT}")
    if strict:
        print("-> strict mode: all warnings escalated to failures")

    all_violations: dict[str, list[str]] = {
        "brand names": check_brand_names(files),
        "broken links": check_links(files),
        "unreferenced files": check_module_coverage(REPO_ROOT),
        "old numbering": check_numbering(files),
        "stale domain": check_stale_domain(files),
        "em dashes": check_em_dashes(files),
        "banned words": check_banned_words(files),
        "percentage figures": check_percentages(files),
    }

    hard_fail = 0
    warn = 0
    print()
    for category, items in all_violations.items():
        if not items:
            print(f"PASS  {category}: 0")
            continue
        is_hard = strict or category in HARD_FAIL_CATEGORIES
        if category == "percentage figures" and len(items) > PERCENT_BASELINE:
            is_hard = True
        label = "FAIL " if is_hard else "WARN "
        if is_hard:
            hard_fail += len(items)
        else:
            warn += len(items)
        print(f"{label} {category}: {len(items)}")
        for item in items[:cap]:
            print(f"    {item}")
        if cap is not None and len(items) > cap:
            print(f"    ... and {len(items) - cap} more (rerun with --all to see them)")
        print()

    print(f"summary: {hard_fail} failure(s), {warn} warning(s)")
    return 1 if hard_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
