"""Measure candidate gate-prompt wordings on one Ação WITHOUT touching src/.

Each variant monkeypatches `evaluation.prompt.relevance_builder` in memory and
reuses audit_gate_flips.py's machinery (same production candidates, same
server, same reasoning capture). Nothing here changes what production sends.

The variants come from what 640 captured reasoning traces on Ação 14 showed:

  V1 procedure  — the model already applies "mentions the topic != contains the
                  required element" in 79% of traces and that test almost always
                  rejects; the accepting traces are the ones that abandon it
                  (e.g. redefining "benefit" as "asset condition"). V1 states
                  that test as the procedure and adds the tiebreak the prompt
                  never had ("em caso de dúvida, false").
  V2 concepts   — 23/164 products list concepts that merely restate the intent,
                  and one accepting trace quoted "Qualquer um dos elementos
                  abaixo também conta" to accept on a looser reading of that
                  restatement. V2 = V1 + drop a concept list that restates the
                  intent (same fuzz rule the identity block already uses) and
                  reframe the list as FORMS of the required element.
  V3 siblings   — the abstract scope rule is cited in 0.8% of traces, and the
                  model names the wrong sibling in 62% of them. V3 = V2 + list
                  the sibling products explicitly as NOT under evaluation, and
                  repeat the product id next to the chunk in the user prompt.
  V4 surgical   — ONLY drop a concept list that restates the intent; no new
                  wording anywhere. By construction it changes the prompt of
                  the 23 degenerate products and nothing else. Added after
                  V1/V2/V3 were measured on Ações 22 and 3 (real evidence) and
                  found to turn the genuine 22.2 risk matrix (p.774) from
                  6/6 accepted into a flipper: generic strictness trades false
                  positives on no-evidence Ações for false negatives on real
                  ones. V4 keeps the one mechanism that was actually observed
                  causing a false accept and nothing that could cause a miss.
  V5 siblings-only — base + sibling contrast list + product id in the user
                  prompt, without V1/V2's text. Isolates the sibling question.
                  PROMOTED TO PRODUCTION 2026-10-02 (ADR-0064): the sibling
                  list and the user-prompt tag now live in relevance_builder,
                  so "base" already includes them and V3/V5 are no longer
                  selectable (they would apply the list twice).

  P1 polarity   — R11's inspection (2026-10-02) found Ação 26's only on-topic
                  chunks — a parecer stating the PPA/LDO/LOA declaration was
                  NOT met (p.136) and the reply that it does not apply to a
                  concession (p.144) — rejected 4/4 because the model reads
                  "evidência DESTE Produto" as evidence THAT it is satisfied.
                  P1 = base + one sentence in the instructions: a chunk that
                  directly addresses what the criterion asks is relevant even
                  when it attests non-fulfilment or inapplicability; judging
                  fulfilment is the next stage's job; this does not make a
                  chunk relevant for merely mentioning the topic. Measured on
                  26 (must flip p.136/p.144) and on 14/22/3 (must not move).
                  Measured at serial+low: 26d/p.136 FFFF -> TTTT, but 26a's
                  p.136/p.144 only became oscillating (FTFT, FTTF).
  P2 polarity   — the same idea stated as a definition ("relevante" = trata do
                  que o critério pede, não que esteja cumprido) with the
                  parecer/manifestação case named explicitly.

Usage:
    python scripts/diagnostics/measure_gate_prompt_variants.py --variant V1 --acao 14 \
        --passes 8 --in-flight 4 --out out.json
    python scripts/diagnostics/measure_gate_prompt_variants.py --variant base ...   # control
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "diagnostics"))

from rapidfuzz import fuzz  # noqa: E402

from evaluation.prompt import relevance_builder as rb  # noqa: E402

# --------------------------------------------------------------------------- texts
PROCEDURE = """\
Procedimento de decisão:
1. Identifique o elemento concreto que o critério exige (um responsável nomeado, \
um método descrito, uma métrica definida, uma análise apresentada, etc.).
2. Verifique se o trecho CONTÉM esse elemento. Tratar do mesmo tema, mencionar o \
projeto ou ser uma obrigação contratual genérica não é suficiente.
3. Responda true somente se o elemento está presente no trecho. Se o trecho apenas \
tangencia o tema, se o elemento pertence a outro Produto Esperado desta Ação, ou se \
restar dúvida, responda false.

