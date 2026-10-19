"""Acceptance test for the stabilisation work: how reproducible is a full run?

Runs the same case N times through the real production path
(assessment.service._retrieve_and_select -> evaluation.evaluate) and reports,
per Ação:

  * the distribution of proposed_score across runs
  * modal agreement — the fraction of runs that produced the most common score
  * whether the accepted-evidence set itself was stable, per product

With --json-out the file also carries, per Ação per run, the gate's explicit
rejections, the per-product examined/accepted counts and the scorer's
per-product verdicts, so a later flip can be attributed to a specific gate
call or to the scorer (the 2026-10-03 acceptance runs could not: only the
final evidence set was kept, and one gate flip cascades through the anchor
target, the cross-product dedup and the budget trim into a different set).

Since 2026-10-16 (finding F8 of the scorer verification) the file also keeps,
per Ação per run, what the scorer wrote: the justificativa of each product, the
reasoning field, the uncertainty flag, and the model's analysis channel with the
finish reason and the token count ("scorer"). The production client's complete()
is complete_detailed().content, so the tap sends the same request and returns the
same bytes; it only keeps what complete() throws away. --no-record-scorer turns
it off.

Target: >=90% modal agreement per Ação across 10 runs, whatever the score is.

Deliberately does NOT persist: a measurement run must never clobber the stored
evaluation_results the auditor is reviewing. Retrieval is deterministic, so any
disagreement this reports comes from the gate or the scorer, not from search.

Imports main.py to reuse the exact production LLM wiring — this calls the real
GPU server. Requires the canonical machine to be up; with the fail-fast wiring
a GPU outage aborts the run loudly instead of silently substituting a model.

Usage:
    python scripts/diagnostics/reproducibility.py --runs 10
    python scripts/diagnostics/reproducibility.py --runs 10 --acoes 31,37,40,43
    python scripts/diagnostics/reproducibility.py --runs 10 --ledger scratchpad/acc/ledger.sqlite
    python scripts/diagnostics/reproducibility.py --runs 1 --no-prompt-cache
    python scripts/diagnostics/reproducibility.py --runs 1 --no-expansion --no-genre-filter
    python scripts/diagnostics/reproducibility.py --runs 1 --acoes 35 --apply 35.2e,35.2f --candidates scripts/diagnostics/candidates_acao35_round5.py
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

import main as app_main  # noqa: E402,F401 — import triggers _bootstrap(): real DB + LLM wiring

from assessment.service import _retrieve_and_select  # noqa: E402
from evaluation import GateLedger, configure_gate_ledger  # noqa: E402

# The gate verdict ledger (ADR-0067) would make every repeated run agree with
# the first by construction. A measurement of the ENGINE needs it off; a
# measurement of the PRODUCTION PATH (--ledger) switches it on, backed by a
# scratch file so the app DB's own ledger is never touched.
configure_gate_ledger(None)
from evaluation import evaluate  # noqa: E402
from evaluation import evidence_selection as _es  # noqa: E402
from ingestion import get_ipmp_store  # noqa: E402
from retrieval import get_document_index  # noqa: E402
from retrieval.genre import GENRE_RULES_VERSION, INSTRUMENT  # noqa: E402

DEFAULT_PROCESS = "SMG-040_101607_2024"


def _outcome(result) -> str:
    """Single comparable label per Ação per run."""
    if result.no_evidence_found:
        return "sem_evidencia"
    if result.parse_failed:
        return "parse_failed"
    return f"score={result.proposed_score}"


def _accepted_signature(result) -> tuple:
    return tuple(
        sorted(
            (c.filename, c.page_number, c.chunk_index, tuple(sorted(c.expected_product_ids)))
            for c in result.retrieved_chunks
        )
    )


RECORD_REASONING = False


def _reasoning_detail(result) -> list:
    """Every gate verdict's reasoning (accepted and rejected), for --record-reasoning."""
    rows = [
        [c.filename, c.page_number, c.chunk_index, pid, True, txt]
        for c in result.retrieved_chunks
        for pid, txt in (c.gate_reasoning or {}).items()
    ]
    rows += [
        [r.filename, r.page_number, r.chunk_index, r.expected_product_id, False, r.gate_reasoning]
        for r in result.rejected_chunks
    ]
    return rows


