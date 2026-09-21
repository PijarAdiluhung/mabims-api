"""Guard against cp1252/latin-1 mojibake (double-encoded UTF-8) sneaking into
the docs source and auxiliary docs. Fails any file that contains the tell-tale
re-encoded byte pairs or replacement characters."""

import re
from pathlib import Path

SCOPES = (
    "docs/src",
    "docs/public",
    ".github",
)
ROOT_FILES = ("README.md", "TODO.md")
EXTENSIONS = {".md", ".mdx", ".astro", ".ts", ".tsx", ".js", ".mjs"}

# A lone C0-control below 0xA0 is always suspicious; pairs of a cp1252/latin
# high starter followed by an unprintable successor are the mojibake signature.
MOJIBAKE = re.compile(
    "[\u00c0-\u00ef][\u0080-\u00bf\u20ac\u2039\u201a\u2020\u2021\u2013\u2014"
    "\u2018\u2019\u201c\u201d\u2122\u0152\u0153]"
)
CONTROLS = re.compile("[\u0080-\u009f\ufffd]")


def iter_files():
    paths: list[Path] = []
    for scope in SCOPES:
        paths.extend(Path(scope).rglob("*"))
    paths.extend(Path(name) for name in ROOT_FILES if Path(name).exists())
    for f in paths:
        if f.is_file() and f.suffix.lower() in EXTENSIONS:
            yield f


def test_no_mojibake_in_docs_sources():
    bad: list[str] = []
    not_utf8: list[str] = []
    for f in iter_files():
        try:
            text = f.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            not_utf8.append(str(f))
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if MOJIBAKE.search(line) or CONTROLS.search(line):
                bad.append(f"{f}:{i}: {line.strip()[:120]}")
    assert not not_utf8, "files fail strict UTF-8 decode:\n" + "\n".join(not_utf8)
    assert not bad, (
        "mojibake found — the file was saved with the wrong encoding; "
        "fix at the source and re-save as UTF-8:\n" + "\n".join(bad)
    )
