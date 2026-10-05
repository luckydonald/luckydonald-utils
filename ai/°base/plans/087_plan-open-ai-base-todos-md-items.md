# Plan: open `ai/°base/todos.md` items

## Context

Four open todos live in `ai/°base/todos.md` (source: `sync_todo` MCP, calendar 7).
Three of them are about the prompt-time `@file` mention pipeline in `scripts/°base/ai/hooks/°reffiles_lib/`, and one is about the `code-style` skill not reliably loading for `/plan`.
Each todo is completed by ticking its box and calling `mcp__sync_todo__complete_todo(calendar_id=7, uid=<uid>)` once it is done and verified.

**Commit style:** `commit-with-lplp-style` is active for the implementation, because the origin is `luckydonald/base` (assumed `yes` per `ai/°base/AGENTS.md` "Plan mode", so no question was asked).
That means a plain new commit after each completed task, `scripts/tag_backup.py` on the prior HEAD, fold `ai:` auto-commits via interactive rebase, messages via `ai/git/pending-commit.md`, and never committing unrelated files (the untracked `ai/°base/errors/*`, `output/agents/*` and `scripts/°base/tests/aaa.py` stay untouched).
Commit format: `[base] topic: ai: Run: Short summary.`

Prose in this plan and in any Markdown changes follows `ai/skills/code-style/references/md.md` (break lines only at sentence ends).

## Where things live

- Wiring: `save-prompt/hook.py:1024` `main()` → `_lib.py:~742` `append_and_commit` → `reffiles_lib.process_referenced_files` (before logging) and `reffiles_lib.stage_and_commit_mentions` (after committing `query.md`).
- `°reffiles_lib/mentions.py`: `_AT_MENTION_RE` (line 7), `_TRAILING_PUNCT` (9), `split_candidates` (50-67), `line_mentions` (84, strips punctuation at ~89), `find_mentions` (109).
- `°reffiles_lib/commit.py`: `is_tracked` (20), `is_gitignored` (29), `resolve_existing` (55-82), `link_target`/`mention_link` (85/91), `process_referenced_files` (126-175), `stage_and_commit_mentions` (178-203).
- Tests: `scripts/°base/tests/test_ai_hooks_base_routing.py` (mentions unit tests ~2582, commit-module tests ~2735, end-to-end ~2351-2403).
- Run tests: `uv run --project scripts/°base python -m unittest discover -s scripts/°base/tests -v`.

## 1. Mention followed by `)` is not detected (`#base`, uid `66f35747…`)

Likely root cause, to confirm with a failing test first: `_AT_MENTION_RE = (?<!\S)@…` requires whitespace (or line start) before `@`, so `(@ai/somefile.txt)` never matches at all, regardless of trailing-punctuation handling.

- Add a failing test for `(@ai/somefile.txt)` in the mentions unit tests.
- Relax the lookbehind to also allow an opening bracket or quote before `@` (`(`, `[`, `{`, `"`, `'`), while still rejecting things like `user@host`.
- Implement the todo's "try combinations" idea for the tail: instead of stripping trailing punctuation unconditionally in `line_mentions`, generate candidates raw-first and stripped-second (e.g. `….txt)` then `….txt`) and let `resolve_existing` pick whichever exists on disk, so a real file named with trailing punctuation still wins.
- Keep the existing `#`/`:` fragment splitting in `split_candidates`, and make the combination order deterministic: fragment cuts and punctuation stripping are combined, most specific first.
- The rendered link must keep the leading `(` and trailing `)` outside the link text.

## 2. Auto-commit referenced files in more git states (`#base`, uid `b7a5299c…`)

Current behavior (`commit.py:178-203`): tracked → only `git add`; ignored → skip; otherwise add + `git commit --no-verify --only <path>`. No staged/clean check, silent failures.

Target behavior per unique mentioned relpath:

1. Skip if gitignored (`git check-ignore -q`), checked first so an ignored path is never staged or committed.
2. Skip if the path has no changes (tracked and clean against `HEAD`, via `git status --porcelain -- <path>`).
3. Otherwise (untracked, staged-new, staged-modified, or modified previously-committed) `git add -- <path>` then `git commit --no-verify --only -m … -- <path>`, so only the referenced file lands in the commit and any other staged files stay staged.
4. Skip committing (but still stage) while a merge, rebase or cherry-pick is in progress (`.git/MERGE_HEAD`, `rebase-merge`, `rebase-apply`, `CHERRY_PICK_HEAD`), since `--only` fails there.
5. Check return codes and log a short warning on failure instead of failing silently.

