#!/usr/bin/env python3
"""UserPromptSubmit hook: make the Markdown code style load for plans.

`/plan` is a built-in command, not a skill, so the `code-style` skill only loads when the model happens to judge its description
relevant. This hook is the deterministic backstop: while the session is in plan mode, or when the prompt starts with `/plan`, it injects
`additionalContext` telling the model to read `ai/skills/code-style/references/md.md` before writing any plan prose.

Synchronous on purpose (no `async`), since async hook output cannot reach the model.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _lib import read_payload  # noqa: E402

CONTEXT = (
    "Plan mode: before writing or editing any plan prose, read `ai/skills/code-style/references/md.md` directly and apply it "
    "(break lines only at sentence ends, not at a fixed column). Do this once per session."
)


def is_plan_prompt(payload: dict) -> bool:
    prompt = str(payload.get("prompt") or "").lstrip()
    return payload.get("permission_mode") == "plan" or prompt == "/plan" or prompt.startswith("/plan ")
# end def


def main() -> int:
    payload = read_payload()
    if is_plan_prompt(payload):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": CONTEXT}}))
    # end if
    return 0
# end def


if __name__ == "__main__":
    raise SystemExit(main())
# end if
