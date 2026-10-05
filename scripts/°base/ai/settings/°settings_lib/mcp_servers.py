from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any

_GIT_ROOT_TOKEN = "$(git rev-parse --show-toplevel)"

MCP_TOML_BEGIN_MARKER = "# --- BEGIN generated mcp_servers (scripts/°base/ai/settings/sync.py) ---"
MCP_TOML_END_MARKER = "# --- END generated mcp_servers ---"

_TABLE_HEADER = re.compile(r'^\[([^\[\]]+)\]\s*$')


def _substitute_git_root(value: str, git_root: Path) -> str:
    return value.replace(_GIT_ROOT_TOKEN, str(git_root))


def _resolve_tool_ref(tools: dict[str, Any], ref: str) -> list[str] | None:
    name, _, variant = ref.partition("@")
    variants = tools.get(name)
    if not isinstance(variants, dict):
        return None
    entry = variants.get(variant)
    if not isinstance(entry, dict) or entry.get("mode") != "prefix":
        return None
    cmd = entry.get("cmd")
    if not isinstance(cmd, list) or not all(isinstance(token, str) for token in cmd):
        return None
    return list(cmd)


def _resolve_server_argv(mcp: dict[str, Any], server: dict[str, Any], git_root: Path) -> list[str] | None:
    tools = mcp.get("tools") or {}
    argv: list[str] = []
    for ref in server.get("tools") or []:
        resolved = _resolve_tool_ref(tools, ref)
        if resolved is None:
            return None
        argv.extend(resolved)
    cmd = server.get("cmd")
    if cmd is not None:
        if not isinstance(cmd, list) or not all(isinstance(token, str) for token in cmd):
            return None
        argv.extend(cmd)
    if not argv:
        return None
    return [_substitute_git_root(token, git_root) for token in argv]


def _tool_ref(name: str, variant: str) -> str:
    return name if variant == "" else f"{name}@{variant}"


def extract_tools_from_cmd(tools: dict[str, Any], cmd: list[str], git_root: Path) -> tuple[list[str], list[str]]:
    """Greedily match `cmd` against known `mcp.tools.<name>.<variant>` prefix
    snippets, from the front, chaining matches left-to-right (mirroring
    `_resolve_server_argv`'s `tools[0].cmd + tools[1].cmd + ... + cmd`
    composition). Ties are broken by longest matching prefix first, then
    alphabetical `(name, variant)`, for determinism. Returns
    `(tool_refs, remaining_cmd)`; when nothing matches at all, degenerates to
    `([], cmd)` — the "just store the flat cmd" fallback."""
    candidates: list[tuple[str, list[str]]] = []
    for name, variants in tools.items():
        if not isinstance(variants, dict):
            continue
        for variant, entry in variants.items():
            if not isinstance(entry, dict) or entry.get("mode") != "prefix":
                continue
            snippet = entry.get("cmd")
            if not isinstance(snippet, list) or not snippet or not all(isinstance(t, str) for t in snippet):
                continue
            resolved = [_substitute_git_root(token, git_root) for token in snippet]
            candidates.append((_tool_ref(name, variant), resolved))
    candidates.sort(key=lambda item: (-len(item[1]), item[0]))

    tool_refs: list[str] = []
    pos = 0
    while pos < len(cmd):
        match = None
        for ref, resolved in candidates:
            end = pos + len(resolved)
            if end <= len(cmd) and cmd[pos:end] == resolved:
                match = (ref, len(resolved))
                break
        if match is None:
            break
        tool_refs.append(match[0])
        pos += match[1]
    return tool_refs, cmd[pos:]


def _reconstruct_stdio_entry(mcp: dict[str, Any], cmd: list[str], enabled: bool, git_root: Path) -> dict[str, Any]:
    tool_refs, remaining = extract_tools_from_cmd(mcp.get("tools") or {}, cmd, git_root)
    entry: dict[str, Any] = {"enabled": enabled, "type": "stdio"}
    if tool_refs:
        entry["tools"] = tool_refs
    if remaining or not tool_refs:
        entry["cmd"] = remaining
    return entry


