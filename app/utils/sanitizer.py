# File: app/utils/sanitizer.py
"""
Public response sanitizer.

Removes vendor / model / infrastructure fingerprints and any internal architecture
references from text shown to end users. The UI never sees LLM vendor names,
internal module names, raw URLs, file paths, or backend identifiers.

Strategy:
- Bare tokens (e.g. `Groq`, `LangGraph`): stripped silently to ``.
- URLs (http://..., bolt://..., wss://..., localhost:port): stripped silently.
- Markdown link/image patterns `[label](url)` and `![alt](url)`: label is kept,
  URL is removed.
- Backticks/code-fence content: scanned for vendor names and replaced with neutral
  wording like `this assistant` only when it would otherwise leak a vendor.
"""

import re
from typing import Any, Dict


# Vendor / brand names that must never appear to end users.
_VENDOR_TOKENS = [
    "antigravity",
    "anvesh mishra",
]

_MODEL_TOKENS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-3",
    "groq",
    "mistral",
    "gemma",
    "claude",
    "gpt-4",
    "gpt-3.5",
]

_INTERNAL_TOKENS = [
    "langgraph stategraph",
    "the brain",
    "orchestration pipeline",
    "hybrid rag",
    "graphrag",
    "postgresql",
    "neo4j",
    "pinecone",
    "milestone ",
]


_URL_PATTERN = re.compile(
    r"(https?://\S+|bolt://\S+|wss?://\S+|"
    r"\bapp\.pinecone\.io\S*|\bapi\.groq\.com\S*|"
    r"\bhuggingface\.co\S*|\blocalhost:\d{2,5}\S*)",
    re.IGNORECASE,
)

# Markdown link: [label](url) -> keep label, drop url
_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# Internal-only markers that must never be shown to end users.
_INTERNAL_HEADER = re.compile(r"^={3,}.*?={3,}\s*$", re.MULTILINE)
_INTERNAL_HEADER_INLINE = re.compile(r"===\s+[A-Z &/\-_,()]+\s+===")

# Retrieval-metadata blocks:
#   [Context 1 | Source: foo - bar | Score: 0.123]
#   [Context 2 | Source Documentation - About | Score 0.001]
_CONTEXT_LINE = re.compile(
    r"\[\s*Context\s*\d+\b[^\]\n]*\]",
    re.IGNORECASE,
)
_SCORE_LINE = re.compile(r"\bScore\s*[:=]?\s*\d+\.\d+\b", re.IGNORECASE)
_URL_LINE = re.compile(r"\bURL\s*[:=]\s*\S+", re.IGNORECASE)
_SOURCE_LINE = re.compile(r"\bSource\s*[:=].*?(?=\s\s|\n|$)", re.IGNORECASE)

# LLM-internal labels sometimes leaked:
_LABEL_NOISE = re.compile(
    r"\b(?:LONG[- ]TERM\s+(?:USER|SESSION)\s+(?:MEMORY|CONTEXT)?|"
    r"SHORT[- ]TERM\s+CONVERSATION\s+WINDOW(?:\s*\(RECENT\s+TURNS\))?|"
    r"RETRIEVED\s+DOCUMENTATION(?:\s*\(HYBRID\s+RAG\))?|"
    r"STRUCTURAL\s+KNOWLEDGE\s+GRAPH(?:\s*\(GRAPHRAG\))?|"
    r"REAL[- ]TIME\s+EXTERNAL\s+TOOL\s+INTELLIGENCE|"
    r"USER\s+PROFILE\s*\(SQL\)|"
    r"ENDURING\s+USER\s+FACTS\s*\(SEMANTIC\s+VECTOR\s+STORE\)|"
    r"RECENT\s+MILESTONES\s*&\s*EVENTS\s*\(EPISODIC\s+MONGODB\))\b",
    re.IGNORECASE,
)

# User/Assistant turn dumps like: "User Hello" or "Assistant: How are you"
_ROLE_TURN_DUMP = re.compile(
    r"(?<!\w)(User|Assistant)\s*[:\-]\s+[^\n]{1,200}",
    re.IGNORECASE,
)