RECORD_SCORER = True


class _ScorerTap:
    """Wraps the production scorer client (F8, 2026-10-16). complete() goes through
    complete_detailed(), as the client's own complete() does, and keeps the last
    completion: the analysis channel, the finish reason and the token count, which
    complete() discards. Every other attribute is the wrapped client's."""

    def __init__(self, inner):
        object.__setattr__(self, "_inner", inner)
        object.__setattr__(self, "last", None)

    def complete(self, system, user, schema=None):
        c = self._inner.complete_detailed(system, user, schema)
        object.__setattr__(self, "last", c)
        return c.content

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def __setattr__(self, name, value):
        setattr(self._inner, name, value)


def _install_scorer_tap():
    """Put the tap in front of the configured scorer client, if it can give details."""
    from evaluation import configure_llm_client
    from evaluation._config import get_llm_client, get_model, get_provider

    inner = get_llm_client()
    if not hasattr(inner, "complete_detailed"):
        print("scorer tap NOT installed: the scorer client has no complete_detailed()")
        return None
    tap = _ScorerTap(inner)
    configure_llm_client(tap, provider=get_provider(), model=get_model())
    print("scorer tap installed: justificativa, reasoning and analysis channel are kept")
    return tap


def _scorer_detail(result, tap) -> dict:
    """What the scorer wrote for one Ação in one run (F8). analise is None when the
    scorer was not called (no evidence) or the tap is off."""
    c = tap.last if tap is not None else None
    return {
        "justificativas": {v.product_id: v.justificativa for v in result.product_verdicts},
        "reasoning": result.reasoning,
        "uncertainty": result.uncertainty_flag,
        "analise": getattr(c, "reasoning", None),
        "finish": getattr(c, "finish_reason", None),
        "tokens": getattr(c, "completion_tokens", None),
    }


def _gate_detail(result) -> dict:
    """What the gate and the scorer decided, beyond the final evidence set.

    rejected: every explicit negative verdict (and failed call) as
    (filename, page, chunk_index, product, failed). products: per Expected
    Product, candidates / examined / accepted / rejected / failures / ledger
    hits (0 without --ledger) / candidates removed as instrument text /
    neighbours not gated as instrument text (ADR-0074; the last two were
    added on 2026-10-13, older files have six elements). verdicts:
    the scorer's evidenced flag per product, plus score_source. Together with
    the accepted signature this pins each run's gate verdicts: an examined
    chunk that is in neither list was accepted and then dropped by the
    post-gate dedup or the budget trim.
    """
    return {
        "rejected": sorted(
            (r.filename, r.page_number, r.chunk_index, r.expected_product_id, bool(r.gate_failed))
            for r in result.rejected_chunks
        ),
        "products": {
            g.expected_product_id: [g.n_candidates, g.n_examined, g.n_accepted, g.n_rejected,
                                    g.n_gate_failures, g.n_ledger_hits, g.n_genre_excluded,
                                    g.n_neighbors_genre_excluded]
            for g in result.product_gate_reports
        },
        "verdicts": {v.product_id: v.evidenced for v in result.product_verdicts},
        "score_source": result.score_source,
        # ADR-0068: the deterministic margin and the optional-review signal, so a
        # measurement can say which runs the auditor would have been pointed at.
        "margin": (
            {
                "review": result.score_margin.review_recommended,
                "floor": result.score_margin.score_floor,
                "band": result.score_margin.band_margin,
                "fragile": [m.product_id for m in result.score_margin.products if m.fragile],
            }
            if result.score_margin is not None else None
        ),
        **({"reasoning": _reasoning_detail(result)} if RECORD_REASONING else {}),
    }


