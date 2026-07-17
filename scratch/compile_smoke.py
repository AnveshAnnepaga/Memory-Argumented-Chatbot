"""Compile + import smoke test for all touched modules."""
import sys
import traceback

files = [
    "app/orchestration/nodes.py",
    "app/orchestration/router.py",
    "app/orchestration/workflow.py",
    "app/orchestration/schemas.py",
    "app/orchestration/state.py",
    "app/orchestration/pipeline.py",
    "app/core/settings.py",
    "app/api/v1/chat.py",
    "app/utils/sanitizer.py",
    "app/utils/__init__.py",
    "app/api/v1/memory.py",
    "app/api/v1/knowledge.py",
    "app/rag/pipeline.py",
    "app/rag/retriever.py",
    "app/memory/retriever.py",
    "app/tools/pipeline.py",
]

# 1) parse-only check
import ast
failures = []
for p in files:
    try:
        with open(p, encoding="utf-8") as f:
            ast.parse(f.read(), p)
    except Exception as exc:
        failures.append((p, exc))
        print(f"PARSE FAIL: {p}: {exc}")

if failures:
    sys.exit(1)
print("All 16 files PARSE OK")

# 2) Import + test
sys.path.insert(0, ".")
from app.utils.sanitizer import sanitize_text, sanitize_payload

# Allow validated cases where leading/trailing spaces or stray ` .` remain acceptable
def _norm(s: str) -> str:
    return s.strip()


test_cases = [
    ("Hello! I'm ready.", "Hello! I'm ready."),
    ("The president of India is Droupadi Murmu.", "The president of India is Droupadi Murmu."),
    ("Here is a [link](https://example.com/foo).", "Here is a [link]."),
    ("[Context 1 | Source: foo - bar | Score: 0.001]", ""),
    ("URL: https://example.com", ""),
    ("=== LONG-TERM USER & SESSION MEMORY ===", ""),
    ("User: Hello\nAssistant: Hi", ""),
    ("Great question. I'd love more context.", "Great question. I'd love more context."),
    ("Groq is fast.", "is fast."),     # 'Groq' stripped
    ("LangChain is popular.", "LangChain is popular."),  # framework name preserved
    ("Based on my general knowledge, X.", "X."),
]

print("\n--- Sanitizer smoke tests ---")
all_pass = True
for src, expected in test_cases:
    out = sanitize_text(src)
    n_out = _norm(out)
    n_exp = _norm(expected)
    ok = n_out == n_exp
    all_pass = all_pass and ok
    marker = "OK  " if ok else "FAIL"
    print(f"{marker} | src={src!r}\n        out={out!r}\n        exp={expected!r}")

print("\n--- All tests passed ---" if all_pass else "\n--- Some tests FAILED ---")
sys.exit(0 if all_pass else 2)
