from __future__ import annotations

import re

_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_MIN_WORD_LEN = 5


def build_bm25_query(
    product_text: str,
    acronym_map: dict[str, str] | None = None,
) -> str:
    """Build an FTS5 OR query from expected-product text and acronym expansions.

    Returns a space-separated quoted OR query, e.g. '"natureza" OR "projeto"'.
    Returns an empty string if no significant words (5+ chars) are found.
    Diacritics are preserved — the FTS5 tokenizer (unicode61 remove_diacritics 2)
    normalises both index and query terms identically.
    """
    texts = [product_text]
    if acronym_map:
        for acronym, expansion in acronym_map.items():
            if acronym in product_text:
                texts.append(expansion)

    words: set[str] = set()
    for text in texts:
        for w in _PUNCT_RE.sub(" ", text).split():
            if len(w) >= _MIN_WORD_LEN:
                words.add(w.lower())

    if not words:
        return ""

    return " OR ".join(f'"{w}"' for w in sorted(words))
