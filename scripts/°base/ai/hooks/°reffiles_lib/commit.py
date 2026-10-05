"""Git side effects for files mentioned in a prompt, and the markdown link
each mention that resolves to a real file gets rendered as."""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

# Sibling-module import (the hooks dir can't be imported as a real package
# because parent dirs contain non-ASCII / hyphenated names).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
base_ai_commit_subject = import_module("°commit_style_lib").base_ai_commit_subject  # noqa: E402

from .mentions import Mention, anchor_target, find_mentions  # noqa: E402


def is_tracked(relpath: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relpath],
        capture_output=True,
    )
    return result.returncode == 0
# end def


def is_gitignored(relpath: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--", relpath],
        capture_output=True,
    )
    return result.returncode == 0
# end def


@dataclass
class ResolvedMention:
    line: int
    start: int
    end: int
    at: bool
    suffix: str
    in_fence: bool
    fence_end_line: int | None
    fence_prefix: str | None
    path: str
    fragment: str | None
    abspath: Path
    relpath: str
    skill: str | None = None
# end class


def resolve_existing(mentions: list[Mention], subproject: Path) -> list[ResolvedMention]:
    """Keep only the mentions with at least one candidate that resolves to a
    real file, picking the first (most conservative) candidate that does."""
    resolved: list[ResolvedMention] = []
    for mention in mentions:
        for path, fragment in mention.candidates:
            abspath = (subproject / path).resolve()
            if not abspath.is_file():
                continue
            # end if
            try:
                relpath = str(abspath.relative_to(Path.cwd()))
            except ValueError:
                continue  # outside the repo -- try the next candidate
            # end try
            suffix = mention.raw[len(path) + len(fragment or ""):] if mention.raw else mention.suffix
            resolved.append(
                ResolvedMention(
                    line=mention.line, start=mention.start, end=mention.end, at=mention.at,
                    suffix=suffix, in_fence=mention.in_fence,
                    fence_end_line=mention.fence_end_line, fence_prefix=mention.fence_prefix,
                    path=path, fragment=fragment, abspath=abspath, relpath=relpath, skill=mention.skill,
                )
            )
            break
        # end for
    # end for
    return resolved
# end def


def link_target(abspath: Path, log_path: Path) -> str:
    target = os.path.relpath(abspath, log_path.parent)
    return target if target.startswith("..") else f"./{target}"
# end def


def mention_link(mention: ResolvedMention, log_path: Path) -> str:
    """The markdown for one resolved mention: a bare-path link, plus a
    second link for its fragment (if any) whose target anchor is
    GitHub-style-normalized while its label stays exactly as typed."""
    target = link_target(mention.abspath, log_path)
    if mention.skill is not None:
        return f"[/{mention.skill}]({target})"
    # end if
    prefix = "@" if mention.at else ""
    text = f"[{prefix}`{mention.path}`]({target})"
    if mention.fragment is not None:
        text += f"[{mention.fragment}]({target}{anchor_target(mention.fragment)})"
    # end if
    return text
# end def


def fence_summary_lines(mentions: list[ResolvedMention], log_path: Path, width: int) -> list[str]:
    """Bare (unprefixed) lines listing the mentions found inside one fenced
    code block, in the same one-liner/`<details>` shape the whole-entry
    summary block used before inline rewriting was introduced."""
    if len(mentions) == 1:
        mention = mentions[0]
        line_no = f"{mention.line:0{width}d}"
        return [f"> _Mentioned file at line `{line_no}`:_ {mention_link(mention, log_path)}"]
    # end if

    lines = ["> <details><summary><i>Mentioned files:</i></summary>", ">"]
    for mention in mentions:
        line_no = f"{mention.line:0{width}d}"
        lines.append(f"> - line `{line_no}`: {mention_link(mention, log_path)}")
    # end for
    lines.append(">")
    lines.append("> </details>")
    return lines
# end def


