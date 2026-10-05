# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A reusable git base that consuming projects adopt via checkout, rebase, or merge from `base/base`. Its files — scripts, hooks, AI settings — live in consuming repos like normal files. Everything base-specific is namespaced under `°base` so it never collides with consuming-repo code.

## Commands

Run all tests (from repo root):
```bash
uv run --project scripts/°base python -m unittest discover -s scripts/°base/tests -v
```

Run a single test module:
```bash
uv run --project scripts/°base python -m unittest ai.scripts.tests.test_<name> -v
```

Sync AI tool settings (Claude ↔ Codex) and skills:
```bash
python3 scripts/°base/ai/settings/sync.py
```

Check sync without writing (used by pre-commit):
```bash
python3 scripts/°base/ai/settings/sync.py --check
```

## Architecture

### Directory layout

| Path | Purpose |
|---|---|
| `scripts/°base/` | All helpers; `°base` namespace keeps them from colliding |
| `ai/°base/` | AI artifacts for the base repo itself (queries, plans, memory) |
| `ai/skills/*/SKILL.md` | Canonical skill source; `sync.py` distributes wrappers |
| `ai/settings/settings.json` | Tracked, tool-neutral settings (Claude + Codex share this) |
| `ai/settings/settings.local.json` | Machine-local settings overlay (gitignored) |
| `ai/settings/settings.schema.json` | JSON Schema for tracked neutral settings |
| `ai/settings/settings-local.schema.json` | JSON Schema for machine-local neutral settings; forbids shared-only policy keys |
| `.claude/settings.json` | Generated from `ai/settings/`; do not edit directly |
| `.claude/hooks/permission-check.py` | PermissionRequest hook — enforces git commit policy |
| `.codex/rules/generated.rules` | Generated Codex command allowlist (Starlark `prefix_rule`s); do not edit — hand edits are picked up and folded back on the next sync, but get overwritten in the process |
| `.codex/config.toml` | Generated project-local Codex config — `[plugins."<id>"].enabled` plus a marked `[mcp_servers.*]` block (see below); other content is preserved if you add it |
| `.mcp.json` | Generated project-scoped Claude MCP server config; do not edit directly — hand-added servers are picked up and folded back into `ai/settings/settings.json` on the next sync (reconstructed into `tools`/`cmd` where the command matches a known tool snippet, otherwise stored as a flat `cmd`) |
| `ai/settings/mcp.schema.json` | JSON Schema composed into the root settings schemas for the `mcp` key below |
| `ai/.env` | Gitignored, project-local secrets (e.g. for MCP servers); see `ai/.env.example` |
| `scripts/°base/ai/settings/°settings_lib/` | The actual sync implementation; `sync.py` is a thin shim over it (mirrors `ai/references/°dllink_lib/`) |

### Settings + skills sync (`scripts/°base/ai/settings/sync.py`)

The single source of truth is `ai/settings/settings.json`. Running `sync.py` renders it into `.claude/settings.json` (Claude), `.codex/hooks.json` (Codex hooks), `.codex/rules/generated.rules` (Codex command allowlist), and `.codex/config.toml` (Codex plugin enable/disable), adjusting async flags and tool-name arguments between the two formats. A pre-commit hook runs `sync.py --check` to block commits when the files drift.

`ai/settings/settings.json` carries a `version` field (`hooks.CURRENT_VERSION`, currently `2`); `sync.py` always writes the current version but still reads older files — v1 (raw Claude permission strings, flat `enabledPlugins: {id: bool}`) upgrades transparently on load, since parsing permission entries and plugin entries is permissive regardless of the source version.

`sync.py` writes `ai/settings/settings.json`/`settings.local.json` with a custom pretty-printer, not plain `json.dumps`: a dict's `"enabled"` key (if present) always renders first, at any depth; `permissions.allow`/`permissions.deny` array elements render one compact single-line object per line; and any `"cmd"` array (only ever `mcp.tools.*.*.cmd` / `mcp.servers.*.cmd`) renders as a single line. Everything else stays normal one-key/one-element-per-line `indent=2` formatting, for readable diffs.