Considere o trecho em português, mesmo que contenha termos em outro idioma. \
Preencha o campo "relevant" do objeto JSON de resposta com true ou false. \
Nenhum outro campo é esperado.\
"""

CONCEPT_INTRO_V2 = (
    "O elemento exigido pode aparecer no documento sob qualquer destas formas "
    "(basta uma, mas o elemento em si precisa estar presente):"
)

def _concepts_restate(concepts: list[str], intent: str) -> bool:
    norm = lambda t: " ".join(t.split()).rstrip(".").lower()  # noqa: E731
    return bool(concepts) and all(fuzz.ratio(norm(c), norm(intent)) >= 90 for c in concepts)


# ------------------------------------------------------------------ patched builders
_ORIGINAL_BUILD = rb.build_relevance_system_prompt
_ORIGINAL_IDENTITY = rb._identity_block
_ORIGINAL_USER = rb.build_relevance_user_prompt


def _build_v2(evidence_intent, concepts=None, negative_patterns=None, *, acao=None, product_id=None):
    """V1's text plus: no concept list when it restates the intent; concept list
    framed as forms of the required element rather than extra ways to pass."""
    criterion = evidence_intent
    if concepts and not _concepts_restate(concepts, evidence_intent):
        bullet_list = "\n".join(f"- {c}" for c in concepts)
        criterion = f"{evidence_intent}\n\n{CONCEPT_INTRO_V2}\n{bullet_list}"
    if negative_patterns:
        negative_list = "\n".join(f"- {p}" for p in negative_patterns)
        criterion = (
            f"{criterion}\n\n"
            "Os padrões abaixo NÃO contam como evidência válida para este critério, "
            f"mesmo que mencionem termos ou o contexto do projeto relacionados:\n{negative_list}"
        )
    header = (
        "Você é um classificador de relevância de evidências para auditoria de "
        "processos de Parceria Público-Privada (PPP), avaliados segundo o "
        "framework IPMP.\n\n"
    )
    if acao is not None and product_id is not None:
        header = f"{header}{rb._identity_block(acao, product_id, evidence_intent)}\n\n"
    return (
        f"{header}"
        f"## Critério de relevância para este Produto Esperado\n\n{criterion}"
        f"\n\n---\n\n{rb._INSTRUCTIONS}"
    )


def _build_v4(evidence_intent, concepts=None, negative_patterns=None, *, acao=None, product_id=None):
    """The production builder with ONE change: no concept list when every
    concept merely restates the intent (promoted to production 2026-10-03,
    item 6 of that day's plan; kept here so the pre-promotion base can still be
    compared by passing the concepts through unfiltered if ever needed)."""
    if concepts and _concepts_restate(concepts, evidence_intent):
        concepts = None
    return _ORIGINAL_BUILD(evidence_intent, concepts, negative_patterns, acao=acao, product_id=product_id)


POLARITY_INSTRUCTIONS = """Considere o trecho em português, mesmo que contenha termos em outro idioma. Um trecho que trate diretamente do que este critério pede é relevante mesmo quando registra que o item NÃO foi atendido, não foi elaborado ou não se aplica a este processo — julgar o cumprimento é da etapa seguinte, não deste classificador; isso não torna relevante um trecho que apenas mencione o tema sem tratar do elemento exigido. Preencha o campo "relevant" do objeto JSON de resposta com true (relevante) ou false (não relevante). Nenhum outro campo é esperado."""


POLARITY_INSTRUCTIONS_P2 = (
    "Considere o trecho em português, mesmo que contenha termos em outro idioma. "
    "\"Relevante\" significa que o trecho trata do que este critério pede — não que o "
    "critério esteja cumprido. Um parecer, manifestação, resposta ou registro que examine "
    "especificamente o item exigido por este critério e conclua que ele NÃO foi apresentado, "
    "não foi atendido ou não se aplica a este processo É relevante (true): é a evidência de "
    "como o processo tratou o critério, e o julgamento sobre cumprimento é da etapa seguinte. "
    "Um trecho que apenas mencione o tema sem tratar do elemento exigido continua não "
    "relevante. "
    "Preencha o campo \"relevant\" do objeto JSON de resposta com true (relevante) ou false "
    "(não relevante). Nenhum outro campo é esperado."
)


def apply_variant(name: str) -> None:
    if name == "base":
        return
    if name == "P1":
        return  # promoted to production 2026-10-03 (ADR-0066): base already contains it
    if name == "P2":
        rb._INSTRUCTIONS = POLARITY_INSTRUCTIONS_P2
        return
    if name == "V4":
        rb.build_relevance_system_prompt = _build_v4
        return
    if name in ("V1", "V2"):
        rb._INSTRUCTIONS = PROCEDURE
    if name == "V2":
        rb.build_relevance_system_prompt = _build_v2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["base", "V1", "V2", "V4", "P1", "P2"], required=True)
    ap.add_argument("--acao", type=int, default=14)
    ap.add_argument("--passes", type=int, default=8)
    ap.add_argument("--in-flight", type=int, default=4)
    ap.add_argument("--cache-prompt", choices=["default", "on", "off"], default="default")
    ap.add_argument("--reasoning-effort", choices=["default", "low", "medium", "high"], default="default")
    ap.add_argument("--pin-slot", type=int, default=None)
    ap.add_argument("--chars", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--show-prompt", default=None, help="print the variant prompt for this product id and exit")
    args = ap.parse_args()

    apply_variant(args.variant)

    import audit_gate_flips as g  # after patching: it imports the builder by name at call time

    # audit_gate_flips bound the builder functions at import; rebind to the patched ones
    g.build_relevance_system_prompt = rb.build_relevance_system_prompt
    g.build_relevance_user_prompt = rb.build_relevance_user_prompt

    if args.show_prompt:
        from ingestion import get_ipmp_store, get_retrieval_profile_store
        acao = get_ipmp_store().acoes[args.acao]
        pp = get_retrieval_profile_store().acoes[args.acao].expected_products[args.show_prompt]
        print(rb.build_relevance_system_prompt(
            pp.evidence_intent, [c.text for c in pp.retrieval_signal_concepts],
            pp.negative_evidence_patterns, acao=acao, product_id=args.show_prompt))
        print("\n--- user ---\n" + rb.build_relevance_user_prompt("<trecho>"))
        return 0

    argv = ["audit_gate_flips.py", "--acao", str(args.acao), "--passes", str(args.passes),
            "--in-flight", str(args.in_flight), "--cache-prompt", args.cache_prompt,
            "--reasoning-effort", args.reasoning_effort, "--chars", str(args.chars)]
    if args.pin_slot is not None:
        argv += ["--pin-slot", str(args.pin_slot)]
    if args.out:
        argv += ["--out", args.out]
    print(f"### variante {args.variant}")
    sys.argv = argv
    return g.main()


if __name__ == "__main__":
    raise SystemExit(main())
