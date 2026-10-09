"""Static audit of every gate system prompt the production path can build.

No LLM, no GPU. For each of the 164 scored Expected Products this builds the
exact system prompt `evidence_selection._gate_chunk` would send and checks:

  injection   — identity block names the right Ação/product and the right
                sibling count; evidence_intent, every retrieval_signal_concept
                and every negative_evidence_pattern appear verbatim; the scope
                rule and the output instruction are present
  degeneracy  — concepts that merely restate the evidence_intent (fuzz >= 90)
                give the model no second discriminator; products with no
                negative pattern have no stated exclusion at all
  siblings    — how alike sibling criteria are (partial_ratio of intent +
                concepts between products of one Ação): the user-reported
                failure mode is a chunk accepted for the wrong sibling
  size        — chars / approx tokens, so no prompt is silently near a cap
  determinism — a global digest over all 164 prompts; run twice (two
                processes) and compare, since a dict/set order leak in the
                builder would show up here before it shows up at the gate

Exit 1 only on an injection failure; everything else is reported.

Usage:
    python scripts/diagnostics/audit_gate_prompts.py
    python scripts/diagnostics/audit_gate_prompts.py --digest-only   # for the 2-process check
"""

from __future__ import annotations

import argparse
import hashlib
import re
import statistics
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from rapidfuzz import fuzz  # noqa: E402

from evaluation.prompt import relevance_builder as rb  # noqa: E402
from ingestion import get_ipmp_store, get_retrieval_profile_store  # noqa: E402

RESTATE = 90  # same bar audit_gate_flips.py uses for "critério repetido"


def norm(t: str) -> str:
    return " ".join(t.split()).rstrip(".").lower()


def _sort_key(pid: str) -> tuple:
    head = pid.split(".")[0].rstrip("abcdefghijklmnopqrstuvwxyz")
    return (int(head), pid)


def build_all() -> list[dict]:
    ipmp = get_ipmp_store()
    profiles = get_retrieval_profile_store()
    rows: list[dict] = []
    for acao_id in sorted(ipmp.acoes):
        acao = ipmp.acoes[acao_id]
        profile = profiles.acoes.get(acao_id)
        scored = [p for p in acao.produtos_esperados if p.scored]
        for product in scored:
            pp = profile.expected_products.get(product.id) if profile else None
            if pp is None or not pp.evidence_intent:
                rows.append({"acao": acao_id, "pid": product.id, "ungated": True})
                continue
            concepts = [c.text for c in pp.retrieval_signal_concepts]
            negatives = list(pp.negative_evidence_patterns)
            system = rb.build_relevance_system_prompt(
                pp.evidence_intent, concepts, negatives, acao=acao, product_id=product.id,
            )
            rows.append({
                "acao": acao_id, "pid": product.id, "ungated": False,
                "n_siblings": len(scored), "texto": product.texto,
                "intent": pp.evidence_intent, "concepts": concepts, "negatives": negatives,
                "system": system,
            })
    return rows


# Padroes que denunciam o caso concreto dentro de um campo canonico. O prompt do
# gate vale para qualquer caso: nome de documento, pagina, data de validacao ou
# referencia de lote nao pertencem a ele. Dez padroes negativos carregavam
# "Validado 2026-09-08 ... SMG-040 p.195/196" antes de 2026-10-03.
VAZAMENTO = [
    # "_" e caractere de palavra, logo um \b final nunca fecharia em
    # SMG-040_101607_2024_1; o grupo repetido cobre o sufixo inteiro.
    ("nome de documento", re.compile(r"\b[A-Z]{2,}[-_]\d{3}(?:[_-]\d+)*")),
    ("página citada", re.compile(r"\b(?:p|pg|pág|fls?)\.?\s?\d{1,4}\b", re.I)),
    ("data de validação", re.compile(r"\bvalidad[oa]\b|\b20\d{2}-\d{2}-\d{2}\b", re.I)),
    ("arquivo", re.compile(r"\.pdf\b", re.I)),
    ("lote do certame", re.compile(r"\bLOTE\s?\d\b")),
]


def check_vazamento(r: dict) -> list[str]:
    """Campos canonicos do produto que carregam marca do caso concreto."""
    achados = []
    campos = [("intent", r["intent"])]
    campos += [(f"conceito[{i}]", c) for i, c in enumerate(r["concepts"])]
    campos += [(f"negativo[{i}]", n) for i, n in enumerate(r["negatives"])]
    for nome_campo, texto in campos:
        for rotulo, padrao in VAZAMENTO:
            m = padrao.search(texto)
            if m:
                achados.append(f"{nome_campo}: {rotulo} ({m.group(0)!r})")
    return achados


