"""Pure text extraction of file-path mentions from a prompt."""
from __future__ import annotations

import re
from dataclasses import dataclass

_AT_MENTION_RE = re.compile(r"(?<![^\s(\[{\"'])@([^\s`]+)")
_BACKTICK_MENTION_RE = re.compile(r"`([^`\n]+)`")
_TRAILING_PUNCT = ".,;:!?)]}\"'"
_SKILL_RE = re.compile(r"(?<![^\s(\[{\"'])/([a-z0-9][a-z0-9-]*)(?![\w/-]|\.\w)")
_FENCE_RE = re.compile(r"^([ \t>]*)(```|~~~)")
_LINE_FRAGMENT_RE = re.compile(r"^#L?(\d+)(?:-L?(\d+))?$")
_COLON_FRAGMENT_RE = re.compile(r"^:(\d+)(?:-(\d+))?$")


def extract_candidate_paths(prompt: str) -> list[str]:
    """@mention and backtick-quoted candidate paths containing '/', deduped, order-preserved."""
    seen: set[str] = set()
    out: list[str] = []
    for regex in (_AT_MENTION_RE, _BACKTICK_MENTION_RE):
        for m in regex.finditer(prompt):
            candidate = m.group(1).strip().rstrip(_TRAILING_PUNCT)
            if "/" in candidate and candidate not in seen:
                seen.add(candidate)
                out.append(candidate)
            # end if
        # end for
    # end for
    return out
# end def


def anchor_target(fragment: str) -> str:
    """The GitHub-style link-target anchor for a raw `#...`/`:...` fragment
    suffix, exactly as it was typed. Line and line-range fragments (however
    written) normalize to `#Lxx` / `#Lxx-Lyy`; anything else starting with
    `#` is treated as a heading anchor and passed through verbatim, with no
    validation against real headings in the target file."""
    match = _COLON_FRAGMENT_RE.match(fragment) or _LINE_FRAGMENT_RE.match(fragment)
    if match is None:
        return fragment
    # end if
    start, end = match.group(1), match.group(2)
    if end is None:
        return f"#L{start}"
    # end if
    return f"#L{start}-L{end}"
# end def


def split_candidates(raw: str) -> list[tuple[str, str | None]]:
    """Ordered `(path, fragment)` candidates for a mention's raw text, most
    conservative first: the whole string as a literal path, then
    progressively shorter prefixes cut at each `#`/`:` position, rightmost
    first -- so a real file whose name happens to contain `#` or `:` is
    preferred over interpreting the tail as a fragment. A `:` position only
    counts as a possible cut when everything from there on looks like a
    line/line-range fragment; otherwise it's left alone, so tokens shaped
    like `https://...` never get split there. Any candidate whose `path`
    half has no `/` is dropped."""
    positions = [i for i, ch in enumerate(raw) if ch == "#"]
    positions += [i for i, ch in enumerate(raw) if ch == ":" and _COLON_FRAGMENT_RE.match(raw[i:])]
    candidates: list[tuple[str, str | None]] = [(raw, None)]
    for i in sorted(positions, reverse=True):
        candidates.append((raw[:i], raw[i:]))
    # end for
    return [(path, fragment) for path, fragment in candidates if "/" in path]
# end def


@dataclass
class Mention:
    line: int                                  # 1-indexed line number of the match
    start: int                                 # start offset of the full raw match within that line
    end: int                                   # end offset of the full raw match within that line
    at: bool                                   # True for @mention, False for backtick mention
    candidates: list[tuple[str, str | None]]   # ordered (path, fragment) options, most-conservative first
    suffix: str                                # trailing punctuation stripped off the match, restored after the rendered link
    in_fence: bool                             # True if found inside a fenced code block
    fence_end_line: int | None = None          # that fence's closing delimiter line (set only when in_fence)
    fence_prefix: str | None = None            # that fence's leading prefix string, verbatim (set only when in_fence)
    skill: str | None = None                   # the slug, for a `/skill` mention (then `candidates` is its SKILL.md path)
    raw: str = ""                              # the match text before trailing punctuation was stripped (empty: use `suffix` as is)
