from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from evaluation import (
    EvaluationResult,
    ProductGateReport,
    RejectedChunk,
    evaluate,
    select_evidence,
)
from evaluation._config import get_gate_llm_client, get_llm_client
from evaluation.llm.llamacpp import LlamaCppBusy, LlamaCppTimeout, LlamaCppUnavailable
from evaluation.progress import set_reporter
from extraction import extract_document
from ingestion import get_ipmp_store
from retrieval import index, invalidate_vector_index, retrieve_hybrid_candidates_for_acao
from retrieval.interfaces.contracts import RetrievedChunk
from retrieval.query.document import retrieve_document_focused

from assessment import progress
from assessment._config import get_db_path

logger = logging.getLogger(__name__)

# Failures that mean the inference server itself is unusable. The LLM wiring is
# GPU-only and deliberately has no fallback (see main.py), so these must abort
# the whole run: continuing would walk all 46 Ações, pay a connect timeout on
# each, and store 46 empty evaluations that look like "no evidence found" but
# are really "nothing was ever asked". Any OTHER per-Ação exception is recorded
# and the run continues, so one bad Ação does not discard 45 good ones.
_INFRASTRUCTURE_FAILURES = (LlamaCppUnavailable, LlamaCppTimeout, LlamaCppBusy)


class AssessmentService:
    def run_assessment(
        self,
        process_number: str,
        document_paths: list[Path],
    ) -> tuple[list[EvaluationResult], list[dict[str, str]]]:
        progress.start_run(process_number)
        set_reporter(progress.make_reporter(process_number))
        try:
            return self._run_assessment(process_number, document_paths)
        except Exception as exc:
            progress.emit(process_number, "erro", f"Falha na avaliação: {exc}", "error")
            raise
        finally:
            set_reporter(None)

    def _run_assessment(
        self,
        process_number: str,
        document_paths: list[Path],
    ) -> tuple[list[EvaluationResult], list[dict[str, str]]]:
        get_llm_client()  # raises RuntimeError if configure_llm() was not called
        get_gate_llm_client()  # raises RuntimeError if configure_gate_llm() was not called

        db_path = get_db_path()

        progress.emit(process_number, "verificando_arquivos", "Verificando arquivos enviados...")

        documents: list[dict[str, str]] = []
        if not document_paths:
            if not _has_indexed_chunks(db_path, process_number):
                raise RuntimeError(
                    f"No document_paths provided and no indexed chunks exist for "
                    f"process_number '{process_number}'. Upload source documents to proceed."
                )
            progress.emit(
                process_number, "documentos_disponiveis",
                "Nenhum arquivo novo — reaproveitando documentos já indexados.",
            )
        else:
            for path in document_paths:
                progress.emit(
                    process_number, "identificando_documentos_processados",
                    f"Verificando se {path.name} já foi processado...",
                )
                disposition = _process_file(db_path, process_number, path)
                documents.append({"filename": path.name, "disposition": disposition})
                label = {"reused": "já processado, reaproveitado", "new": "novo, indexado agora",
                          "replaced": "alterado, reindexado"}.get(disposition, disposition)
                progress.emit(
                    process_number, "documentos_disponiveis", f"{path.name}: {label}.", "success"
                )

        _preflight_llm(process_number)

        store = get_ipmp_store()
        results: list[EvaluationResult] = []
        failed: list[int] = []
        for acao_id in store.acoes:
            try:
                accepted, rejected, gate_reports = _retrieve_and_select(acao_id, process_number)
                result = evaluate(
                    acao_id,
                    process_number,
                    accepted,
                    rejected_chunks=rejected,
                    product_gate_reports=gate_reports,
                    # ADR-0070: the Ações already scored in this run, in order —
                    # every dependency with effect points backwards, so the
                    # cited result exists here or failed (then: unknown, no cap).
                    prior_results={r.acao_id: r for r in results},
                )
            except _INFRASTRUCTURE_FAILURES as exc:
                # Server gone mid-run: stop immediately rather than producing 40+
                # more empty evaluations that would be indistinguishable from
                # genuine "no evidence" outcomes.
                progress.emit(
                    process_number, "erro",
                    f"Servidor de inferência indisponível na Ação {acao_id} "
                    f"({type(exc).__name__}) — execução interrompida. "
                    f"{len(results)} Ação(ões) já avaliada(s) foram preservadas.",
                    "error",
                )
                raise
            except Exception as exc:  # noqa: BLE001 — one Ação must not kill the run
                logger.exception("Ação %s failed; continuing with the rest.", acao_id)
                failed.append(acao_id)
                progress.emit(
                    process_number, "erro",
                    f"Ação {acao_id} falhou ({type(exc).__name__}: {exc}) — "
                    "seguindo para a próxima.",
                    "error",
                )
                continue
            _persist_evaluation_result(db_path, result)
            results.append(result)

        suffix = f" {len(failed)} com falha: {failed}." if failed else ""
        progress.emit(
            process_number, "concluido",
            f"Avaliação concluída — {len(results)} Ação(ões) processada(s).{suffix}",
            "warning" if failed else "success",
        )
        return results, documents


