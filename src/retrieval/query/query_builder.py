from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ingestion.retrieval_profile import NearQueryTerm, PhraseQueryTerm

_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_MIN_WORD_LEN = 5


def build_query_from_terms(
    terms: list[PhraseQueryTerm | NearQueryTerm],
) -> str:
    """Build an FTS5 OR query from a list of retrieval profile QueryTerm objects.

    Phrase terms become "exact phrase" clauses.
    NEAR terms become NEAR("tok1" "tok2", N) proximity clauses.
    Returns empty string when terms is empty.
    """
    clauses: list[str] = []
    for term in terms:
        if term.encoding == "phrase":
            clauses.append(f'"{term.text}"')
        else:  # near
            token_str = " ".join(f'"{t}"' for t in term.tokens)
            clauses.append(f"NEAR({token_str}, {term.distance})")
    return " OR ".join(clauses)


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
