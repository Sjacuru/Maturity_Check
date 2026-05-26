# Deterministic identifiers (law numbers, contract numbers, regulations) use regex search, not BM25

BM25 scores term frequency and proximity — it is appropriate for natural language where partial and fuzzy matches improve recall. Law numbers, regulation numbers, and contract numbers are exact identifiers where BM25 adds no value. However, some laws are themselves instructions (e.g., Lei 11.079/2004 is the PPP law) and finding them in case documents is valid evidence. We store these identifiers in the Rio Manual JSON with pre-computed regex search patterns covering known formatting variants (dot/no-dot, slash/space separator, full/abbreviated year — e.g., `11\.079`, `11079`, `11\.079[/\s]2004`). Retrieval uses SQLite with a Python-registered regex function. These identifiers are never used as BM25 query terms.

**Considered Options:** SQL LIKE vs regex. LIKE requires one pattern per variant; regex covers all variants in one expression. Regex chosen.

