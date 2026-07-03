from __future__ import annotations

import re

INLINE_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")


def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    return INLINE_WHITESPACE_RE.sub(" ", text).strip()


def normalize_multiline_text(text: str) -> str:
    if not text:
        return ""
    lines = [normalize_whitespace(line) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)