def process_referenced_files(
    content: str, subproject: Path, log_path: Path
) -> tuple[str, list[ResolvedMention]]:
    """Rewrite every mention that resolves to a real file into a markdown
    link. A non-fenced mention is rewritten in place. A mention found inside
    a fenced code block is left untouched where it is, and instead listed in
    a summary block inserted right after that fence's closing delimiter,
    every line prefixed with that fence's own leading indent/blockquote
    prefix so it stays nested the same way the fence itself was.

    Assumes cwd is already the git root (as `resolve_log_path` leaves it).
    """
    mentions = find_mentions(content)
    resolved = resolve_existing(mentions, subproject)
    if not resolved:
        return content, []
    # end if

    lines = content.split("\n")
    width = len(str(len(lines)))

    inline_by_line: dict[int, list[ResolvedMention]] = {}
    fenced_by_fence: dict[tuple[int, str], list[ResolvedMention]] = {}
    for mention in resolved:
        if mention.in_fence:
            key = (mention.fence_end_line, mention.fence_prefix)
            fenced_by_fence.setdefault(key, []).append(mention)
        else:
            inline_by_line.setdefault(mention.line, []).append(mention)
        # end if
    # end for

    for lineno, line_group in inline_by_line.items():
        line = lines[lineno - 1]
        for mention in sorted(line_group, key=lambda m: m.start, reverse=True):
            line = line[:mention.start] + mention_link(mention, log_path) + mention.suffix + line[mention.end:]
        # end for
        lines[lineno - 1] = line
    # end for

    for fence_end_line, fence_prefix in sorted(fenced_by_fence, key=lambda key: key[0], reverse=True):
        fence_group = fenced_by_fence[(fence_end_line, fence_prefix)]
        body = fence_summary_lines(fence_group, log_path, width)
        blank = fence_prefix.rstrip()
        block = [blank, *(f"{fence_prefix}{body_line}" for body_line in body), blank]
        lines[fence_end_line:fence_end_line] = block
    # end for

    return "\n".join(lines), resolved
# end def


_IN_PROGRESS_MARKERS = ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply")


def has_uncommitted_changes(relpath: str) -> bool:
    """True if `relpath` is untracked, or differs from `HEAD` in the index or the working tree."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", relpath],
        capture_output=True, text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())
# end def


def operation_in_progress() -> bool:
    """True while a merge, rebase, cherry-pick or revert is underway, where `git commit --only` is refused."""
    for marker in _IN_PROGRESS_MARKERS:
        result = subprocess.run(["git", "rev-parse", "--git-path", marker], capture_output=True, text=True)
        if result.returncode == 0 and Path(result.stdout.strip()).exists():
            return True
        # end if
    # end for
    return False
# end def


def stage_and_commit_mentions(resolved: list[ResolvedMention]) -> None:
    """Best-effort: commit the files in `resolved` that have changes -- untracked, staged, or modified previously-committed ones --
    each on its own via `--only`, so other staged files stay staged. Respects .gitignore, leaves unchanged files alone, and only
    stages (no commit) while a merge/rebase/cherry-pick is in progress. Failures are reported on stderr."""
    busy: bool | None = None  # looked up lazily, once, on the first file that really needs it
    seen: set[str] = set()
    for mention in resolved:
        if mention.skill is not None or mention.relpath in seen:
            continue
        # end if
        seen.add(mention.relpath)

        if not is_tracked(mention.relpath) and is_gitignored(mention.relpath):
            continue
        # end if

        if not has_uncommitted_changes(mention.relpath):
            continue
        # end if

        added = subprocess.run(["git", "add", "--", mention.relpath], capture_output=True, text=True)
        if added.returncode != 0:
            print(f"reffiles: git add failed for {mention.relpath}: {added.stderr.strip()}", file=sys.stderr)
            continue
        # end if
        if busy is None:
            busy = operation_in_progress()
        # end if
        if busy:
            continue
        # end if

        committed = subprocess.run(
            ["git", "commit", "--no-verify", "--only", "-m", base_ai_commit_subject("ai: referenced file for task added."),
             "--", mention.relpath],
            capture_output=True, text=True,
        )
        if committed.returncode != 0:
            print(f"reffiles: git commit failed for {mention.relpath}: {committed.stderr.strip() or committed.stdout.strip()}",
                  file=sys.stderr)
        # end if
    # end for
# end def