def _preflight_llm(process_number: str) -> None:
    """Probe the inference server before the Ação loop starts.

    The wiring is GPU-only with no fallback, so a switched-off server otherwise
    surfaces as a connect timeout on the first gate call of every Ação in turn.
    One cheap /health probe turns that into an immediate, unambiguous failure.
    Clients that do not expose health_check() (test stubs, Ollama) are skipped.
    """
    for label, client in (("avaliador", get_llm_client()), ("gate", get_gate_llm_client())):
        probe = getattr(client, "health_check", None)
        if probe is None:
            continue
        try:
            probe()
        except _INFRASTRUCTURE_FAILURES as exc:
            progress.emit(
                process_number, "erro",
                f"Servidor de inferência ({label}) não está respondendo "
                f"({type(exc).__name__}). Nenhuma Ação foi avaliada.",
                "error",
            )
            raise


def _retrieve_and_select(
    acao_id: int, process_number: str
) -> tuple[list[RetrievedChunk], list[RejectedChunk], list[ProductGateReport]]:
    """Step A/B short-circuit (ungated) -> Step C gate (ADR-0050).

    Document-focused matches (Step A/B) already return all of a single
    document's chunks; that's a different evidentiary basis than per-product
    query-based retrieval, so the relevance gate — built around per-product
    evidence_intent — does not apply to them, and there are no per-product gate
    reports to return for that route.

    Regex (Step D) was removed in ADR-0052 — see cascade.py for reasoning.
    """
    progress.emit(
        process_number, "recuperando_evidencias",
        f"Ação {acao_id}: buscando documento focal reconhecido...",
    )
    doc_result = retrieve_document_focused(acao_id, process_number)
    if doc_result is not None:
        progress.emit(
            process_number, "selecionando_rota",
            f"Ação {acao_id}: documento focal encontrado — usando correspondência "
            "direta (sem gate de relevância).",
        )
        return doc_result, [], []

    progress.emit(
        process_number, "selecionando_rota",
        f"Ação {acao_id}: sem documento focal — usando busca BM25 + vetorial com gate.",
    )
    candidates = retrieve_hybrid_candidates_for_acao(acao_id, process_number)
    selection = select_evidence(acao_id, process_number, candidates)
    return selection.accepted, selection.rejected, selection.product_reports


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _get_stored_fingerprint(db_path: Path, process_number: str, filename: str) -> str | None:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT sha256 FROM document_fingerprints "
            "WHERE process_number = ? AND filename = ?",
            (process_number, filename),
        ).fetchone()
        return row[0] if row else None
    finally:
        con.close()


def _upsert_fingerprint(db_path: Path, process_number: str, filename: str, sha256: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "INSERT OR REPLACE INTO document_fingerprints "
            "(process_number, filename, sha256, indexed_at) VALUES (?, ?, ?, ?)",
            (process_number, filename, sha256, now),
        )
        con.commit()
    finally:
        con.close()


def _delete_chunks_for_file(db_path: Path, process_number: str, filename: str) -> None:
    # Module 5 deletes stale retrieval-owned chunk rows during file replacement.
    # The retrieval module has no deindex API; direct DELETE is the approved Phase 1 approach.
    # chunks_fts is a content table — deleting the shadow row keeps FTS consistent.
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA foreign_keys = OFF")
        rows = con.execute(
            "SELECT id FROM chunks WHERE process_number = ? AND filename = ?",
            (process_number, filename),
        ).fetchall()
        for (row_id,) in rows:
            con.execute("DELETE FROM chunks_fts WHERE rowid = ?", (row_id,))
        con.execute(
            "DELETE FROM chunks WHERE process_number = ? AND filename = ?",
            (process_number, filename),
        )
        con.commit()
    finally:
        con.close()


def _has_indexed_chunks(db_path: Path, process_number: str) -> bool:
    con = sqlite3.connect(str(db_path))
    try:
        row = con.execute(
            "SELECT 1 FROM chunks WHERE process_number = ? LIMIT 1",
            (process_number,),
        ).fetchone()
        return row is not None
    except sqlite3.OperationalError:
        # chunks table may not exist yet if retrieval init_db hasn't been called
        return False
    finally:
        con.close()


def _process_file(db_path: Path, process_number: str, path: Path) -> str:
    filename = path.name
    sha256 = _compute_sha256(path)
    stored = _get_stored_fingerprint(db_path, process_number, filename)

    if stored == sha256:
        logger.info("Fingerprint match for %s/%s — reusing indexed chunks.", process_number, filename)
        return "reused"

    is_replacement = stored is not None
    logger.info(
        "Fingerprint mismatch for %s/%s — %s stale chunks.",
        process_number,
        filename,
        "replacing" if is_replacement else "indexing new",
    )
    _delete_chunks_for_file(db_path, process_number, filename)
    invalidate_vector_index(process_number)
    chunks = extract_document(path)
    index(process_number, chunks)
    _upsert_fingerprint(db_path, process_number, filename, sha256)
    return "replaced" if is_replacement else "new"


def _persist_evaluation_result(db_path: Path, result: EvaluationResult) -> None:
    now = datetime.now(timezone.utc).isoformat()
    raw_json = result.model_dump_json()
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "DELETE FROM evaluation_results WHERE acao_id = ? AND process_number = ?",
            (result.acao_id, result.process_number),
        )
        con.execute(
            "INSERT INTO evaluation_results "
            "(acao_id, process_number, proposed_score, uncertainty_flag, parse_failed, "
            "no_evidence_found, provider, model, created_at, raw_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                result.acao_id,
                result.process_number,
                result.proposed_score,
                int(result.uncertainty_flag),
                int(result.parse_failed),
                int(result.no_evidence_found),
                result.provider,
                result.model,
                now,
                raw_json,
            ),
        )
        con.commit()
    finally:
        con.close()
