from __future__ import annotations

import contextlib
import io
import importlib
import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path


LIB_ROOT = Path(__file__).resolve().parents[1] / "ai" / "settings"
sys.path.insert(0, str(LIB_ROOT))

paths = importlib.import_module("°settings_lib.paths")
commands = importlib.import_module("°settings_lib.commands")
hooks = importlib.import_module("°settings_lib.hooks")
codex_rules = importlib.import_module("°settings_lib.codex_rules")
codex_toml = importlib.import_module("°settings_lib.codex_toml")
mcp_servers = importlib.import_module("°settings_lib.mcp_servers")
json_io = importlib.import_module("°settings_lib.json_io")
skills = importlib.import_module("°settings_lib.skills")
cli = importlib.import_module("°settings_lib.cli")

ENTRYPOINT_PATH = LIB_ROOT / "sync.py"
SPEC = importlib.util.spec_from_file_location("ai_settings_sync_entrypoint", ENTRYPOINT_PATH)
ENTRYPOINT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ENTRYPOINT)


class EntrypointTests(unittest.TestCase):
    def test_shim_exposes_main(self):
        self.assertIs(ENTRYPOINT.main, cli.main)


class HooksTests(unittest.TestCase):
    def test_render_codex_rewrites_prompt_tool_arg(self):
        shared = {
            "hooks": {
                "UserPromptSubmit": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 scripts/°base/ai/hooks/save-prompt/hook.py 'claude'",
                            }
                        ]
                    }
                ]
            }
        }

        rendered = hooks.render_codex_hooks(shared)
        command = rendered["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]

        self.assertIn("'codex'", command)
        self.assertNotIn("'claude'", command)

    def test_render_codex_rewrites_codex_memory_tool_arg(self):
        shared = {
            "hooks": {
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 scripts/°base/ai/hooks/record-codex-memory/hook.py 'claude'",
                            }
                        ]
                    }
                ]
            }
        }

        codex = hooks.render_codex_hooks(shared)
        claude = hooks.render_claude(shared)
        codex_command = codex["hooks"]["Stop"][0]["hooks"][0]["command"]
        claude_command = claude["hooks"]["Stop"][0]["hooks"][0]["command"]

        self.assertIn("'codex'", codex_command)
        self.assertNotIn("'claude'", codex_command)
        self.assertIn("'claude'", claude_command)
        self.assertNotIn("'codex'", claude_command)

    def test_render_codex_narrows_codex_memory_posttooluse_matcher(self):
        shared = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Write|Edit|Bash|shell|unified_exec|apply_patch",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 scripts/°base/ai/hooks/record-codex-memory/hook.py 'claude'",
                                "timeout": 30,
                            }
                        ],
                    }
                ]
            }
        }

        codex = hooks.render_codex_hooks(shared)
        claude = hooks.render_claude(shared)
        codex_hook = codex["hooks"]["PostToolUse"][0]
        claude_hook = claude["hooks"]["PostToolUse"][0]

        self.assertEqual(codex_hook["matcher"], "Write|Edit|apply_patch")
        self.assertEqual(claude_hook["matcher"], "Write|Edit|Bash|shell|unified_exec|apply_patch")
        self.assertEqual(codex_hook["hooks"][0]["timeout"], 30)

    def test_render_codex_rewrites_compact_tool_arg(self):
        shared = {
            "hooks": {
                "PostCompact": [
                    {
                        "matcher": "manual|auto",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 scripts/°base/ai/hooks/save-compact-prompt/hook.py 'claude'",
                            }
                        ],
                    }
                ]
            }
        }

        codex = hooks.render_codex_hooks(shared)
        claude = hooks.render_claude(shared)
        codex_command = codex["hooks"]["PostCompact"][0]["hooks"][0]["command"]
        claude_command = claude["hooks"]["PostCompact"][0]["hooks"][0]["command"]

        self.assertIn("'codex'", codex_command)
        self.assertNotIn("'claude'", codex_command)
        self.assertIn("'claude'", claude_command)
        self.assertNotIn("'codex'", claude_command)

    def test_render_codex_rewrites_plan_tool_arg(self):
        shared = {
            "hooks": {
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 scripts/°base/ai/hooks/save-plan/hook.py 'claude'",
                            }
                        ]
                    }
                ]
            }
        }

        codex = hooks.render_codex_hooks(shared)
        claude = hooks.render_claude(shared)
        codex_command = codex["hooks"]["Stop"][0]["hooks"][0]["command"]
        claude_command = claude["hooks"]["Stop"][0]["hooks"][0]["command"]

        self.assertIn("'codex'", codex_command)
        self.assertNotIn("'claude'", codex_command)
        self.assertIn("'claude'", claude_command)
        self.assertNotIn("'codex'", claude_command)

    def test_render_save_decision_uses_uv_project_environment(self):
        shared = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "AskUserQuestion|request_user_input",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 \"$(git rev-parse --show-toplevel)/scripts/°base/ai/hooks/save-decision/hook.py\" 'claude'",
                            }
                        ],
                    }
                ]
            }
        }

        rendered = hooks.render_codex_hooks(shared)
        command = rendered["hooks"]["PostToolUse"][0]["hooks"][0]["command"]

        self.assertIn('"$(git rev-parse --show-toplevel)/scripts/°base/git/hooks/tool_path.sh"', command)
        self.assertIn('uv run --project "$(git rev-parse --show-toplevel)/scripts/°base"', command)
        self.assertIn('python "$(git rev-parse --show-toplevel)/scripts/°base/ai/hooks/save-decision/hook.py"', command)
        self.assertIn("'codex'", command)

    def test_uv_wrapped_save_decision_neutralizes_to_same_identity(self):
        plain = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "AskUserQuestion|request_user_input",
                        "hooks": [
                            {
                                "command": "python3 \"$(git rev-parse --show-toplevel)/scripts/°base/ai/hooks/save-decision/hook.py\" 'claude'",
                            }
                        ],
                    }
                ]
            }
        }
        wrapped = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "AskUserQuestion|request_user_input",
                        "hooks": [
                            {
                                "command": "\"$(git rev-parse --show-toplevel)/scripts/°base/git/hooks/tool_path.sh\" uv run --project \"$(git rev-parse --show-toplevel)/scripts/°base\" python \"$(git rev-parse --show-toplevel)/scripts/°base/ai/hooks/save-decision/hook.py\" 'codex'",
                                "async": True,
                            }
                        ],
                    }
                ]
            }
        }

        merged = hooks._merge(plain, wrapped)
        entries = merged["hooks"]["PostToolUse"]

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["hooks"][0]["async"])

    def test_normalize_native_adds_default_plan_tool_arg(self):
        native = {
            "hooks": {
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 scripts/°base/ai/hooks/save-plan/hook.py",
                            }
                        ]
                    }
                ]
            }
        }

        normalized = hooks._normalize_native(native)
        command = normalized["hooks"]["Stop"][0]["hooks"][0]["command"]

        self.assertTrue(command.endswith("'claude'"))

    def test_render_codex_strips_async(self):
        shared = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 hook.py",
                                "async": True,
                            }
                        ]
                    }
                ]
            }
        }

        rendered = hooks.render_codex_hooks(shared)
        hook = rendered["hooks"]["SessionStart"][0]["hooks"][0]

        self.assertNotIn("async", hook)

    def test_render_copilot_rewrites_tool_arg(self):
        shared = {
            "hooks": {
                "UserPromptSubmit": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 scripts/°base/ai/hooks/save-prompt/hook.py 'claude'",
                            }
                        ]
                    }
                ]
            }
        }

        rendered = hooks.render_copilot_hooks(shared)
        command = rendered["hooks"]["UserPromptSubmit"][0]["hooks"][0]["bash"]

        self.assertIn("'copilot'", command)
        self.assertNotIn("'claude'", command)

    def test_render_copilot_uses_bash_and_timeout_sec(self):
        shared = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 hook.py",
                                "timeout": 5,
                                "statusMessage": "Doing a thing",
                                "async": True,
                            }
                        ]
                    }
                ]
            }
        }

        rendered = hooks.render_copilot_hooks(shared)
        hook = rendered["hooks"]["SessionStart"][0]["hooks"][0]

        self.assertEqual(hook["bash"], "python3 hook.py")
        self.assertNotIn("command", hook)
        self.assertEqual(hook["timeoutSec"], 5)
        self.assertNotIn("timeout", hook)
        self.assertNotIn("statusMessage", hook)
        self.assertNotIn("async", hook)

    def test_render_copilot_top_level_shape_has_version_and_no_extra_keys(self):
        shared = {"hooks": {}, "permissions": {"allow": ["Bash(git status:*)"]}}

        rendered = hooks.render_copilot_hooks(shared)

        self.assertEqual(rendered["version"], 1)
        self.assertEqual(set(rendered.keys()), {"version", "hooks"})

    def test_render_copilot_matches_claude_matcher(self):
        shared = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Write|Edit|ExitPlanMode|create|edit|exit_plan_mode",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 scripts/°base/ai/hooks/save-plan/hook.py 'claude'",
                            }
                        ],
                    }
                ]
            }
        }

        rendered = hooks.render_copilot_hooks(shared)
        entry = rendered["hooks"]["PostToolUse"][0]

        self.assertEqual(entry["matcher"], "Write|Edit|ExitPlanMode|create|edit|exit_plan_mode")
        self.assertIn("'copilot'", entry["hooks"][0]["bash"])

    def test_normalize_native_accepts_copilot_bash_and_timeout_sec(self):
        native = {
            "hooks": {
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "bash": "python3 scripts/°base/ai/hooks/save-plan/hook.py 'copilot'",
                                "timeoutSec": 7,
                            }
                        ]
                    }
                ]
            }
        }

        normalized = hooks._normalize_native(native)
        hook = normalized["hooks"]["Stop"][0]["hooks"][0]

        self.assertIn("'claude'", hook["command"])
        self.assertEqual(hook["timeout"], 7)

    def test_render_claude_keeps_permissions(self):
        shared = {
            "hooks": {},
            "permissions": {"allow": ["Bash(git status:*)"], "deny": ["Read(**/.env*)"]},
        }

        rendered = hooks.render_claude(shared)

        self.assertEqual(rendered["permissions"]["allow"], ["Bash(git status:*)"])
        self.assertEqual(rendered["permissions"]["deny"], ["Read(**/.env*)"])

    def test_render_claude_renders_structured_permission_entries(self):
        shared = {
            "hooks": {},
            "permissions": {
                "allow": [{"type": "bash", "command": "git status:*"}, {"type": "skill", "name": "demo"}],
                "deny": [{"type": "read", "path": "**/.env*"}],
            },
        }

        rendered = hooks.render_claude(shared)

        self.assertEqual(rendered["permissions"]["allow"], ["Bash(git status:*)", "Skill(demo)"])
        self.assertEqual(rendered["permissions"]["deny"], ["Read(**/.env*)"])

    def test_merge_unions_permissions_without_duplicates(self):
        base = {"permissions": {"allow": ["A", "B"], "deny": ["X"]}}
        incoming = {"permissions": {"allow": ["B", "C"], "deny": ["X", "Y"]}}

        merged = hooks._merge(base, incoming)

        self.assertEqual(
            merged["permissions"]["allow"],
            [{"type": "raw", "value": v} for v in ("A", "B", "C")],
        )
        self.assertEqual(
            merged["permissions"]["deny"],
            [{"type": "raw", "value": v} for v in ("X", "Y")],
        )

    def test_merge_replaces_same_hook_identity(self):
        base = {
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"command": "cmd"}], "matcher": "old", "extra": "old"}
                ]
            }
        }
        incoming = {
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"command": "cmd"}], "matcher": "old", "extra": "new"}
                ]
            }
        }

        merged = hooks._merge(base, incoming)

        self.assertEqual(merged["hooks"]["SessionStart"][0]["extra"], "new")

    def test_merge_preserves_missing_hook_fields_for_same_identity(self):
        base = {
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"command": "cmd", "async": True}], "matcher": ""}
                ]
            }
        }
        incoming = {
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"command": "cmd"}], "matcher": ""}
                ]
            }
        }

        merged = hooks._merge(base, incoming)

        self.assertTrue(merged["hooks"]["SessionStart"][0]["hooks"][0]["async"])

    def test_merge_mcp_updates_tools_and_servers_by_name(self):
        base = {"mcp": {"tools": {".env": {"": {"mode": "prefix", "cmd": ["envmcp"]}}}, "servers": {"a": {"type": "http", "url": "https://old"}}}}
        incoming = {"mcp": {"tools": {}, "servers": {"a": {"type": "http", "url": "https://new"}, "b": {"type": "http", "url": "https://b"}}}}

        merged = hooks._merge(base, incoming)

        self.assertEqual(merged["mcp"]["tools"], {".env": {"": {"mode": "prefix", "cmd": ["envmcp"]}}})
        self.assertEqual(merged["mcp"]["servers"]["a"]["url"], "https://new")
        self.assertEqual(merged["mcp"]["servers"]["b"]["url"], "https://b")

    def test_render_claude_emits_enabled_and_disabled_mcp_server_lists(self):
        shared = {
            "hooks": {},
            "mcp": {
                "servers": {
                    "on": {"type": "stdio", "cmd": ["x"]},
                    "off": {"type": "stdio", "cmd": ["y"], "enabled": False},
                }
            },
        }

        rendered = hooks.render_claude(shared)

        self.assertEqual(rendered["enabledMcpjsonServers"], ["on"])
        self.assertEqual(rendered["disabledMcpjsonServers"], ["off"])

    def test_render_claude_omits_mcp_server_lists_when_no_servers(self):
        rendered = hooks.render_claude({"hooks": {}})

        self.assertNotIn("enabledMcpjsonServers", rendered)
        self.assertNotIn("disabledMcpjsonServers", rendered)

    def test_render_claude_populates_empty_bucket_when_all_servers_same_state(self):
        rendered = hooks.render_claude({"hooks": {}, "mcp": {"servers": {"on": {"type": "stdio", "cmd": ["x"]}}}})
        self.assertEqual(rendered["enabledMcpjsonServers"], ["on"])
        self.assertEqual(rendered["disabledMcpjsonServers"], [])

        rendered = hooks.render_claude(
            {"hooks": {}, "mcp": {"servers": {"off": {"type": "stdio", "cmd": ["x"], "enabled": False}}}}
        )
        self.assertEqual(rendered["enabledMcpjsonServers"], [])
        self.assertEqual(rendered["disabledMcpjsonServers"], ["off"])

    def test_normalize_native_upgrades_v1_file_shape(self):
        # Modeled on the pre-95f48bc "plain Claude schema" shape: raw string
        # permissions, flat enabledPlugins, no mcp key, version 1.
        v1_fixture = {
            "version": 1,
            "hooks": {},
            "permissions": {
                "allow": ["Bash(tree:*)", "Skill(demo)"],
                "deny": ["Read(**/.env*)"],
            },
            "enabledPlugins": {"openai-developers@openai-developers": True},
        }

        normalized = hooks._normalize_native(v1_fixture)

        self.assertEqual(normalized["version"], hooks.CURRENT_VERSION)
        self.assertEqual(normalized["version"], 2)
        self.assertEqual(
            normalized["permissions"]["allow"],
            [{"type": "bash", "command": "tree:*"}, {"type": "skill", "name": "demo"}],
        )
        self.assertEqual(normalized["permissions"]["deny"], [{"type": "read", "path": "**/.env*"}])
        self.assertEqual(normalized["plugins"], {"openai-developers@openai-developers": {"enabled": True}})
        self.assertEqual(normalized["mcp"], {"tools": {}, "servers": {}})

    def test_normalize_native_converts_flat_enabled_plugins_to_nested_shape(self):
        normalized = hooks._normalize_native({"enabledPlugins": {"a@m": True, "b@m": False}})
        self.assertEqual(normalized["plugins"], {"a@m": {"enabled": True}, "b@m": {"enabled": False}})

    def test_normalize_native_passes_through_nested_plugins_shape(self):
        normalized = hooks._normalize_native({"plugins": {"a@m": {"enabled": False}}})
        self.assertEqual(normalized["plugins"], {"a@m": {"enabled": False}})

    def test_render_claude_builds_flat_enabled_plugins_from_nested_shape(self):
        rendered = hooks.render_claude({"hooks": {}, "plugins": {"a@m": {"enabled": True}, "b@m": {"enabled": False}}})
        self.assertEqual(rendered["enabledPlugins"], {"a@m": True, "b@m": False})

    def test_skill_overrides_are_normalized_merged_and_rendered_into_claude(self):
        merged = hooks._merge({"skillOverrides": {"a": "off", "b": "off"}}, {"skillOverrides": {"b": "on", "c": "off"}})
        self.assertEqual(merged["skillOverrides"], {"a": "off", "b": "on", "c": "off"})
        self.assertEqual(hooks.render_claude(merged)["skillOverrides"], {"a": "off", "b": "on", "c": "off"})
        self.assertNotIn("skillOverrides", hooks.render_claude({"hooks": {}}))
        self.assertNotIn("skillOverrides", hooks._normalize_native({}))

    def test_enable_only_mcp_servers_only_reach_claude_enabled_lists(self):
        shared = {
            "hooks": {},
            "mcp": {"tools": {}, "servers": {"bugsink": {"enabled": True}, "coolify": {"enabled": False}}},
        }
        rendered = hooks.render_claude(shared)
        self.assertEqual(rendered["enabledMcpjsonServers"], ["bugsink"])
        self.assertEqual(rendered["disabledMcpjsonServers"], ["coolify"])
        mcp_json, skipped = mcp_servers.render_claude_mcp(shared, Path("/repo"))
        self.assertEqual((mcp_json, skipped), ({"mcpServers": {}}, []))
        block, skipped = mcp_servers.render_codex_mcp_block(shared, Path("/repo"))
        self.assertEqual(skipped, [])
        self.assertNotIn("bugsink", block)


