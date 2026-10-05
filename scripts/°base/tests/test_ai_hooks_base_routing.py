from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]


def _encode_project_path(p: Path) -> str:
    """Replicate Claude Code's project-dir encoding: all non-alphanumeric chars → '-'."""
    return re.sub(r"[^a-zA-Z0-9]", "-", str(p))
PROMPT_HOOK = ROOT / "scripts" / "°base" / "ai" / "hooks" / "save-prompt" / "hook.py"
PLAN_HOOK = ROOT / "scripts" / "°base" / "ai" / "hooks" / "save-plan" / "hook.py"
MEMORY_HOOK = ROOT / "scripts" / "°base" / "ai" / "hooks" / "record-memory" / "hook.py"
CODEX_MEMORY_HOOK = ROOT / "scripts" / "°base" / "ai" / "hooks" / "record-codex-memory" / "hook.py"
DECISION_HOOK = ROOT / "scripts" / "°base" / "ai" / "hooks" / "save-decision" / "hook.py"
COMPACT_PROMPT_HOOK = ROOT / "scripts" / "°base" / "ai" / "hooks" / "save-compact-prompt" / "hook.py"
COMMAND_DECISION_HOOK = ROOT / "scripts" / "°base" / "ai" / "hooks" / "save-command-decision" / "hook.py"


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def init_repo(repo: Path, origin: str) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "tester@example.com")
    run_git(repo, "config", "user.name", "Test User")
    run_git(repo, "remote", "add", "origin", origin)
    (repo / "README.md").write_text("test repo\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "init")


def run_hook(
    repo: Path,
    hook: Path,
    payload: dict,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(repo.resolve())
    # Don't let this test process's own (possibly Copilot CLI) ambient
    # environment leak into simulated hook invocations: tests exercise
    # specific tool identities via CLI args/payloads and must not be skipped
    # by the cross-tool-duplicate guard just because the *test runner*
    # happens to be running under Copilot CLI.
    env.pop("COPILOT_CLI", None)
    env.pop("COPILOT_AGENT_SESSION_ID", None)
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [sys.executable, str(hook), *args],
        cwd=repo,
        env=env,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"hook failed with {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def last_subject(repo: Path) -> str:
    return run_git(repo, "log", "-1", "--pretty=%s").stdout.strip()


CODEX_FORWARDED_PLAN_PREFIX = (
    "A previous agent produced the plan below to accomplish the user's task. "
    "Implement the plan in a fresh context. Treat the plan as the source of user intent, "
    "re-read files as needed, and carry the work through implementation and verification."
)


def long_plan(title: str = "Saved Plan") -> str:
    lines = [
        f"# {title}",
        "",
        "## Summary",
        "This plan is intentionally long enough to look like a real captured plan file.",
        "",
        "## Implementation",
    ]
    lines.extend(
        f"- Step {i}: preserve the relevant behavior while avoiding duplicate prompt logging."
        for i in range(1, 18)
    )
    lines.extend(
        [
            "",
            "## Tests",
            "- Verify exact-prefix stripping.",
            "- Verify changed-prefix fallback stripping.",
            "- Verify Claude pass-through.",
        ]
    )
    return "\n".join(lines) + "\n"


def transcript_user_message(text: str, turn_id: str) -> dict:
    return {
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": text}],
            "internal_chat_message_metadata_passthrough": {"turn_id": turn_id},
        },
    }


def transcript_user_event(message: str) -> dict:
    return {"type": "event_msg", "payload": {"type": "user_message", "message": message}}


def transcript_shell_command(
    command: str,
    *,
    turn_id: str,
    exit_code: int = 0,
    duration: str = "0.125 seconds",
    output: str = "",
) -> dict:
    text = (
        "<user_shell_command>\n"
        f"<command>\n{command}\n</command>\n"
        "<result>\n"
        f"Exit code: {exit_code}\n"
        f"Duration: {duration}\n"
        f"Output:\n{output}\n"
        "</result>\n"
        "</user_shell_command>"
    )
    return transcript_user_message(text, turn_id)


def write_transcript(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def claude_github_worker_prompt(
    *,
    title: str,
    body: str,
    issue_number: int = 3,
    trigger_comment: str = "",
) -> str:
    trigger_block = (
        f"<trigger_comment>\n{trigger_comment}\n</trigger_comment>\n"
        if trigger_comment
        else ""
    )
    return (
        "You are Claude, an AI assistant designed to help with GitHub issues and pull requests. "
        "Think carefully as you analyze the context and respond appropriately. "
        "Here's the context for your current task:\n\n"
        "<formatted_context>\n"
        f"Issue Title: {title}\n"
        "Issue Author: luckydonald\n"
        "Issue State: OPEN\n"
        "Issue Labels: none\n"
        "</formatted_context>\n\n"
        f"<pr_or_issue_body>\n{body}\n</pr_or_issue_body>\n\n"
        "<event_type>ISSUE_CREATED</event_type>\n"
        "<is_pr>false</is_pr>\n"
        "<trigger_context>new issue with '@claude' in body</trigger_context>\n"
        "<repository>luckydonald/AllMyStorage</repository>\n\n"
        f"<issue_number>{issue_number}</issue_number>\n"
        "<claude_comment_id>4756572381</claude_comment_id>\n"
        "<trigger_username>luckydonald</trigger_username>\n"
        "<trigger_display_name>Lucky Lucy</trigger_display_name>\n"
        "<trigger_phrase>@claude</trigger_phrase>\n"
        f"{trigger_block}"
        "IMPORTANT: Use the mcp__github_comment__update_claude_comment tool to update your comment.\n\n"
        "Your task is to analyze the context, understand the request, and provide helpful responses "
        "and/or implement code changes as needed.\n\n"
        "Before taking any action, conduct your analysis inside <analysis> tags:\n"
        "a. Summarize the event type and context\n"
        "b. Determine if this is a request for code review feedback or for implementation\n"
    )


class AiHooksBaseRoutingTests(unittest.TestCase):
    def test_codex_prompt_catches_up_direct_shell_commands_with_output_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            transcript = Path(tmp) / "rollout.jsonl"
            current_prompt = "Investigate both failures"
            write_transcript(
                transcript,
                [
                    transcript_user_message("Earlier prompt", "turn-earlier"),
                    transcript_user_event("Earlier prompt"),
                    transcript_shell_command(
                        "printf 'first\\n'",
                        turn_id="turn-command-1",
                        output="first\n",
                    ),
                    transcript_shell_command(
                        "git pull\necho after",
                        turn_id="turn-command-2",
                        exit_code=1,
                        duration="1.0816 seconds",
                        output="fatal: failed\nsecond line\n",
                    ),
                    # Context fragments share the current turn id but are not
                    # ordinary prompt boundaries and must not clear commands.
                    transcript_user_message(
                        "<environment_context>test</environment_context>",
                        "turn-current",
                    ),
                    transcript_user_message(current_prompt, "turn-current"),
                ],
            )

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": current_prompt,
                    "turn_id": "turn-current",
                    "transcript_path": str(transcript),
                },
                "codex",
            )

            commands_dir = repo / "ai" / "°base" / "output" / "commands"
            self.assertEqual((commands_dir / "001.log").read_text(encoding="utf-8"), "first\n")
            self.assertEqual(
                (commands_dir / "002.log").read_text(encoding="utf-8"),
                "fatal: failed\nsecond line\n",
            )
            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertEqual(query.count("› Command executed."), 2)
            self.assertLess(
                query.index("output/commands/001.log"),
                query.index("output/commands/002.log"),
            )
            self.assertLess(query.index("output/commands/002.log"), query.index(current_prompt))
            self.assertIn("<code>$ git pull …</code>", query)
            self.assertIn("Exit code: <kbd>1</kbd> · Duration: `1.0816 seconds`", query)
            self.assertIn("› Investigate both failures\n\n", query)
            subjects = run_git(repo, "log", "--pretty=%s").stdout.strip().splitlines()
            self.assertEqual(
                subjects[:2],
                [
                    "[base] ai: updated prompt",
                    "[base] ai: commands 001-002 results",
                ],
            )
            command_commit_files = run_git(
                repo,
                "-c",
                "core.quotepath=false",
                "show",
                "--pretty=",
                "--name-only",
                "HEAD~1",
            ).stdout.strip().splitlines()
            self.assertEqual(
                command_commit_files,
                [
                    "ai/°base/output/commands/001.log",
                    "ai/°base/output/commands/002.log",
                    "ai/°base/query.md",
                ],
            )

    def test_codex_command_catchup_uses_latest_prompt_boundary_and_next_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            transcript = Path(tmp) / "rollout.jsonl"
            records = [
                transcript_shell_command("old command", turn_id="turn-old", output="old\n"),
                transcript_user_message("Previous prompt", "turn-previous"),
                transcript_user_event("Previous prompt"),
                transcript_shell_command("new command", turn_id="turn-new", output="new\n"),
                transcript_user_message("Current prompt", "turn-current"),
            ]
            write_transcript(transcript, records)

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": "Current prompt",
                    "turn_id": "turn-current",
                    "transcript_path": str(transcript),
                },
                "codex",
            )

            commands_dir = repo / "ai" / "°base" / "output" / "commands"
            self.assertEqual((commands_dir / "001.log").read_text(encoding="utf-8"), "new\n")
            self.assertFalse((commands_dir / "002.log").exists())
            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertNotIn("old command", query)
            self.assertIn("new command", query)

            records.extend(
                [
                    transcript_user_event("Current prompt"),
                    transcript_shell_command("second new command", turn_id="turn-next-command"),
                    transcript_user_message("Next prompt", "turn-next"),
                ]
            )
            write_transcript(transcript, records)
            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": "Next prompt",
                    "turn_id": "turn-next",
                    "transcript_path": str(transcript),
                },
                "codex",
            )

            self.assertEqual((commands_dir / "002.log").read_text(encoding="utf-8"), "")
            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertEqual(query.count("<code>$ new command</code>"), 1)
            self.assertEqual(query.count("<code>$ second new command</code>"), 1)
            self.assertEqual(query.count("output/commands/001.log"), 1)
            self.assertEqual(query.count("output/commands/002.log"), 1)

    def test_codex_skipped_prompt_still_flushes_direct_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            transcript = Path(tmp) / "rollout.jsonl"
            write_transcript(
                transcript,
                [
                    transcript_shell_command("pwd", turn_id="turn-command", output="/tmp\n"),
                    transcript_user_message("yes", "turn-current"),
                ],
            )

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": "yes",
                    "turn_id": "turn-current",
                    "transcript_path": str(transcript),
                },
                "codex",
            )

            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertIn("<code>$ pwd</code>", query)
            self.assertNotIn("› yes", query)
            self.assertEqual(last_subject(repo), "[base] ai: command 001 result")

    def test_codex_command_output_follows_consumer_by_issue_routing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "myproject"
            init_repo(repo, "https://github.com/example/consumer.git")
            issue_file = repo / "ai" / ".by-issue"
            issue_file.parent.mkdir(parents=True)
            issue_file.write_text("DEMO-42\n", encoding="utf-8")
            transcript = Path(tmp) / "rollout.jsonl"
            write_transcript(
                transcript,
                [
                    transcript_shell_command("pwd", turn_id="turn-command", output="/repo\n"),
                    transcript_user_message("Continue", "turn-current"),
                ],
            )

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": "Continue",
                    "turn_id": "turn-current",
                    "transcript_path": str(transcript),
                },
                "codex",
            )

            issue_dir = repo / "ai" / "by-issue" / "DEMO-42"
            self.assertEqual(
                (issue_dir / "output" / "commands" / "001.log").read_text(encoding="utf-8"),
                "/repo\n",
            )
            query = (issue_dir / "query.md").read_text(encoding="utf-8")
            self.assertIn("output/commands/001.log", query)
            self.assertEqual(last_subject(repo), "DEMO-42: ai: updated prompt")

    def test_codex_malformed_or_missing_transcript_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            transcript = Path(tmp) / "rollout.jsonl"
            write_transcript(
                transcript,
                [
                    transcript_user_message(
                        "<user_shell_command>changed shape</user_shell_command>",
                        "command",
                    ),
                    transcript_user_message("Normal prompt", "turn-current"),
                ],
            )

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": "Normal prompt",
                    "turn_id": "turn-current",
                    "transcript_path": str(transcript),
                },
                "codex",
            )
            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": "Another prompt",
                    "turn_id": "turn-another",
                    "transcript_path": str(Path(tmp) / "missing.jsonl"),
                },
                "codex",
            )

            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertEqual(query, "› Normal prompt\n\n› Another prompt\n\n")
            self.assertFalse((repo / "ai" / "°base" / "output" / "commands").exists())

    def test_codex_prompt_in_base_repo_with_only_origin_routes_and_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(repo, PROMPT_HOOK, {"prompt": "Capture this prompt"}, "codex")

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "› Capture this prompt\n\n",
            )
            self.assertFalse((repo / "ai" / "query.md").exists())
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_codex_prompt_in_base_repo_prefixes_base_marker_before_by_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            issue_file = repo / "ai" / "°base" / ".by-issue"
            issue_file.parent.mkdir(parents=True)
            issue_file.write_text("BASE-123\n", encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "Capture this prompt"}, "codex")

            self.assertEqual(
                (repo / "ai" / "°base" / "by-issue" / "BASE-123" / "query.md").read_text(
                    encoding="utf-8",
                ),
                "› Capture this prompt\n\n",
            )
            self.assertFalse((repo / "ai" / "°base" / "query.md").exists())
            self.assertEqual(last_subject(repo), "[base] BASE-123: ai: updated prompt")

    def test_codex_prompt_in_base_repo_accepts_optional_existing_prefix_pieces(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            issue_file = repo / "ai" / "°base" / ".by-issue"
            issue_file.parent.mkdir(parents=True)
            issue_file.write_text("BASE-123\n", encoding="utf-8")
            template = repo / "ai" / "commit-templates" / "prompt.md"
            template.parent.mkdir(parents=True)
            template.write_text("BASE-123: ai: templated prompt", encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "Capture this prompt"}, "codex")

            self.assertEqual(last_subject(repo), "[base] BASE-123: ai: templated prompt")

    def test_codex_prompt_in_base_repo_normalizes_reversed_existing_prefix_pieces(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            issue_file = repo / "ai" / "°base" / ".by-issue"
            issue_file.parent.mkdir(parents=True)
            issue_file.write_text("BASE-123\n", encoding="utf-8")
            template = repo / "ai" / "commit-templates" / "prompt.md"
            template.parent.mkdir(parents=True)
            template.write_text("BASE-123: [base] ai: templated prompt", encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "Capture this prompt"}, "codex")

            self.assertEqual(last_subject(repo), "[base] BASE-123: ai: templated prompt")

    def test_codex_prompt_logs_plan_link_for_exact_forwarded_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            plan = long_plan("Forwarded Plan")
            plan_path = repo / "ai" / "°base" / "plans" / "001_forwarded-plan.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(plan, encoding="utf-8")

            run_hook(
                repo,
                PROMPT_HOOK,
                {"prompt": f"{CODEX_FORWARDED_PLAN_PREFIX}\n\n{plan}"},
                "codex",
            )

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "> › Implement the [Plan](./plans/001_forwarded-plan.md). <kbd>cleared</kbd>\n\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_codex_prompt_logs_only_instruction_after_exact_forwarded_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            plan = long_plan("Instruction Plan")
            plan_path = repo / "ai" / "°base" / "plans" / "001_instruction-plan.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(plan, encoding="utf-8")

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": (
                        f"{CODEX_FORWARDED_PLAN_PREFIX}\n\n"
                        f"{plan}\n"
                        "Also make the warning actionable."
                    )
                },
                "codex",
            )

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "> › Implement the [Plan](./plans/001_instruction-plan.md). <kbd>cleared</kbd>\n\n"
                "› Also make the warning actionable.\n\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_codex_prompt_strips_changed_prefix_by_saved_plan_match_and_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            old_plan = long_plan("Older Plan")
            latest_plan = long_plan("Latest Plan")
            plans_dir = repo / "ai" / "°base" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "001_older-plan.md").write_text(old_plan, encoding="utf-8")
            (plans_dir / "002_latest-plan.md").write_text(latest_plan, encoding="utf-8")

            result = run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": (
                        "A previous agent made a plan. Start from this updated handoff text.\n\n"
                        f"{latest_plan}\n"
                        "Keep the fallback Codex-only."
                    )
                },
                "codex",
            )

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "> › Implement the [Plan](./plans/002_latest-plan.md). <kbd>cleared</kbd>\n\n"
                "› Keep the fallback Codex-only.\n\n",
            )
            self.assertIn("prompt prefix may have changed", result.stderr)
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_codex_prompt_does_not_file_match_tiny_latest_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            tiny_plan = "# Tiny Plan\n\nToo small.\n"
            plan_path = repo / "ai" / "°base" / "plans" / "001_tiny-plan.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(tiny_plan, encoding="utf-8")
            prompt = (
                "A previous agent made a plan. Start from this updated handoff text.\n\n"
                f"{tiny_plan}"
            )

            result = run_hook(repo, PROMPT_HOOK, {"prompt": prompt}, "codex")

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                f"› {prompt}\n\n",
            )
            self.assertEqual(result.stderr, "")
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_codex_short_plan_prompt_logs_latest_plan_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            old_plan = long_plan("Old Session Plan")
            latest_plan = long_plan("Non Resetting Session Plan")
            plans_dir = repo / "ai" / "°base" / "plans"
            plans_dir.mkdir(parents=True)
            (plans_dir / "001_old-session-plan.md").write_text(old_plan, encoding="utf-8")
            (plans_dir / "002_non-resetting-session-plan.md").write_text(
                latest_plan,
                encoding="utf-8",
            )

            result = run_hook(repo, PROMPT_HOOK, {"prompt": "Implement the plan."}, "codex")

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "> › Implement the [Plan](./plans/002_non-resetting-session-plan.md).\n\n",
            )
            self.assertEqual(result.stderr, "")
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_codex_short_plan_prompt_does_not_link_tiny_latest_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            plan_path = repo / "ai" / "°base" / "plans" / "001_tiny-plan.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text("# Tiny Plan\n\nToo small.\n", encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "Implement the plan."}, "codex")

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "› Implement the plan.\n\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_claude_short_plan_prompt_logs_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            plan = long_plan("Claude Short Prompt Plan")
            plan_path = repo / "ai" / "°base" / "plans" / "001_claude-short-prompt-plan.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(plan, encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "Implement the plan."}, "claude")

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "❯ Implement the plan.\n\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_claude_prompt_logs_forwarded_plan_text_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            plan = long_plan("Claude Pass Through")
            plan_path = repo / "ai" / "°base" / "plans" / "001_claude-pass-through.md"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(plan, encoding="utf-8")
            prompt = f"{CODEX_FORWARDED_PLAN_PREFIX}\n\n{plan}"

            run_hook(repo, PROMPT_HOOK, {"prompt": prompt}, "claude")

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                f"❯ {prompt}\n\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_claude_github_worker_prompt_logs_issue_request_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            body = (
                "It seems the issue is that the API uses a get request.\n\n"
                "Maybe that flow is not yet fully implemented in the barcode add overlay?\n\n"
                "@claude"
            )

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": claude_github_worker_prompt(
                        title="Can't add barcodes",
                        body=body,
                        issue_number=3,
                    )
                },
                "claude",
            )

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "> ❯ [query](./plans/000_online_query.md) for issue "
                "[#3](https://github.com/luckydonald/AllMyStorage/issues/3):\n"
                "> type: `ISSUE_CREATED`\n"
                "> trigger: @luckydonald (Lucky Lucy) via _@claude_.\n"
                "> comment: (none)\n"
                "> It seems the issue is that the API uses a get request.\n"
                ">\n"
                "> Maybe that flow is not yet fully implemented in the barcode add overlay?\n\n",
            )
            self.assertEqual(
                (repo / "ai" / "°base" / "plans" / "000_online_query.md").read_text(
                    encoding="utf-8",
                ),
                "# Online Query\n\n"
                "Issue: #3 Can't add barcodes\n"
                "URL: https://github.com/luckydonald/AllMyStorage/issues/3\n"
                "Event type: ISSUE_CREATED\n"
                "Trigger: @luckydonald (Lucky Lucy) via @claude\n\n"
                "## Trigger Comment\n\n"
                "(none)\n\n"
                "## Query\n\n"
                "It seems the issue is that the API uses a get request.\n\n"
                "Maybe that flow is not yet fully implemented in the barcode add overlay?\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_claude_github_worker_prompt_prefers_trigger_comment_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": claude_github_worker_prompt(
                        title="Page does not install as app on ios",
                        body="It should not open in the normal safari browser.",
                        issue_number=4,
                        trigger_comment="@claude\nPlease check the PWA manifest only.",
                    )
                },
                "claude",
            )

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "> ❯ [query](./plans/000_online_query.md) for issue "
                "[#4](https://github.com/luckydonald/AllMyStorage/issues/4):\n"
                "> type: `ISSUE_CREATED`\n"
                "> trigger: @luckydonald (Lucky Lucy) via _@claude_.\n"
                "> comment: @claude\n"
                "> Please check the PWA manifest only.\n"
                "> Please check the PWA manifest only.\n\n",
            )
            self.assertEqual(
                (repo / "ai" / "°base" / "plans" / "000_online_query.md").read_text(
                    encoding="utf-8",
                ),
                "# Online Query\n\n"
                "Issue: #4 Page does not install as app on ios\n"
                "URL: https://github.com/luckydonald/AllMyStorage/issues/4\n"
                "Event type: ISSUE_CREATED\n"
                "Trigger: @luckydonald (Lucky Lucy) via @claude\n\n"
                "## Trigger Comment\n\n"
                "@claude\n"
                "Please check the PWA manifest only.\n\n"
                "## Query\n\n"
                "Please check the PWA manifest only.\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_claude_task_notification_writes_agent_files_and_summary_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            output_file = Path(tmp) / "agent.output"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            output_file.write_text(
                json.dumps(
                    {
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": "toolu_test",
                                    "name": "Agent",
                                    "input": {"prompt": "Inspect the compose window."},
                                }
                            ]
                        }
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": (
                        "<task-notification>\n"
                        "<task-id>a6f364ce63ffebb84</task-id>\n"
                        "<tool-use-id>toolu_test</tool-use-id>\n"
                        f"<output-file>{output_file}</output-file>\n"
                        "<status>completed</status>\n"
                        "<summary>Agent came to rest</summary>\n"
                        "<result>Done.</result>\n"
                        "<usage><subagent_tokens>67643</subagent_tokens>"
                        "<tool_uses>6</tool_uses><duration_ms>69837</duration_ms></usage>\n"
                        "</task-notification>"
                    )
                },
                "claude",
            )

            agent_dir = repo / "ai" / "°base" / "output" / "agents" / "001.a6f364ce63ffebb84"
            self.assertEqual(
                (agent_dir / "prompt.md").read_text(encoding="utf-8"),
                "Inspect the compose window.",
            )
            self.assertEqual((agent_dir / "result.md").read_text(encoding="utf-8"), "Done.")
            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "❯ Task Notification:\n"
                "> - Task `a6f364ce63ffebb84` <kbd>completed</kbd>\n"
                "> - Tool `toolu_test`\n"
                "> - > Agent came to rest\n"
                "> - [Query (`27` chars, `27 B`)](output/agents/001.a6f364ce63ffebb84/prompt.md)\n"
                "> - [Answer (`5` chars, `5 B`)](output/agents/001.a6f364ce63ffebb84/result.md)\n"
                f"> - [Raw log (`{len(output_file.read_text(encoding='utf-8'))}` chars, "
                f"`{output_file.stat().st_size} B`)]({output_file})\n"
                "> - `6` tools, `67643` tokens, `1.16395 s`\n"
                "\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: agent 001.a6f364ce63ffebb84 results")
            self.assertEqual(
                run_git(repo, "log", "--oneline").stdout.strip().count("\n"), 1,
                "artifact files and query.md must land in a single commit, not two",
            )

    def test_claude_task_notification_usage_line_with_hyphen_tags(self):
        """<usage> children with hyphenated tag names (production format) still produce the usage line."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            output_file = Path(tmp) / "agent.output"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            output_file.write_text("", encoding="utf-8")

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": (
                        "<task-notification>\n"
                        "<task-id>hyphen_task_001</task-id>\n"
                        "<tool-use-id>toolu_hyphen</tool-use-id>\n"
                        f"<output-file>{output_file}</output-file>\n"
                        "<status>completed</status>\n"
                        "<summary>Hyphen usage test</summary>\n"
                        "<result>OK.</result>\n"
                        "<usage><subagent-tokens>12345</subagent-tokens>"
                        "<tool-uses>4</tool-uses><duration-ms>30000</duration-ms></usage>\n"
                        "</task-notification>"
                    )
                },
                "claude",
            )

            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertIn("> - `4` tools, `12345` tokens, `0.5 s`\n", query)

    def test_claude_task_notification_trailing_prompt_logged_separately(self):
        """Text typed while an agent runs (after </task-notification>) is logged as its own entry."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            output_file = Path(tmp) / "agent.output"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            output_file.write_text("", encoding="utf-8")

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": (
                        "<task-notification>\n"
                        "<task-id>trailing_task_001</task-id>\n"
                        "<tool-use-id>toolu_trailing</tool-use-id>\n"
                        f"<output-file>{output_file}</output-file>\n"
                        "<status>completed</status>\n"
                        "<summary>Some agent work</summary>\n"
                        "<result>Done.</result>\n"
                        "</task-notification>\n"
                        "Change the output dir to ai/output/agents/"
                    )
                },
                "claude",
            )

            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertIn("❯ Task Notification:\n", query)
            self.assertIn("❯ Change the output dir to ai/output/agents/\n", query)

    def test_claude_explore_notification_writes_result_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            output_file = Path(tmp) / "explore.output"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            output_file.write_text(
                json.dumps(
                    {
                        "message": {
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": "toolu_explore",
                                    "name": "Agent",
                                    "input": {
                                        "subagent_type": "Explore",
                                        "description": "Explore record-memory hook and commit logic",
                                        "prompt": "Search for...",
                                    },
                                }
                            ]
                        }
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": (
                        "<task-notification>\n"
                        "<task-id>b5dyyqcfr</task-id>\n"
                        "<tool-use-id>toolu_explore</tool-use-id>\n"
                        f"<output-file>{output_file}</output-file>\n"
                        "<status>completed</status>\n"
                        "<summary>Explore agent came to rest</summary>\n"
                        "<result>Done.</result>\n"
                        "<usage><subagent_tokens>46900</subagent_tokens>"
                        "<tool_uses>33</tool_uses><duration_ms>101000</duration_ms></usage>\n"
                        "</task-notification>"
                    )
                },
                "claude",
            )

            result_dir = repo / "ai" / "°base" / "output" / "explore" / "001.b5dyyqcfr"
            self.assertEqual(
                (result_dir / "result.md").read_text(encoding="utf-8"),
                "Done.",
            )
            self.assertFalse((repo / "ai" / "°base" / "agents").exists())
            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "❯ Exploration <kbd>finished</kbd>:\n"
                "> - > Explore record-memory hook and commit logic\n"
                "> - [Answer (`5` chars, `5 B`)](output/explore/001.b5dyyqcfr/result.md)\n"
                f"> - [Raw log (`{len(output_file.read_text(encoding='utf-8'))}` chars, "
                f"`{output_file.stat().st_size} B`)]({output_file})\n"
                "> - `33` tools · `46.9k` tokens · `1m 41s`\n"
                "\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: explore 001.b5dyyqcfr result")
            self.assertEqual(
                run_git(repo, "log", "--oneline").stdout.strip().count("\n"), 1,
                "the result file and query.md must land in a single commit, not two",
            )

    def test_codex_plan_in_base_repo_routes_and_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            session_id = f"test-{uuid.uuid4()}"

            run_hook(
                repo,
                PLAN_HOOK,
                {
                    "hook_event_name": "Stop",
                    "session_id": session_id,
                    "last_assistant_message": (
                        "<proposed_plan>\n"
                        "# Base Route Plan\n"
                        "Write the routed plan artifact.\n"
                        "</proposed_plan>"
                    ),
                },
                "codex",
            )

            plan_path = repo / "ai" / "°base" / "plans" / "001_base-route-plan.md"
            self.assertEqual(
                plan_path.read_text(encoding="utf-8"),
                "# Base Route Plan\nWrite the routed plan artifact.\n",
            )
            self.assertFalse((repo / "ai" / "plans").exists())
            self.assertEqual(last_subject(repo), "[base] ai: save plan 001_base-route-plan")

    def test_codex_plan_ignores_post_tool_use_stdout_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(
                repo,
                PLAN_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "session_id": f"test-{uuid.uuid4()}",
                    "tool_name": "ExitPlanMode",
                    "tool_response": "Exit code: 0\nstdout from some command\n",
                },
                "codex",
            )

            self.assertFalse((repo / "ai" / "°base" / "plans").exists())
            self.assertEqual(last_subject(repo), "init")

    def test_codex_plan_uses_session_transcript_plan_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            session_id = f"test-{uuid.uuid4()}"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            session_dir = home / ".codex" / "sessions" / "2026" / "05" / "27"
            session_dir.mkdir(parents=True)
            session_file = session_dir / f"rollout-2026-05-27T14-20-27-{session_id}.jsonl"
            session_file.write_text(
                json.dumps(
                    {
                        "type": "event_msg",
                        "payload": {
                            "type": "item_completed",
                            "item": {
                                "type": "Plan",
                                "text": "# Transcript Plan\n\nUse the Codex plan event.\n",
                            },
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            run_hook(
                repo,
                PLAN_HOOK,
                {"hook_event_name": "Stop", "session_id": session_id},
                "codex",
                extra_env={"HOME": str(home)},
            )

            plan_path = repo / "ai" / "°base" / "plans" / "001_transcript-plan.md"
            self.assertEqual(
                plan_path.read_text(encoding="utf-8"),
                "# Transcript Plan\n\nUse the Codex plan event.\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: save plan 001_transcript-plan")

    def test_codex_plan_falls_back_to_forwarded_plan_query_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            query_path = repo / "ai" / "°base" / "query.md"
            query_path.parent.mkdir(parents=True)
            query_path.write_text(
                "› A previous agent produced the plan below to accomplish the user's task.\n"
                "Implement the plan in a fresh context.\n\n"
                "# Forwarded Plan\n\n"
                "Save this markdown plan.\n\n",
                encoding="utf-8",
            )

            run_hook(
                repo,
                PLAN_HOOK,
                {"hook_event_name": "Stop", "session_id": f"test-{uuid.uuid4()}"},
                "codex",
            )

            plan_path = repo / "ai" / "°base" / "plans" / "001_forwarded-plan.md"
            self.assertEqual(
                plan_path.read_text(encoding="utf-8"),
                "# Forwarded Plan\n\nSave this markdown plan.\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: save plan 001_forwarded-plan")

    def test_claude_write_plan_still_captures_claude_plan_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            plan_file = home / ".claude" / "plans" / "test-plan.md"

            run_hook(
                repo,
                PLAN_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "session_id": f"test-{uuid.uuid4()}",
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": str(plan_file),
                        "content": "# Claude Write Plan\n\nKeep Claude behavior.\n",
                    },
                },
                "claude",
            )

            plan_path = repo / "ai" / "°base" / "plans" / "001_claude-write-plan.md"
            self.assertEqual(
                plan_path.read_text(encoding="utf-8"),
                "# Claude Write Plan\n\nKeep Claude behavior.\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: save plan 001_claude-write-plan")

    def test_memory_in_base_repo_routes_and_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            encoded = _encode_project_path(repo.resolve())
            src_dir = home / ".claude" / "projects" / encoded / "memory"
            src_dir.mkdir(parents=True)
            (src_dir / "note.md").write_text("remember this\n", encoding="utf-8")

            run_hook(
                repo,
                MEMORY_HOOK,
                {"hook_event_name": "SessionStart"},
                extra_env={"HOME": str(home)},
            )

            self.assertEqual(
                (repo / "ai" / "°base" / "memory" / "note.md").read_text(encoding="utf-8"),
                "remember this\n",
            )
            self.assertFalse((repo / "ai" / "memory").exists())
            self.assertEqual(last_subject(repo), "[base] ai: record memory note")

    def test_memory_session_start_restores_missing_claude_source_from_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            memory_file = repo / "ai" / "°base" / "memory" / "note.md"
            memory_file.parent.mkdir(parents=True)
            memory_file.write_text("repo is durable\n", encoding="utf-8")
            run_git(repo, "add", str(memory_file.relative_to(repo)))
            run_git(repo, "commit", "-m", "seed memory")

            run_hook(
                repo,
                MEMORY_HOOK,
                {"hook_event_name": "SessionStart"},
                extra_env={"HOME": str(home)},
            )

            encoded = _encode_project_path(repo.resolve())
            src_file = home / ".claude" / "projects" / encoded / "memory" / "note.md"
            self.assertEqual(src_file.read_text(encoding="utf-8"), "repo is durable\n")
            self.assertEqual(last_subject(repo), "seed memory")

    def test_memory_session_start_does_not_resurrect_marked_deleted_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            memory_file = repo / "ai" / "°base" / "memory" / "old.md"
            memory_file.parent.mkdir(parents=True)
            memory_file.write_text("old memory\n", encoding="utf-8")
            run_git(repo, "add", str(memory_file.relative_to(repo)))
            run_git(repo, "commit", "-m", "seed old memory")
            run_git(repo, "rm", str(memory_file.relative_to(repo)))
            run_git(
                repo,
                "commit",
                "-m",
                "ai: delete memory old",
                "-m",
                "Deleted Memory: old.md",
            )
            encoded = _encode_project_path(repo.resolve())
            src_file = home / ".claude" / "projects" / encoded / "memory" / "old.md"
            src_file.parent.mkdir(parents=True)
            src_file.write_text("stale local memory\n", encoding="utf-8")

            run_hook(
                repo,
                MEMORY_HOOK,
                {"hook_event_name": "SessionStart"},
                extra_env={"HOME": str(home)},
            )

            self.assertFalse(memory_file.exists())
            self.assertFalse(src_file.exists())
            self.assertEqual(last_subject(repo), "ai: delete memory old")

    def test_memory_posttooluse_write_with_underscore_in_project_path(self):
        """PostToolUse(Write) must commit memory files when the project dir
        contains underscores — the encoded Claude state path uses hyphens
        for all non-alphanumeric chars, not just slashes."""
        with tempfile.TemporaryDirectory() as tmp:
            # Repo dir name contains an underscore (the bug trigger).
            repo = Path(tmp) / "my_project"
            home = Path(tmp) / "home"
            init_repo(repo, "https://github.com/user/my_project.git")

            encoded = _encode_project_path(repo.resolve())
            src_dir = home / ".claude" / "projects" / encoded / "memory"
            src_dir.mkdir(parents=True)
            src_file = src_dir / "tip.md"
            src_file.write_text("useful tip\n", encoding="utf-8")

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(src_file)},
                },
                extra_env={"HOME": str(home)},
            )

            dst = repo / "ai" / "memory" / "tip.md"
            self.assertTrue(dst.exists(), "memory file was not synced to repo")
            self.assertEqual(dst.read_text(encoding="utf-8"), "useful tip\n")
            self.assertEqual(last_subject(repo), "ai: record memory tip")

    def test_memory_posttooluse_write_from_subproject_syncs_via_git_root_source(self):
        """A session launched inside a monorepo subdirectory (CLAUDE_PROJECT_DIR
        != git root) must still find memory written under Claude Code's
        git-root-encoded source dir -- see ai/°base/errors/25.*."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "DockerTgBot"
            subproject = repo / "sticker_tag_bot"
            home = Path(tmp) / "home"
            init_repo(repo, "https://github.com/luckydonald/docker-tg-bot.git")
            subproject.mkdir()

            encoded_root = _encode_project_path(repo.resolve())
            src_dir = home / ".claude" / "projects" / encoded_root / "memory"
            src_dir.mkdir(parents=True)
            src_file = src_dir / "tip.md"
            src_file.write_text("useful tip\n", encoding="utf-8")

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(src_file)},
                },
                extra_env={"HOME": str(home), "CLAUDE_PROJECT_DIR": str(subproject)},
            )

            dst = subproject / "ai" / "memory" / "tip.md"
            self.assertTrue(dst.exists(), "memory file was not synced to repo")
            self.assertEqual(dst.read_text(encoding="utf-8"), "useful tip\n")
            self.assertEqual(last_subject(repo), "ai: record memory tip")

    def test_memory_posttooluse_write_honors_project_dir_name_override(self):
        """When CLAUDE_CODE_PROJECT_DIR_NAME (+ CLAUDE_CONFIG_DIR) is set —
        e.g. via a linked subproject's `.claude-project.env` — the hook must
        read from `<config-dir>/projects/<override>/`, matching Claude
        Code's own gated override behavior, instead of the sanitized-cwd
        directory it would otherwise compute."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "my_subproject"
            home = Path(tmp) / "home"
            init_repo(repo, "https://github.com/user/my_subproject.git")

            src_dir = home / ".claude" / "projects" / "monorepo-my-subproject" / "memory"
            src_dir.mkdir(parents=True)
            src_file = src_dir / "tip.md"
            src_file.write_text("useful tip\n", encoding="utf-8")

            # A sanitized-cwd bucket also exists but must NOT be read from
            # while the override is set — proves the override takes priority.
            decoy_dir = home / ".claude" / "projects" / _encode_project_path(repo.resolve()) / "memory"
            decoy_dir.mkdir(parents=True)
            (decoy_dir / "tip.md").write_text("wrong tip\n", encoding="utf-8")

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(src_file)},
                },
                extra_env={
                    "HOME": str(home),
                    "CLAUDE_CONFIG_DIR": str(home / ".claude"),
                    "CLAUDE_CODE_PROJECT_DIR_NAME": "monorepo-my-subproject",
                },
            )

            dst = repo / "ai" / "memory" / "tip.md"
            self.assertTrue(dst.exists(), "memory file was not synced to repo")
            self.assertEqual(dst.read_text(encoding="utf-8"), "useful tip\n")
            self.assertEqual(last_subject(repo), "ai: record memory tip")

    def test_memory_posttooluse_write_ignores_project_dir_name_without_config_dir(self):
        """CLAUDE_CODE_PROJECT_DIR_NAME alone (no CLAUDE_CONFIG_DIR) must be
        ignored, mirroring Claude Code's own gating — the hook falls back to
        the sanitized-cwd directory."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "my_subproject"
            home = Path(tmp) / "home"
            init_repo(repo, "https://github.com/user/my_subproject.git")

            encoded = _encode_project_path(repo.resolve())
            src_dir = home / ".claude" / "projects" / encoded / "memory"
            src_dir.mkdir(parents=True)
            src_file = src_dir / "tip.md"
            src_file.write_text("useful tip\n", encoding="utf-8")

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Write",
                    "tool_input": {"file_path": str(src_file)},
                },
                extra_env={
                    "HOME": str(home),
                    # Explicitly cleared: this test asserts the override is
                    # ignored when CLAUDE_CONFIG_DIR is unset, regardless of
                    # whatever the test runner's own ambient shell has.
                    "CLAUDE_CONFIG_DIR": "",
                    "CLAUDE_CODE_PROJECT_DIR_NAME": "should-be-ignored",
                },
            )

            dst = repo / "ai" / "memory" / "tip.md"
            self.assertTrue(dst.exists(), "memory file was not synced to repo")
            self.assertEqual(dst.read_text(encoding="utf-8"), "useful tip\n")

    def test_memory_session_start_does_not_resurrect_across_promoted_directory(self):
        """A memory promoted (via promote.py) from `ai/°base/memory/` to root
        `ai/memory/` must not get resurrected back into `ai/°base/memory/`
        just because the Claude-side source file still exists."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            promoted = repo / "ai" / "memory" / "shared.md"
            promoted.parent.mkdir(parents=True)
            promoted.write_text("the real, promoted copy\n", encoding="utf-8")
            run_git(repo, "add", str(promoted.relative_to(repo)))
            run_git(repo, "commit", "-m", "seed promoted memory")

            encoded = _encode_project_path(repo.resolve())
            src_file = home / ".claude" / "projects" / encoded / "memory" / "shared.md"
            src_file.parent.mkdir(parents=True)
            src_file.write_text("stale claude-side copy\n", encoding="utf-8")

            run_hook(
                repo,
                MEMORY_HOOK,
                {"hook_event_name": "SessionStart"},
                extra_env={"HOME": str(home)},
            )

            self.assertFalse((repo / "ai" / "°base" / "memory" / "shared.md").exists())
            self.assertEqual(
                src_file.read_text(encoding="utf-8"), "the real, promoted copy\n"
            )

    def test_codex_memory_sync_does_not_resurrect_across_promoted_directory(self):
        """Same guard, exercised through `record-codex-memory/hook.py`'s
        resource->project reverse sync. `$CODEX_HOME/memories` is a plain
        folder here, not a git repo -- that is not a supported setup."""
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            project = Path(tmp) / "base"
            codex_home = Path(tmp) / "codex"
            memory_repo = codex_home / "memories"
            init_repo(project, "https://luckydonald@github.com/luckydonald/base.git")
            memory_repo.mkdir(parents=True)
            (memory_repo / "MEMORY.md").write_text("# Memories\n", encoding="utf-8")

            promoted = project / "ai" / "memory" / "shared.md"
            promoted.parent.mkdir(parents=True)
            promoted.write_text("the real, promoted copy\n", encoding="utf-8")
            run_git(project, "add", str(promoted.relative_to(project)))
            run_git(project, "commit", "-m", "seed promoted memory")

            encoded = _encode_project_path(project.resolve())
            resource = memory_repo / "extensions" / "base_synced" / "resources" / encoded
            resource.mkdir(parents=True)
            (resource / "shared.md").write_text("stale resource-side copy\n", encoding="utf-8")

            run_hook(
                project,
                CODEX_MEMORY_HOOK,
                {"hook_event_name": "Stop"},
                "codex",
                extra_env={"CODEX_HOME": str(codex_home)},
            )

            self.assertFalse((project / "ai" / "°base" / "memory" / "shared.md").exists())
            self.assertEqual(
                (resource / "shared.md").read_text(encoding="utf-8"),
                "the real, promoted copy\n",
            )

    def test_codex_memory_hook_syncs_and_is_idempotent(self):
        """`$CODEX_HOME/memories` is a plain folder -- the hook never runs
        git there, only inside the project repo (`project`)."""
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            project = Path(tmp) / "project"
            codex_home = Path(tmp) / "codex"
            memory_repo = codex_home / "memories"
            init_repo(project, "https://github.com/user/project.git")
            memory_repo.mkdir(parents=True)
            (memory_repo / "MEMORY.md").write_text("# Memories\n", encoding="utf-8")

            note = memory_repo / "extensions" / "ad_hoc" / "note.md"
            note.parent.mkdir(parents=True)
            note.write_text("remember this\n", encoding="utf-8")

            run_hook(
                project,
                CODEX_MEMORY_HOOK,
                {"hook_event_name": "PostToolUse", "tool_name": "apply_patch"},
                "codex",
                extra_env={"CODEX_HOME": str(codex_home)},
            )

            mirror = project / "ai" / "memory" / "note.md"
            self.assertTrue(mirror.exists())
            self.assertEqual(last_subject(project), "ai: sync codex memory")
            index = project / "ai" / "memory" / "MEMORY.md"
            self.assertIn("[note](note.md) — TODO: summarize this file.", index.read_text())
            encoded = _encode_project_path(project.resolve())
            resource = memory_repo / "extensions" / "base_synced" / "resources" / encoded
            self.assertEqual(
                json.loads((resource / "scope.json").read_text(encoding="utf-8")),
                {"cwd": str(project.resolve())},
            )
            key = _encode_project_path(project.resolve())
            registry = json.loads((memory_repo / "extensions" / "base_synced" / "registry.json").read_text())
            self.assertEqual(
                registry["notes"]["extensions/ad_hoc/note.md"],
                {
                    "status": "assigned",
                    "project": key,
                    "target": "ai/memory/note.md",
                    "hash": registry["notes"]["extensions/ad_hoc/note.md"]["hash"],
                    "recorded_by": registry["notes"]["extensions/ad_hoc/note.md"]["recorded_by"],
                },
            )
            project_sync = json.loads((project / "ai" / "memory" / ".codex-sync.json").read_text())
            self.assertEqual(project_sync["notes"]["extensions/ad_hoc/note.md"]["target"], "ai/memory/note.md")
            self.assertNotIn("project", project_sync["notes"]["extensions/ad_hoc/note.md"])

            project_commit_count = run_git(project, "log", "--oneline").stdout.count("ai: sync codex memory")
            run_hook(
                project,
                CODEX_MEMORY_HOOK,
                {"hook_event_name": "Stop"},
                "codex",
                extra_env={"CODEX_HOME": str(codex_home)},
            )
            self.assertTrue(note.exists())
            # No new note was imported and nothing changed, so no new commit.
            self.assertEqual(
                run_git(project, "log", "--oneline").stdout.count("ai: sync codex memory"),
                project_commit_count,
            )

    def test_codex_memory_stop_reports_unassigned_note_as_json(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            project = Path(tmp) / "project"
            codex_home = Path(tmp) / "codex"
            memory_repo = codex_home / "memories"
            init_repo(project, "https://github.com/user/project.git")
            memory_repo.mkdir(parents=True)
            (memory_repo / "MEMORY.md").write_text("# Memories\n", encoding="utf-8")
            note = memory_repo / "extensions" / "ad_hoc" / "later.md"
            note.parent.mkdir(parents=True)
            note.write_text("# Later\n", encoding="utf-8")

            result = run_hook(
                project,
                CODEX_MEMORY_HOOK,
                {"hook_event_name": "Stop"},
                "codex",
                extra_env={"CODEX_HOME": str(codex_home)},
            )

            output = json.loads(result.stdout)
            self.assertIn("unassigned native note", output["systemMessage"])
            self.assertIn("import-codex.py later.md", output["systemMessage"])
            self.assertFalse((project / "ai" / "memory" / "later.md").exists())

    def test_claude_memory_stop_reports_unassigned_note_as_plain_text(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            project = Path(tmp) / "project"
            codex_home = Path(tmp) / "codex"
            memory_repo = codex_home / "memories"
            init_repo(project, "https://github.com/user/project.git")
            memory_repo.mkdir(parents=True)
            (memory_repo / "MEMORY.md").write_text("# Memories\n", encoding="utf-8")
            note = memory_repo / "extensions" / "ad_hoc" / "later.md"
            note.parent.mkdir(parents=True)
            note.write_text("# Later\n", encoding="utf-8")

            result = run_hook(
                project,
                CODEX_MEMORY_HOOK,
                {"hook_event_name": "Stop"},
                "claude",
                extra_env={"CODEX_HOME": str(codex_home)},
            )

            self.assertIn("unassigned native note", result.stdout)
            self.assertIn("import-codex.py later.md", result.stdout)

    def _seed_memory_pair(self, repo: Path, home: Path, name: str) -> Path:
        """Seed a repo-tracked mirror file plus a matching external source
        file under the fake `$HOME`. Returns the external source path."""
        memory_file = repo / "ai" / "°base" / "memory" / name
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        memory_file.write_text(f"{name} content\n", encoding="utf-8")
        run_git(repo, "add", str(memory_file.relative_to(repo)))
        run_git(repo, "commit", "-m", f"seed {name}")

        encoded = _encode_project_path(repo.resolve())
        src_file = home / ".claude" / "projects" / encoded / "memory" / name
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text(f"{name} content\n", encoding="utf-8")
        return src_file

    def test_memory_bash_rm_of_source_file_deletes_repo_mirror(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            src_file = self._seed_memory_pair(repo, home, "gone.md")
            src_file.unlink()  # the Bash tool already ran `rm` by the time we fire PostToolUse

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": f'rm "{src_file}"'},
                },
                extra_env={"HOME": str(home)},
            )

            self.assertFalse((repo / "ai" / "°base" / "memory" / "gone.md").exists())
            message = run_git(repo, "log", "-1", "--pretty=%B").stdout
            self.assertIn("Deleted Memory: gone.md", message.splitlines())

    def test_memory_bash_rm_outside_source_dir_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            self._seed_memory_pair(repo, home, "keep.md")
            unrelated = home / "elsewhere" / "keep.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("not a memory\n", encoding="utf-8")
            unrelated.unlink()

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": f'rm "{unrelated}"'},
                },
                extra_env={"HOME": str(home)},
            )

            self.assertTrue((repo / "ai" / "°base" / "memory" / "keep.md").exists())
            self.assertEqual(last_subject(repo), "seed keep.md")

    def test_memory_bash_non_rm_command_mentioning_md_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            src_file = self._seed_memory_pair(repo, home, "keep.md")

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": f'cat "{src_file}"'},
                },
                extra_env={"HOME": str(home)},
            )

            self.assertTrue((repo / "ai" / "°base" / "memory" / "keep.md").exists())
            self.assertTrue(src_file.exists())
            self.assertEqual(last_subject(repo), "seed keep.md")

    def test_memory_bash_rm_of_untracked_source_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            encoded = _encode_project_path(repo.resolve())
            src_file = home / ".claude" / "projects" / encoded / "memory" / "untracked.md"
            src_file.parent.mkdir(parents=True)
            src_file.write_text("never committed\n", encoding="utf-8")
            src_file.unlink()

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": f'rm "{src_file}"'},
                },
                extra_env={"HOME": str(home)},
            )

            self.assertEqual(last_subject(repo), "init")

    def test_memory_bash_rm_chained_command_still_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            src_file = self._seed_memory_pair(repo, home, "chained.md")
            src_file.unlink()

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": f'rm "{src_file}" && echo done'},
                },
                extra_env={"HOME": str(home)},
            )

            self.assertFalse((repo / "ai" / "°base" / "memory" / "chained.md").exists())
            message = run_git(repo, "log", "-1", "--pretty=%B").stdout
            self.assertIn("Deleted Memory: chained.md", message.splitlines())

    def test_memory_session_start_content_mismatch_repo_wins(self):
        """When both copies exist but diverge, the repo (git-tracked) copy is
        authoritative: the untracked Claude source gets overwritten from the
        repo, not the other way around, and nothing new is committed."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            src_file = self._seed_memory_pair(repo, home, "drift.md")
            src_file.write_text("untracked local drift\n", encoding="utf-8")

            run_hook(
                repo,
                MEMORY_HOOK,
                {"hook_event_name": "SessionStart"},
                extra_env={"HOME": str(home)},
            )

            self.assertEqual(src_file.read_text(encoding="utf-8"), "drift.md content\n")
            self.assertEqual(last_subject(repo), "seed drift.md")

    def test_memory_session_start_warns_on_orphaned_repo_file(self):
        """A repo memory file with no MEMORY.md entry should warn, not vanish
        or get silently re-indexed."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            memory_dir = repo / "ai" / "°base" / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "MEMORY.md").write_text("(empty index)\n", encoding="utf-8")
            (memory_dir / "orphan.md").write_text("nobody points at me\n", encoding="utf-8")
            run_git(repo, "add", "ai")
            run_git(repo, "commit", "-m", "seed orphaned memory")

            result = run_hook(
                repo,
                MEMORY_HOOK,
                {"hook_event_name": "SessionStart"},
                extra_env={"HOME": str(home)},
            )

            self.assertIn("orphan.md", result.stderr)
            self.assertIn("orphaned", result.stderr)

    def test_memory_session_start_warns_on_dangling_index_link(self):
        """A MEMORY.md line pointing at a file that doesn't exist should warn,
        not be silently dropped or resurrect anything."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            memory_dir = repo / "ai" / "°base" / "memory"
            memory_dir.mkdir(parents=True)
            (memory_dir / "MEMORY.md").write_text(
                "- [ghost](missing.md) — this file was never created.\n",
                encoding="utf-8",
            )
            run_git(repo, "add", "ai")
            run_git(repo, "commit", "-m", "seed dangling index entry")

            result = run_hook(
                repo,
                MEMORY_HOOK,
                {"hook_event_name": "SessionStart"},
                extra_env={"HOME": str(home)},
            )

            self.assertIn("missing.md", result.stderr)
            self.assertIn("dangling", result.stderr)

    # ------------------------------------------------------------------
    # save-plan: Stop false-positive and ExitPlanMode fixes
    # ------------------------------------------------------------------

    def test_claude_stop_ignores_string_tool_response(self):
        """Stop event with a plain-string tool_response must produce no commit."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(
                repo,
                PLAN_HOOK,
                {
                    "hook_event_name": "Stop",
                    "session_id": f"test-{uuid.uuid4()}",
                    "tool_name": "",
                    "tool_input": {},
                    "tool_response": "Exit code: 0\nWall time: 0.2 seconds\nSuccess.",
                },
                "claude",
            )

            self.assertEqual(last_subject(repo), "init")
            self.assertFalse((repo / "ai" / "°base" / "plans").exists())
            self.assertFalse((repo / "ai" / "plans").exists())

    def test_claude_stop_ignores_dict_tool_response_without_plan(self):
        """Stop event with a dict tool_response that has no plan/filePath → no commit."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(
                repo,
                PLAN_HOOK,
                {
                    "hook_event_name": "Stop",
                    "session_id": f"test-{uuid.uuid4()}",
                    "tool_name": "",
                    "tool_input": {},
                    "tool_response": {"status": "ok", "duration_ms": 120},
                },
                "claude",
            )

            self.assertEqual(last_subject(repo), "init")
            self.assertFalse((repo / "ai" / "°base" / "plans").exists())

    def test_claude_exit_plan_mode_captures_plan_from_file_path(self):
        """ExitPlanMode with tool_response.filePath still commits the plan."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            plan_file = Path(tmp) / "harness-plan.md"
            plan_file.write_text("# My Test Plan\n\nStep 1.\nStep 2.\n", encoding="utf-8")
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(
                repo,
                PLAN_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "session_id": f"test-{uuid.uuid4()}",
                    "tool_name": "ExitPlanMode",
                    "tool_input": {},
                    "tool_response": {"filePath": str(plan_file)},
                },
                "claude",
            )

            plan_files = list((repo / "ai" / "°base" / "plans").glob("001_*.md"))
            self.assertEqual(len(plan_files), 1, plan_files)
            self.assertIn("Step 1.", plan_files[0].read_text(encoding="utf-8"))
            self.assertEqual(last_subject(repo), "[base] ai: save plan 001_my-test-plan")

    def test_new_plan_in_same_session_gets_fresh_prefix(self):
        """A second /plan in the same session gets prefix 002, not 001 again."""
        import tempfile as _tempfile
        state_file = Path(_tempfile.gettempdir()) / "save-plan-state.json"

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            session_id = f"test-{uuid.uuid4()}"
            fake_plan_path = f"/home/user/.claude/plans/session-plan.md"

            # Step 1: Write trigger → plan A → prefix 001
            run_hook(
                repo,
                PLAN_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "session_id": session_id,
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": fake_plan_path,
                        "content": "# Plan Alpha\n\nDo thing A.\n",
                    },
                },
                "claude",
            )
            self.assertTrue((repo / "ai" / "°base" / "plans" / "001_plan-alpha.md").exists())

            # Step 2: ExitPlanMode → sets done=True in state
            run_hook(
                repo,
                PLAN_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "session_id": session_id,
                    "tool_name": "ExitPlanMode",
                    "tool_input": {},
                    "tool_response": {"plan": "# Plan Alpha\n\nDo thing A."},
                },
                "claude",
            )
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertTrue(state.get(session_id, {}).get("done"), "done flag not set after ExitPlanMode")

            # Step 3: Write trigger with a different plan → must allocate 002
            run_hook(
                repo,
                PLAN_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "session_id": session_id,
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": fake_plan_path,
                        "content": "# Plan Beta\n\nDo thing B.\n",
                    },
                },
                "claude",
            )
            self.assertTrue(
                (repo / "ai" / "°base" / "plans" / "002_plan-beta.md").exists(),
                "second plan must get prefix 002",
            )
            self.assertTrue(
                (repo / "ai" / "°base" / "plans" / "001_plan-alpha.md").exists(),
                "first plan must still exist",
            )

    def test_prompt_in_repo_named_base_with_different_origin_is_unprefixed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/example/consumer.git")

            run_hook(repo, PROMPT_HOOK, {"prompt": "Capture downstream prompt"}, "codex")

            self.assertEqual(
                (repo / "ai" / "query.md").read_text(encoding="utf-8"),
                "› Capture downstream prompt\n\n",
            )
            self.assertFalse((repo / "ai" / "°base" / "query.md").exists())
            self.assertEqual(last_subject(repo), "ai: updated prompt")

    def test_debug_payload_written_when_flag_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "myproject"
            init_repo(repo, "https://github.com/example/consumer.git")
            (repo / "ai").mkdir(parents=True, exist_ok=True)
            (repo / "ai" / ".debug").touch()
            payload = {"prompt": "debug me", "session_id": "abc123"}

            run_hook(repo, PROMPT_HOOK, payload, "claude")

            debug_dir = repo / "ai" / "output" / "debug"
            self.assertTrue(debug_dir.is_dir(), "debug dir should be created")
            files = list(debug_dir.glob("*-save-prompt.json"))
            self.assertEqual(len(files), 1, f"expected 1 debug file, got {files}")
            written = json.loads(files[0].read_text(encoding="utf-8"))
            self.assertEqual(written.get("prompt"), "debug me")
            self.assertEqual(written.get("session_id"), "abc123")

    def test_debug_payload_not_written_without_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "myproject"
            init_repo(repo, "https://github.com/example/consumer.git")

            run_hook(repo, PROMPT_HOOK, {"prompt": "no debug"}, "claude")

            self.assertFalse((repo / "ai" / "output" / "debug").exists())

    def test_debug_payload_routes_to_base_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            (repo / "ai" / "°base").mkdir(parents=True, exist_ok=True)
            (repo / "ai" / "°base" / ".debug").touch()
            payload = {"prompt": "base debug", "session_id": "xyz789"}

            run_hook(repo, PROMPT_HOOK, payload, "claude")

            base_debug_dir = repo / "ai" / "°base" / "output" / "debug"
            self.assertTrue(base_debug_dir.is_dir(), "debug dir should be under ai/°base/")
            files = list(base_debug_dir.glob("*-save-prompt.json"))
            self.assertEqual(len(files), 1, f"expected 1 debug file in base prefix, got {files}")
            written = json.loads(files[0].read_text(encoding="utf-8"))
            self.assertEqual(written.get("prompt"), "base debug")
            self.assertFalse((repo / "ai" / "output" / "debug").exists(), "should NOT write to ai/output/debug/")

    def test_compact_prompt_writes_autoloads_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")

            compact_prompt = (
                "/compact\n"
                "  ⎿  Compacted\n"
                "  ⎿  Read ai/git/pending-commit.md (18 lines)\n"
                "  ⎿  Referenced file archive_apps.sh\n"
                "  ⎿  Plan file referenced (~/.claude/plans/my-plan.md)\n"
                "  ⎿  Skills restored (commit-with-lplp-style)\n"
            )
            run_hook(repo, PROMPT_HOOK, {"prompt": compact_prompt}, "claude")

            autoloads_file = repo / "ai" / "°base" / "output" / "compact" / "001" / "autoloads.md"
            self.assertTrue(autoloads_file.exists(), "autoloads.md should be created")
            autoloads = autoloads_file.read_text(encoding="utf-8")
            self.assertIn("- Read `ai/git/pending-commit.md` (`18` lines)", autoloads)
            self.assertIn("- Referenced file `archive_apps.sh`", autoloads)
            self.assertIn("- Plan file referenced (`~/.claude/plans/my-plan.md`)", autoloads)
            self.assertIn("- Skills restored (`commit-with-lplp-style`)", autoloads)
            self.assertNotIn("Compacted", autoloads)

            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertIn("❯ Conversation compacted:\n", query)
            self.assertIn("output/compact/001/autoloads.md", query)

    def test_compact_autoloads_skips_compacted_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")

            compact_prompt = (
                "/compact\n"
                "  ⎿  Compacted\n"
                "  ⎿  Read notes.md (5 lines)\n"
            )
            run_hook(repo, PROMPT_HOOK, {"prompt": compact_prompt}, "claude")

            autoloads = (
                repo / "ai" / "°base" / "output" / "compact" / "001" / "autoloads.md"
            ).read_text(encoding="utf-8")
            self.assertNotIn("Compacted", autoloads)
            self.assertIn("- Read `notes.md` (`5` lines)", autoloads)

    def test_compact_sequential_numbering(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")

            compact_prompt = "/compact\n  ⎿  Compacted\n  ⎿  Read a.md (1 lines)\n"
            run_hook(repo, PROMPT_HOOK, {"prompt": compact_prompt}, "claude")
            run_hook(repo, PROMPT_HOOK, {"prompt": compact_prompt}, "claude")

            compact_dir = repo / "ai" / "°base" / "output" / "compact"
            self.assertTrue((compact_dir / "001").is_dir(), "first compact → 001")
            self.assertTrue((compact_dir / "002").is_dir(), "second compact → 002")

    def test_postcompact_manual_writes_prompt_id_result_and_marked_query_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            prompt_id = "ed11c17f-abf7-40a0-839a-64dd37b4976b"
            summary = "Exact compact summary.\n\nKeep this whitespace.\n"

            run_hook(
                repo,
                COMPACT_PROMPT_HOOK,
                {
                    "hook_event_name": "PostCompact",
                    "trigger": "manual",
                    "compact_summary": summary,
                    "prompt_id": prompt_id,
                },
                "claude",
            )

            result = (
                repo / "ai" / "°base" / "output" / "compact"
                / f"001.{prompt_id}" / "result.md"
            )
            self.assertEqual(result.read_text(encoding="utf-8"), summary)
            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertIn("❯ Conversation compacted <kbd>manual</kbd>:\n", query)
            self.assertIn(f"output/compact/001.{prompt_id}/result.md", query)
        # end with
    # end def

    def test_postcompact_auto_routes_to_consumer_and_marks_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "consumer"
            init_repo(repo, "https://github.com/luckydonald/example.git")
            prompt_id = "4ce3a7b9-3c0e-4a75-a5c7-e01a40f15aae"

            run_hook(
                repo,
                COMPACT_PROMPT_HOOK,
                {
                    "hook_event_name": "PostCompact",
                    "trigger": "auto",
                    "compact_summary": "Automatic compact summary",
                    "prompt_id": prompt_id,
                },
                "claude",
            )

            result = repo / "ai" / "output" / "compact" / f"001.{prompt_id}" / "result.md"
            self.assertEqual(result.read_text(encoding="utf-8"), "Automatic compact summary")
            query = (repo / "ai" / "query.md").read_text(encoding="utf-8")
            self.assertIn("❯ Conversation compacted <kbd>auto</kbd>:\n", query)
            self.assertFalse((repo / "ai" / "°base").exists())
        # end with
    # end def

    def test_postcompact_deduplicates_same_result_but_keeps_distinct_same_prompt_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            prompt_id = "0885277c-7e0b-42cd-8de8-b57be1a84c72"
            first_payload = {
                "hook_event_name": "PostCompact",
                "trigger": "auto",
                "compact_summary": "first summary",
                "prompt_id": prompt_id,
            }

            run_hook(repo, COMPACT_PROMPT_HOOK, first_payload, "claude")
            run_hook(repo, COMPACT_PROMPT_HOOK, first_payload, "claude")
            run_hook(
                repo,
                COMPACT_PROMPT_HOOK,
                {**first_payload, "compact_summary": "second summary"},
                "claude",
            )

            compact_root = repo / "ai" / "°base" / "output" / "compact"
            self.assertEqual(
                sorted(path.name for path in compact_root.iterdir()),
                [f"001.{prompt_id}", f"002.{prompt_id}"],
            )
            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertEqual(query.count("Conversation compacted <kbd>auto</kbd>"), 2)
        # end with
    # end def

    def test_postcompact_without_prompt_id_uses_numeric_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")

            run_hook(
                repo,
                COMPACT_PROMPT_HOOK,
                {
                    "hook_event_name": "PostCompact",
                    "trigger": "manual",
                    "compact_summary": "older payload",
                },
                "claude",
            )

            result = repo / "ai" / "°base" / "output" / "compact" / "001" / "result.md"
            self.assertEqual(result.read_text(encoding="utf-8"), "older payload")
        # end with
    # end def

    def test_compact_autoload_reuses_prompt_id_result_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            prompt_id = "51a1531e-7495-4677-a4cd-a0184d462662"
            run_hook(
                repo,
                COMPACT_PROMPT_HOOK,
                {
                    "hook_event_name": "PostCompact",
                    "trigger": "manual",
                    "compact_summary": "summary",
                    "prompt_id": prompt_id,
                },
                "claude",
            )

            run_hook(
                repo,
                PROMPT_HOOK,
                {
                    "prompt": "/compact\n  ⎿  Compacted\n  ⎿  Read notes.md (5 lines)\n",
                    "prompt_id": prompt_id,
                },
                "claude",
            )

            result_directory = (
                repo / "ai" / "°base" / "output" / "compact" / f"001.{prompt_id}"
            )
            self.assertTrue((result_directory / "result.md").is_file())
            self.assertTrue((result_directory / "autoloads.md").is_file())
            self.assertEqual(len(list(result_directory.parent.iterdir())), 1)
        # end with
    # end def

    def test_memory_session_start_compact_captures_latest_transcript_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            prompt_id = "8fe56710-dc43-4622-aa10-42dc1d5a9978"
            transcript = Path(tmp) / "transcript.jsonl"
            entries = [
                {
                    "type": "system",
                    "subtype": "compact_boundary",
                    "uuid": "boundary-manual",
                    "compactMetadata": {"trigger": "manual"},
                },
                {
                    "type": "user",
                    "parentUuid": "boundary-manual",
                    "isCompactSummary": True,
                    "message": {"role": "user", "content": "older summary"},
                },
                {"type": "user", "message": {"role": "user", "content": "ordinary turn"}},
                {
                    "type": "system",
                    "subtype": "compact_boundary",
                    "uuid": "boundary-auto",
                    "compactMetadata": {"trigger": "auto"},
                },
                {
                    "type": "user",
                    "parentUuid": "boundary-auto",
                    "isCompactSummary": True,
                    "message": {"role": "user", "content": "latest automatic summary"},
                },
            ]
            transcript.write_text(
                "".join(json.dumps(entry) + "\n" for entry in entries),
                encoding="utf-8",
            )

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "SessionStart",
                    "source": "compact",
                    "transcript_path": str(transcript),
                    "prompt_id": prompt_id,
                },
                extra_env={"HOME": str(home)},
            )

            result = (
                repo / "ai" / "°base" / "output" / "compact"
                / f"001.{prompt_id}" / "result.md"
            )
            self.assertEqual(result.read_text(encoding="utf-8"), "latest automatic summary")
            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertIn("Conversation compacted <kbd>auto</kbd>", query)
        # end with
    # end def

    def test_postcompact_and_session_start_fallback_store_one_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            home = Path(tmp) / "home"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            prompt_id = "9857e585-a9e0-4868-8731-09d106b5fc07"
            summary = "same summary from both lifecycle events"
            run_hook(
                repo,
                COMPACT_PROMPT_HOOK,
                {
                    "hook_event_name": "PostCompact",
                    "trigger": "manual",
                    "compact_summary": summary,
                    "prompt_id": prompt_id,
                },
                "claude",
            )
            transcript = Path(tmp) / "transcript.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "system",
                        "subtype": "compact_boundary",
                        "uuid": "boundary",
                        "compactMetadata": {"trigger": "manual"},
                    }
                )
                + "\n"
                + json.dumps(
                    {
                        "type": "user",
                        "parentUuid": "boundary",
                        "isCompactSummary": True,
                        "message": {"role": "user", "content": summary},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            run_hook(
                repo,
                MEMORY_HOOK,
                {
                    "hook_event_name": "SessionStart",
                    "source": "compact",
                    "transcript_path": str(transcript),
                    "prompt_id": prompt_id,
                },
                extra_env={"HOME": str(home)},
            )

            result_files = list(
                (repo / "ai" / "°base" / "output" / "compact").glob("*/result.md")
            )
            self.assertEqual(len(result_files), 1)
            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertEqual(query.count("Conversation compacted <kbd>manual</kbd>"), 1)
        # end with
    # end def

    def test_precompact_manual_with_instructions_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")

            run_hook(
                repo, COMPACT_PROMPT_HOOK,
                {"trigger": "manual", "custom_instructions": "focus on the auth refactor"},
                "claude",
            )

            compacted_file = repo / "ai" / "°base" / "output" / "compacted" / "001.md"
            self.assertTrue(compacted_file.exists(), "001.md should be created")
            self.assertEqual(compacted_file.read_text(encoding="utf-8"), "focus on the auth refactor")

            query = (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8")
            self.assertIn("[`/compact` possible prompt](./output/compacted/001.md)", query)

    def test_precompact_manual_no_instructions_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")

            run_hook(repo, COMPACT_PROMPT_HOOK, {"trigger": "manual", "custom_instructions": ""}, "claude")

            self.assertFalse((repo / "ai" / "°base" / "output" / "compacted").exists())
            self.assertFalse((repo / "ai" / "°base" / "query.md").exists())

    def test_precompact_auto_trigger_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")

            run_hook(
                repo, COMPACT_PROMPT_HOOK,
                {"trigger": "auto", "custom_instructions": "some text"},
                "claude",
            )

            self.assertFalse((repo / "ai" / "°base" / "output" / "compacted").exists())

    def test_precompact_sequential_numbering(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")

            run_hook(repo, COMPACT_PROMPT_HOOK, {"trigger": "manual", "custom_instructions": "first"}, "claude")
            run_hook(repo, COMPACT_PROMPT_HOOK, {"trigger": "manual", "custom_instructions": "second"}, "claude")

            compacted_dir = repo / "ai" / "°base" / "output" / "compacted"
            self.assertEqual((compacted_dir / "001.md").read_text(encoding="utf-8"), "first")
            self.assertEqual((compacted_dir / "002.md").read_text(encoding="utf-8"), "second")

    def test_precompact_consuming_repo_routes_to_plain_ai_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "consumer"
            init_repo(repo, "https://github.com/luckydonald/hoass_plugin-template.git")

            run_hook(
                repo, COMPACT_PROMPT_HOOK,
                {"trigger": "manual", "custom_instructions": "consumer repo prompt"},
                "claude",
            )

            compacted_file = repo / "ai" / "output" / "compacted" / "001.md"
            self.assertTrue(compacted_file.exists(), "consuming repo should route to ai/output/compacted/")
            self.assertFalse((repo / "ai" / "°base").exists(), "should NOT write to ai/°base/ outside base repo")

    def test_referenced_file_mention_untracked_gets_own_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            (repo / "sub").mkdir(parents=True, exist_ok=True)
            (repo / "sub" / "file.txt").write_text("hello\n", encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "please check @sub/file.txt for bugs"}, "claude")

            self.assertEqual(last_subject(repo), "[base] ai: referenced file for task added.")
            subjects = run_git(repo, "log", "--pretty=%s").stdout.strip().splitlines()
            self.assertIn("[base] ai: updated prompt", subjects)
            tracked = run_git(repo, "ls-files", "--", "sub/file.txt").stdout.strip()
            self.assertEqual(tracked, "sub/file.txt")

    def _consumer_with_committed_file(self, tmp: str) -> Path:
        repo = Path(tmp) / "myproject"
        init_repo(repo, "https://github.com/example/consumer.git")
        (repo / "sub").mkdir(parents=True, exist_ok=True)
        (repo / "sub" / "file.txt").write_text("v1\n", encoding="utf-8")
        run_git(repo, "add", "sub/file.txt")
        run_git(repo, "commit", "-m", "add file")
        return repo

    def test_referenced_file_mention_tracked_modified_gets_own_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._consumer_with_committed_file(tmp)
            (repo / "sub" / "file.txt").write_text("v2\n", encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "see `sub/file.txt` for context"}, "claude")

            self.assertEqual(last_subject(repo), "ai: referenced file for task added.")
            self.assertEqual(run_git(repo, "status", "--porcelain", "--", "sub/file.txt").stdout.strip(), "")

    def test_referenced_file_mention_tracked_clean_not_committed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._consumer_with_committed_file(tmp)

            run_hook(repo, PROMPT_HOOK, {"prompt": "see `sub/file.txt` for context"}, "claude")

            self.assertEqual(last_subject(repo), "ai: updated prompt")

    def test_referenced_file_mention_staged_new_file_committed_other_staged_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._consumer_with_committed_file(tmp)
            (repo / "sub" / "new.txt").write_text("new\n", encoding="utf-8")
            (repo / "sub" / "other.txt").write_text("other\n", encoding="utf-8")
            run_git(repo, "add", "sub/new.txt", "sub/other.txt")

            run_hook(repo, PROMPT_HOOK, {"prompt": "see `sub/new.txt` for context"}, "claude")

            self.assertEqual(last_subject(repo), "ai: referenced file for task added.")
            self.assertEqual(run_git(repo, "ls-files", "--", "sub/new.txt").stdout.strip(), "sub/new.txt")
            staged = run_git(repo, "diff", "--cached", "--name-only").stdout.strip().splitlines()
            self.assertEqual(staged, ["sub/other.txt"])

    def test_referenced_file_mention_during_merge_only_staged(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._consumer_with_committed_file(tmp)
            (repo / "sub" / "file.txt").write_text("v2\n", encoding="utf-8")
            git_dir = Path(run_git(repo, "rev-parse", "--absolute-git-dir").stdout.strip())
            (git_dir / "MERGE_HEAD").write_text(run_git(repo, "rev-parse", "HEAD").stdout, encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "see `sub/file.txt` for context"}, "claude")

            subjects = run_git(repo, "log", "--pretty=%s").stdout.strip().splitlines()
            self.assertNotIn("ai: referenced file for task added.", subjects)
            staged = run_git(repo, "diff", "--cached", "--name-only").stdout.strip().splitlines()
            self.assertIn("sub/file.txt", staged)

    def test_referenced_file_mention_gitignored_ai_path_not_committed(self):
        """Regression test: an `ai/`-prefixed mention used to be force-added
        (`git add -f`) past `.gitignore`; it must now be respected like any
        other gitignored path, with no `ai/`-prefix exception."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://github.com/luckydonald/base.git")
            (repo / ".gitignore").write_text("ai/°base/scratch/\n", encoding="utf-8")
            run_git(repo, "add", ".gitignore")
            run_git(repo, "commit", "-m", "add gitignore")
            (repo / "ai" / "°base" / "scratch").mkdir(parents=True, exist_ok=True)
            (repo / "ai" / "°base" / "scratch" / "notes.md").write_text("notes\n", encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "see @ai/°base/scratch/notes.md"}, "claude")

            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")
            tracked = run_git(
                repo, "-c", "core.quotepath=false", "ls-files", "--", "ai/°base/scratch/notes.md"
            ).stdout.strip()
            self.assertEqual(tracked, "")

    def test_referenced_file_mention_missing_file_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "myproject"
            init_repo(repo, "https://github.com/example/consumer.git")

            run_hook(repo, PROMPT_HOOK, {"prompt": "see @sub/does-not-exist.txt"}, "claude")

            self.assertEqual(last_subject(repo), "ai: updated prompt")

    def test_referenced_file_mention_rewritten_inline(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "myproject"
            init_repo(repo, "https://github.com/example/consumer.git")
            (repo / "sub").mkdir(parents=True, exist_ok=True)
            (repo / "sub" / "file.txt").write_text("hello\n", encoding="utf-8")

            run_hook(repo, PROMPT_HOOK, {"prompt": "please check @sub/file.txt for bugs"}, "claude")

            query_md = (repo / "ai" / "query.md").read_text(encoding="utf-8")
            self.assertIn(
                "❯ please check [@`sub/file.txt`](../sub/file.txt) for bugs\n\n",
                query_md,
            )

    def test_referenced_file_mention_inside_fenced_code_block_gets_trailing_summary(self):
        """An example mention inside a fenced code block (like this very /plan
        request's own diff example) must not have its raw text rewritten, but
        it still resolves and gets a summary block right after the fence."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "myproject"
            init_repo(repo, "https://github.com/example/consumer.git")
            (repo / "sub").mkdir(parents=True, exist_ok=True)
            (repo / "sub" / "file.txt").write_text("hello\n", encoding="utf-8")
            prompt = "before\n```diff\nsee @sub/file.txt\n```\nafter"

            run_hook(repo, PROMPT_HOOK, {"prompt": prompt}, "claude")

            query_md = (repo / "ai" / "query.md").read_text(encoding="utf-8")
            self.assertIn("```diff\nsee @sub/file.txt\n```", query_md)
            self.assertIn(
                "> _Mentioned file at line `3`:_ [@`sub/file.txt`](../sub/file.txt)",
                query_md,
            )
            self.assertEqual(last_subject(repo), "ai: referenced file for task added.")
            tracked = run_git(repo, "ls-files", "--", "sub/file.txt").stdout.strip()
            self.assertEqual(tracked, "sub/file.txt")

    def test_ask_user_question_answer_mention_gets_summary_and_commit(self):
        """Mentions inside an AskUserQuestion answer -- not just typed prompts --
        now also trigger the summary + auto-commit mechanism, since it's
        centralized in append_and_commit()."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "consumer"
            init_repo(repo, "https://github.com/example/consumer.git")
            (repo / "sub").mkdir(parents=True, exist_ok=True)
            (repo / "sub" / "file.txt").write_text("hello\n", encoding="utf-8")

            run_hook(
                repo,
                DECISION_HOOK,
                {
                    "hook_event_name": "PostToolUse",
                    "session_id": "session-mention",
                    "tool_name": "AskUserQuestion",
                    "tool_use_id": "toolu_mention_1",
                    "tool_input": {"questions": [
                        {
                            "question": "Pick one?",
                            "header": "Test",
                            "multiSelect": False,
                            "options": [
                                {"label": "A", "description": "first"},
                                {"label": "B", "description": "second"},
                            ],
                        }
                    ]},
                    "tool_response": {"answers": {"Pick one?": "please check @sub/file.txt"}},
                },
                "claude",
            )

            query_md = (repo / "ai" / "query.md").read_text(encoding="utf-8")
            self.assertIn("[@`sub/file.txt`](../sub/file.txt)", query_md)
            tracked = run_git(repo, "ls-files", "--", "sub/file.txt").stdout.strip()
            self.assertEqual(tracked, "sub/file.txt")

    def test_copilot_plan_marker_prompt_rendered_as_slash_plan(self):
        """Copilot CLI's `/plan` mode prepends a literal `[[PLAN]] ` marker to the
        submitted prompt (not a typed slash command); it should be rendered using
        the same `/plan ...` convention already used for Claude's typed prompts."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(repo, PROMPT_HOOK, {"prompt": "[[PLAN]] Investigate the bug."}, "copilot")

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "◆ /plan Investigate the bug.\n\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_copilot_harness_task_complete_reminder_is_not_logged(self):
        """The harness-injected autonomous-continuation nudge is not something the
        user typed and must be skipped rather than committed to query.md."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")
            reminder = (
                "You have not yet marked the task as complete using the task_complete tool. "
                "If you were planning, stop planning and start implementing."
            )

            run_hook(repo, PROMPT_HOOK, {"prompt": reminder}, "copilot")

            self.assertFalse((repo / "ai" / "°base" / "query.md").exists())
            self.assertEqual(last_subject(repo), "init")

    def test_copilot_cross_read_duplicate_firing_is_skipped(self):
        """When the actually-running harness is Copilot (detected via env vars)
        but this firing's baked-in CLI arg says `claude` — i.e. it came from
        Copilot's unconditional cross-read of `.claude/settings.json` alongside
        its own native `.github/hooks/generated.json` — the redundant duplicate
        firing must be skipped entirely, leaving no trace in query.md."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(
                repo,
                PROMPT_HOOK,
                {"prompt": "Capture this prompt"},
                "claude",
                extra_env={"COPILOT_CLI": "1"},
            )

            self.assertFalse((repo / "ai" / "°base" / "query.md").exists())
            self.assertEqual(last_subject(repo), "init")

    def test_copilot_native_firing_not_treated_as_duplicate(self):
        """The genuine native firing (ai_tool == 'copilot') still runs normally
        even when Copilot's env markers are present."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(
                repo,
                PROMPT_HOOK,
                {"prompt": "Capture this prompt"},
                "copilot",
                extra_env={"COPILOT_CLI": "1"},
            )

            self.assertEqual(
                (repo / "ai" / "°base" / "query.md").read_text(encoding="utf-8"),
                "◆ Capture this prompt\n\n",
            )
            self.assertEqual(last_subject(repo), "[base] ai: updated prompt")

    def test_copilot_record_memory_is_noop_even_on_session_start(self):
        """record-memory has no CLI arg to compare, so it must unconditionally
        no-op whenever the detected harness is Copilot (no local memory-file
        representation exists to sync from under Copilot)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "base"
            init_repo(repo, "https://luckydonald@github.com/luckydonald/base.git")

            run_hook(
                repo,
                MEMORY_HOOK,
                {"hook_event_name": "SessionStart", "session_id": "abc123"},
                extra_env={"COPILOT_CLI": "1"},
            )

            self.assertEqual(last_subject(repo), "init")


class ReffilesLibMentionsTests(unittest.TestCase):
    """Unit tests for °reffiles_lib.mentions, imported via importlib like °split_lib."""

    @classmethod
    def setUpClass(cls) -> None:
        import importlib

        lib_root = Path(__file__).resolve().parents[1] / "ai" / "hooks"
        sys.path.insert(0, str(lib_root))
        cls.mentions = importlib.import_module("°reffiles_lib.mentions")

    def test_extracts_at_mention_and_backtick_path(self):
        prompt = "look at @sub/file.txt and also `other/dir/file.md` please"
        self.assertEqual(
            self.mentions.extract_candidate_paths(prompt),
            ["sub/file.txt", "other/dir/file.md"],
        )

    def test_strips_trailing_punctuation(self):
        prompt = "see @sub/file.txt, and (`other/file.md`)."
        self.assertEqual(
            self.mentions.extract_candidate_paths(prompt),
            ["sub/file.txt", "other/file.md"],
        )

    def test_at_mention_inside_parentheses(self):
        self.assertEqual(self.mentions.extract_candidate_paths("see (@ai/somefile.txt)"), ["ai/somefile.txt"])
        mentions = self.mentions.find_mentions("see (@ai/somefile.txt) here")
        self.assertEqual(len(mentions), 1)
        self.assertEqual(mentions[0].candidates, [("ai/somefile.txt", None), ("ai/somefile.txt)", None)])
        self.assertEqual(mentions[0].suffix, ")")

    def test_at_mention_ignores_email_like_text(self):
        self.assertEqual(self.mentions.find_mentions("mail user@host/path now"), [])

    def test_ignores_non_path_tokens(self):
        prompt = "ping @someone and `just_a_word` about this"
        self.assertEqual(self.mentions.extract_candidate_paths(prompt), [])

    def test_dedupes_repeated_mentions(self):
        prompt = "see @sub/file.txt and again `sub/file.txt`"
        self.assertEqual(self.mentions.extract_candidate_paths(prompt), ["sub/file.txt"])

    def test_find_mentions_reports_candidates_and_line(self):
        content = "line one\nsee `sub/file.txt` here\n"
        mentions = self.mentions.find_mentions(content)
        self.assertEqual(len(mentions), 1)
        self.assertEqual(mentions[0].line, 2)
        self.assertFalse(mentions[0].at)
        self.assertEqual(mentions[0].candidates, [("sub/file.txt", None)])
        self.assertFalse(mentions[0].in_fence)

    def test_find_mentions_finds_mentions_inside_fenced_code_block(self):
        content = (
            "Implement `ai/some_file.md`,\n"
            "```diff\n"
            "- Implement `ai/some_file.md`,\n"
            "+ Implement [`ai/some_file.md`](./some_file.md),\n"
            "```\n"
            "and @src/other_file.py!\n"
        )
        mentions = self.mentions.find_mentions(content)
        self.assertEqual(
            [(m.line, m.candidates[0][0], m.in_fence) for m in mentions],
            [
                (1, "ai/some_file.md", False),
                (3, "ai/some_file.md", True),
                (4, "ai/some_file.md", True),
                (6, "src/other_file.py", False),
            ],
        )
        fenced = [m for m in mentions if m.in_fence]
        self.assertTrue(all(m.fence_end_line == 5 for m in fenced))
        self.assertTrue(all(m.fence_prefix == "" for m in fenced))

    def test_find_mentions_captures_indented_fence_prefix(self):
        content = (
            "- Example:\n"
            "  ```diff\n"
            "  - Implement `ai/some_file.md`,\n"
            "  ```\n"
            "see @sub/file.txt\n"
        )
        mentions = self.mentions.find_mentions(content)
        self.assertEqual(
            [(m.line, m.candidates[0][0], m.in_fence) for m in mentions],
            [(3, "ai/some_file.md", True), (5, "sub/file.txt", False)],
        )
        fenced = [m for m in mentions if m.in_fence]
        self.assertEqual(fenced[0].fence_end_line, 4)
        self.assertEqual(fenced[0].fence_prefix, "  ")

    def test_find_mentions_captures_blockquote_fence_prefix(self):
        content = (
            "> quoting:\n"
            "> ```diff\n"
            "> - see `sub/file.txt`,\n"
            "> ```\n"
        )
        mentions = self.mentions.find_mentions(content)
        self.assertEqual(len(mentions), 1)
        self.assertTrue(mentions[0].in_fence)
        self.assertEqual(mentions[0].fence_end_line, 4)
        self.assertEqual(mentions[0].fence_prefix, "> ")

    def test_find_mentions_drops_unterminated_fence(self):
        content = "before\n```diff\nsee @sub/file.txt\n"
        mentions = self.mentions.find_mentions(content)
        self.assertEqual(mentions, [])

    def test_split_candidates_prefers_whole_string_first(self):
        self.assertEqual(
            self.mentions.split_candidates("foo/bar.ext:1234#245"),
            [("foo/bar.ext:1234#245", None), ("foo/bar.ext:1234", "#245")],
        )

    def test_split_candidates_skips_non_numeric_colon_split(self):
        self.assertEqual(
            self.mentions.split_candidates("foo/bar.ext:1234#245:123"),
            [
                ("foo/bar.ext:1234#245:123", None),
                ("foo/bar.ext:1234#245", ":123"),
                ("foo/bar.ext:1234", "#245:123"),
            ],
        )

    def test_split_candidates_hash_line_fragment(self):
        self.assertEqual(
            self.mentions.split_candidates("docs/README.md#L123"),
            [("docs/README.md#L123", None), ("docs/README.md", "#L123")],
        )

    def test_split_candidates_colon_line_range_fragment(self):
        self.assertEqual(
            self.mentions.split_candidates("docs/README.md:346-400"),
            [("docs/README.md:346-400", None), ("docs/README.md", ":346-400")],
        )

    def test_split_candidates_does_not_split_url_shaped_colon(self):
        self.assertEqual(
            self.mentions.split_candidates("https://host/path"),
            [("https://host/path", None)],
        )

    def test_anchor_target_normalizes_hash_line(self):
        self.assertEqual(self.mentions.anchor_target("#L123"), "#L123")
        self.assertEqual(self.mentions.anchor_target("#123"), "#L123")

    def test_anchor_target_normalizes_hash_line_range(self):
        self.assertEqual(self.mentions.anchor_target("#123-456"), "#L123-L456")
        self.assertEqual(self.mentions.anchor_target("#L123-456"), "#L123-L456")
        self.assertEqual(self.mentions.anchor_target("#L123-L456"), "#L123-L456")

    def test_anchor_target_normalizes_colon_line(self):
        self.assertEqual(self.mentions.anchor_target(":345"), "#L345")

    def test_anchor_target_normalizes_colon_line_range(self):
        self.assertEqual(self.mentions.anchor_target(":346-400"), "#L346-L400")

    def test_anchor_target_passes_through_heading_anchor(self):
        self.assertEqual(self.mentions.anchor_target("#some-title"), "#some-title")


class ReffilesLibCommitTests(unittest.TestCase):
    """Unit tests for °reffiles_lib.commit's mention resolution and
    rendering."""

    @classmethod
    def setUpClass(cls) -> None:
        import importlib

        lib_root = Path(__file__).resolve().parents[1] / "ai" / "hooks"
        sys.path.insert(0, str(lib_root))
        cls.mentions_mod = importlib.import_module("°reffiles_lib.mentions")
        cls.commit_mod = importlib.import_module("°reffiles_lib.commit")

    def _resolved(
        self, *, line: int = 1, start: int = 0, end: int = 0, at: bool = False, suffix: str = "",
        in_fence: bool = False, fence_end_line: int | None = None, fence_prefix: str | None = None,
        path: str, fragment: str | None = None, abspath: str,
    ):
        return self.commit_mod.ResolvedMention(
            line=line, start=start, end=end, at=at, suffix=suffix, in_fence=in_fence,
            fence_end_line=fence_end_line, fence_prefix=fence_prefix,
            path=path, fragment=fragment, abspath=Path(abspath), relpath=path,
        )

    def test_mention_link_plain(self):
        log_path = Path("/repo/ai/query.md")
        mention = self._resolved(at=True, path="sub/file.txt", abspath="/repo/sub/file.txt")
        self.assertEqual(self.commit_mod.mention_link(mention, log_path), "[@`sub/file.txt`](../sub/file.txt)")

    def test_mention_link_hash_anchor(self):
        log_path = Path("/repo/ai/query.md")
        mention = self._resolved(path="docs/README.md", fragment="#some-title", abspath="/repo/docs/README.md")
        self.assertEqual(
            self.commit_mod.mention_link(mention, log_path),
            "[`docs/README.md`](../docs/README.md)[#some-title](../docs/README.md#some-title)",
        )

    def test_mention_link_colon_line_range(self):
        log_path = Path("/repo/ai/query.md")
        mention = self._resolved(at=True, path="docs/README.md", fragment=":346-400", abspath="/repo/docs/README.md")
        self.assertEqual(
            self.commit_mod.mention_link(mention, log_path),
            "[@`docs/README.md`](../docs/README.md)[:346-400](../docs/README.md#L346-L400)",
        )

    def test_fence_summary_lines_single(self):
        log_path = Path("/repo/ai/query.md")
        mention = self._resolved(line=124, path="path/foo/bar/foo.py", abspath="/repo/path/foo/bar/foo.py")
        lines = self.commit_mod.fence_summary_lines([mention], log_path, width=3)
        self.assertEqual(
            lines,
            ["> _Mentioned file at line `124`:_ [`path/foo/bar/foo.py`](../path/foo/bar/foo.py)"],
        )

    def test_fence_summary_lines_multiple(self):
        log_path = Path("/repo/ai/query.md")
        resolved = [
            self._resolved(line=2, path="./some/path/file", abspath="/repo/ai/some/path/file"),
            self._resolved(line=12, at=True, path="ai/query.md", abspath="/repo/ai/query.md"),
        ]
        lines = self.commit_mod.fence_summary_lines(resolved, log_path, width=2)
        self.assertEqual(
            lines,
            [
                "> <details><summary><i>Mentioned files:</i></summary>",
                ">",
                "> - line `02`: [`./some/path/file`](./some/path/file)",
                "> - line `12`: [@`ai/query.md`](./query.md)",
                ">",
                "> </details>",
            ],
        )

    def test_resolve_existing_prefers_whole_string_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "sub").mkdir()
            (repo / "sub" / "foo.ext:1234#245").write_text("literal\n", encoding="utf-8")
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                mention = self.mentions_mod.Mention(
                    line=1, start=0, end=0, at=True,
                    candidates=self.mentions_mod.split_candidates("sub/foo.ext:1234#245"),
                    suffix="", in_fence=False,
                )
                resolved = self.commit_mod.resolve_existing([mention], repo)
            finally:
                os.chdir(cwd)

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].path, "sub/foo.ext:1234#245")
        self.assertIsNone(resolved[0].fragment)

    def test_resolve_existing_falls_back_to_split_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "sub").mkdir()
            (repo / "sub" / "foo.ext:1234").write_text("split\n", encoding="utf-8")
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                mention = self.mentions_mod.Mention(
                    line=1, start=0, end=0, at=True,
                    candidates=self.mentions_mod.split_candidates("sub/foo.ext:1234#245"),
                    suffix="", in_fence=False,
                )
                resolved = self.commit_mod.resolve_existing([mention], repo)
            finally:
                os.chdir(cwd)

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].path, "sub/foo.ext:1234")
        self.assertEqual(resolved[0].fragment, "#245")

    def test_process_referenced_files_rewrites_inline_plain_mention(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "sub").mkdir()
            (repo / "sub" / "file.txt").write_text("hi\n", encoding="utf-8")
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                content, resolved = self.commit_mod.process_referenced_files(
                    "please check @sub/file.txt for bugs\n", repo, repo / "ai" / "query.md",
                )
            finally:
                os.chdir(cwd)

        self.assertEqual(content, "please check [@`sub/file.txt`](../sub/file.txt) for bugs\n")
        self.assertEqual(len(resolved), 1)

    def test_process_referenced_files_trailing_punctuation_outside_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "sub").mkdir()
            (repo / "sub" / "file.txt").write_text("hi\n", encoding="utf-8")
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                content, _ = self.commit_mod.process_referenced_files(
                    "see @sub/file.txt, thanks\n", repo, repo / "ai" / "query.md",
                )
            finally:
                os.chdir(cwd)

        self.assertEqual(content, "see [@`sub/file.txt`](../sub/file.txt), thanks\n")

    def test_process_referenced_files_parenthesized_mention(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "sub").mkdir()
            (repo / "sub" / "file.txt").write_text("hi\n", encoding="utf-8")
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                content, resolved = self.commit_mod.process_referenced_files(
                    "see (@sub/file.txt) there\n", repo, repo / "ai" / "query.md",
                )
            finally:
                os.chdir(cwd)

        self.assertTrue(content.startswith("see ([@`sub/file.txt`]("), content)
        self.assertTrue(content.endswith("sub/file.txt)) there\n"), content)
        self.assertEqual(resolved[0].suffix, ")")

    def test_process_referenced_files_prefers_real_file_with_trailing_punctuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "sub").mkdir()
            (repo / "sub" / "file.txt)").write_text("hi\n", encoding="utf-8")
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                content, resolved = self.commit_mod.process_referenced_files(
                    "see (@sub/file.txt)\n", repo, repo / "ai" / "query.md",
                )
            finally:
                os.chdir(cwd)

        self.assertEqual(resolved[0].path, "sub/file.txt)")
        self.assertEqual(resolved[0].suffix, "")

    def _process_with_skill(self, prompt: str) -> tuple[str, list]:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "ai" / "skills" / "code-style").mkdir(parents=True)
            (repo / "ai" / "skills" / "code-style" / "SKILL.md").write_text("x\n", encoding="utf-8")
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                return self.commit_mod.process_referenced_files(prompt, repo, repo / "ai" / "query.md")
            finally:
                os.chdir(cwd)

    def test_process_referenced_files_links_existing_skill(self):
        content, resolved = self._process_with_skill("please /code-style this, then /code-style.\n")
        self.assertEqual(content.count("[/code-style]("), 2, content)
        self.assertEqual(content.count("ai/skills/code-style/SKILL.md)"), 2, content)
        self.assertTrue(content.endswith(", then [/code-style](" + content.rsplit("](", 1)[1]), content)
        self.assertTrue(all(m.skill == "code-style" for m in resolved))

    def test_process_referenced_files_ignores_unknown_skill_and_paths(self):
        prompt = "run /nonexistent and look in /etc/code-style/x and /code-style/x and /code-style.md\n"
        content, resolved = self._process_with_skill(prompt)
        self.assertEqual(content, prompt)
        self.assertEqual(resolved, [])

    def test_stage_and_commit_mentions_ignores_skill_mentions(self):
        _, resolved = self._process_with_skill("/code-style\n")
        self.assertEqual(len(resolved), 1)
        with mock.patch.object(self.commit_mod.subprocess, "run") as run:
            self.commit_mod.stage_and_commit_mentions(resolved)
        run.assert_not_called()

    def test_process_referenced_files_two_mentions_same_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "a").mkdir()
            (repo / "b").mkdir()
            (repo / "a" / "one.txt").write_text("1\n", encoding="utf-8")
            (repo / "b" / "two.txt").write_text("2\n", encoding="utf-8")
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                content, resolved = self.commit_mod.process_referenced_files(
                    "see @a/one.txt and @b/two.txt\n", repo, repo / "ai" / "query.md",
                )
            finally:
                os.chdir(cwd)

        self.assertEqual(content, "see [@`a/one.txt`](../a/one.txt) and [@`b/two.txt`](../b/two.txt)\n")
        self.assertEqual(len(resolved), 2)

    def test_process_referenced_files_no_resolved_mentions_returns_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                content, resolved = self.commit_mod.process_referenced_files(
                    "see @sub/does-not-exist.txt\n", repo, repo / "ai" / "query.md",
                )
            finally:
                os.chdir(cwd)

        self.assertEqual(content, "see @sub/does-not-exist.txt\n")
        self.assertEqual(resolved, [])

    def test_process_referenced_files_fenced_mention_gets_summary_after_fence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "sub").mkdir()
            (repo / "sub" / "file.txt").write_text("hi\n", encoding="utf-8")
            prompt = "\n".join(["before", "```diff", "see @sub/file.txt", "```", "after", ""])
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                content, resolved = self.commit_mod.process_referenced_files(
                    prompt, repo, repo / "ai" / "query.md",
                )
            finally:
                os.chdir(cwd)

        expected = "\n".join([
            "before",
            "```diff",
            "see @sub/file.txt",
            "```",
            "",
            "> _Mentioned file at line `3`:_ [@`sub/file.txt`](../sub/file.txt)",
            "",
            "after",
            "",
        ])
        self.assertEqual(content, expected)
        self.assertEqual(len(resolved), 1)

    def test_process_referenced_files_fenced_mention_in_blockquote_gets_nested_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "sub").mkdir()
            (repo / "sub" / "file.txt").write_text("hi\n", encoding="utf-8")
            prompt = "\n".join(["> quoting:", "> ```diff", "> see @sub/file.txt", "> ```", "after", ""])
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                content, resolved = self.commit_mod.process_referenced_files(
                    prompt, repo, repo / "ai" / "query.md",
                )
            finally:
                os.chdir(cwd)

        expected = "\n".join([
            "> quoting:",
            "> ```diff",
            "> see @sub/file.txt",
            "> ```",
            ">",
            "> > _Mentioned file at line `3`:_ [@`sub/file.txt`](../sub/file.txt)",
            ">",
            "after",
            "",
        ])
        self.assertEqual(content, expected)
        self.assertEqual(len(resolved), 1)

    def test_process_referenced_files_two_fenced_blocks_each_get_own_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "a").mkdir()
            (repo / "b").mkdir()
            (repo / "a" / "one.txt").write_text("1\n", encoding="utf-8")
            (repo / "b" / "two.txt").write_text("2\n", encoding="utf-8")
            prompt = "\n".join([
                "```diff", "see @a/one.txt", "```", "middle", "```diff", "see @b/two.txt", "```", "",
            ])
            cwd = Path.cwd()
            os.chdir(repo)
            try:
                content, resolved = self.commit_mod.process_referenced_files(
                    prompt, repo, repo / "ai" / "query.md",
                )
            finally:
                os.chdir(cwd)

        expected = "\n".join([
            "```diff",
            "see @a/one.txt",
            "```",
            "",
            "> _Mentioned file at line `2`:_ [@`a/one.txt`](../a/one.txt)",
            "",
            "middle",
            "```diff",
            "see @b/two.txt",
            "```",
            "",
            "> _Mentioned file at line `6`:_ [@`b/two.txt`](../b/two.txt)",
            "",
            "",
        ])
        self.assertEqual(content, expected)
        self.assertEqual(len(resolved), 2)


if __name__ == "__main__":
    unittest.main()
