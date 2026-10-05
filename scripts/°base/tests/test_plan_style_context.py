from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "ai" / "hooks" / "plan-style-context" / "hook.py"


def run(payload: dict) -> str:
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, check=True).stdout


class PlanStyleContextTests(unittest.TestCase):
    def test_slash_plan_injects_md_style_context(self):
        out = json.loads(run({"prompt": "/plan do it"}))
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("references/md.md", out["hookSpecificOutput"]["additionalContext"])

    def test_plan_permission_mode_injects_context(self):
        self.assertIn("references/md.md", run({"prompt": "Plan @x", "permission_mode": "plan"}))

    def test_other_prompts_inject_nothing(self):
        self.assertEqual(run({"prompt": "hello", "permission_mode": "default"}), "")
        self.assertEqual(run({"prompt": "/planet"}), "")


if __name__ == "__main__":
    unittest.main()