class CommandsTests(unittest.TestCase):
    def test_parse_render_round_trip_bash(self):
        entry = commands._parse_claude_permission_entry("Bash(git status:*)")
        self.assertEqual(entry, {"type": "bash", "command": "git status:*"})
        self.assertEqual(commands._render_claude_permission_entry(entry), "Bash(git status:*)")

    def test_render_bash_escapes_literal_parens(self):
        entry = {"type": "bash", "command": 'mv foo ".bar.$(date +%Y-%m-%d).bak"'}
        self.assertEqual(
            commands._render_claude_permission_entry(entry),
            'Bash(mv foo ".bar.$\\(date +%Y-%m-%d\\).bak")',
        )

    def test_parse_bash_unescapes_literal_parens(self):
        entry = commands._parse_claude_permission_entry(
            'Bash(mv foo ".bar.$\\(date +%Y-%m-%d\\).bak")'
        )
        self.assertEqual(entry, {"type": "bash", "command": 'mv foo ".bar.$(date +%Y-%m-%d).bak"'})

    def test_parse_render_round_trip_bash_with_parens(self):
        original = 'Bash(mv foo ".bar.$\\(date +%Y-%m-%d\\).bak")'
        entry = commands._parse_claude_permission_entry(original)
        self.assertEqual(commands._render_claude_permission_entry(entry), original)

    def test_parse_render_round_trip_read(self):
        entry = commands._parse_claude_permission_entry("Read(**/.env*)")
        self.assertEqual(entry, {"type": "read", "path": "**/.env*"})
        self.assertEqual(commands._render_claude_permission_entry(entry), "Read(**/.env*)")

    def test_parse_render_round_trip_skill(self):
        entry = commands._parse_claude_permission_entry("Skill(commit-with-lplp-style)")
        self.assertEqual(entry, {"type": "skill", "name": "commit-with-lplp-style"})
        self.assertEqual(commands._render_claude_permission_entry(entry), "Skill(commit-with-lplp-style)")

    def test_parse_render_round_trip_unknown_tool_uses_pattern_field(self):
        entry = commands._parse_claude_permission_entry("WebFetch(https://example.com)")
        self.assertEqual(entry, {"type": "webfetch", "pattern": "https://example.com"})
        self.assertEqual(commands._render_claude_permission_entry(entry), "WebFetch(https://example.com)")

    def test_parse_render_round_trip_mcp_tool(self):
        entry = commands._parse_claude_permission_entry("mcp__bugsink__list_projects")
        self.assertEqual(entry, {"type": "mcp", "server": "bugsink", "tool": "list_projects"})
        self.assertEqual(commands._render_claude_permission_entry(entry), "mcp__bugsink__list_projects")

    def test_parse_malformed_string_is_lossless_raw(self):
        entry = commands._parse_claude_permission_entry("not-a-tool-call")
        self.assertEqual(entry, {"type": "raw", "value": "not-a-tool-call"})
        self.assertEqual(commands._render_claude_permission_entry(entry), "not-a-tool-call")

    def test_parse_passes_through_existing_object(self):
        entry = {"type": "bash", "command": "tree:*"}
        self.assertIs(commands._parse_claude_permission_entry(entry), entry)

    def test_bash_pattern_to_prefix_strips_colon_wildcard(self):
        self.assertEqual(commands._bash_pattern_to_prefix("git status:*"), ["git", "status"])

    def test_bash_pattern_to_prefix_strips_bare_wildcard(self):
        self.assertEqual(commands._bash_pattern_to_prefix("uv lock *"), ["uv", "lock"])

    def test_bash_pattern_to_prefix_plain_literal(self):
        self.assertEqual(commands._bash_pattern_to_prefix("git branch --show-current"), ["git", "branch", "--show-current"])

    def test_bash_pattern_to_prefix_rejects_substitution(self):
        self.assertIsNone(commands._bash_pattern_to_prefix('echo "exit: $?"'))

    def test_bash_pattern_to_prefix_rejects_compound_commands(self):
        self.assertIsNone(commands._bash_pattern_to_prefix("git add . && rm -rf /"))

    def test_bash_pattern_to_prefix_rejects_env_assignment_prefix(self):
        self.assertIsNone(commands._bash_pattern_to_prefix("GIT_SEQUENCE_EDITOR=/tmp/x.sh git rebase --continue"))


