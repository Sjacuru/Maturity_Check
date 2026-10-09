"""Shared helpers for the offline diagnostic scripts.

Sets the HuggingFace offline flags before any transformers import: a newer
huggingface_hub probes huggingface.co for an optional adapter_config.json even
for a fully-cached model, and that probe fails with CERTIFICATE_VERIFY_FAILED
behind the corporate proxy (see CLAUDE.md "Environment").
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Windows consoles default to cp1252 and mangle the Portuguese output of these
# scripts; rebind stdout/stderr rather than asking the caller to set a codepage.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "app.db"
LANCEDB_PATH = REPO_ROOT / "data" / "lancedb"
IPMP_DIR = REPO_ROOT / "data" / "ipmp"
PROFILE_DIR = REPO_ROOT / "data" / "retrieval_profiles"

if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

DEFAULT_PROCESS = "SMG-040_101607_2024"


def load_ipmp_scored_products() -> dict[int, list[str]]:
    """{acao_id: [scored product ids]} read straight from the JSON artifacts."""
    import json

    out: dict[int, list[str]] = {}
    for path in sorted(IPMP_DIR.glob("acao_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out[data["acao_id"]] = [
            p["id"] for p in data["produtos_esperados"] if p.get("scored", True)
        ]
    return out


def load_profiles() -> dict[int, dict]:
    """{acao_id: {product_id: profile_dict}} read straight from the JSON artifacts."""
    import json

    out: dict[int, dict] = {}
    for path in sorted(PROFILE_DIR.glob("acao_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out[data["acao_id"]] = data["expected_products"]
    return out


def active_terms(product: dict) -> list[dict]:
    return [
        t for t in product["query_terms"]
        if t.get("status", "active") in ("active", "validated")
    ]


def fts_query_for(product: dict) -> str:
    """Reproduce build_query_from_terms() without importing the retrieval module,
    so the diagnostic stays valid even if that module is mid-refactor."""
    clauses = []
    for t in active_terms(product):
        if t["encoding"] == "phrase":
            clauses.append(f'"{t["text"]}"')
        else:
            tokens = " ".join(f'"{x}"' for x in t["tokens"])
            clauses.append(f"NEAR({tokens}, {t['distance']})")
    return " OR ".join(clauses)


def vector_query_for(product: dict) -> str:
    """Reproduce hybrid._vector_query_text() for a product with a profile."""
    concepts = " ".join(c["text"] for c in product["retrieval_signal_concepts"])
    return f"{product['evidence_intent']} {concepts}".strip()
