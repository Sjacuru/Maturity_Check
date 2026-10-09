"""Are the two search stores trustworthy? Integrity audit of SQLite + LanceDB.

Retrieval reads from three places that must agree: the `chunks` table (the
canonical extracted artifact store, ADR-0028), the `chunks_fts` FTS5 index that
BM25 queries, and one LanceDB table per process for the vector lane. Nothing in
the codebase checks that they agree, and two of the three are built once and
reused (FTS5 by trigger, LanceDB by ensure_vector_index_exists' reuse semantics,
ADR-0035), so a divergence would be silent and permanent.

Every check below answers one of two questions the project owner posed:
  * can a store hand back the WRONG rows (another process's, or stale ones)?
  * can a store FAIL TO hand back rows that exist?

Exit code is 0 when every check passes, 1 when any FAILHA is reported, so this
can gate a run.

Usage:
    python scripts/diagnostics/audit_search_stores.py
    python scripts/diagnostics/audit_search_stores.py --process SMG-040_101607_2024
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

DB_PATH = ROOT / "data" / "app.db"
LANCEDB_PATH = ROOT / "data" / "lancedb"

_failures: list[str] = []
_warnings: list[str] = []


def ok(label: str, detail: str = "") -> None:
    print(f"  [ok]     {label}{(' — ' + detail) if detail else ''}")


def fail(label: str, detail: str) -> None:
    _failures.append(f"{label}: {detail}")
    print(f"  [FALHA]  {label} — {detail}")


def warn(label: str, detail: str) -> None:
    _warnings.append(f"{label}: {detail}")
    print(f"  [aviso]  {label} — {detail}")


def section(title: str) -> None:
    print(f"\n{'=' * 90}\n{title}\n{'=' * 90}")


# ── 1. the chunks table itself ───────────────────────────────────────────────

def audit_chunks(con: sqlite3.Connection) -> dict[str, list[tuple]]:
    section("1. tabela chunks — a fonte canônica (ADR-0028)")

    rows = con.execute(
        "SELECT process_number, filename, page_number, chunk_index, text FROM chunks"
    ).fetchall()
    print(f"  {len(rows)} linhas no total")

    by_process: dict[str, list[tuple]] = defaultdict(list)
    for r in rows:
        by_process[r[0]].append(r)
    for pn, rs in sorted(by_process.items()):
        files = len({x[1] for x in rs})
        print(f"    {pn:<28} {len(rs):>6} chunks  {files} arquivo(s)")

    # A duplicated identity key would make retrieval return the same chunk twice
    # and make the LanceDB join ambiguous.
    keys = Counter((r[0], r[1], r[2], r[3]) for r in rows)
    dupes = [k for k, n in keys.items() if n > 1]
    if dupes:
        fail("chave de identidade duplicada",
             f"{len(dupes)} chave(s) (processo, arquivo, página, chunk_index) repetida(s)")
    else:
        ok("chave de identidade única", "(processo, arquivo, página, chunk_index)")

    # Empty text would be retrievable but carry no evidence.
    empty = [r[:4] for r in rows if not (r[4] or "").strip()]
    if empty:
        fail("chunks com texto vazio", f"{len(empty)}: {empty[:5]}")
    else:
        ok("nenhum chunk com texto vazio")

    # Exact text duplicates inside one process are what _prefilter_near_duplicates
    # exists to absorb; they are not corruption, but their volume matters because
    # they consume the per-product candidate budget before dedup runs.
    #
    # Measured on both forms, because they disagree sharply and only one of them
    # is what any consumer sees: the RAW column has no duplicates at all in this
    # corpus, while after strip_extraction_noise — which is what the gate reads,
    # and what the pre-gate dedup compares — 9.4% of rows become exact copies.
    # Auditing only the raw column reports a clean store and hides the fact that
    # the same risk-matrix page exists four times over.
    from evaluation.evidence_selection import strip_extraction_noise

    for pn, rs in sorted(by_process.items()):
        for label, project in (
            ("cru", lambda t: t),
            ("após strip_extraction_noise", strip_extraction_noise),
        ):
            digests = Counter(
                hashlib.sha256(project(r[4] or "").encode()).hexdigest() for r in rs
            )
            repeated = {d: n for d, n in digests.items() if n > 1}
            extra = sum(n - 1 for n in repeated.values())
            if extra:
                worst = max(repeated.values())
                warn(f"texto repetido em {pn} ({label})",
                     f"{len(repeated)} texto(s) distinto(s) em {extra} linha(s) extra "
                     f"({100 * extra / len(rs):.1f}%); o mais repetido aparece {worst}x")
            else:
                ok(f"sem texto repetido em {pn} ({label})")

    return by_process


# ── 2. redundant copies of the same corpus ───────────────────────────────────

def audit_redundancy(by_process: dict[str, list[tuple]]) -> None:
    section("2. redundância entre processos")

    fingerprints: dict[str, frozenset] = {}
    for pn, rs in by_process.items():
        fingerprints[pn] = frozenset(
            hashlib.sha256((r[4] or "").encode()).hexdigest() for r in rs
        )

    names = sorted(fingerprints)
    found = False
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            fa, fb = fingerprints[a], fingerprints[b]
            if not fa or not fb:
                continue
            shared = len(fa & fb)
            if shared and shared == len(fa) == len(fb):
                found = True
                warn("corpus duplicado entre processos",
                     f"'{a}' e '{b}' têm conteúdo idêntico ({shared} textos distintos)")
            elif shared > 0.5 * min(len(fa), len(fb)):
                found = True
                warn("corpus parcialmente duplicado",
                     f"'{a}' e '{b}' compartilham {shared} textos")
    if not found:
        ok("nenhum processo duplica o conteúdo de outro")


# ── 3. FTS5 index vs chunks ──────────────────────────────────────────────────

def audit_fts(con: sqlite3.Connection) -> None:
    section("3. índice FTS5 — a via BM25")

    try:
        con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('integrity-check')")
        ok("integrity-check do FTS5", "índice interno consistente")
    except sqlite3.DatabaseError as exc:
        fail("integrity-check do FTS5", str(exc))

    n_chunks = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    n_fts = con.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
    if n_chunks == n_fts:
        ok("contagem FTS5 == contagem chunks", f"{n_fts}")
    else:
        fail("contagem FTS5 divergente",
             f"chunks={n_chunks} mas chunks_fts={n_fts} "
             f"({abs(n_chunks - n_fts)} linha(s) {'ausente' if n_fts < n_chunks else 'extra'})")

    # A row present in chunks but unreachable through FTS5 is the silent
    # "fails to provide information" failure: BM25 would never surface it.
    missing = con.execute(
        "SELECT COUNT(*) FROM chunks c "
        "WHERE NOT EXISTS (SELECT 1 FROM chunks_fts f WHERE f.rowid = c.id)"
    ).fetchone()[0]
    if missing:
        fail("chunks invisíveis ao BM25", f"{missing} linha(s) sem entrada no FTS5")
    else:
        ok("todo chunk tem entrada no FTS5")

    orphan = con.execute(
        "SELECT COUNT(*) FROM chunks_fts f "
        "WHERE NOT EXISTS (SELECT 1 FROM chunks c WHERE c.id = f.rowid)"
    ).fetchone()[0]
    if orphan:
        fail("entradas órfãs no FTS5", f"{orphan} rowid(s) sem chunk correspondente")
    else:
        ok("nenhuma entrada órfã no FTS5")

    # The join bm25.py performs is on rowid, and it must carry the same text:
    # a mismatch would rank one chunk and return another's content.
    bad = con.execute(
        "SELECT COUNT(*) FROM chunks c JOIN chunks_fts f ON f.rowid = c.id "
        "WHERE f.text IS NOT c.text"
    ).fetchone()[0]
    if bad:
        fail("texto divergente entre chunks e FTS5", f"{bad} linha(s)")
    else:
        ok("texto idêntico em chunks e FTS5")


# ── 4. LanceDB vs chunks ─────────────────────────────────────────────────────

def audit_lancedb(by_process: dict[str, list[tuple]]) -> None:
    section("4. LanceDB — a via vetorial")

    try:
        import lancedb
        import numpy as np
    except ImportError as exc:
        fail("lancedb indisponível", str(exc))
        return
    from retrieval.query.vector import _table_name

    db = lancedb.connect(str(LANCEDB_PATH))
    listed = set(db.list_tables().tables)
    print(f"  {len(listed)} tabela(s) no diretório: {sorted(listed)}")

    expected = {pn: _table_name(pn) for pn in by_process}
    reachable = {pn: t for pn, t in expected.items() if t in listed}
    print(f"  {len(reachable)} de {len(expected)} processo(s) com tabela construída")

    unreachable = listed - set(expected.values())
    if unreachable:
        warn("tabelas que nenhum processo alcança",
             f"{sorted(unreachable)} — órfãs do nome antigo, reconstruíveis a "
             "partir do SQLite; inalcançáveis pelo código atual")

    for pn, tname in sorted(reachable.items()):
        frame = db.open_table(tname).to_pandas()
        sql_rows = by_process[pn]
        print(f"\n  --- {pn} -> {tname} ---")

        if len(frame) == len(sql_rows):
            ok("contagem igual ao SQLite", f"{len(frame)}")
        else:
            fail(f"contagem divergente em {pn}",
                 f"SQLite={len(sql_rows)} LanceDB={len(frame)}")

        sql_keys = {(r[1], r[2], r[3]) for r in sql_rows}
        lance_keys = set(
            map(tuple, frame[["filename", "page_number", "chunk_index"]].values.tolist())
        )
        only_sql, only_lance = sql_keys - lance_keys, lance_keys - sql_keys
        if only_sql:
            fail(f"chunks invisíveis à via vetorial em {pn}",
                 f"{len(only_sql)} chave(s) no SQLite sem vetor: {sorted(only_sql)[:3]}")
        if only_lance:
            fail(f"vetores sem chunk de origem em {pn}",
                 f"{len(only_lance)} chave(s): {sorted(only_lance)[:3]} — índice ESTAGNADO")
        if not only_sql and not only_lance:
            ok("mesmas chaves que o SQLite")

        # Stale text is the dangerous case: the key matches, so nothing detects
        # it, but the embedding describes text the corpus no longer holds.
        sql_text = {(r[1], r[2], r[3]): (r[4] or "") for r in sql_rows}
        drift = [
            k for row in frame.itertuples()
            if (k := (row.filename, int(row.page_number), int(row.chunk_index))) in sql_text
            and sql_text[k] != row.text
        ]
        if drift:
            fail(f"texto divergente em {pn}",
                 f"{len(drift)} vetor(es) descrevem texto que o SQLite não tem mais: "
                 f"{drift[:3]}")
        else:
            ok("texto idêntico ao SQLite", "índice não está estagnado")

        vectors = np.vstack(frame["vector"].values).astype(np.float32)
        norms = np.linalg.norm(vectors, axis=1)
        if np.allclose(norms, 1.0, atol=1e-3):
            ok("vetores normalizados", f"norma {norms.min():.4f}-{norms.max():.4f}")
        else:
            warn("vetores não normalizados",
                 f"norma {norms.min():.4f}-{norms.max():.4f} — cosseno e L2 divergem")
        degenerate = int((norms < 1e-6).sum())
        if degenerate:
            fail(f"vetores nulos em {pn}", f"{degenerate} vetor(es) de norma ~0")

        dim = {len(v) for v in frame["vector"].values}
        if len(dim) == 1:
            ok("dimensão uniforme", str(dim.pop()))
        else:
            fail(f"dimensões mistas em {pn}", str(sorted(dim)))


# ── 5. reuse / invalidation contract ─────────────────────────────────────────

def audit_reuse_contract() -> None:
    section("5. contrato de reuso e invalidação")

    import re as _re
    src = (ROOT / "src" / "retrieval" / "query" / "vector.py").read_text(encoding="utf-8")
    if "db.open_table(tname)" in src and "return  # table exists" in src:
        ok("ensure_vector_index_exists reusa tabela existente", "ADR-0035")
        warn("reuso não revalida conteúdo",
             "a tabela é reusada sem comparar com o SQLite; a seção 4 é o único "
             "detector de estagnação — rode-a após qualquer reindexação")

    callers: list[str] = []
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "invalidate_vector_index(" in text and "def invalidate_vector_index" not in text:
            for m in _re.finditer(r"invalidate_vector_index\(", text):
                line = text[: m.start()].count("\n") + 1
                callers.append(f"{path.relative_to(ROOT)}:{line}")
    if callers:
        ok("invalidação é chamada na reindexação", ", ".join(sorted(set(callers))))
    else:
        fail("invalidação nunca chamada",
             "um processo reindexado manteria o índice vetorial antigo")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--process", default=None, help="restrict to one process_number")
    args = ap.parse_args()

    con = sqlite3.connect(DB_PATH)
    con.row_factory = None
    by_process = audit_chunks(con)
    if args.process:
        by_process = {k: v for k, v in by_process.items() if k == args.process}
    audit_redundancy(by_process)
    audit_fts(con)
    con.close()
    audit_lancedb(by_process)
    audit_reuse_contract()

    section("resumo")
    print(f"  falhas : {len(_failures)}")
    for f in _failures:
        print(f"      - {f}")
    print(f"  avisos : {len(_warnings)}")
    for w in _warnings:
        print(f"      - {w}")
    return 1 if _failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
