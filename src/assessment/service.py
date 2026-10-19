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
    filter_focal_document,
    recompute_dependency_cap,
    select_evidence,
)
from evaluation._config import get_gate_llm_client, get_llm_client
from evaluation.llm.llamacpp import LlamaCppBusy, LlamaCppTimeout, LlamaCppUnavailable
from evaluation.progress import set_reporter
from extraction import extract_document
from ingestion import get_dependency_store, get_ipmp_store
from retrieval import (
    index,
    invalidate_document_index,
    invalidate_vector_index,
    retrieve_hybrid_candidates_for_acao,
)
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
# The re-evaluation route turns these into 503 (ADR-0078).
INFRASTRUCTURE_FAILURES = _INFRASTRUCTURE_FAILURES


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

    def run_reevaluation(self, process_number: str, acao_ids: list[int]) -> dict:
        """Re-evaluate the given Ações from the documents already indexed (ADR-0078)."""
        progress.start_run(process_number)
        set_reporter(progress.make_reporter(process_number))
        try:
            return self._run_reevaluation(process_number, acao_ids)
        except Exception as exc:
            progress.emit(process_number, "erro", f"Falha na reavaliação: {exc}", "error")
            raise
        finally:
            set_reporter(None)

    def _run_reevaluation(self, process_number: str, acao_ids: list[int]) -> dict:
        """One ascending walk over the Ações (ADR-0078).

        A target is evaluated again: retrieval and the gate run as in an
        assessment, so the ledger replays every frozen verdict and every
        auditor override (ADR-0067); the scorer runs again. Its evaluation is
        replaced and its review deleted. Any other Ação that cites, with
        effect (ADR-0070), an Ação whose score changed has its cap recomputed
        on the stored result, without the model; when that changes its score,
        its review is deleted too and its own dependents follow. Every
        dependency points backwards, so one ascending pass reaches them all.

        An infrastructure failure stops the model calls; the Ações already
        re-evaluated stay, and their dependents are still recalculated.
        """
        get_llm_client()
        get_gate_llm_client()
        db_path = get_db_path()
        targets = sorted(set(acao_ids))

        progress.emit(
            process_number, "reavaliacao",
            f"Reavaliando {len(targets)} Ação(ões) com os documentos já indexados: "
            f"{', '.join(str(a) for a in targets)}.",
        )
        _preflight_llm(process_number)

        current = _load_stored_results(db_path, process_number)
        dep_store = get_dependency_store()
        report: dict = {
            "process_number": process_number,
            "reevaluated": [],
            "failed": [],
            "not_reached": [],
            "dependents": [],
            "interrupted": None,
        }
        changed: set[int] = set()
        for acao_id in sorted(get_ipmp_store().acoes):
            if acao_id < targets[0]:
                continue
            prior = {k: v for k, v in current.items() if k < acao_id}
            if acao_id in targets:
                if report["interrupted"]:
                    report["not_reached"].append(acao_id)
                    continue
                before = current.get(acao_id)
                try:
                    accepted, rejected, gate_reports = _retrieve_and_select(acao_id, process_number)
                    result = evaluate(
                        acao_id,
                        process_number,
                        accepted,
                        rejected_chunks=rejected,
                        product_gate_reports=gate_reports,
                        prior_results=prior,
                    )
                except _INFRASTRUCTURE_FAILURES as exc:
                    report["interrupted"] = (
                        f"Servidor de inferência indisponível na Ação {acao_id} "
                        f"({type(exc).__name__})."
                    )
                    report["not_reached"].append(acao_id)
                    progress.emit(
                        process_number, "erro",
                        report["interrupted"] + " As Ações já reavaliadas foram mantidas; "
                        "as restantes não foram reavaliadas.",
                        "error",
                    )
                    continue
                except Exception as exc:  # noqa: BLE001 — one Ação must not kill the run
                    logger.exception("Re-evaluation of Ação %s failed.", acao_id)
                    report["failed"].append(acao_id)
                    progress.emit(
                        process_number, "erro",
                        f"Ação {acao_id} falhou ({type(exc).__name__}: {exc}) — a avaliação "
                        "gravada e a revisão foram mantidas.",
                        "error",
                    )
                    continue
                _persist_evaluation_result(db_path, result)
                review_deleted = _delete_review(db_path, process_number, acao_id)
                current[acao_id] = result
                changed.add(acao_id)
                report["reevaluated"].append(_change(acao_id, before, result, review_deleted))
                continue

            before = current.get(acao_id)
            if before is None or not any(
                d.citada in changed for d in dep_store.com_efeito(acao_id)
            ):
                continue
            after = recompute_dependency_cap(before, prior, dep_store)
            if after.model_dump() == before.model_dump():
                continue
            # Same gate and scorer run: the row keeps its created_at, so an
            # override recorded on this Ação still reads as pending.
            _update_evaluation_result(db_path, after)
            current[acao_id] = after
            review_deleted = False
            if after.proposed_score != before.proposed_score:
                changed.add(acao_id)
                review_deleted = _delete_review(db_path, process_number, acao_id)
            report["dependents"].append(_change(acao_id, before, after, review_deleted))
            progress.emit(
                process_number, "dependencia",
                f"Ação {acao_id}: teto por dependência recalculado — "
                f"{_score_label(before)} → {_score_label(after)}.",
            )

        progress.emit(
            process_number, "concluido",
            f"Reavaliação concluída — {len(report['reevaluated'])} Ação(ões) reavaliada(s), "
            f"{len(report['dependents'])} dependente(s) recalculada(s).",
            "warning" if (report["failed"] or report["interrupted"]) else "success",
        )
        return report

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

    Both routes pass the genre filter (ADR-0074): the focal document through
    filter_focal_document(), the per-product candidates inside select_evidence().
    """
    progress.emit(
        process_number, "recuperando_evidencias",
        f"Ação {acao_id}: buscando documento focal reconhecido...",
    )
    doc_result = retrieve_document_focused(acao_id, process_number)
    if doc_result is not None:
        # ADR-0074: a focal document passes the genre filter too; when only
        # the per-product route can filter it, it falls through to that route.
        doc_result = filter_focal_document(acao_id, process_number, doc_result)
        if doc_result is None:
            progress.emit(
                process_number, "selecionando_rota",
                f"Ação {acao_id}: documento focal é texto de instrumento — seguindo pela "
                "busca BM25 + vetorial com gate.",
            )
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
    invalidate_document_index(process_number)
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


# ── re-evaluation helpers (ADR-0078) ─────────────────────────────────────────

def _load_stored_results(db_path: Path, process_number: str) -> dict[int, EvaluationResult]:
    """The stored evaluations of the case. A row that no longer validates is
    left out: for the cap it then reads as unknown, which never caps."""
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute(
            "SELECT acao_id, raw_json FROM evaluation_results WHERE process_number = ?",
            (process_number,),
        ).fetchall()
    finally:
        con.close()
    out: dict[int, EvaluationResult] = {}
    for acao_id, raw in rows:
        try:
            out[acao_id] = EvaluationResult.model_validate_json(raw)
        except ValueError:
            logger.warning("Stored evaluation of Ação %s does not validate; left out.", acao_id)
    return out


def _update_evaluation_result(db_path: Path, result: EvaluationResult) -> None:
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "UPDATE evaluation_results SET proposed_score = ?, raw_json = ? "
            "WHERE acao_id = ? AND process_number = ?",
            (result.proposed_score, result.model_dump_json(), result.acao_id,
             result.process_number),
        )
        con.commit()
    finally:
        con.close()


def _delete_review(db_path: Path, process_number: str, acao_id: int) -> bool:
    con = sqlite3.connect(str(db_path))
    try:
        cur = con.execute(
            "DELETE FROM review_outcomes WHERE process_number = ? AND acao_id = ?",
            (process_number, acao_id),
        )
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()


def _score_label(result: EvaluationResult | None) -> str:
    if result is None:
        return "sem avaliação"
    if result.parse_failed:
        return "falha de parsing"
    if result.no_evidence_found or result.proposed_score is None:
        return "sem evidência"
    return str(result.proposed_score)


def _change(
    acao_id: int,
    before: EvaluationResult | None,
    after: EvaluationResult,
    review_deleted: bool,
) -> dict:
    return {
        "acao_id": acao_id,
        "before": _score_label(before),
        "after": _score_label(after),
        "review_deleted": review_deleted,
    }


def pending_gate_overrides(db_path: Path, process_number: str) -> list[dict]:
    """Auditor overrides recorded after the evaluation of their Ação was
    produced: the stored score does not reflect them yet (ADR-0078)."""
    con = sqlite3.connect(str(db_path))
    try:
        if con.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'gate_verdicts'"
        ).fetchone() is None:
            return []
        rows = con.execute(
            "SELECT g.acao_id, g.product_id, g.filename, g.page_number, g.chunk_index, "
            "g.relevant, g.overridden_at, g.override_justification, e.created_at "
            "FROM gate_verdicts g JOIN evaluation_results e "
            "ON e.process_number = g.process_number AND e.acao_id = g.acao_id "
            "WHERE g.process_number = ? AND g.overridden_at IS NOT NULL "
            "ORDER BY g.acao_id, g.product_id, g.filename, g.page_number, g.chunk_index",
            (process_number,),
        ).fetchall()
    finally:
        con.close()
    out: list[dict] = []
    for acao_id, pid, filename, page, chunk, relevant, at, why, evaluated_at in rows:
        if datetime.fromisoformat(at) <= datetime.fromisoformat(evaluated_at):
            continue
        out.append({
            "acao_id": acao_id, "product_id": pid, "filename": filename,
            "page_number": page, "chunk_index": chunk, "relevant": bool(relevant),
            "overridden_at": at, "justification": why,
        })
    return out


def reviews_at_stake(
    db_path: Path, process_number: str, acao_ids: list[int]
) -> tuple[list[int], list[int]]:
    """(reviewed targets, reviewed possible dependents) of a re-evaluation.

    A target's review is always deleted. A dependent's review is deleted only
    if its score changes, which is known only after the run, so every
    reviewed Ação that cites, with effect and transitively, a target is listed.
    """
    dep_store = get_dependency_store()
    targets = set(acao_ids)
    reach = set(targets)
    for acao_id in sorted(get_ipmp_store().acoes):
        if acao_id not in reach and any(d.citada in reach for d in dep_store.com_efeito(acao_id)):
            reach.add(acao_id)
    con = sqlite3.connect(str(db_path))
    try:
        reviewed = {
            a for (a,) in con.execute(
                "SELECT acao_id FROM review_outcomes WHERE process_number = ?",
                (process_number,),
            )
        }
    finally:
        con.close()
    return sorted(reviewed & targets), sorted(reviewed & (reach - targets))
