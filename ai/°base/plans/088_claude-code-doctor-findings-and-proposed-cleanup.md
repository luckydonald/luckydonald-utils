# Claude Code Doctor: findings and proposed cleanup

## Context

Read-only health check of the Claude Code setup (scan window: 50 sessions since 2026-09-21).
Nothing has been changed yet.
All proposed changes are reversible, and each is applied only after confirmation.

## Healthy (no action)

- **Install:** native 2.1.289, which matches the latest release on the `latest` channel. No npm leftovers, `~/.local/bin` is on PATH, and `installMethod` agrees.
- **Config files:** all settings, `~/.claude.json` and `.mcp.json` parse cleanly. No agent definitions exist, and all 10 skill frontmatters parse.
- **CLAUDE.md:** the only file is 330 chars (about 80 est. tokens), so it is already lean. There are no local CLAUDE.md files to dedup (checks 2, 3 and 4).
- **Hooks:** SessionStart averages 164 ms with no timeouts.
- **Context:** the skill listing is about 1.2k est. tokens, MCP tools are deferred (about 0), and CLAUDE.md is about 80 tokens. Run `/context` for the exact live figure.

## Check 1: unused extensions (proposed disables)

| Item | Scope | Uses | Used in window? | Verdict |
|---|---|---|---|---|
| `rust-analyzer-lsp@claude-plugins-official` | user | 0 (LSP tracking is recent) | no | remove, since this is a Python repo |
| `openai-developers@openai-developers` | project (checked in) | no counter | no signal | remove unless you use it |
| MCP `chrome-devtools` | `.mcp.json` | n/a | 0 calls | remove (decluttering, not token savings) |
| MCP `coolify` | `.mcp.json` | n/a | 0 calls | remove (decluttering) |
| skill `bugsink-triage` | project | 4 | last used 2026-07 | off (about 125 est. tokens) |
| skill `coolify-compose-deploy` | project | 1 | last used 2026-08 | off (about 125 est. tokens) |
| skill `uvicorn-app-logging` | project | none | no | off (about 125 est. tokens) |

Kept because they are in use: `sync_todo` and `bugsink` MCP, `claude-in-chrome`, `skill-creator` (4 uses), and the skills `code-style`, `commit-with-lplp-style`, `install-base`, `sync-todo-mcp`, `bugsink-setup` and `sanitize-error-logs`.

Mechanics:

- `rust-analyzer-lsp` is set to `false` in `~/.claude/settings.json` under `enabledPlugins`.
- `openai-developers` is enabled by checked-in settings, so its `false` goes in `.claude/settings.local.json`.
- Only `chrome-devtools` and `coolify` are added to `disabledMcpjsonServers` in `.claude/settings.local.json`.
- `bugsink` and `sync_todo` stay enabled, and are listed in `enabledMcpjsonServers` in the same gitignored `.claude/settings.local.json`, so they remain available locally and nothing is committed.
- Nothing is written to `.mcp.json` or `.claude/settings.json`.
- The three skills get `"off"` under `skillOverrides` in `.claude/settings.local.json`.
- Values are merged with a `mktemp` file and `jq --slurpfile`, never inlined.
- Undo by deleting those entries, or use `/mcp enable` and `/plugin`.

Side notes (no action proposed):

- `install-base` exists both in `~/.claude/skills` and in the project, so one shadows the other.
- `.claude/commands/*.md` mirrors the skill names, so the same entries may be listed twice.

## Check 5: hook warnings (no action)

- PostToolUse runs 6 Python hooks plus a `uv run` hook on every tool call.
- No timing data is recorded because silent successes are not persisted, so this is config inspection only.
- If tool calls feel sluggish, make those hooks async or narrow their matchers.

## Check 8: auto mode as default (separate permission question)

- `~/.claude/settings.json` currently has `permissions.defaultMode: "plan"`, which looks deliberate.
- Switching to `"auto"` would replace the plan default in every project.
- No project or local file pins a mode, and no policy disables auto mode.
- Recommendation: only apply if you want the classifier instead of plan-first. Otherwise decline.

## Check 9: pre-approve denied read-only commands

Nothing to propose.
Of 46 denials in the window, 27 were `ExitPlanMode` rejections, and the few `git status`/`git diff`/`ls` denials came from deny rules or the classifier, which an allow rule won't override.

## Confirmation gates (asked after plan approval)

1. Cleanup question: clean up everything (recommended), let me pick, or keep everything. It covers the 7 disables above, with `bugsink` and `sync_todo` explicitly kept enabled locally.
2. Permission question: switch the default to auto mode (only change in scope), apply or keep plan.

## Verification

After applying, re-run `jq empty` on each edited file, then confirm in `/mcp`, `/plugin` and `/skills` that the items are off.