`permissions.allow`/`permissions.deny` entries use a structured schema, not raw Claude strings: `{"type": "bash", "command": "git status:*"}`, `{"type": "read", "path": "**/.env*"}`, `{"type": "skill", "name": "..."}` (unrecognized tools fall back to a `pattern` field; unparseable legacy strings become `{"type": "raw", "value": "..."}`). This is what lets `sync.py` render the same entry into both Claude's `Tool(content)` syntax and Codex's `prefix_rule(pattern=[...], decision=...)` syntax. Only `bash` entries reach Codex — Codex `.rules` files govern command execution only, not file reads or skill invocation. Commands that can't be reduced to a static argv prefix (shell substitution, redirection, `&&`/`||`/`;`/`|`, env-var-assignment prefixes) stay Claude-only.

Codex's `.rules` file and `.codex/config.toml` plugin blocks are genuinely bidirectional: `sync.py` parses them back (Starlark via `ast`, TOML via `tomllib`) and folds new entries into `ai/settings/settings.json`. Because a Codex prefix rule has no "exact match" concept, re-parsed bash commands are compared by their token-prefix (not their rendered string) before merging, so re-importing `sync.py`'s own generated output never duplicates entries.

Plugins live under the `plugins` key (`{"<id>": {"enabled": bool}}`, not the old flat `enabledPlugins: {id: bool}` — that shape is still read for backward compatibility but never written). `render_claude` flattens it back into Claude's native `enabledPlugins: {id: bool}`; `render_codex_plugins` (TOML-only, unaffected by the nesting) still takes a flat `dict[str, bool]`, so `sync.py` flattens `plugins` before calling it.

MCP servers are configured under the `mcp` key (schema: `ai/settings/mcp.schema.json`), split into
reusable `mcp.tools.<name>.<variant>` command-prefix snippets (`{"mode": "prefix", "cmd": [...]}` — only
`prefix` is implemented) and `mcp.servers.<name>` definitions (`type: "stdio"|"http"`, `enabled`, and
either an ordered `tools` list of `"tool"`/`"tool@variant"` references and/or `cmd` (at least one of the
two is required for `stdio`), or `url`/`headers`).
`sync.py` resolves each server's final argv as `tools[0].cmd + tools[1].cmd + ... + cmd` (leftmost tool is
the outermost/first-spawned process) and substitutes any literal `$(git rev-parse --show-toplevel)` token
with the absolute repo root itself — this is **not** shell-expanded, since MCP servers are spawned as a
plain argv array by both clients. The built-in `.env` tool wraps a server with `envmcp` reading
`ai/.env` (gitignored; see `ai/.env.example`), so servers needing secrets (e.g. `bugsink`, which reads
`BUGSINK_URL`/`BUGSINK_TOKEN`) don't need per-client `env`/`env_vars` wiring — `envmcp` loads the file
into its own process env and spawns the wrapped server inheriting it, identically for Claude and Codex.
Resolved servers render into `.mcp.json` (Claude) and a marked `[mcp_servers.*]` block in
`.codex/config.toml` (Codex, `enabled` native, rendered first in the table for readable diffs); both are
parsed back on the next sync as flat entries (no `tools` field — native formats have no such concept).
Since a flat parsed-back entry would otherwise permanently flatten an authored `tools`-based server on
every round-trip, `sync.py` (`mcp_servers.extract_tools_from_cmd`) re-matches the flat `cmd` against known
`mcp.tools` snippets (greedy longest-prefix-first, chained left-to-right) and reconstructs a `tools`/`cmd`
split whenever a native entry is new or its resolved command genuinely changed; when only `enabled`
changed, that field is updated on the existing authored entry in place instead. `.mcp.json` has no
`enabled` concept at all (every server renders into it regardless of state), so a parsed-back Claude entry
never carries that key — the merge falls back to whatever `ai/settings/settings.json` (or Codex's
`config.toml`, which does carry a real `enabled`) already knows, rather than assuming `True`.
`enabledMcpjsonServers`/`disabledMcpjsonServers` in `.claude/settings.json` are derived one-directionally
from each server's `enabled` flag and — once at least one server exists — both arrays are always written
(one may be empty), so toggling a server only changes an array's contents, not which keys are present.