class CodexRulesTests(unittest.TestCase):
    def test_render_codex_rules_allow_and_deny(self):
        shared = {
            "permissions": {
                "allow": [{"type": "bash", "command": "git status:*"}],
                "deny": [{"type": "bash", "command": "rm -rf /"}],
            }
        }

        text = codex_rules.render_codex_rules(shared)

        self.assertIn('prefix_rule(pattern = ["git", "status"], decision = "allow")', text)
        self.assertIn('prefix_rule(pattern = ["rm", "-rf", "/"], decision = "forbidden")', text)

    def test_render_codex_rules_skips_non_bash_and_untranslatable(self):
        shared = {
            "permissions": {
                "allow": [
                    {"type": "skill", "name": "demo"},
                    {"type": "bash", "command": 'echo "exit: $?"'},
                ],
                "deny": [],
            }
        }

        text = codex_rules.render_codex_rules(shared)

        self.assertNotIn("prefix_rule", text)
        self.assertIn("1 command permission(s) could not be translated", text)
        self.assertIn('# {"type": "bash", "command": "echo \\"exit: $?\\""}', text)

    def test_parse_codex_rules_round_trips_generated_output(self):
        shared = {
            "permissions": {
                "allow": [{"type": "bash", "command": "git status:*"}],
                "deny": [{"type": "bash", "command": "rm -rf /"}],
            }
        }
        text = codex_rules.render_codex_rules(shared)

        parsed = codex_rules.parse_codex_rules(text)

        self.assertEqual(parsed["allow"], [{"type": "bash", "command": "git status:*"}])
        self.assertEqual(parsed["deny"], [{"type": "bash", "command": "rm -rf /:*"}])

    def test_parse_codex_rules_skips_prompt_decision_and_bad_input(self):
        text = 'prefix_rule(pattern = ["gh", "pr", "view"], decision = "prompt")\n'
        parsed = codex_rules.parse_codex_rules(text)
        self.assertEqual(parsed, {"allow": [], "deny": []})

        self.assertEqual(codex_rules.parse_codex_rules("not even python(("), {"allow": [], "deny": []})


