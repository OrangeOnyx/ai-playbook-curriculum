#!/usr/bin/env python3
"""Structural em-dash pass.

Rewrites the em dashes that carry no judgment: the separator in a heading,
a link-list bullet, a bold-term bullet, a placeholder line, or a numbered
bullet becomes a colon or a period. Prose em dashes are left alone for a
reader to reword. Fenced code blocks are never touched. Idempotent.

Run from the repo root:
    python scripts/voice_pass.py
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".github" / "scripts"))
import quality_check as Q  # noqa: E402

EM = "—"
SEP = rf"\s+{EM}\s+"

# Order matters: the first pattern that matches wins.
PATTERNS: list[tuple[str, re.Pattern, object]] = [
    ("heading",   re.compile(rf"^(#+ .*?){SEP}(.*)$"),                      lambda m: f"{m.group(1)}: {m.group(2)}"),
    ("link-list", re.compile(rf"^(\s*[-*] \[[^\]]+\]\([^)]+\)){SEP}(.*)$"), lambda m: f"{m.group(1)}: {m.group(2)}"),
    ("bold-term", re.compile(rf"^(\s*[-*] \*\*[^*]+\*\*){SEP}(\w)(.*)$"),   lambda m: f"{m.group(1)[:-2]}.** {m.group(2).upper()}{m.group(3)}"),
    ("placeholder", re.compile(rf"^(\s*[-*] \[[A-Z _/]+\]){SEP}(.*)$"),      lambda m: f"{m.group(1)}: {m.group(2)}"),
    ("numbered",  re.compile(rf"^(\s*\d+\. .*?){SEP}(.*)$"),                lambda m: f"{m.group(1)}: {m.group(2)}"),
]


def rewrite_line(line: str) -> str:
    """Return the line with its one structural em dash rewritten, or the line unchanged."""
    if line.count(EM) != 1:
        return line
    for _name, rx, repl in PATTERNS:
        m = rx.match(line)
        if m:
            return repl(m)
    return line


def rewrite_text(text: str) -> tuple[str, dict[str, int]]:
    """Apply rewrite_line outside fences; return the new text and counts per pattern."""
    counts = {name: 0 for name, _, _ in PATTERNS}
    out = []
    in_fence = False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or line.count(EM) != 1:
            out.append(line)
            continue
        new = line
        for name, rx, repl in PATTERNS:
            m = rx.match(line)
            if m:
                new = repl(m)
                counts[name] += 1
                break
        out.append(new)
    return "\n".join(out), counts


def main() -> int:
    root = Q.REPO_ROOT
    totals = {name: 0 for name, _, _ in PATTERNS}
    changed = 0
    for p in Q.iter_markdown_files(root):
        rel = str(p.relative_to(root)).replace("\\", "/")
        if rel.startswith(Q.EXEMPT_PREFIXES):
            continue
        text = p.read_text(encoding="utf-8")
        new, counts = rewrite_text(text)
        if new != text:
            io.open(p, "w", encoding="utf-8", newline="\n").write(new)
            changed += 1
            for k, v in counts.items():
                totals[k] += v
    for k, v in totals.items():
        print(f"{k:12} {v}")
    print(f"files changed {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