def _install_gate_variant(name: str) -> None:
    """Swap the gate system-prompt builder for a measured variant, in memory.

    'rotulado' (P1a, 2026-10-09): the product under evaluation is labelled the
    way its siblings are, `- 1b (EM AVALIAÇÃO) — texto`, and the criterion
    heading carries its id. Nothing else changes. Uses measure_sibling_text's
    own rotula_alvo(), so the bytes are the ones P1a measured inside one process
    — here they are measured across independent processes.

    'posicionado' (variant G, 2026-10-13): the opening sentence becomes a section
    on the gate's place in the process (search, triage, final stage, what each
    error costs, the question to ask) and the criterion heading says the
    criterion describes the whole product the final stage will require. Uses
    gate_positioning.posiciona(), the bytes measure_gate_positioning.py measured
    inside one process.

    'posicionado2' (variant G2, 2026-10-14): G plus one paragraph that names
    the right reasons the old 'no details' argument stood in for (naming the
    element or saying where it is is not treating it; a rule about what will
    be done is not the record that it was done). gate_positioning.posiciona(
    ..., versao='g2'), the bytes measure_gate_positioning.py --condicoes g,g2
    measured. Its product pattern for 18b goes with --candidates
    scripts/diagnostics/candidates_g2.py --apply 18b.

    'qualificadores' (variant Q, cycle 9, 2026-10-18): one sentence after the
    polarity clause saying the criterion's qualifiers are the final stage's
    condition (gate_qualifiers.qualifica). Failed its pre-registered rule and
    discarded (ADR-0074, "Variants tried after cycle 8"); kept as the record.
    """
    sys.path.insert(0, str(ROOT / "scripts" / "diagnostics"))
    import measure_sibling_text as mst

    from evaluation import evidence_selection as es

    if name == "qualificadores":
        import gate_qualifiers as gq

        original = es.build_relevance_system_prompt

        def qualified(evidence_intent, concepts=None, negative_patterns=None, *, acao=None, product_id=None):
            return gq.qualifica(
                original(evidence_intent, concepts, negative_patterns, acao=acao, product_id=product_id))

        es.build_relevance_system_prompt = qualified
        print(f"gate variant '{name}' installed in memory")
        return
    if name in ("posicionado", "posicionado2"):
        import gate_positioning as gp

        original = es.build_relevance_system_prompt
        versao = "g" if name == "posicionado" else "g2"

        def positioned(evidence_intent, concepts=None, negative_patterns=None, *, acao=None, product_id=None):
            return gp.posiciona(
                original(evidence_intent, concepts, negative_patterns, acao=acao, product_id=product_id),
                versao=versao)

        es.build_relevance_system_prompt = positioned
        print(f"gate variant '{name}' installed in memory")
        return
    if name != "rotulado":
        raise SystemExit(f"unknown gate variant: {name}")
    original = es.build_relevance_system_prompt

    def labelled(evidence_intent, concepts=None, negative_patterns=None, *, acao=None, product_id=None):
        system = original(evidence_intent, concepts, negative_patterns, acao=acao, product_id=product_id)
        texto = next(p.texto for p in acao.produtos_esperados if p.id == product_id)
        return mst.rotula_alvo(system, product_id, texto)

    es.build_relevance_system_prompt = labelled
    print(f"gate variant '{name}' installed in memory")


def _term_label(term) -> str:
    """A query term as the candidates files name it: the phrase, or NEAR(tok, ...)."""
    return term.text if term.encoding == "phrase" else "NEAR(" + ", ".join(term.tokens) + ")"


def _patch_terms(pid: str, terms: list, cand: dict) -> list:
    """Drop the terms named in remover_termos; turn those in rebaixar_termos
    into synthetic/experimental (out of BM25, ADR-0056). Every named term must
    exist, so a typo cannot silently measure the unpatched profile."""
    remover, rebaixar = set(cand.get("remover_termos", [])), set(cand.get("rebaixar_termos", []))
    out, seen = [], set()
    for t in terms:
        label = _term_label(t)
        if label in remover:
            seen.add(label)
            continue
        if label in rebaixar:
            seen.add(label)
            t = t.model_copy(update={"status": "experimental", "provenance": "synthetic"})
        out.append(t)
    missing = (remover | rebaixar) - seen
    if missing:
        raise SystemExit(f"{pid}: terms not found in the profile: {sorted(missing)}")
    return out