class CodexTomlTests(unittest.TestCase):
    def test_rewrite_codex_feature_flag(self):
        text = "model = \"gpt-5\"\n[features]\ncodex_hooks = true\n\n[projects]\n"

        rewritten, changed = codex_toml._rewrite_codex_feature_flag(text)

        self.assertTrue(changed)
        self.assertEqual(
            rewritten,
            "model = \"gpt-5\"\n[features]\nhooks = true\n\n[projects]\n",
        )

    def test_rewrite_codex_feature_flag_removes_deprecated_when_hooks_exists(self):
        text = "[features]\nhooks = true\ncodex_hooks = true\n"

        rewritten, changed = codex_toml._rewrite_codex_feature_flag(text)

        self.assertTrue(changed)
        self.assertEqual(rewritten, "[features]\nhooks = true\n")

    def test_migrate_codex_feature_flag_yes_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text("[features]\ncodex_hooks = true\n", encoding="utf-8")
            previous_input = getattr(codex_toml, "input", None)
            codex_toml.input = lambda _prompt: "y"
            out = io.StringIO()
            try:
                with contextlib.redirect_stdout(out):
                    status = codex_toml._migrate_codex_feature_flag(path, True, True)
            finally:
                if previous_input is None:
                    delattr(codex_toml, "input")
                else:
                    codex_toml.input = previous_input

            self.assertEqual(status, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), "[features]\nhooks = true\n")

    def test_migrate_codex_feature_flag_exit_prints_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            original = "[features]\ncodex_hooks = true\n"
            path.write_text(original, encoding="utf-8")
            previous_input = getattr(codex_toml, "input", None)
            codex_toml.input = lambda _prompt: "exit"
            out = io.StringIO()
            try:
                with contextlib.redirect_stdout(out):
                    status = codex_toml._migrate_codex_feature_flag(path, True, True)
            finally:
                if previous_input is None:
                    delattr(codex_toml, "input")
                else:
                    codex_toml.input = previous_input

            self.assertEqual(status, 1)
            self.assertIn(str(path), out.getvalue())
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_parse_render_plugins_round_trip(self):
        text = codex_toml.render_codex_plugins("", {"openai-developers@openai-developers": True})

        parsed = codex_toml.parse_codex_plugins(text)

        self.assertEqual(parsed, {"openai-developers@openai-developers": True})
        self.assertIn('[plugins."openai-developers@openai-developers"]', text)
        self.assertIn("enabled = true", text)

    def test_render_codex_plugins_preserves_unrelated_content(self):
        existing = (
            "model = \"gpt-5.5\"\n"
            "\n"
            "# a comment that must survive\n"
            "[projects.\"/home/user/repo\"]\n"
            "trust_level = \"trusted\"\n"
            "\n"
            "[plugins.\"gmail@openai-curated\"]\n"
            "enabled = false\n"
        )

        rendered = codex_toml.render_codex_plugins(existing, {"gmail@openai-curated": True, "new@marketplace": True})

        self.assertIn("model = \"gpt-5.5\"", rendered)
        self.assertIn("# a comment that must survive", rendered)
        self.assertIn("trust_level = \"trusted\"", rendered)
        self.assertIn('[plugins."new@marketplace"]', rendered)
        parsed = codex_toml.parse_codex_plugins(rendered)
        self.assertEqual(parsed["gmail@openai-curated"], True)
        self.assertEqual(parsed["new@marketplace"], True)

    def test_parse_codex_plugins_ignores_garbage(self):
        self.assertEqual(codex_toml.parse_codex_plugins("not { valid toml"), {})