Refactor into one small helper returning the file's state, so the decision table is unit-testable.
Extend the end-to-end tests near line 2351: staged-new file, modified tracked file, clean tracked file (no commit), ignored file, tracked-but-ignored file, and mid-merge state.

## 3. Link `/skill` calls to `ai/skills/<slug>/SKILL.md` (uid `be604b2a…`)

- Add a `skill_mentions` finder in `mentions.py` (fence-aware like `find_mentions`) matching `/<slug>` tokens preceded by whitespace or line start, where `<slug>` matches `[a-z0-9][a-z0-9-]*` and `ai/skills/<slug>/SKILL.md` exists on disk (obviously the skill must exist, so `/plan`, `/compact` and paths like `/etc/hosts` never match).
- Reuse `link_target`/`mention_link` from `commit.py` to render `[/slug](./relative/path/to/ai/skills/slug/SKILL.md)` inline in `query.md`, consistent with how `@file` mentions render.
- Hook it into `process_referenced_files` so both mention kinds share one rewrite pass, without overlapping spans with `@` mentions.
- Linked skill files are not auto-committed (they are tracked canonical sources, not task files), so `stage_and_commit_mentions` must ignore skill mentions.
- Tests: existing skill linked, nonexistent slug left alone, skill inside a fenced block, skill mid-sentence, and a `/slug` that is part of a longer path.
- Side finding, verify separately before touching: `save-prompt/hook.py:~99` may be missing a comma after `"fix it"`, which would make `SKIP_PROMPTS` contain `"fix it/rename"`.

## 4. Code style not loading for `/plan` (uid `268ba6c5…`)

Findings: `/plan` is a built-in command, not a skill, and `ai/settings/settings.json` has no hook that injects `code-style`; today it relies on the model reading the skill description, and the `/plan` clause sits at the end of a long code-oriented description. `ai/°base/AGENTS.md` line 120 already tells the model to read `md.md` directly, but nothing enforces it.

- Use the official `anthropic-skills:skill-creator` skill (as the todo asks) to rework `ai/skills/code-style/SKILL.md`: move the plan trigger to the front of the description ("Use for any /plan or plan-file writing (always load `references/md.md`) and for writing, modifying or reviewing py/ts/vue/md code"), keep it concise, and trial its triggering with the skill-creator description-optimization flow.
- Add a deterministic backstop: a `UserPromptSubmit` hook (extend `save-command-decision/hook.py` or add a small sibling under `scripts/°base/ai/hooks/`) that, when the prompt starts with `/plan`, returns `additionalContext` instructing to read `ai/skills/code-style/references/md.md` before writing plan prose.
  Also try an `EnterPlanMode` `PostToolUse` matcher for the model-initiated case, and keep it only if Claude Code actually fires it (verify empirically).
- Register the hook in `ai/settings/settings.json`, then run `python3 scripts/°base/ai/settings/sync.py` so `.claude/settings.json` and `.codex/hooks.json` regenerate (never hand-edit generated files).
- Add a test for the hook output, and update `AGENTS.md` "Plan mode" to mention the hook.

## Order of work

1 → 3 → 2 → 4: items 1 and 3 touch `mentions.py` and share test scaffolding, 2 is isolated to `commit.py`, 4 is config plus skill text and benefits from the skill-creator eval loop at the end.

## Verification

- Run the full unittest suite (command above) after each item; each item starts with a failing test.
- Manual end-to-end in this repo: submit prompts containing `(@ai/°base/todos.md)`, a modified tracked file mention, a staged new file mention, and `/code-style` / `/nonexistent`; inspect `ai/°base/query.md` links and `git log` for the expected `ai:` commits.
- For item 4: start a fresh session, run `/plan`, and confirm `md.md` is read before the plan is written; run `sync.py --check` to confirm no drift.
- After each verified item, tick it in `ai/°base/todos.md` and call `complete_todo` with its uid.