def _apply_candidates(path: str, products: str | None) -> dict:
    """Append each named candidate's patch to the in-memory profile store."""
    import importlib.util

    from ingestion import get_retrieval_profile_store

    if not products:
        raise SystemExit("--candidates needs --apply with the product ids to patch")
    spec = importlib.util.spec_from_file_location("_candidates", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    store = get_retrieval_profile_store()
    applied = {}
    for pid in (x.strip() for x in products.split(",")):
        cand = mod.CANDIDATOS[pid]
        pp = store.acoes[cand["acao"]].expected_products[pid]
        if cand.get("intent_add"):
            pp.evidence_intent = pp.evidence_intent.rstrip() + cand["intent_add"]
        if cand.get("negativo"):
            pp.negative_evidence_patterns = list(pp.negative_evidence_patterns) + [cand["negativo"]]
        if cand.get("negativos_substitui"):
            trocas = dict(cand["negativos_substitui"])
            atuais = list(pp.negative_evidence_patterns)
            faltam = [velho[:60] for velho in trocas if atuais.count(velho) != 1]
            if faltam:
                raise SystemExit(f"{pid}: negative patterns to replace not found exactly once: {faltam}")
            pp.negative_evidence_patterns = [trocas.get(n, n) for n in atuais]
        if cand.get("remover_termos") or cand.get("rebaixar_termos"):
            pp.query_terms = _patch_terms(pid, pp.query_terms, cand)
        if cand.get("conceitos_texto"):
            novos = dict(cand["conceitos_texto"])
            missing = set(novos) - {c.key for c in pp.retrieval_signal_concepts}
            if missing:
                raise SystemExit(f"{pid}: concepts not found in the profile: {sorted(missing)}")
            pp.retrieval_signal_concepts = [
                c.model_copy(update={"text": novos[c.key]}) if c.key in novos else c
                for c in pp.retrieval_signal_concepts
            ]
        chaves = ("intent_add", "negativo", "negativos_substitui", "remover_termos", "rebaixar_termos",
                  "conceitos_texto", "sem_isencao_genero")
        applied[pid] = {k: cand[k] for k in chaves if cand.get(k)}
        print(f"candidate applied in memory: {pid} ({', '.join(applied[pid])})")
    assert get_retrieval_profile_store() is store
    sem_isencao = frozenset(pid for pid, a in applied.items() if a.get("sem_isencao_genero"))
    if sem_isencao:
        _drop_genre_exemptions(sem_isencao)
    return {"file": str(path), "products": applied}


def _drop_genre_exemptions(products: frozenset[str]) -> None:
    """Treat these products as not exempt from the genre filter (ADR-0074), in memory.

    A candidate with sem_isencao_genero (2026-10-14, Acao 45) leaves the exemption
    list for this process only; data/ipmp/isencoes_genero.json is not touched. The
    per-product filter and the focal route of evidence_selection both read the store
    through this module attribute, so both see the change.
    """
    base = _es.get_genre_exemption_store

    class _SemIsencao:
        def __init__(self, store):
            self._store = store

        def produtos(self, acao_id=None):
            return frozenset(p for p in self._store.produtos(acao_id) if p not in products)

    _es.get_genre_exemption_store = lambda: _SemIsencao(base())
    print(f"genre exemption dropped in memory for: {', '.join(sorted(products))}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--process", default=DEFAULT_PROCESS)
    ap.add_argument("--acoes", default=None, help="comma-separated subset, e.g. 31,37,40")
    ap.add_argument("--json-out", default=None)
    ap.add_argument(
        "--ledger", default=None, metavar="SQLITE_FILE",
        help="switch the gate verdict ledger ON, backed by this scratch SQLite file: run 1 fills it, "
             "later runs answer repeated gate prompts from it. Measures the production path "
             "(ADR-0067) instead of the bare engine; what remains is the scorer. Never data/app.db.",
    )
    ap.add_argument(
        "--no-prompt-cache", action="store_true",
        help="send cache_prompt=false on every call, so the server rebuilds the KV prefix "
             "from scratch instead of reusing it. A server internal: use only when a clean "
             "run with no cache of anything is explicitly wanted. Costs prefill time and was "
             "measured on 2026-10-02 not to improve stability at serial+low.",
    )
    ap.add_argument(
        "--expansion", action="store_true",
        help="kept for old command lines: neighbour expansion is ON by default since "
             "2026-10-13, behind the genre filter (ADR-0074).",
    )
    ap.add_argument(
        "--no-expansion", action="store_true",
        help="turn neighbour expansion OFF for this run (the production state from "
             "2026-10-06 to 2026-10-12, ADR-0069), to measure what the filtered expansion "
             "costs in constancy.",
    )
    ap.add_argument(
        "--no-genre-filter", action="store_true",
        help="turn the genre filter OFF for this run (ADR-0074): candidates, neighbours and "
             "focal documents of instrument text reach the gate and the scorer again.",
    )
    ap.add_argument(
        "--candidates", default=None, metavar="PY_FILE",
        help="a candidates file (dict CANDIDATOS, the format of measure_integral_candidates.py); "
             "with --apply, the named products get the candidate's negative pattern / intent "
             "addition / query-term removal or demotion (remover_termos, rebaixar_termos) / "
             "concept text replacement (conceitos_texto) / in-place negative-pattern replacement (negativos_substitui) "
             "/ removal from the genre-exemption list (sem_isencao_genero) "
             "IN MEMORY for this process only. This is how a patch is measured across "
             "independent processes (the only valid constancy measurement, ADR-0071) before it "
             "is written to a profile.",
    )
    ap.add_argument("--apply", default=None, help="comma-separated product ids from --candidates")
    ap.add_argument(
        "--gate-variant", default=None, choices=("rotulado", "posicionado", "posicionado2", "qualificadores"),
        help="measure a gate-prompt variant across independent processes, in memory only "
             "(src/ untouched). 'rotulado': the product under evaluation labelled like its "
             "siblings (measure_sibling_text.rotula_alvo). 'posicionado': the gate's place in "
             "the process stated in the prompt (gate_positioning.posiciona, variant G). "
             "'posicionado2': variant G2, G plus the NOMEAR paragraph. 'qualificadores': variant Q, "
             "one sentence saying the criterion's qualifiers belong to the final stage (gate_qualifiers.qualifica).",
    )
    ap.add_argument(
        "--lane-genre-filter", action="store_true",
        help="variant F20 (cycle 10, 2026-10-19; failed and discarded, kept as the record, "
             "ADR-0074): the genre filter inside each lane, before the RRF fusion; each lane of a non-exempt product goes down until it has 20 chunks that "
             "are not instrument text and not empty (lane_genre_filter.instala). In memory only.",
    )
    ap.add_argument(
        "--record-reasoning", action="store_true",
        help="store the gate reasoning of every verdict in the JSON (gate.reasoning), so the "
             "target-product confusion rate can be read across independent processes",
    )
    ap.add_argument(
        "--no-record-scorer", action="store_true",
        help="do not keep the scorer's justificativa, reasoning and analysis channel in the "
             "JSON (kept by default since 2026-10-16, finding F8 of the scorer verification)",
    )
    args = ap.parse_args()
    global RECORD_REASONING, RECORD_SCORER
    RECORD_REASONING = args.record_reasoning
    RECORD_SCORER = not args.no_record_scorer
    if args.gate_variant:
        _install_gate_variant(args.gate_variant)
    if args.lane_genre_filter:
        sys.path.insert(0, str(ROOT / "scripts" / "diagnostics"))
        import lane_genre_filter

        lane_genre_filter.instala()
        print("lane genre filter (F20) installed in memory")
    patch = _apply_candidates(args.candidates, args.apply) if args.candidates else {}
    if args.expansion and args.no_expansion:
        ap.error("--expansion and --no-expansion contradict each other")
    if args.no_expansion:
        _es.EXPANSION_ENABLED = False
        print("neighbour expansion DISABLED for this run")
    elif args.expansion:
        _es.EXPANSION_ENABLED = True
    if args.no_genre_filter:
        _es.GENRE_FILTER_ENABLED = False
        print("genre filter DISABLED for this run")
    if args.no_prompt_cache:
        from evaluation._config import get_gate_llm_client, get_llm_client
        for _client in (get_llm_client(), get_gate_llm_client()):
            _client.cache_prompt = False
        print("cache_prompt=false on the scorer and the gate client")
    if args.ledger:
        ledger_path = Path(args.ledger).resolve()
        if ledger_path.name == "app.db":
            ap.error("--ledger must be a scratch file, not the app DB")
        configure_gate_ledger(GateLedger(ledger_path))
        print(f"gate verdict ledger ON: {ledger_path} ({GateLedger(ledger_path).count()} verdicts before this run)")

    tap = _install_scorer_tap() if RECORD_SCORER else None

    acao_ids = sorted(get_ipmp_store().acoes)
    if args.acoes:
        wanted = {int(x) for x in args.acoes.split(",")}
        acao_ids = [a for a in acao_ids if a in wanted]

    print(f"reproducibility: {args.runs} runs x {len(acao_ids)} Ação(ões), case '{args.process}'")
    print(f"neighbour expansion: {'on' if _es.EXPANSION_ENABLED else 'off'}; "
          f"genre filter: {'on' if _es.GENRE_FILTER_ENABLED else 'off'}")
    if _es.GENRE_FILTER_ENABLED:
        # Build (or find current) the canonical document index before the first
        # Acao, so no run pays for it and the log says what it holds.
        documents = get_document_index(args.process)
        instrument = [d for d in documents if d.genre == INSTRUMENT]
        print(f"document index (rules {GENRE_RULES_VERSION}): {len(documents)} documents, "
              f"{len(instrument)} instrument text, "
              f"{sum(d.n_chunks for d in instrument)}/{sum(d.n_chunks for d in documents)} chunks")
    print("results are NOT persisted\n")

    outcomes: dict[int, list[str]] = collections.defaultdict(list)
    signatures: dict[int, list[tuple]] = collections.defaultdict(list)
    accepted_counts: dict[int, list[int]] = collections.defaultdict(list)
    errors: dict[int, list[str]] = collections.defaultdict(list)
    details: dict[int, list[dict]] = collections.defaultdict(list)
    scorer: dict[int, list[dict]] = collections.defaultdict(list)

    for run in range(1, args.runs + 1):
        started = time.monotonic()
        # ADR-0070: production derives the dependency cap from the Ações already
        # scored in the run; a subset run (--acoes) sees only the subset, like
        # a production run that failed on the missing ones (unknown -> no cap).
        prior: dict[int, object] = {}
        for acao_id in acao_ids:
            if tap is not None:
                object.__setattr__(tap, "last", None)
            try:
                accepted, rejected, gate_reports = _retrieve_and_select(acao_id, args.process)
                result = evaluate(
                    acao_id,
                    args.process,
                    accepted,
                    rejected_chunks=rejected,
                    product_gate_reports=gate_reports,
                    prior_results=prior,
                )
                prior[acao_id] = result
            except Exception as exc:  # a run must not die on one Ação
                errors[acao_id].append(f"{type(exc).__name__}: {exc}")
                outcomes[acao_id].append("erro")
                signatures[acao_id].append(())
                accepted_counts[acao_id].append(0)
                details[acao_id].append({})
                scorer[acao_id].append({})
                continue
            outcomes[acao_id].append(_outcome(result))
            signatures[acao_id].append(_accepted_signature(result))
            accepted_counts[acao_id].append(len(result.retrieved_chunks))
            details[acao_id].append(_gate_detail(result))
            scorer[acao_id].append(_scorer_detail(result, tap) if RECORD_SCORER else {})
        print(f"  run {run}/{args.runs} done in {time.monotonic()-started:.0f}s")

    print("\n" + "=" * 86)
    print("PER-AÇÃO REPRODUCIBILITY")
    print("=" * 86)
    print("Ação  concord.  desfechos observados                       evid.estável  n_aceitos")
    below = []
    for acao_id in acao_ids:
        obs = outcomes[acao_id]
        counts = collections.Counter(obs)
        modal, modal_n = counts.most_common(1)[0]
        agreement = modal_n / len(obs)
        sig_stable = len(set(signatures[acao_id])) == 1
        counts_txt = " ".join(f"{k}x{v}" for k, v in counts.most_common())
        acc = accepted_counts[acao_id]
        acc_txt = f"{min(acc)}-{max(acc)}" if min(acc) != max(acc) else str(acc[0])
        flag = "" if agreement >= 0.9 else "  <-- abaixo de 90%"
        if agreement < 0.9:
            below.append(acao_id)
        print(
            f"{acao_id:>4}  {100*agreement:>6.0f}%  {counts_txt:<42} "
            f"{'sim' if sig_stable else 'NAO':<12} {acc_txt:>9}{flag}"
        )

    print("\n" + "=" * 86)
    overall = sum(
        collections.Counter(outcomes[a]).most_common(1)[0][1] / len(outcomes[a])
        for a in acao_ids
    ) / len(acao_ids)
    fully = sum(1 for a in acao_ids if len(set(outcomes[a])) == 1)
    print(f"mean modal agreement            : {100*overall:.1f}%")
    print(f"Ações identical in all {args.runs} runs : {fully}/{len(acao_ids)} ({100*fully/len(acao_ids):.0f}%)")
    print(f"Ações below the 90% target      : {len(below)} {below or ''}")
    stable_evidence = sum(1 for a in acao_ids if len(set(signatures[a])) == 1)
    print(f"Ações with an identical accepted-evidence set every run: {stable_evidence}/{len(acao_ids)}")
    if errors:
        print("\nerrors encountered:")
        for acao_id, msgs in sorted(errors.items()):
            print(f"  Ação {acao_id}: {len(msgs)}x  {msgs[0]}")

    if args.json_out:
        payload = {
            "process": args.process,
            "runs": args.runs,
            "outcomes": {str(a): outcomes[a] for a in acao_ids},
            "accepted_counts": {str(a): accepted_counts[a] for a in acao_ids},
            # Which chunks were accepted, per run: (filename, page, chunk_index,
            # product ids). Without it two sweeps with the same accepted COUNT
            # cannot be told apart (R10->R11, 2026-10-02: Ações 20 and 40 went
            # score 0->1 at an unchanged count, and the files could not say
            # whether the evidence or only the scorer had moved).
            "accepted": {
                str(a): [[list(sig) for sig in run_sig] for run_sig in signatures[a]]
                for a in acao_ids
            },
            "errors": {str(a): errors[a] for a in errors},
            # Gate rejections, per-product counts and scorer verdicts per run
            # (see _gate_detail). Added after the 2026-10-03 acceptance runs.
            "gate": {str(a): details[a] for a in acao_ids},
            # F8 (2026-10-16): per Ação per run, the scorer's justificativas, reasoning,
            # uncertainty and analysis channel (see _scorer_detail); empty when off.
            "scorer": {str(a): scorer[a] for a in acao_ids},
            "record_scorer": RECORD_SCORER,
            # The in-memory candidate patch this process ran with (empty = the
            # profiles as they are on disk).
            "patch": patch,
            "gate_variant": args.gate_variant,
            "lane_genre_filter": args.lane_genre_filter,
            # ADR-0074: the switches this process ran with and the rules of the
            # document index, so runs under different filters are never mixed.
            "expansion": _es.EXPANSION_ENABLED,
            "genre_filter": _es.GENRE_FILTER_ENABLED,
            "genre_rules_version": GENRE_RULES_VERSION,
        }
        Path(args.json_out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nraw outcomes written to {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