Skills follow the same pattern: the canonical file is `ai/skills/<slug>/SKILL.md`. `sync.py` symlinks `.claude/skills/<slug>/SKILL.md` and `.agents/skills/<slug>/SKILL.md` to the canonical path (Linux/Mac only — this repo does not support Windows checkouts). Always edit the canonical file, then run `sync.py`. No `.claude/commands/<slug>.md` shim is generated: Claude Code's Terminal already lists skills directly in its `/` autocomplete (and Codex reads `.agents/skills` directly), so a command wrapper would just duplicate the skill.

### AI artifact routing (`scripts/°base/ai/hooks/_lib.py`)

Every Claude Code hook calls `resolve_log_path()`, which routes output based on whether it is running inside the base repo (`ai/°base/…`) or a consuming repo (`ai/…`). Detection: `_is_inside_base_repo()` — directory named `base` **and** origin URL matches `luckydonald/base`.

Hooks:

| Hook | Trigger | Output |
|---|---|---|
| `save-prompt/hook.py` | `UserPromptSubmit` | `ai/°base/query.md`, plus caught-up direct Codex command output under `output/commands/` |
| `save-decision/hook.py` | `AskUserQuestion` post | `ai/°base/query.md` |
| `save-plan/hook.py` | `Write`, `ExitPlanMode`, `Stop` | `ai/°base/plans/NNN_*.md` |
| `record-memory/hook.py` | `Write`, `Edit`, `Bash`, `SessionStart` | syncs memory hardlinks |
| `record-codex-memory/hook.py` | Codex write tools, `SessionStart`, `Stop` | syncs scoped Codex memory into the shared project memory tree |

### Pre-commit hooks

- `reject_co_authored_by.py` — blocks `Co-Authored-By:` in commit messages (stage: commit-msg)
- `require_memory_delete_marker.py` — requires an explicit marker when memory files are deleted (stage: commit-msg)
- `require_yarn_4.py` — enforces Yarn 4 project state when Node/package-manager files exist (stage: pre-commit)

### Plan mode

While still in Plan Mode, before presenting or leaving the approved plan, ask once per session through the user-question dialog (`AskUserQuestion`, choices `yes`/`no`) whether to enable the `commit-with-lplp-style` skill for the implementation. Do not defer this to implementation mode or replace the dialog with a normal assistant message. Skip the question and assume `yes` when the repository's GitHub origin belongs to `luckydonald/*` or `littlepipslittleparty/*`. Otherwise, skip asking again for the rest of the session after the first answer and respect that answer for every later plan unless the user changes their mind. Whenever the answer resolves to `yes` (asked or assumed), also apply `commit-with-lplp-style`'s own rule 9 before the plan is saved: note the active commit style in the plan file itself, since the implementation may run in a session or subagent that only ever sees that document.

Before writing or editing the plan document's prose, read `ai/skills/code-style/references/md.md` directly and apply it — do not rely on the `code-style` skill's own triggering to fire, since its description is code-oriented and easy to miss for a plan write. Do this once per session; a later plan revision only needs a re-read if the guidance may have changed. The synchronous `plan-style-context/hook.py` (`UserPromptSubmit`) backs this up: while in plan mode or on a `/plan` prompt it injects that same instruction as `additionalContext`.

### Commit format

```
[base] topic: ai: Run: Short summary.
```

`[base]` is the where-tag; `topic` is a component or subsystem name (not a Conventional Commit type like `feat` or `fix`).

**Optional source-repo bracket:** `[base] [source repo] topic: ai: Run: ...`. The nested bracket names a `luckydonald/`-owned repo that this base change is *for* — the reason the change is happening, e.g. a hook or feature ported in from, or requested by, a session working in that linked repo.

Only add it when one of these holds:
- The source repo was stated explicitly this session (at session start, or named while describing the task), or
- The exact file/area has a source-repo tag in *recent* history (not a months-old match) whose topic matches the current change.

Otherwise omit the bracket entirely — plain `[base] topic: ai: Run: ...` is the default when there's no current-session signal. Never guess a source repo from a stale or topically-unrelated prior commit just because it touched the same file — that produced a real bug once (a commit tagged `[hoass_plugin-template]` reusing a tag whose only prior use on that file was over two months old).

This is distinct from feature-area tags like `[ssp]` (see `ai/°base/memory/feedback_commit_prefix_ssp_tag.md`), which are a standing convention for a specific feature area, not a "where did this originate" tag — don't conflate the two.
