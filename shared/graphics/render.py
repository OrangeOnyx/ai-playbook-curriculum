"""Regenerate the repository's plates from plates.py (the Playbook's plate library, vendored).
Run from the repository root: python shared/graphics/render.py"""
import io, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plates as P

STAGES = ["Starter", "Intermediate", "Expert", "Frontier Operator"]


def stage_plate(n):
    """A stage plate for the top of a stage README: emblem, number, name, the climb with this stage haloed."""
    ink, td, isoft = P.T["ink"], P.T["terra_deep"], P.T["ink_soft"]
    climb = P.climb_line(n, 720, labels=True, numerals=True).replace("<svg ", '<svg x="120" y="200" width="720" height="64" ', 1)
    emblem = P.stage_emblem(n, 120).replace("<svg ", '<svg x="120" y="40" ', 1)
    return (f'<svg viewBox="0 0 960 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stage {n} {STAGES[n-1]}.">'
            f'<rect width="960" height="300" fill="{P.T["paper"]}"/>{emblem}'
            + P._txt(280, 90, "THE AI PLAYBOOK CURRICULUM", 11, td, "start", 700, 2.5)
            + P._txt(280, 150, f"STAGE {n}", 40, ink, "start", 900, -1)
            + P._txt(280, 185, STAGES[n - 1].upper(), 22, isoft, "start", 800, 1)
            + climb + "</svg>")


def main():
    out = {"hero-cover.svg": P.cover_plate(), "stage-map.svg": P.climb_line(None, 720, labels=True, numerals=True)}
    for n in (1, 2, 3, 4):
        out[f"stage-{n}.svg"] = stage_plate(n)
    for name, svg in out.items():
        io.open(HERE / name, "w", encoding="utf-8", newline="\n").write(svg + "\n")
        print("wrote", name)


if __name__ == "__main__":
    main()