def _is_enable_only(server: dict[str, Any]) -> bool:
    """An entry with no definition at all (no `type`/`cmd`/`tools`/`url`), only `enabled`. It toggles a server that is
    defined elsewhere (e.g. `.mcp.json`) and is only rendered into Claude's enabled/disabledMcpjsonServers lists."""
    return not ({"type", "cmd", "tools", "url"} & server.keys())


def render_claude_mcp(shared: dict[str, Any], git_root: Path) -> tuple[dict[str, Any], list[str]]:
    """Build `.mcp.json` content. Returns (data, skipped_server_names)."""
    mcp = shared.get("mcp") or {}
    servers = mcp.get("servers") or {}
    rendered: dict[str, Any] = {}
    skipped: list[str] = []
    for name, server in servers.items():
        if not isinstance(server, dict) or _is_enable_only(server):
            continue
        if server.get("type") == "http":
            entry: dict[str, Any] = {"type": "http", "url": server.get("url", "")}
            if server.get("headers"):
                entry["headers"] = dict(server["headers"])
            rendered[name] = entry
            continue
        argv = _resolve_server_argv(mcp, server, git_root)
        if argv is None:
            skipped.append(name)
            continue
        rendered[name] = {"type": "stdio", "command": argv[0], "args": argv[1:]}
    return {"mcpServers": rendered}, skipped


