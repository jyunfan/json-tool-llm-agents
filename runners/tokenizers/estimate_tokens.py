"""Lightweight token estimation utilities.

This is intentionally dependency-free for early benchmark diagnostics. Formal
experiments can later replace this with model-specific tokenizers.
"""

from __future__ import annotations

import re


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", re.UNICODE)


def estimate_tokens(text: str) -> int:
    """Return a rough, deterministic token estimate for text."""
    return len(TOKEN_RE.findall(text))
