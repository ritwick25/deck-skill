# /deck commands: draft for SKILL.md (ruling 23)

Input for the docs agent. Section 1 is the frontmatter, section 2 goes at the very top of the SKILL.md body,
section 3 is how Claude Code delivers the arguments (verified 2026-10-03 against code.claude.com/docs/en/skills).

## 1. Frontmatter

```yaml
---
name: deck
description: House deck builder. Use whenever a message contains /deck anywhere, or asks to plan, build, extend, restyle, review or fix a slide, deck, pptx, proposal, RFP or RFI response, POV, pitch, capability or credentials deck, roadmap, chart, or architecture or technical diagram, including before any project folder exists. Once loaded, every later deck iteration in the session goes through it, one slide or one edit included. Picks a storyline and one archetype per slide from 45 measured archetypes, builds natively in python-pptx with the house kit, asks for the client's colours, logo and font when a client deck has none, gates every deck against the house rules and renders and reads every slide. Not for Word, Excel or PDF documents.
when_to_use: The user types /deck with or without a mode word (new, slide, edit, review, diagram, chart, brand), names a deck or slide to change, or asks for one more slide or one more change after the skill was used earlier in the session.
argument-hint: "[new|slide|edit|review|diagram|chart|brand] [brief, path or change]"
---
```

- `description` is 734 characters, under the 1,024 that selftest holds (the Agent Skills limit). Claude Code caps
  `description` plus `when_to_use` at 1,536 in the skill listing, and together they are 961.
- No square or angle brackets in `description` (selftest refuses angle brackets). `argument-hint` is quoted YAML.
- Do not declare `arguments:`. A declared name such as `mode` would turn every `$mode` in the body into an argument,
  and the body already uses `$PY` and `$K`. Those two are safe: only `$ARGUMENTS`, `$0` to `$9` style indexes and
  declared names are substituted.
- Leave `disable-model-invocation` unset (false). The mid-prompt route below depends on Claude invoking the skill.
- Optional: `allowed-tools: Bash(/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 *)` pre-approves the
  pinned interpreter for the invoking turn only (the grant clears on the next user message).

## 2. Top of the SKILL.md body

```markdown
Request: $ARGUMENTS

## Commands

| Command | Does | Asks for, when missing |
|---|---|---|
| `/deck new <brief>` | Plans and builds a deck: restate, storyline, ghost deck, build, gates, read every slide | audience and the decision the deck must win, and for a client deck the brand (see `/deck brand`) |
| `/deck slide <what> [--deck path]` | Adds or rebuilds one slide: archetype, build in the deck's `build.py`, gates, read it | which deck, when more than one is in reach, and the claim the slide makes |
| `/deck edit <path> <change>` | Changes only what was pointed at, rebuilds, re-gates, re-reads. A deletion sweeps the whole deck | the slide, when the change could land on more than one |
| `/deck review <path>` | Runs the gates, reads every slide, reports. Changes nothing | the path, when the folder holds more than one deck |
| `/deck diagram <type> <subject>` | Architecture or technical diagram from the diagram engine (aws, azure or house grammar, L0 or deep dive) | the stack and cloud, and which components are in scope |
| `/deck chart <what>` | A native chart slide from supplied data, under the dataviz rules | the numbers and their source. Never invents a figure |
| `/deck brand <client>` | Client theme and logo lockup from `scripts/brand.py`, contrast-solved, identity colours kept | brand colours (hex, or a site to read the CSS from), logo file, font |
| `/deck` | Picks the mode from context: a path plus a change is edit, a brief is new, a deck alone is review | what the user wants, when context does not decide |

- `/deck` may sit anywhere in a longer prompt. The whole message is the brief, and the word after `/deck` picks the mode.
- Once loaded, the skill governs the session. Every later deck iteration, one slide or one word, follows this file
  (build, gates, read the changed slides) without the user typing `/deck` again.
- A client deck with no colour system or logo given stops at intake: ask for the brand colours, the logo file and
  the font, then run `brand.py`. The house theme is used for a client deck only when the user says so.
- After a context compaction, invoke the skill again before the next change.
```

`Request: $ARGUMENTS` is the first line so the mode word and the brief land where the procedure reads them. With
no arguments it expands to an empty string and the request is the user's message.

## 3. How Claude Code delivers /deck (verified 2026-10-03)

| Where `/deck` is typed | What happens |
|---|---|
| Start of the message | Claude Code expands the skill and passes the rest of the message as the argument string. `$ARGUMENTS` receives it whole, and `$0`, `$1` take shell-quoted words. Without a placeholder in the body, Claude Code appends `ARGUMENTS: <text>` to the skill content. |
| Stacked at the start, `/deck /other ...` | Up to six skills expand and each receives the trailing text. |
| Middle or end of the message | Claude Code does not expand it. Claude reads `/deck` as a request to load the skill (the Skill tool's own instructions say so) and invokes it, passing the request as `args`. The description's "a message contains /deck anywhere" makes this reliable. |
| Later turns | The rendered SKILL.md stays in the conversation and is not re-read. After auto-compaction Claude Code re-attaches only the first 5,000 tokens of each invoked skill, within a 25,000-token budget across skills. |

Consequences for SKILL.md:
- The commands table and the standing rules belong in the first 5,000 tokens, which is why they open the body.
  SKILL.md is about 5,000 tokens today, so anything placed last is the first to be cut.
- `${CLAUDE_SKILL_DIR}` is substituted in the body. `K=${CLAUDE_SKILL_DIR}` in the setup block would keep the commands
  right if the skill is ever installed somewhere other than `~/.claude/skills/deck`.

Sources: code.claude.com/docs/en/skills (frontmatter reference, "Pass arguments to skills", "Skill content
lifecycle").
