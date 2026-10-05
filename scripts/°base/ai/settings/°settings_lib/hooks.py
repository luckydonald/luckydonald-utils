from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from .commands import _parse_claude_permission_entry, _render_claude_permission_entry
from .json_io import _unique

CURRENT_VERSION = 2

# "enabledPlugins" is the deprecated v1 name for "plugins" — still recognized
# here (so `_normalize_plugins` can read it and `_shared_extras` won't treat
# it as opaque user metadata to preserve verbatim), even though nothing ever
# writes it back out at this level again.
_CORE_SHARED_KEYS = {"$schema", "version", "hooks", "permissions", "plugins", "enabledPlugins", "mcp", "skillOverrides"}


def _hook_id(event: str, entry: dict[str, Any]) -> str:
    matcher = entry.get("matcher") or ""
    commands = []
    for hook in entry.get("hooks") or []:
        if isinstance(hook, dict):
            commands.append(_neutralize_command(hook.get("command") or ""))
    return "\0".join([event, matcher, "\0".join(commands)])


def _matcher_tokens(entry: dict[str, Any]) -> set[str]:
    matcher = str(entry.get("matcher") or "")
    return {part for part in matcher.split("|") if part} or {""}


def _entry_commands(entry: dict[str, Any]) -> set[str]:
    commands: set[str] = set()
    for hook in entry.get("hooks") or []:
        if isinstance(hook, dict):
            commands.add(_neutralize_command(str(hook.get("command") or "")))
    return commands