class McpServersTests(unittest.TestCase):
    GIT_ROOT = Path("/repo")

    def _mcp(self):
        return {
            "tools": {
                ".env": {
                    "": {"mode": "prefix", "cmd": ["npx", "-y", "envmcp", "--env-file", "ai/.env"]},
                    "repo-root": {
                        "mode": "prefix",
                        "cmd": ["npx", "-y", "envmcp", "--env-file", "$(git rev-parse --show-toplevel)/.env"],
                    },
                }
            },
            "servers": {
                "bugsink": {
                    "enabled": True,
                    "type": "stdio",
                    "tools": [".env"],
                    "cmd": ["npx", "-y", "bugsink-mcp"],
                }
            },
        }

    def test_resolve_tool_ref_default_variant(self):
        tools = self._mcp()["tools"]
        self.assertEqual(mcp_servers._resolve_tool_ref(tools, ".env"), ["npx", "-y", "envmcp", "--env-file", "ai/.env"])

    def test_resolve_tool_ref_named_variant(self):
        tools = self._mcp()["tools"]
        resolved = mcp_servers._resolve_tool_ref(tools, ".env@repo-root")
        self.assertIn("$(git rev-parse --show-toplevel)/.env", resolved)

    def test_resolve_tool_ref_missing_tool_or_variant_is_none(self):
        tools = self._mcp()["tools"]
        self.assertIsNone(mcp_servers._resolve_tool_ref(tools, "nope"))
        self.assertIsNone(mcp_servers._resolve_tool_ref(tools, ".env@nope"))

    def test_resolve_server_argv_prepends_tools_left_to_right_and_substitutes_git_root(self):
        mcp = self._mcp()
        mcp["servers"]["bugsink"]["tools"] = [".env@repo-root"]
        argv = mcp_servers._resolve_server_argv(mcp, mcp["servers"]["bugsink"], self.GIT_ROOT)
        self.assertEqual(
            argv,
            ["npx", "-y", "envmcp", "--env-file", "/repo/.env", "npx", "-y", "bugsink-mcp"],
        )

    def test_resolve_server_argv_none_on_unresolvable_tool(self):
        mcp = self._mcp()
        mcp["servers"]["bugsink"]["tools"] = ["missing"]
        self.assertIsNone(mcp_servers._resolve_server_argv(mcp, mcp["servers"]["bugsink"], self.GIT_ROOT))

    def test_resolve_server_argv_allows_tools_only_server_with_no_cmd(self):
        mcp = self._mcp()
        server = {"tools": [".env"]}
        self.assertEqual(
            mcp_servers._resolve_server_argv(mcp, server, self.GIT_ROOT),
            ["npx", "-y", "envmcp", "--env-file", "ai/.env"],
        )

    def test_resolve_server_argv_none_when_combined_argv_empty(self):
        mcp = self._mcp()
        self.assertIsNone(mcp_servers._resolve_server_argv(mcp, {}, self.GIT_ROOT))

    def test_extract_tools_from_cmd_matches_single_tool_prefix(self):
        tools = self._mcp()["tools"]
        cmd = ["npx", "-y", "envmcp", "--env-file", "ai/.env", "npx", "-y", "bugsink-mcp"]
        refs, remaining = mcp_servers.extract_tools_from_cmd(tools, cmd, self.GIT_ROOT)
        self.assertEqual(refs, [".env"])
        self.assertEqual(remaining, ["npx", "-y", "bugsink-mcp"])

    def test_extract_tools_from_cmd_chains_multiple_tools(self):
        tools = {
            "wrapA": {"": {"mode": "prefix", "cmd": ["a1", "a2"]}},
            "wrapB": {"": {"mode": "prefix", "cmd": ["b1"]}},
        }
        cmd = ["a1", "a2", "b1", "server-bin"]
        refs, remaining = mcp_servers.extract_tools_from_cmd(tools, cmd, self.GIT_ROOT)
        self.assertEqual(refs, ["wrapA", "wrapB"])
        self.assertEqual(remaining, ["server-bin"])

    def test_extract_tools_from_cmd_no_match_returns_full_cmd_unchanged(self):
        tools = self._mcp()["tools"]
        cmd = ["totally", "unrelated", "cmd"]
        refs, remaining = mcp_servers.extract_tools_from_cmd(tools, cmd, self.GIT_ROOT)
        self.assertEqual(refs, [])
        self.assertEqual(remaining, cmd)

    def test_extract_tools_from_cmd_prefers_longest_match_on_ambiguous_prefix(self):
        tools = {
            "short": {"": {"mode": "prefix", "cmd": ["x"]}},
            "long": {"": {"mode": "prefix", "cmd": ["x", "y"]}},
        }
        refs, remaining = mcp_servers.extract_tools_from_cmd(tools, ["x", "y", "z"], self.GIT_ROOT)
        self.assertEqual(refs, ["long"])
        self.assertEqual(remaining, ["z"])

    def test_extract_tools_from_cmd_selects_variant_and_substitutes_git_root(self):
        tools = self._mcp()["tools"]
        cmd = ["npx", "-y", "envmcp", "--env-file", "/repo/.env", "npx", "-y", "bugsink-mcp"]
        refs, remaining = mcp_servers.extract_tools_from_cmd(tools, cmd, self.GIT_ROOT)
        self.assertEqual(refs, [".env@repo-root"])
        self.assertEqual(remaining, ["npx", "-y", "bugsink-mcp"])

    def test_reconstruct_stdio_entry_falls_back_to_flat_cmd_when_no_match(self):
        mcp = self._mcp()
        cmd = ["echo", "hi"]
        entry = mcp_servers._reconstruct_stdio_entry(mcp, cmd, True, self.GIT_ROOT)
        self.assertEqual(entry, {"enabled": True, "type": "stdio", "cmd": ["echo", "hi"]})

    def test_reconstruct_stdio_entry_extracts_tools_and_keeps_enabled(self):
        mcp = self._mcp()
        cmd = ["npx", "-y", "envmcp", "--env-file", "ai/.env", "npx", "-y", "bugsink-mcp"]
        entry = mcp_servers._reconstruct_stdio_entry(mcp, cmd, False, self.GIT_ROOT)
        self.assertEqual(entry, {"enabled": False, "type": "stdio", "tools": [".env"], "cmd": ["npx", "-y", "bugsink-mcp"]})

    def test_render_claude_mcp_stdio_and_skips_unresolvable(self):
        mcp = self._mcp()
        mcp["servers"]["broken"] = {"type": "stdio", "tools": ["missing"], "cmd": ["x"]}
        data, skipped = mcp_servers.render_claude_mcp({"mcp": mcp}, self.GIT_ROOT)

        self.assertEqual(skipped, ["broken"])
        entry = data["mcpServers"]["bugsink"]
        self.assertEqual(entry["type"], "stdio")
        self.assertEqual(entry["command"], "npx")
        self.assertEqual(entry["args"], ["-y", "envmcp", "--env-file", "ai/.env", "npx", "-y", "bugsink-mcp"])
        self.assertNotIn("enabled", entry)
        self.assertNotIn("tools", entry)

    def test_render_claude_mcp_http(self):
        shared = {"mcp": {"tools": {}, "servers": {"remote": {"type": "http", "url": "https://mcp.example.com", "headers": {"X": "1"}}}}}
        data, skipped = mcp_servers.render_claude_mcp(shared, self.GIT_ROOT)
        self.assertEqual(skipped, [])
        self.assertEqual(data["mcpServers"]["remote"], {"type": "http", "url": "https://mcp.example.com", "headers": {"X": "1"}})

    def test_parse_claude_mcp_round_trip(self):
        shared = {"mcp": self._mcp()}
        rendered, _ = mcp_servers.render_claude_mcp(shared, self.GIT_ROOT)

        parsed = mcp_servers.parse_claude_mcp(rendered)

        self.assertEqual(
            parsed["bugsink"],
            {
                "type": "stdio",
                "cmd": ["npx", "-y", "envmcp", "--env-file", "ai/.env", "npx", "-y", "bugsink-mcp"],
            },
        )
        self.assertNotIn("tools", parsed["bugsink"])

    def test_render_codex_mcp_block_and_parse_round_trip(self):
        shared = {"mcp": self._mcp()}
        block, skipped = mcp_servers.render_codex_mcp_block(shared, self.GIT_ROOT)

        self.assertEqual(skipped, [])
        self.assertIn(mcp_servers.MCP_TOML_BEGIN_MARKER, block)
        self.assertIn(mcp_servers.MCP_TOML_END_MARKER, block)
        self.assertIn('[mcp_servers."bugsink"]', block)

        parsed = mcp_servers.parse_codex_mcp_toml(block)
        self.assertEqual(
            parsed["bugsink"],
            {
                "type": "stdio",
                "cmd": ["npx", "-y", "envmcp", "--env-file", "ai/.env", "npx", "-y", "bugsink-mcp"],
                "enabled": True,
            },
        )

    def test_parse_codex_mcp_toml_ignores_garbage(self):
        self.assertEqual(mcp_servers.parse_codex_mcp_toml("not { valid toml"), {})

    def test_render_codex_mcp_block_includes_tool_approval_and_disabled_tools(self):
        shared = {
            "mcp": self._mcp(),
            "permissions": {
                "allow": [{"type": "mcp", "server": "bugsink", "tool": "list_projects"}],
                "deny": [{"type": "mcp", "server": "bugsink", "tool": "delete_project"}],
            },
        }
        block, skipped = mcp_servers.render_codex_mcp_block(shared, self.GIT_ROOT)

        self.assertEqual(skipped, [])
        self.assertIn('disabled_tools = ["delete_project"]', block)
        self.assertIn('[mcp_servers."bugsink".tools."list_projects"]', block)
        self.assertIn('approval_mode = "auto"', block)

    def test_parse_codex_mcp_tool_permissions_round_trip(self):
        shared = {
            "mcp": self._mcp(),
            "permissions": {
                "allow": [{"type": "mcp", "server": "bugsink", "tool": "list_projects"}],
                "deny": [{"type": "mcp", "server": "bugsink", "tool": "delete_project"}],
            },
        }
        block, _ = mcp_servers.render_codex_mcp_block(shared, self.GIT_ROOT)

        parsed = mcp_servers.parse_codex_mcp_tool_permissions(block)

        self.assertEqual(parsed["allow"], [{"type": "mcp", "server": "bugsink", "tool": "list_projects"}])
        self.assertEqual(parsed["deny"], [{"type": "mcp", "server": "bugsink", "tool": "delete_project"}])

    def test_parse_codex_mcp_tool_permissions_ignores_garbage(self):
        self.assertEqual(mcp_servers.parse_codex_mcp_tool_permissions("not { valid toml"), {"allow": [], "deny": []})

    def test_insert_or_replace_block_appends_when_absent(self):
        text = 'model = "gpt-5.5"\n'
        result = mcp_servers.insert_or_replace_block(text, "# BEGIN", "# END", "# BEGIN\nnew content\n# END\n")

        self.assertIn('model = "gpt-5.5"', result)
        self.assertIn("new content", result)

    def test_insert_or_replace_block_replaces_only_marked_region(self):
        text = (
            "# a comment that must survive\n"
            "# BEGIN\n"
            "old content\n"
            "# END\n"
            "trailing = true\n"
        )
        result = mcp_servers.insert_or_replace_block(text, "# BEGIN", "# END", "# BEGIN\nnew content\n# END\n")

        self.assertIn("# a comment that must survive", result)
        self.assertIn("trailing = true", result)
        self.assertIn("new content", result)
        self.assertNotIn("old content", result)

    def test_plugins_and_mcp_blocks_coexist_in_one_config_toml(self):
        base_text = codex_toml.render_codex_plugins("", {"demo@marketplace": True})
        block, _ = mcp_servers.render_codex_mcp_block({"mcp": self._mcp()}, self.GIT_ROOT)
        final_text = mcp_servers.insert_or_replace_block(
            base_text, mcp_servers.MCP_TOML_BEGIN_MARKER, mcp_servers.MCP_TOML_END_MARKER, block
        )

        self.assertEqual(codex_toml.parse_codex_plugins(final_text), {"demo@marketplace": True})
        self.assertIn("bugsink", mcp_servers.parse_codex_mcp_toml(final_text))


