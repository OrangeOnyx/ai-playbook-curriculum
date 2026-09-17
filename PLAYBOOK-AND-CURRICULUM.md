# The Playbook and the Curriculum: how the two fit together

**TL;DR.** The AI Playbook is what you build for a business: ten sections in four stages, each one interviewed out of you, tested, and used on real work before the next. The Curriculum is the same four stages for a person or a team who wants to build the tooling rather than operate it. Same stage numbers, deeper at each.

- The Playbook: [playbook.adamabdalla.com](https://playbook.adamabdalla.com)
- The Curriculum: this repository. Start at [README.md](README.md).

## One climb, two tracks

| Stage | The Playbook (what you build) | The Curriculum (what you learn) |
|---|---|---|
| 1 Starter | Choose one workflow, know me, learn my work. One real run, human-reviewed. | Use every top AI product well; your own prompts, rituals, and jargon. |
| 2 Intermediate | Know what is true, remember my world, capture and commit. | Build agents, RAG, MCP servers, evals; control cost. |
| 3 Expert | Know your limits, help me operate. A bounded operator inside enforced limits. | Ship to real users with SLOs; multi-agent systems; drift and incidents; lead an AI team; custom training; alignment and safety engineering. |
| 4 Frontier Operator | Automate the proven work, improve and survive. | Novel systems, research, open weights, foundation infrastructure. |

The Playbook's core rule is **do not automate chaos**: automation enters at Stage 4 only, and only inside the limits Stage 3 wrote down. The Curriculum starts where a serious learner needs help: not "how do I organize my business" but "how do I get genuinely good at this, and eventually build systems without shipping something that hurts someone."

## Where they hand off

The Playbook's section 3.2, Help me operate, is the bridge. It hands off to Curriculum Stage 2 the moment you want to build automation as software rather than configure it as a tool. Everything in the Curriculum from Stage 2 up assumes the Playbook's Stage 1 and 2 artifacts exist: an identity file, a source register, a memory the system keeps.

## Which one first

- Your files, identity, and knowledge are not yet in a shape AI can use: the Playbook, Stage 1.
- You already run a working system and want to build the tooling yourself: the Curriculum, Stage 2.
- You are a team lead deciding what to roll out: the Playbook's company lane, then the Curriculum's company track at the same stage.

## Lineage

Formerly "Groundwork and the Curriculum": Groundwork's six standing orders and the Curriculum's five levels were two numbering systems for one program. In September 2026 both were folded into the Playbook's four stages. The site's `/lineage/` page keeps the full mapping.