def _scrub_token(text: str, token: str) -> str:
    """Remove a vendor/model/internal token from `text` (case-insensitive, word-boundary)."""
    pattern = re.compile(r"\b" + re.escape(token) + r"\b", re.IGNORECASE)
    cleaned = pattern.sub("", text)
    cleaned = re.sub(r"[\s\.,;:!\?]+(?=[\s\.,;:!\?])", " ", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


def _strip_urls(text: str) -> str:
    """Remove URLs but keep any markdown-link label text and surrounding punctuation intact."""
    # Markdown links: drop only the (url) part, keep [label].
    text = _MD_LINK.sub(lambda m: f"[{m.group(1)}]" if m.group(2) else m.group(0), text)
    # Strip bare URLs. We use a non-capturing lookahead so we don't eat trailing whitespace/punctuation.
    text = _URL_PATTERN.sub("", text)
    # Collapse only runs of pure whitespace (not punctuation).
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Remove dangling whitespace immediately after a removed URL like "  " -> " ".
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def _strip_url_label_orphans(text: str) -> str:
    """Remove dangling `URL:` / `Source:` / `Score:` prefixes left after URL/score removal."""
    if not text:
        return text
    cleaned = text
    # Drop `URL:` followed by nothing or by punctuation/whitespace only.
    cleaned = re.sub(r"\bURL\s*[:=]\s*[\s.,;:!?]*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bSource\s*[:=]\s*[\s.,;:!?]*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bScore\s*[:=]\s*[\s.,;:!?]*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[\s*\]", "", cleaned)            # leftover empty brackets
    cleaned = re.sub(r"\(\s*\)", "", cleaned)            # leftover empty parens
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned


def _strip_source_disclosures(text: str) -> str:
    """Remove sentences / clauses that disclose information source or meta commentary.

    Implements a two-strategy pass for each marker phrase:

    1. Comma-flavored removal - if the disclosure continues into a trailing comma clause
       (e.g. ``"Based on my general knowledge, X."`` -> keep ``"X."``), drop everything from
       the start through the next comma+whitespace.
    2. Sentence-flavored removal - if the disclosure ends at a sentence boundary
       (``.`` / ``!`` / ``?``), drop it through the next sentence terminator.

    Walks the input repeatedly until no more matches are found.
    """
    if not text:
        return text

    markers = [
        "Note:",
        "Note -",
        "Based on my ",
        "Based on the ",
        "Based on provided ",
        "Based on real-time ",
        "According to my ",
        "According to the ",
        "According to provided ",
        "This answer is based on ",
        "This information is based on ",
        "This data is based on ",
        "This response is based on ",
        "I would also like to take this opportunity to ",
        "Also, I'd like to address ",
        "If you'd like more detail",
        "Let me know if you want more",
        "Feel free to ask",
    ]

    cleaned = text
    for marker in markers:
        # Build pattern: marker words with flexible whitespace
        words = marker.strip().split()
        escaped_words = [re.escape(w) for w in words]
        marker_pat = r"\b" + r"\s+".join(escaped_words) + r"\s*"

        # Strategy 1: comma-flavored - clause ends at next `,`. Strip marker through `, `.
        comma_pat = re.compile(
            marker_pat + r".*?,\s*",
            re.IGNORECASE | re.DOTALL,
        )
        while True:
            m = comma_pat.search(cleaned)
            if not m:
                break
            cleaned = cleaned[: m.start()] + cleaned[m.end():]

        # Strategy 2: sentence-flavored - clause ends at next `.!?`. Strip marker + clause.
        sent_pat = re.compile(
            marker_pat + r"[^.!?]*[.!?]",
            re.IGNORECASE | re.DOTALL,
        )
        while True:
            m = sent_pat.search(cleaned)
            if not m:
                break
            cleaned = cleaned[: m.start()] + cleaned[m.end():]

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def sanitize_text(text: Any) -> str:
    """Strip confidential, vendor, internal, and retriever-marker references from a string.

    IMPORTANT: This sanitizer must NEVER alter ordinary punctuation in valid answers.
    It only removes confidential/internal markers and trims dangling whitespace.
    Code blocks (```...```) are protected from all transformations.

    Defense-in-depth policy:
    1) URLs and markdown URLs (label preserved when present)
    2) Internal section headers (=== ... ===)
    3) Inline section labels
    4) [Context N | ... | Score: ...] retrieval metadata
    5) Source: ... / Score: ... / URL: ... lines and tokens
    6) Known noisy category labels
    7) User: ... / Assistant: ... turn dumps from leaked conversation-window
    8) Source-disclosure sentences ("based on my general knowledge", etc.)
    9) Vendor / model / internal tokens
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Protect code blocks from all sanitization patterns
    code_blocks = []
    def _save_code(m):
        code_blocks.append(m.group(0))
        return f"__CODEBLOCK_{len(code_blocks)-1}__"
    cleaned = re.sub(r"```[\w-]*\n.*?```", _save_code, text, flags=re.DOTALL)

    # 1) Drop URLs (preserve surrounding punctuation).
    cleaned = _strip_urls(cleaned)

    # 2) Drop orphan URL/Source/Score label prefixes left after URL removal.
    cleaned = _strip_url_label_orphans(cleaned)

    # 3) Drop stand-alone section headers (=== ... ===) lines.
    cleaned = _INTERNAL_HEADER.sub("", cleaned)

    # 4) Drop inline section labels like '=== LONG-TERM USER & SESSION MEMORY ==='.
    cleaned = _INTERNAL_HEADER_INLINE.sub("", cleaned)

    # 5) Drop "User: ... / Assistant: ..." turn dumps from leaked conversation-window.
    cleaned = _ROLE_TURN_DUMP.sub("", cleaned)

    # 6) Drop "[Context N | Source: ... | Score: 0.123]" style retrieval metadata.
    cleaned = _CONTEXT_LINE.sub("", cleaned)
    cleaned = _URL_LINE.sub("", cleaned)
    cleaned = _SCORE_LINE.sub("", cleaned)
    cleaned = _SOURCE_LINE.sub("", cleaned)
    cleaned = _strip_url_label_orphans(cleaned)

    # 7) Drop internal category labels.
    cleaned = _LABEL_NOISE.sub("", cleaned)

    # 8) Strip source-disclosure sentences.
    cleaned = _strip_source_disclosures(cleaned)

    # 9) Strip "Here's what I found" / "Based on your question" dumps.
    cleaned = re.sub(
        r"(?im)^\s*Here'?s what I found\s*:?\s*\n[\s\S]*?(?:Want me to dig deeper\?.*?)?\s*$",
        "",
        cleaned,
    )
    cleaned = re.sub(
        r"(?im)^\s*Based on your question\s*[-—–]+\s*\"[^\"]+\"\s*[-—–]+\s*Here's what I can offer.*?the most (?:useful|helpful) answer\??\s*$",
        "",
        cleaned,
    )

    # 10) Strip vendor / model / internal tokens.
    for tok in _INTERNAL_TOKENS + _MODEL_TOKENS + _VENDOR_TOKENS:
        cleaned = re.sub(r"\b" + re.escape(tok) + r"\b", "", cleaned, flags=re.IGNORECASE)

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        cleaned = cleaned.replace(f"__CODEBLOCK_{i}__", block)

    # Re-protect code blocks for final cleanup so regexes don't damage code
    final_blocks: list[str] = []
    cleaned = re.sub(
        r"```[\w-]*\n.*?```",
        lambda m: final_blocks.append(m.group(0)) or f"__FINALBLOCK_{len(final_blocks)-1}__",
        cleaned,
        flags=re.DOTALL,
    )

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = _strip_url_label_orphans(cleaned)

    for i, block in enumerate(final_blocks):
        cleaned = cleaned.replace(f"__FINALBLOCK_{i}__", block)

    return cleaned.strip()


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Walk a dict response payload and sanitize every string value recursively."""
    if payload is None:
        return {}
    return _walk(payload)


def _walk(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _walk(v) for k, v in node.items() if k not in _DROP_KEYS}
    if isinstance(node, list):
        return [_walk(v) for v in node]
    if isinstance(node, str):
        return sanitize_text(node)
    return node


# Dropped from public payloads because they leak internals.
_DROP_KEYS = {
    "model",
    "raw",
    "fallback_triggered",
    "usage",
    "prompt_context",
    "node_path",
    "errors",
    "internal_routing",
}

