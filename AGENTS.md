# ui-redesign for any coding agent

This repository is a skill for redesigning existing products and their design systems.
Claude Code loads `SKILL.md` automatically. Other agents (Codex, Cursor, Gemini CLI,
Windsurf, Aider…) should read `SKILL.md` before any UI, redesign or design-system work.

The short version:

1. **New branch first.** Run `git status`.
   - If the tree is dirty, ask the user to commit or stash.
   - If it's clean, run `git switch -c redesign/<scope>` and tell the user their app stays untouched.
   - Never commit to or merge into their main branch.
2. **Capture before.** `python3 scripts/shots.py <url> <routes…> --out shots/before`.
3. **Audit.** `python3 scripts/audit.py <repo> --out redesign-audit.md --propose redesign-tokens.md`.
4. **Ask before merging** the design system when the verdict is CONSOLIDATE: give the numbers and the three options (merge / keep tokens / only named screens), then wait.
5. **Direction.** Write `DESIGN.md` with five decisions: feeling, type, colour, shape, depth.
6. **Tokens, then the eight layers**, one commit each: type, colour, shape & space, imagery, icons, components & states, data, depth & glass. Details are in `references/layers.md`.
7. **Verify on renders.** `python3 scripts/shots.py --compare shots/before shots/after-<layer> --out shots/compare`. Check contrast, focus, 44-pt targets, 360 and 1440 widths.
8. **Hand off.** Report the branch, one line per layer, what is left, and UX suggestions not built.

Design only: same routes, data, copy and behaviour. Big projects follow `references/large-projects.md`.
