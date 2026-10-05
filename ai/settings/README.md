# AI Tool Settings

`ai/settings/settings.json` is the tracked, human-editable settings file shared by Claude and Codex.
`scripts/°base/ai/settings/sync.py` reads it, preserves non-native metadata there, and renders the native files
under `.claude/` and `.codex/`.

Core keys:

- `$schema`: IDE-visible JSON Schema for this settings layer
- `version`: settings format version
- `hooks`: hook definitions shared across tools
- `permissions`: allow/deny command lists for Claude-style configuration
- `skillOverrides`: Claude skill toggles like `{"my-skill": "off"}`, rendered verbatim into `.claude/settings*.json`
- `mcp.servers.<name>`: besides full definitions, an enable-only entry (`{"enabled": false}`) toggles a server defined elsewhere (e.g. `.mcp.json`) and is rendered only into Claude's `enabledMcpjsonServers`/`disabledMcpjsonServers`
- `pre_commit.yarn@4.enabled`: shared, enabled-by-default Yarn 4 repository policy

Downloader settings:

- `download_link.ide`: default IDE command used by `scripts/°base/ai/references/download-link.py`

Recommended values for `download_link.ide` are executable names that accept a file path as their final argument,
such as `pycharm`, `rustrover`, `codium`, or `code`.

`settings.local.json` is the ignored machine-local overlay for per-machine overrides. Keep shared defaults in
`settings.json` and machine-specific preferences in `settings.local.json`.

The Yarn 4 commit policy is deliberately repository-wide. Other `pre_commit` settings may be added to
`settings.local.json`, but `pre_commit.yarn@4` must only appear in tracked `settings.json`; putting it in the
local overlay is an error. The settings sync adds `./settings-local.schema.json` to local settings so IDEs flag
that mistake immediately. Legacy Node projects can opt out with tracked configuration:

```json
{
  "pre_commit": {
    "yarn@4": {
      "enabled": false
    }
  }
}
```