# end class


def mention_candidates(raw: str) -> tuple[list[tuple[str, str | None]], str]:
    """`(candidates, suffix)` for a mention's raw text. The candidates are those of the text with trailing punctuation trimmed (so
    `@ai/a.txt)` resolves to `ai/a.txt`), followed by the untrimmed text as a last-resort literal path, in case a real file is named
    with the trailing punctuation. `suffix` is the trimmed punctuation."""
    trimmed = raw.rstrip(_TRAILING_PUNCT)
    suffix = raw[len(trimmed):]
    candidates = split_candidates(trimmed)
    if suffix and "/" in raw:
        candidates.append((raw, None))
    # end if
    return candidates, suffix
# end def


def skill_path(slug: str) -> str:
    return f"ai/skills/{slug}/SKILL.md"
# end def


def line_skill_mentions(line: str) -> list[tuple[int, int, str]]:
    """(start, end, slug) tuples for `/slug` tokens on a single line. Whether the skill really exists is decided on resolving."""
    return [(m.start(), m.end(), m.group(1)) for m in _SKILL_RE.finditer(line)]
# end def


def line_mentions(line: str) -> list[tuple[int, int, bool, list[tuple[str, str | None]], str, str]]:
    """(start, end, at, candidates, suffix, raw) tuples for @mentions and backtick mentions on a single line."""
    found: list[tuple[int, int, bool, list[tuple[str, str | None]], str, str]] = []
    for regex, at in ((_AT_MENTION_RE, True), (_BACKTICK_MENTION_RE, False)):
        for m in regex.finditer(line):
            raw = m.group(1)
            candidates, suffix = mention_candidates(raw)
            if candidates:
                found.append((m.start(), m.end(), at, candidates, suffix, raw))
            # end if
        # end for
    # end for
    return found
# end def


def find_mentions(content: str) -> list[Mention]:
    """Line-aware, fence-aware mention scan. Mentions found inside a ``` or
    ~~~ fenced block (including one indented under a list item, or nested in
    a `>` blockquote) are still returned, stamped with `in_fence=True`,
    `fence_end_line` (that fence's closing delimiter line), and
    `fence_prefix` (that fence's leading indent/blockquote prefix, verbatim)
    -- so a caller can list them in a summary after the fence instead of
    rewriting the fenced text itself. A fence left unterminated at the end
    of `content` contributes no mentions.

    Matches are not deduplicated -- each occurrence becomes its own `Mention`.
    """
    mentions: list[Mention] = []
    fence_pending: list[Mention] = []
    in_fence = False
    fence_prefix = ""
    for lineno, line in enumerate(content.split("\n"), start=1):
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            if not in_fence:
                in_fence = True
                fence_prefix = fence_match.group(1)
                fence_pending = []
            else:
                for pending in fence_pending:
                    pending.fence_end_line = lineno
                    pending.fence_prefix = fence_prefix
                # end for
                mentions.extend(fence_pending)
                in_fence = False
                fence_pending = []
            # end if
            continue
        # end if
        matches = [
            Mention(line=lineno, start=start, end=end, at=at, candidates=candidates, suffix=suffix, in_fence=in_fence, raw=raw)
            for start, end, at, candidates, suffix, raw in line_mentions(line)
        ]
        matches += [
            Mention(line=lineno, start=start, end=end, at=False, candidates=[(skill_path(slug), None)], suffix="", in_fence=in_fence,
                    skill=slug)
            for start, end, slug in line_skill_mentions(line)
        ]
        if in_fence:
            fence_pending.extend(matches)
        else:
            mentions.extend(matches)
        # end if
    # end for
    return mentions
# end def