def check_injection(r: dict) -> list[str]:
    s, acao, pid = r["system"], r["acao"], r["pid"]
    problems = []
    if f"Ação {acao} —" not in s:
        problems.append("sem 'Ação N —' no bloco de identidade")
    if f"Produto Esperado {pid}" not in s:
        problems.append("product_id ausente do bloco de identidade")
    expected_pos = (
        f"um dos {r['n_siblings']} Produtos Esperados" if r["n_siblings"] > 1
        else "o único Produto Esperado"
    )
    if expected_pos not in s:
        problems.append(f"contagem de irmãos errada (esperado '{expected_pos}')")
    if r["intent"] not in s:
        problems.append("evidence_intent não aparece verbatim")
    # V4 rule (2026-10-03): a concept list whose every entry restates the intent is
    # omitted by the builder; the audit checks the omission exactly as it checks
    # the presence of a genuine list. Older builders have no such rule.
    restates = getattr(rb, "_concepts_restate_intent", None)
    omitted = bool(restates and r["concepts"] and restates(r["concepts"], r["intent"]))
    if omitted:
        if "Qualquer um dos elementos abaixo" in s or any(f"- {c}" in s for c in r["concepts"]):
            problems.append("lista de conceitos degenerada deveria ter sido omitida (V4)")
    else:
        for c in r["concepts"]:
            if f"- {c}" not in s:
                problems.append(f"conceito ausente: {c[:50]!r}")
    for n in r["negatives"]:
        if f"- {n}" not in s:
            problems.append(f"padrão negativo ausente: {n[:50]!r}")
    if rb._SCOPE_RULE not in s:
        problems.append("_SCOPE_RULE ausente")
    if rb._INSTRUCTIONS not in s:
        problems.append("_INSTRUCTIONS ausente")
    if s.count("## Critério de relevância") != 1:
        problems.append("secção de critério duplicada ou ausente")
    # The quote rule: product text quoted iff it does not restate the intent.
    a, b = " ".join(r["texto"].split()).lower(), " ".join(r["intent"].split()).lower()
    should_quote = fuzz.partial_ratio(a, b) < rb._INTENT_RESTATES_PRODUCT
    quoted = f"«{r['texto']}»" in s
    if should_quote != quoted:
        problems.append(f"regra da citação violada (deveria citar={should_quote}, citou={quoted})")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest-only", action="store_true")
    ap.add_argument("--sibling-threshold", type=int, default=75,
                    help="partial_ratio above which two sibling criteria count as 'alike'")
    args = ap.parse_args()

    rows = build_all()
    gated = [r for r in rows if not r["ungated"]]
    global_digest = hashlib.sha256(
        "\n\x00\n".join(f"{r['acao']}|{r['pid']}|{r['system']}" for r in gated).encode()
    ).hexdigest()[:16]
    if args.digest_only:
        print(global_digest)
        return 0

    print(f"produtos pontuados: {len(rows)}  |  com gate: {len(gated)}  |  "
          f"sem evidence_intent (passam SEM gate): {len(rows) - len(gated)}")
    print(f"digest global dos {len(gated)} prompts: {global_digest}\n")

    # ---- injection -------------------------------------------------------
    failures = 0
    for r in gated:
        probs = check_injection(r)
        if probs:
            failures += 1
            print(f"  [FALHA] {r['acao']}/{r['pid']}: " + "; ".join(probs))
    print(f"injeção: {len(gated) - failures}/{len(gated)} prompts corretos"
          + ("" if not failures else f"  <<< {failures} com problema"))

    # ---- degeneracy --------------------------------------------------------
    degenerate, partial, no_neg, quoted = [], [], [], 0
    for r in gated:
        ratios = [fuzz.ratio(norm(c), norm(r["intent"])) for c in r["concepts"]]
        if ratios and all(x >= RESTATE for x in ratios):
            degenerate.append(r["pid"])
        elif any(x >= RESTATE for x in ratios):
            partial.append(r["pid"])
        if not r["negatives"]:
            no_neg.append(r["pid"])
        if f"«{r['texto']}»" in r["system"]:
            quoted += 1
    restates = getattr(rb, "_concepts_restate_intent", None)
    omitted_v4 = [r["pid"] for r in gated if restates and r["concepts"] and restates(r["concepts"], r["intent"])]
    print("\ndegenerescência:")
    print(f"  lista de conceitos omitida do prompt (V4): {len(omitted_v4)}/{len(gated)}"
          + ("" if restates else "  (builder sem a regra V4)"))
    print(f"  todos os conceitos repetem o intent ({RESTATE}+): {len(degenerate)}/{len(gated)}"
          f"  -> {' '.join(degenerate)}")
    print(f"  algum conceito repete o intent: {len(partial)}/{len(gated)}")
    print(f"  sem nenhum padrão negativo: {len(no_neg)}/{len(gated)}  -> {' '.join(no_neg)}")
    both = sorted(set(degenerate) & set(no_neg), key=_sort_key)
    print(f"  AMBOS (critério repetido E sem padrão negativo): {len(both)}  -> {' '.join(both)}")
    print(f"  produto citado no bloco de identidade: {quoted}/{len(gated)}")
    n_conc = [len(r["concepts"]) for r in gated]
    n_neg = [len(r["negatives"]) for r in gated]
    print(f"  conceitos/produto: min={min(n_conc)} mediana={statistics.median(n_conc)} max={max(n_conc)}"
          f"   padrões negativos/produto: min={min(n_neg)} mediana={statistics.median(n_neg)} max={max(n_neg)}")


    # ---- vazamento de corpus ------------------------------------------------
    vaz = [(r["pid"], check_vazamento(r)) for r in gated]
    vaz = [(pid, a) for pid, a in vaz if a]
    print("\nvazamento de corpus em campo canônico (nome de documento, página, "
          "data de validação, arquivo, lote):")
    if vaz:
        print(f"  produtos afetados: {len(vaz)}/{len(gated)}")
        for pid, achados in sorted(vaz, key=lambda x: _sort_key(x[0])):
            for a in achados:
                print(f"    {pid:8} {a}")
    else:
        print(f"  nenhum em {len(gated)} produtos")
    # ---- siblings -----------------------------------------------------------
    print("\nsemelhança entre critérios irmãos (partial_ratio sobre intent+conceitos):")
    by_acao: dict[int, list[dict]] = {}
    for r in gated:
        by_acao.setdefault(r["acao"], []).append(r)
    alike_pairs, all_pairs, worst = [], 0, []
    for acao_id, prods in by_acao.items():
        for x, y in combinations(prods, 2):
            all_pairs += 1
            cx = norm(x["intent"] + " " + " ".join(x["concepts"]))
            cy = norm(y["intent"] + " " + " ".join(y["concepts"]))
            score = fuzz.partial_ratio(cx, cy)
            worst.append((score, x["pid"], y["pid"]))
            if score >= args.sibling_threshold:
                alike_pairs.append((score, x["pid"], y["pid"]))
    worst.sort(reverse=True)
    scores = [w[0] for w in worst]
    print(f"  pares de irmãos: {all_pairs}  mediana={statistics.median(scores):.0f}"
          f"  >= {args.sibling_threshold}: {len(alike_pairs)}")
    print("  os 12 pares mais parecidos:")
    for score, a, b in worst[:12]:
        print(f"    {a:>6} ~ {b:<6}  {score:.0f}")
    identical = [(a, b) for s_, a, b in worst if s_ >= 100]
    if identical:
        print(f"  IDÊNTICOS (100): {identical}")

    # ---- size ---------------------------------------------------------------
    sizes = [len(r["system"]) for r in gated]
    print(f"\ntamanho do prompt de sistema (chars): min={min(sizes)} mediana={statistics.median(sizes):.0f}"
          f" média={statistics.mean(sizes):.0f} max={max(sizes)}  (~{max(sizes)//4} tokens no maior)")
    big = sorted(gated, key=lambda r: -len(r["system"]))[:5]
    print("  5 maiores: " + ", ".join(f"{r['pid']}={len(r['system'])}" for r in big))

    # ---- what the model is told, structurally ------------------------------
    user_sample = rb.build_relevance_user_prompt("<trecho>", product_id="NNx")
    has_tiebreak = "dúvida" in (rb._INSTRUCTIONS + rb._SCOPE_RULE).lower()
    print(f"\nestrutura fixa do prompt (igual para os {len(gated)}):")
    print("  ordem: cabeçalho -> identidade+escopo -> critério(intent, conceitos, negativos) -> instrução")
    print(f"  regra de decisão explícita para casos limítrofes: {'presente' if has_tiebreak else 'AUSENTE'}")
    print(f"  prompt de usuário: {user_sample!r}  (product_id junto ao trecho: "
          f"{'sim' if 'Produto' in user_sample else 'não'})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