class CliLoadLayerTests(unittest.TestCase):
    def test_load_layer_preserves_shared_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"version": 1, "hooks": {}, "permissions": {"allow": [], "deny": []}, "download_link": {"ide": "pycharm"}}',
                encoding="utf-8",
            )

            shared = cli._load_layer(shared_path, claude_path, codex_path)

            self.assertEqual(shared["download_link"], {"ide": "pycharm"})
            self.assertNotIn("download_link", hooks.render_claude(shared))

    def test_load_layer_injects_shared_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            shared_path.parent.mkdir(parents=True)
            shared_path.write_text('{"version": 2}', encoding="utf-8")

            shared = cli._load_layer(
                shared_path,
                root / ".claude" / "settings.json",
                root / ".codex" / "hooks.json",
            )

            self.assertEqual(shared["$schema"], "./settings.schema.json")
            self.assertNotIn("$schema", hooks.render_claude(shared))

    def test_load_layer_injects_local_schema_and_allows_other_pre_commit_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.local.json"
            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"pre_commit": {"other": {"enabled": false}}}',
                encoding="utf-8",
            )

            shared = cli._load_layer(
                shared_path,
                root / ".claude" / "settings.local.json",
                root / ".codex" / "hooks.local.json",
            )

            self.assertEqual(shared["$schema"], "./settings-local.schema.json")
            self.assertEqual(shared["pre_commit"], {"other": {"enabled": False}})
            self.assertNotIn("pre_commit", hooks.render_codex_hooks(shared))

    def test_load_layer_rejects_local_yarn_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.local.json"
            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"pre_commit": {"yarn@4": {"enabled": false}}}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "shared repository policy"):
                cli._load_layer(
                    shared_path,
                    root / ".claude" / "settings.local.json",
                    root / ".codex" / "hooks.local.json",
                )

    def test_load_layer_does_not_leak_legacy_enabled_plugins_as_extra_key(self):
        # Regression test: "enabledPlugins" (the deprecated v1 name for
        # "plugins") must not survive as an opaque extra key alongside the
        # new "plugins" key once migrated.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"version": 1, "hooks": {}, "permissions": {"allow": [], "deny": []}, '
                '"enabledPlugins": {"a@m": true}}',
                encoding="utf-8",
            )

            shared = cli._load_layer(shared_path, claude_path, codex_path)

            self.assertEqual(shared["plugins"], {"a@m": {"enabled": True}})
            self.assertNotIn("enabledPlugins", shared)
            self.assertNotIn("download_link", hooks.render_codex_hooks(shared))

    def test_load_layer_merges_hand_edited_codex_rules_and_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            rules_path = root / ".codex" / "rules" / "generated.rules"
            config_path = root / ".codex" / "config.toml"

            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"version": 1, "hooks": {}, "permissions": {"allow": [], "deny": []}, "enabledPlugins": {}}',
                encoding="utf-8",
            )
            rules_path.parent.mkdir(parents=True)
            rules_path.write_text(
                'prefix_rule(pattern = ["tree"], decision = "allow")\n',
                encoding="utf-8",
            )
            config_path.write_text(
                '[plugins."hand-added@marketplace"]\nenabled = true\n',
                encoding="utf-8",
            )

            shared = cli._load_layer(shared_path, claude_path, codex_path, rules_path, config_path)

            self.assertIn({"type": "bash", "command": "tree:*"}, shared["permissions"]["allow"])
            self.assertEqual(shared["plugins"], {"hand-added@marketplace": {"enabled": True}})

            claude = hooks.render_claude(shared)
            self.assertIn("Bash(tree:*)", claude["permissions"]["allow"])

    def test_load_layer_merges_hand_edited_mcp_tool_approval_and_is_stable_on_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            config_path = root / ".codex" / "config.toml"

            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"version": 1, "hooks": {}, "permissions": {"allow": [], "deny": []}, "enabledPlugins": {}}',
                encoding="utf-8",
            )
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                '[mcp_servers.bugsink]\ncommand = "npx"\nargs = ["-y", "bugsink-mcp"]\nenabled = true\n'
                '\n[mcp_servers.bugsink.tools.list_projects]\napproval_mode = "auto"\n',
                encoding="utf-8",
            )

            shared = cli._load_layer(shared_path, claude_path, codex_path, None, config_path)

            self.assertIn(
                {"type": "mcp", "server": "bugsink", "tool": "list_projects"},
                shared["permissions"]["allow"],
            )

            shared_path.write_text(json.dumps(shared), encoding="utf-8")
            shared_again = cli._load_layer(shared_path, claude_path, codex_path, None, config_path)
            self.assertEqual(shared_again["permissions"]["allow"], shared["permissions"]["allow"])

    def test_load_layer_merges_hand_added_claude_mcp_server_as_flat_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            mcp_path = root / ".mcp.json"

            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"version": 1, "hooks": {}, "permissions": {"allow": [], "deny": []}}',
                encoding="utf-8",
            )
            mcp_path.write_text(
                json.dumps({"mcpServers": {"handadded": {"type": "stdio", "command": "echo", "args": ["hi"]}}}),
                encoding="utf-8",
            )

            shared = cli._load_layer(shared_path, claude_path, codex_path, claude_mcp_path=mcp_path)

            server = shared["mcp"]["servers"]["handadded"]
            self.assertEqual(server["cmd"], ["echo", "hi"])
            self.assertNotIn("tools", server)

    def test_load_layer_keeps_authored_tools_form_when_native_mcp_matches_resolved_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            mcp_path = root / ".mcp.json"

            shared_path.parent.mkdir(parents=True)
            shared_json = {
                "version": 1,
                "hooks": {},
                "permissions": {"allow": [], "deny": []},
                "mcp": {
                    "tools": {".env": {"": {"mode": "prefix", "cmd": ["envmcp", "--env-file", "ai/.env"]}}},
                    "servers": {"bugsink": {"enabled": True, "type": "stdio", "tools": [".env"], "cmd": ["bugsink-mcp"]}},
                },
            }
            shared_path.write_text(json.dumps(shared_json), encoding="utf-8")
            rendered, _ = mcp_servers.render_claude_mcp(shared_json, Path.cwd())
            mcp_path.write_text(json.dumps(rendered), encoding="utf-8")

            shared = cli._load_layer(shared_path, claude_path, codex_path, claude_mcp_path=mcp_path)

            self.assertEqual(shared["mcp"]["servers"]["bugsink"]["tools"], [".env"])

    def test_load_layer_merges_codex_mcp_enabled_flag_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            config_path = root / ".codex" / "config.toml"

            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "hooks": {},
                        "permissions": {"allow": [], "deny": []},
                        "mcp": {"tools": {}, "servers": {"demo": {"enabled": True, "type": "stdio", "cmd": ["echo", "hi"]}}},
                    }
                ),
                encoding="utf-8",
            )
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                '[mcp_servers."demo"]\ncommand = "echo"\nargs = ["hi"]\nenabled = false\n',
                encoding="utf-8",
            )

            shared = cli._load_layer(shared_path, claude_path, codex_path, codex_config_path=config_path)

            self.assertEqual(shared["mcp"]["servers"]["demo"]["enabled"], False)

    def test_load_layer_preserves_authored_tools_when_native_enabled_flag_only_changes(self):
        # Regression test for the real drift observed in this repo: an
        # authored tools-based, disabled server survives a native round-trip
        # through both `.mcp.json` (which structurally has no `enabled`
        # concept and used to fabricate `True`) and `.codex/config.toml`
        # (which carries the real, unchanged `enabled: False`). `.mcp.json`
        # is written after `.codex/config.toml` in a real sync run, so it
        # reliably has the later mtime — reproduced here explicitly.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            config_path = root / ".codex" / "config.toml"
            mcp_path = root / ".mcp.json"

            shared_path.parent.mkdir(parents=True)
            shared_json = {
                "version": 1,
                "hooks": {},
                "permissions": {"allow": [], "deny": []},
                "mcp": {
                    "tools": {".env": {"": {"mode": "prefix", "cmd": ["npx", "-y", "envmcp", "--env-file", "ai/.env"]}}},
                    "servers": {
                        "bugsink": {"enabled": False, "type": "stdio", "tools": [".env"], "cmd": ["npx", "-y", "bugsink-mcp"]}
                    },
                },
            }
            shared_path.write_text(json.dumps(shared_json), encoding="utf-8")

            block, _ = mcp_servers.render_codex_mcp_block(shared_json, Path.cwd())
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(block, encoding="utf-8")

            rendered, _ = mcp_servers.render_claude_mcp(shared_json, Path.cwd())
            mcp_path.write_text(json.dumps(rendered), encoding="utf-8")

            now = time.time()
            os.utime(config_path, (now - 1, now - 1))
            os.utime(mcp_path, (now, now))

            shared = cli._load_layer(
                shared_path, claude_path, codex_path, codex_config_path=config_path, claude_mcp_path=mcp_path
            )

            server = shared["mcp"]["servers"]["bugsink"]
            self.assertEqual(server["enabled"], False)
            self.assertEqual(server["tools"], [".env"])
            self.assertEqual(server["cmd"], ["npx", "-y", "bugsink-mcp"])

    def test_load_layer_reconstructs_tools_when_native_cmd_content_genuinely_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            config_path = root / ".codex" / "config.toml"

            shared_path.parent.mkdir(parents=True)
            shared_json = {
                "version": 1,
                "hooks": {},
                "permissions": {"allow": [], "deny": []},
                "mcp": {
                    "tools": {".env": {"": {"mode": "prefix", "cmd": ["npx", "-y", "envmcp", "--env-file", "ai/.env"]}}},
                    "servers": {
                        "bugsink": {"enabled": True, "type": "stdio", "tools": [".env"], "cmd": ["npx", "-y", "bugsink-mcp"]}
                    },
                },
            }
            shared_path.write_text(json.dumps(shared_json), encoding="utf-8")

            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                '[mcp_servers."bugsink"]\n'
                "enabled = true\n"
                'command = "npx"\n'
                'args = ["-y", "envmcp", "--env-file", "ai/.env", "npx", "-y", "bugsink-mcp-v2"]\n',
                encoding="utf-8",
            )

            shared = cli._load_layer(shared_path, claude_path, codex_path, codex_config_path=config_path)

            server = shared["mcp"]["servers"]["bugsink"]
            self.assertEqual(server["tools"], [".env"])
            self.assertEqual(server["cmd"], ["npx", "-y", "bugsink-mcp-v2"])
            self.assertEqual(server["enabled"], True)

    def test_load_layer_stores_flat_cmd_when_no_tool_prefix_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            config_path = root / ".codex" / "config.toml"

            shared_path.parent.mkdir(parents=True)
            shared_json = {
                "version": 1,
                "hooks": {},
                "permissions": {"allow": [], "deny": []},
                "mcp": {
                    "tools": {".env": {"": {"mode": "prefix", "cmd": ["npx", "-y", "envmcp", "--env-file", "ai/.env"]}}},
                    "servers": {
                        "bugsink": {"enabled": True, "type": "stdio", "tools": [".env"], "cmd": ["npx", "-y", "bugsink-mcp"]}
                    },
                },
            }
            shared_path.write_text(json.dumps(shared_json), encoding="utf-8")

            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                '[mcp_servers."bugsink"]\nenabled = true\ncommand = "totally-different"\nargs = ["binary"]\n',
                encoding="utf-8",
            )

            shared = cli._load_layer(shared_path, claude_path, codex_path, codex_config_path=config_path)

            server = shared["mcp"]["servers"]["bugsink"]
            self.assertNotIn("tools", server)
            self.assertEqual(server["cmd"], ["totally-different", "binary"])

    def test_load_layer_claude_only_source_does_not_reset_enabled_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            mcp_path = root / ".mcp.json"

            shared_path.parent.mkdir(parents=True)
            shared_json = {
                "version": 1,
                "hooks": {},
                "permissions": {"allow": [], "deny": []},
                "mcp": {"tools": {}, "servers": {"demo": {"enabled": False, "type": "stdio", "cmd": ["echo", "hi"]}}},
            }
            shared_path.write_text(json.dumps(shared_json), encoding="utf-8")
            mcp_path.write_text(
                json.dumps({"mcpServers": {"demo": {"type": "stdio", "command": "echo", "args": ["hi"]}}}),
                encoding="utf-8",
            )

            shared = cli._load_layer(shared_path, claude_path, codex_path, claude_mcp_path=mcp_path)

            self.assertEqual(shared["mcp"]["servers"]["demo"]["enabled"], False)


