"""Debug the marker pattern issue."""
import re

def _make_marker_pattern(marker: str) -> str:
    words = marker.strip().split()
    escaped_words = [re.escape(w) for w in words]
    return r"\b" + r"\s+".join(escaped_words) + r"\s*"

marker = "Based on my "
marker_pat = _make_marker_pattern(marker)
print(f"Marker: {marker!r}")
print(f"Pattern: {marker_pat!r}")

# Test comma-flavored
comma_pat = re.compile(marker_pat + r".*?,\s*", re.IGNORECASE | re.DOTALL)
text = "Based on my general knowledge, X."
print(f"Input: {text!r}")
m = comma_pat.search(text)
if m:
    print(f"Match: {m.group()!r} at {m.start()}-{m.end()}")
    cleaned = text[:m.start()] + text[m.end():]
    print(f"Cleaned: {cleaned!r}")
else:
    print("No match!")