def _subsumes(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """True when entry ``a`` covers everything entry ``b`` covers."""
    return _matcher_tokens(a).issuperset(_matcher_tokens(b)) and _entry_commands(a).issuperset(_entry_commands(b))


def _overlay_entry(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(existing)
    for key, value in incoming.items():
        if key != "hooks":
            merged[key] = deepcopy(value)

    existing_hooks = merged.get("hooks") if isinstance(merged.get("hooks"), list) else []
    incoming_hooks = incoming.get("hooks") if isinstance(incoming.get("hooks"), list) else []
    hooks = []
    for index, hook in enumerate(incoming_hooks):
        if not isinstance(hook, dict):
            continue
        if index < len(existing_hooks) and isinstance(existing_hooks[index], dict):
            merged_hook = deepcopy(existing_hooks[index])
            merged_hook.update(deepcopy(hook))
            hooks.append(merged_hook)
        else:
            hooks.append(deepcopy(hook))
    if hooks:
        merged["hooks"] = hooks
    return merged


def _normalize_permissions(permissions: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(permissions)
    for key in ("allow", "deny"):
        values = permissions.get(key)
        if values is not None:
            normalized[key] = [_parse_claude_permission_entry(v) for v in values]
    return normalized


def _normalize_plugins(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build the neutral `plugins: {id: {"enabled": bool}}` shape from either
    an already-nested `plugins` key, or the legacy/native flat
    `enabledPlugins: {id: bool}` shape (v1 files, or Codex's
    `parse_codex_plugins` round-trip, which only ever produces flat bools)."""
    plugins = data.get("plugins")
    if isinstance(plugins, dict):
        result: dict[str, dict[str, Any]] = {}
        for plugin_id, entry in plugins.items():
            if isinstance(entry, dict):
                result[plugin_id] = {"enabled": bool(entry.get("enabled", True))}
            else:
                result[plugin_id] = {"enabled": bool(entry)}
        return result
    enabled_plugins = data.get("enabledPlugins") or {}
    return {plugin_id: {"enabled": bool(enabled)} for plugin_id, enabled in enabled_plugins.items()}


def _normalize_native(data: dict[str, Any]) -> dict[str, Any]:
    hooks = deepcopy(data.get("hooks") or {})
    for entries in hooks.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for hook in entry.get("hooks") or []:
                if isinstance(hook, dict):
                    raw_command = hook.get("command")
                    if raw_command is None:
                        raw_command = hook.pop("bash", None) or hook.pop("powershell", None)
                    else:
                        hook.pop("bash", None)
                        hook.pop("powershell", None)
                    hook["command"] = _neutralize_command(str(raw_command or ""))
                    if "timeout" not in hook and "timeoutSec" in hook:
                        hook["timeout"] = hook.pop("timeoutSec")
                    else:
                        hook.pop("timeoutSec", None)
    mcp = data.get("mcp") or {}
    normalized = {
        "version": CURRENT_VERSION,
        "hooks": hooks,
        "permissions": _normalize_permissions(data.get("permissions") or {}),
        "plugins": _normalize_plugins(data),
        "mcp": {
            "tools": deepcopy(mcp.get("tools") or {}),
            "servers": deepcopy(mcp.get("servers") or {}),
        },
    }
    skill_overrides = data.get("skillOverrides")
    if isinstance(skill_overrides, dict) and skill_overrides:
        normalized["skillOverrides"] = deepcopy(skill_overrides)
    return normalized


def _shared_extras(data: dict[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in data.items() if key not in _CORE_SHARED_KEYS}


def _merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = _normalize_native(base)
    incoming = _normalize_native(incoming)

    hooks = deepcopy(merged.get("hooks") or {})
    for event, entries in (incoming.get("hooks") or {}).items():
        if not isinstance(entries, list):
            continue
        current = [deepcopy(entry) for entry in hooks.get(event, []) if isinstance(entry, dict)]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_id = _hook_id(event, entry)
            replaced = False
            for index, existing in enumerate(current):
                if _hook_id(event, existing) == entry_id:
                    current[index] = _overlay_entry(existing, entry)
                    replaced = True
                    break
            if replaced:
                continue
            if any(_subsumes(existing, entry) for existing in current):
                continue
            current = [existing for existing in current if not _subsumes(entry, existing)]
            by_id = {_hook_id(event, existing): existing for existing in current}
            by_id[entry_id] = deepcopy(entry)
            current = list(by_id.values())
        hooks[event] = current
    merged["hooks"] = hooks

    permissions = deepcopy(merged.get("permissions") or {})
    incoming_permissions = incoming.get("permissions") or {}
    for key in ("allow", "deny"):
        values = list(permissions.get(key) or [])
        values.extend(incoming_permissions.get(key) or [])
        permissions[key] = _unique(values)
    merged["permissions"] = permissions

    plugins = deepcopy(merged.get("plugins") or {})
    for plugin_id, entry in (incoming.get("plugins") or {}).items():
        plugins[plugin_id] = deepcopy(entry)
    merged["plugins"] = plugins

    skill_overrides = {**(merged.get("skillOverrides") or {}), **(incoming.get("skillOverrides") or {})}
    if skill_overrides:
        merged["skillOverrides"] = skill_overrides

    merged_mcp = deepcopy(merged.get("mcp") or {"tools": {}, "servers": {}})
    incoming_mcp = incoming.get("mcp") or {}
    merged_mcp.setdefault("tools", {}).update(incoming_mcp.get("tools") or {})
    merged_mcp.setdefault("servers", {}).update(incoming_mcp.get("servers") or {})
    merged["mcp"] = merged_mcp
    return merged


def _replace_tool_arg(command: str, tool: str) -> str:
    if (
        "save-prompt/hook.py" in command
        or "save-decision/hook.py" in command
        or "save-command-decision/hook.py" in command
        or "save-plan/hook.py" in command
        or "save-compact-prompt/hook.py" in command
        or "record-codex-memory/hook.py" in command
    ):
        command = command.replace("'claude'", f"'{tool}'")
        command = command.replace('"claude"', f'"{tool}"')
        if "save-plan/hook.py" in command and not re.search(r"['\"](?:claude|codex|copilot)['\"]", command):
            command = f"{command} '{tool}'"
    return command


def _normalize_command_path(command: str) -> str:
    command = command.replace("python3 .claude/hooks/permission-check.py", 'python3 "$(git rev-parse --show-toplevel)/.claude/hooks/permission-check.py"')
    return command


def _uv_project_hook_command(command: str) -> str:
    if "save-decision/hook.py" not in command:
        return command
    match = re.search(r"(?:python3|python)\s+\"?([^\"']*save-decision/hook\.py)\"?\s*(.*)\Z", command)
    if not match:
        return command
    script, args = match.groups()
    if "uv run --project" in command:
        return command
    script = script.strip()
    args = args.strip()
    if "$(git rev-parse --show-toplevel)" not in script:
        script = f"$(git rev-parse --show-toplevel)/{script.lstrip('./')}"
    return (
        f'"$(git rev-parse --show-toplevel)/scripts/°base/git/hooks/tool_path.sh" '
        f'uv run --project "$(git rev-parse --show-toplevel)/scripts/°base" '
        f'python "{script}"'
        + (f" {args}" if args else "")
    )


def _neutralize_uv_project_hook_command(command: str) -> str:
    match = re.search(
        r'\A(?:"?\$\(git rev-parse --show-toplevel\)/scripts/°base/git/hooks/tool_path\.sh"? )?'
        r"uv run --project \"?\$\(git rev-parse --show-toplevel\)/scripts/°base\"? "
        r"python \"?([^\"']*save-decision/hook\.py)\"?\s*(.*)\Z",
        command,
    )
    if not match:
        return command
    script, args = match.groups()
    script = script.strip()
    args = args.strip()
    return f'python3 "{script}"' + (f" {args}" if args else "")


def _neutralize_command(command: str) -> str:
    command = _normalize_command_path(command)
    command = _neutralize_uv_project_hook_command(command)
    if (
        "save-prompt/hook.py" in command
        or "save-decision/hook.py" in command
        or "save-command-decision/hook.py" in command
        or "save-plan/hook.py" in command
        or "save-compact-prompt/hook.py" in command
        or "record-codex-memory/hook.py" in command
    ):
        command = command.replace("'codex'", "'claude'")
        command = command.replace('"codex"', '"claude"')
        command = command.replace("'copilot'", "'claude'")
        command = command.replace('"copilot"', '"claude"')
        if "save-plan/hook.py" in command and not re.search(r"['\"](?:claude|codex|copilot)['\"]", command):
            command = f"{command} 'claude'"
    return command


def _render_hooks(shared: dict[str, Any], tool: str) -> dict[str, Any]:
    rendered: dict[str, Any] = {"hooks": {}}
    for event, entries in (shared.get("hooks") or {}).items():
        if not isinstance(entries, list):
            continue
        rendered_entries = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            new_entry = deepcopy(entry)
            if tool == "codex" and event == "PostToolUse" and any(
                "record-codex-memory/hook.py" in str(hook.get("command") or "")
                for hook in new_entry.get("hooks") or []
                if isinstance(hook, dict)
            ):
                new_entry["matcher"] = "Write|Edit|apply_patch"
            # end if
            hooks = []
            for hook in new_entry.get("hooks") or []:
                if not isinstance(hook, dict):
                    continue
                new_hook = deepcopy(hook)
                command = str(new_hook.get("command") or "")
                command = _normalize_command_path(_replace_tool_arg(command, tool))
                command = _uv_project_hook_command(command)
                new_hook["command"] = command
                if tool == "codex":
                    new_hook.pop("async", None)
                hooks.append(new_hook)
            new_entry["hooks"] = hooks
            rendered_entries.append(new_entry)
        if rendered_entries:
            rendered["hooks"][event] = rendered_entries
    return rendered


def render_claude(shared: dict[str, Any]) -> dict[str, Any]:
    data = _render_hooks(shared, "claude")
    if "allowCoAuthoredEtc" in shared:
        data["includeCoAuthoredBy"] = shared["allowCoAuthoredEtc"]
    permissions = shared.get("permissions")
    if permissions:
        rendered_permissions: dict[str, Any] = {}
        for key in ("allow", "deny"):
            values = permissions.get(key)
            if values is not None:
                rendered_permissions[key] = [_render_claude_permission_entry(v) for v in values]
        for key, value in permissions.items():
            if key not in ("allow", "deny"):
                rendered_permissions[key] = deepcopy(value)
        data["permissions"] = rendered_permissions
    plugins = shared.get("plugins")
    if plugins:
        data["enabledPlugins"] = {
            plugin_id: bool(entry.get("enabled", True))
            for plugin_id, entry in plugins.items()
            if isinstance(entry, dict)
        }
    skill_overrides = shared.get("skillOverrides")
    if skill_overrides:
        data["skillOverrides"] = deepcopy(skill_overrides)
    servers = (shared.get("mcp") or {}).get("servers") or {}
    if servers:
        enabled = [name for name, server in servers.items() if isinstance(server, dict) and server.get("enabled", True)]
        disabled = [name for name, server in servers.items() if isinstance(server, dict) and server.get("enabled", True) is False]
        data["enabledMcpjsonServers"] = enabled
        data["disabledMcpjsonServers"] = disabled
    return data


def render_codex_hooks(shared: dict[str, Any]) -> dict[str, Any]:
    return _render_hooks(shared, "codex")


def render_copilot_hooks(shared: dict[str, Any]) -> dict[str, Any]:
    """Render the neutral shared hooks into Copilot CLI's native
    `{"version": 1, "hooks": {...}}` format (`.github/hooks/*.json`).

    Copilot's command-hook shape differs from Claude/Codex's: `bash` instead
    of `command`, `timeoutSec` instead of `timeout`, and no `statusMessage`/
    `async` (Copilot has no fire-and-forget flag for arbitrary command
    hooks). The file is hooks-only — no `permissions`/`plugins`/`mcp`.
    """
    data = _render_hooks(shared, "copilot")
    copilot_hooks: dict[str, Any] = {}
    for event, entries in (data.get("hooks") or {}).items():
        rendered_entries = []
        for entry in entries:
            new_entry = deepcopy(entry)
            new_hooks = []
            for hook in new_entry.get("hooks") or []:
                new_hook = deepcopy(hook)
                command = new_hook.pop("command", None)
                if command is not None:
                    new_hook["bash"] = command
                new_hook.pop("statusMessage", None)
                new_hook.pop("async", None)
                timeout = new_hook.pop("timeout", None)
                if timeout is not None and "timeoutSec" not in new_hook:
                    new_hook["timeoutSec"] = timeout
                new_hooks.append(new_hook)
            new_entry["hooks"] = new_hooks
            rendered_entries.append(new_entry)
        if rendered_entries:
            copilot_hooks[event] = rendered_entries
    return {"version": 1, "hooks": copilot_hooks}