class CliApplyOrCheckTests(unittest.TestCase):
    def test_apply_or_check_writes_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            rules_path = root / ".codex" / "rules" / "generated.rules"
            config_path = root / ".codex" / "config.toml"

            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"version": 1, "hooks": {}, '
                '"permissions": {"allow": [{"type": "bash", "command": "tree:*"}], "deny": []}, '
                '"enabledPlugins": {"demo@marketplace": true}}',
                encoding="utf-8",
            )

            changed = cli._apply_or_check(shared_path, claude_path, codex_path, True, rules_path, config_path)

            self.assertIn(str(rules_path), changed)
            self.assertIn(str(config_path), changed)
            self.assertTrue(rules_path.is_file())
            self.assertTrue(config_path.is_file())
            self.assertIn('prefix_rule(pattern = ["tree"], decision = "allow")', rules_path.read_text(encoding="utf-8"))
            self.assertIn('[plugins."demo@marketplace"]', config_path.read_text(encoding="utf-8"))

            second_pass = cli._apply_or_check(shared_path, claude_path, codex_path, True, rules_path, config_path)
            self.assertEqual(second_pass, [])

    def test_content_change_preserves_existing_native_key_order(self):
        # Regression test: `render_claude` always builds its result dict in a
        # fixed key order (hooks, permissions, enabledPlugins, ...). Without
        # preserving the existing file's order, a single unrelated content
        # change (e.g. one new permission) would reorder every top-level key
        # in `.claude/settings.json` and turn a one-line diff into a
        # whole-file rewrite.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            rules_path = root / ".codex" / "rules" / "generated.rules"
            config_path = root / ".codex" / "config.toml"

            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"version": 1, "hooks": {}, '
                '"permissions": {"allow": [{"type": "bash", "command": "tree:*"}], "deny": []}, '
                '"enabledPlugins": {"demo@marketplace": true}}',
                encoding="utf-8",
            )

            claude_path.parent.mkdir(parents=True)
            claude_path.write_text(
                '{"permissions": {"allow": ["Bash(tree:*)"], "deny": []}, '
                '"enabledPlugins": {"demo@marketplace": true}, "hooks": {}}',
                encoding="utf-8",
            )

            shared_path.write_text(
                '{"version": 1, "hooks": {}, '
                '"permissions": {"allow": [{"type": "bash", "command": "tree:*"}, '
                '{"type": "bash", "command": "ls:*"}], "deny": []}, '
                '"enabledPlugins": {"demo@marketplace": true}}',
                encoding="utf-8",
            )

            cli._apply_or_check(shared_path, claude_path, codex_path, True, rules_path, config_path)

            claude = json.loads(claude_path.read_text(encoding="utf-8"))
            self.assertEqual(list(claude.keys()), ["permissions", "enabledPlugins", "hooks"])

    def test_exact_command_without_wildcard_does_not_duplicate_across_runs(self):
        # Regression test: `render_codex_rules` always emits a prefix rule (no
        # exact-match concept in Codex), so an exact Claude command like
        # "yarn" comes back out of `parse_codex_rules` as "yarn:*" — a
        # different-looking string. Reading that back naively as a "new"
        # permission would duplicate it, growing the list on every run.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            rules_path = root / ".codex" / "rules" / "generated.rules"
            config_path = root / ".codex" / "config.toml"

            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                '{"version": 1, "hooks": {}, '
                '"permissions": {"allow": [{"type": "bash", "command": "yarn"}], "deny": []}, '
                '"enabledPlugins": {}}',
                encoding="utf-8",
            )

            for _ in range(3):
                cli._apply_or_check(shared_path, claude_path, codex_path, True, rules_path, config_path)

            shared = json.loads(shared_path.read_text(encoding="utf-8"))
            self.assertEqual(shared["permissions"]["allow"], [{"type": "bash", "command": "yarn"}])
            claude = json.loads(claude_path.read_text(encoding="utf-8"))
            self.assertEqual(claude["permissions"]["allow"], ["Bash(yarn)"])

    def test_mcp_json_and_codex_toml_are_written_and_idempotent_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared_path = root / "ai" / "settings" / "settings.json"
            claude_path = root / ".claude" / "settings.json"
            codex_path = root / ".codex" / "hooks.json"
            config_path = root / ".codex" / "config.toml"
            mcp_path = root / ".mcp.json"

            shared_path.parent.mkdir(parents=True)
            shared_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "hooks": {},
                        "permissions": {"allow": [], "deny": []},
                        "mcp": {
                            "tools": {".env": {"": {"mode": "prefix", "cmd": ["envmcp", "--env-file", "ai/.env"]}}},
                            "servers": {
                                "bugsink": {"enabled": True, "type": "stdio", "tools": [".env"], "cmd": ["bugsink-mcp"]}
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            changed = cli._apply_or_check(
                shared_path, claude_path, codex_path, True, codex_config_path=config_path, claude_mcp_path=mcp_path
            )

            self.assertIn(str(mcp_path), changed)
            self.assertIn(str(config_path), changed)
            mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
            self.assertEqual(mcp_data["mcpServers"]["bugsink"]["command"], "envmcp")
            self.assertIn('[mcp_servers."bugsink"]', config_path.read_text(encoding="utf-8"))
            claude = json.loads(claude_path.read_text(encoding="utf-8"))
            self.assertEqual(claude["enabledMcpjsonServers"], ["bugsink"])

            for _ in range(3):
                second_pass = cli._apply_or_check(
                    shared_path, claude_path, codex_path, True, codex_config_path=config_path, claude_mcp_path=mcp_path
                )
                self.assertEqual(second_pass, [])

            shared = json.loads(shared_path.read_text(encoding="utf-8"))
            self.assertEqual(shared["mcp"]["servers"]["bugsink"]["tools"], [".env"])


class SkillsTests(unittest.TestCase):
    @contextlib.contextmanager
    def patched_skill_paths(self, root: Path):
        names = [
            "SHARED_SKILLS",
            "AGENTS_SKILLS",
            "CLAUDE_SKILLS",
            "CLAUDE_COMMANDS",
            "CODEX_COMMANDS",
        ]
        previous = {name: getattr(paths, name) for name in names}
        paths.SHARED_SKILLS = root / "ai" / "skills"
        paths.AGENTS_SKILLS = root / ".agents" / "skills"
        paths.CLAUDE_SKILLS = root / ".claude" / "skills"
        paths.CLAUDE_COMMANDS = root / ".claude" / "commands"
        paths.CODEX_COMMANDS = root / ".codex" / "commands"
        try:
            yield
        finally:
            for name, value in previous.items():
                setattr(paths, name, value)

    def test_sync_skills_preserves_shared_source_over_newer_claude_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared = root / "ai" / "skills" / "demo" / "SKILL.md"
            shared.parent.mkdir(parents=True)
            shared.write_text(
                "---\n"
                "name: demo\n"
                "description: Old shared source.\n"
                "---\n\n"
                "Old body.\n",
                encoding="utf-8",
            )

            claude_skill = root / ".claude" / "skills" / "demo" / "SKILL.md"
            claude_skill.parent.mkdir(parents=True)
            claude_skill.write_text(
                "---\n"
                "name: demo\n"
                "description: New Claude skill.\n"
                "---\n\n"
                "New body.\n",
                encoding="utf-8",
            )
            os.utime(claude_skill, (shared.stat().st_mtime + 10, shared.stat().st_mtime + 10))

            with self.patched_skill_paths(root):
                skills._sync_skills(True)

            shared_text = shared.read_text(encoding="utf-8")
            self.assertIn("Old shared source.", shared_text)
            self.assertIn("Old body.", shared_text)
            self.assertNotIn("New Claude skill.", shared_text)
            self.assertNotIn("New body.", shared_text)
            # `_sync_skills` symlinks the whole skill directory (not each file
            # individually) so multi-file skills mirror completely.
            self.assertTrue(claude_skill.parent.is_symlink())
            self.assertEqual(claude_skill.resolve(), shared.resolve())

    def test_sync_skills_imports_claude_skill_when_shared_source_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared = root / "ai" / "skills" / "demo" / "SKILL.md"
            claude_skill = root / ".claude" / "skills" / "demo" / "SKILL.md"
            claude_skill.parent.mkdir(parents=True)
            claude_skill.write_text(
                "---\n"
                "name: demo\n"
                "description: Claude skill.\n"
                "---\n\n"
                "Claude body.\n",
                encoding="utf-8",
            )

            with self.patched_skill_paths(root):
                skills._sync_skills(True)

            shared_text = shared.read_text(encoding="utf-8")
            self.assertIn("Claude skill.", shared_text)
            self.assertIn("Claude body.", shared_text)
            self.assertTrue(claude_skill.parent.is_symlink())
            self.assertEqual(claude_skill.resolve(), shared.resolve())


class JsonIoTests(unittest.TestCase):
    def test_write_json_compacts_permission_entries_one_per_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            data = {
                "permissions": {
                    "allow": [{"type": "bash", "command": "tree:*"}, {"type": "skill", "name": "demo"}],
                    "deny": [],
                }
            }
            json_io._write_json(path, data)
            text = path.read_text(encoding="utf-8")
            self.assertIn('{"type": "bash", "command": "tree:*"}', text)
            self.assertIn('{"type": "skill", "name": "demo"}', text)
            self.assertEqual(json.loads(text), data)

    def test_write_json_compacts_cmd_arrays_single_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            data = {"mcp": {"servers": {"bugsink": {"type": "stdio", "cmd": ["npx", "-y", "bugsink-mcp"]}}}}
            json_io._write_json(path, data)
            text = path.read_text(encoding="utf-8")
            self.assertIn('"cmd": ["npx", "-y", "bugsink-mcp"]', text)
            self.assertEqual(json.loads(text), data)

    def test_write_json_puts_enabled_first_at_any_depth(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            data = {"mcp": {"servers": {"bugsink": {"type": "stdio", "cmd": ["x"], "enabled": False}}}}
            json_io._write_json(path, data)
            text = path.read_text(encoding="utf-8")
            server_block = text[text.index('"bugsink"'):]
            self.assertLess(server_block.index('"enabled"'), server_block.index('"type"'))
            self.assertEqual(json.loads(text), data)

    def test_write_json_normal_dict_stays_one_key_per_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            data = {"hooks": {}, "version": 2}
            json_io._write_json(path, data)
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text, '{\n  "hooks": {},\n  "version": 2\n}\n')


if __name__ == "__main__":
    unittest.main()