def parse_claude_mcp(mcp_json_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """`.mcp.json` has no enabled/disabled concept — `render_claude_mcp` writes
    every server into it regardless of state — so parsed-back entries omit
    `enabled` entirely rather than fabricating a value; callers fall back to
    whatever the shared config already knows."""
    result: dict[str, dict[str, Any]] = {}
    for name, entry in (mcp_json_data.get("mcpServers") or {}).items():
        if not isinstance(entry, dict):
            continue
        if entry.get("type") == "http" or "url" in entry:
            neutral: dict[str, Any] = {"type": "http", "url": entry.get("url", "")}
            if entry.get("headers"):
                neutral["headers"] = dict(entry["headers"])
            result[name] = neutral
            continue
        command = entry.get("command")
        if not isinstance(command, str):
            continue
        args = entry.get("args") or []
        result[name] = {
            "type": "stdio",
            "cmd": [command, *[str(arg) for arg in args]],
        }
    return result


def _mcp_tool_permissions(shared: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    """Group `{"type": "mcp", "server": ..., "tool": ...}` permission entries
    by server, keyed by bucket (`allow`/`deny`)."""
    permissions = shared.get("permissions") or {}
    result: dict[str, dict[str, list[str]]] = {}
    for bucket in ("allow", "deny"):
        for entry in permissions.get(bucket) or []:
            if not isinstance(entry, dict) or entry.get("type") != "mcp":
                continue
            server = entry.get("server")
            tool = entry.get("tool")
            if not server or not tool:
                continue
            result.setdefault(server, {}).setdefault(bucket, []).append(tool)
    return result


def _server_table_lines(
    name: str,
    server: dict[str, Any],
    mcp: dict[str, Any],
    git_root: Path,
    tool_permissions: dict[str, list[str]] | None = None,
) -> list[str] | None:
    table_name = f'mcp_servers.{json.dumps(name)}'
    lines = [f"[{table_name}]"]
    enabled = server.get("enabled", True)
    lines.append(f'enabled = {"true" if enabled else "false"}')
    if server.get("type") == "http":
        lines.append(f'url = {json.dumps(server.get("url", ""))}')
        headers = server.get("headers")
        if headers:
            lines.append(f'http_headers = {json.dumps(headers)}')
    else:
        argv = _resolve_server_argv(mcp, server, git_root)
        if argv is None:
            return None
        lines.append(f'command = {json.dumps(argv[0])}')
        lines.append(f'args = {json.dumps(argv[1:])}')

    tool_permissions = tool_permissions or {}
    denied = sorted(set(tool_permissions.get("deny") or []))
    if denied:
        lines.append(f'disabled_tools = {json.dumps(denied)}')
    for tool in sorted(set(tool_permissions.get("allow") or [])):
        lines.append("")
        lines.append(f'[{table_name}.tools.{json.dumps(tool)}]')
        lines.append('approval_mode = "auto"')
    return lines


def render_codex_mcp_block(shared: dict[str, Any], git_root: Path) -> tuple[str, list[str]]:
    """Render the `[mcp_servers.*]` marked block. Returns (block_text, skipped_server_names)."""
    mcp = shared.get("mcp") or {}
    servers = mcp.get("servers") or {}
    tool_permissions = _mcp_tool_permissions(shared)
    lines = [MCP_TOML_BEGIN_MARKER]
    skipped: list[str] = []
    for name, server in servers.items():
        if not isinstance(server, dict) or _is_enable_only(server):
            continue
        table_lines = _server_table_lines(name, server, mcp, git_root, tool_permissions.get(name))
        if table_lines is None:
            skipped.append(name)
            continue
        lines.append("")
        lines.extend(table_lines)
    lines.append("")
    lines.append(MCP_TOML_END_MARKER)
    return "\n".join(lines) + "\n", skipped


def insert_or_replace_block(text: str, begin_marker: str, end_marker: str, body: str) -> str:
    if not text.strip():
        text = ""

    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    start = end = None
    for index, line in enumerate(lines):
        if line.strip() == begin_marker:
            start = index
        elif line.strip() == end_marker and start is not None:
            end = index
            break

    body_lines = body.splitlines(keepends=True)
    if body_lines and not body_lines[-1].endswith("\n"):
        body_lines[-1] += "\n"

    if start is not None and end is not None:
        lines[start:end + 1] = body_lines
        return "".join(lines)

    if lines and lines[-1].strip() != "":
        lines.append("\n")
    lines.extend(body_lines)
    return "".join(lines)


def parse_codex_mcp_toml(text: str) -> dict[str, dict[str, Any]]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}
    mcp_servers = data.get("mcp_servers")
    if not isinstance(mcp_servers, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for name, entry in mcp_servers.items():
        if not isinstance(entry, dict):
            continue
        enabled = bool(entry.get("enabled", True))
        if "url" in entry:
            neutral: dict[str, Any] = {"type": "http", "url": entry.get("url", ""), "enabled": enabled}
            if entry.get("http_headers"):
                neutral["headers"] = dict(entry["http_headers"])
            result[name] = neutral
            continue
        command = entry.get("command")
        if not isinstance(command, str):
            continue
        args = entry.get("args") or []
        result[name] = {
            "type": "stdio",
            "cmd": [command, *[str(arg) for arg in args]],
            "enabled": enabled,
        }
    return result


def parse_codex_mcp_tool_permissions(text: str) -> dict[str, list[dict[str, Any]]]:
    """Parse per-tool `disabled_tools` / `approval_mode = "auto"` overrides
    back out of a Codex `config.toml` into neutral `{"type": "mcp", ...}`
    permission entries, keyed by bucket (`allow`/`deny`)."""
    result: dict[str, list[dict[str, Any]]] = {"allow": [], "deny": []}
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return result
    mcp_servers = data.get("mcp_servers")
    if not isinstance(mcp_servers, dict):
        return result
    for name, entry in mcp_servers.items():
        if not isinstance(entry, dict):
            continue
        for tool in entry.get("disabled_tools") or []:
            if isinstance(tool, str):
                result["deny"].append({"type": "mcp", "server": name, "tool": tool})
        tools = entry.get("tools")
        if not isinstance(tools, dict):
            continue
        for tool, tool_entry in tools.items():
            if isinstance(tool_entry, dict) and tool_entry.get("approval_mode") == "auto":
                result["allow"].append({"type": "mcp", "server": name, "tool": tool})
    return result
