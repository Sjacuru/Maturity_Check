"""Raciocínio do scorer sobre levas fixas: item 3 do plano de 2026-10-04 (§4.3 de
scratchpad/CICLO1_2026-10-04.md), retomado a pedido do usuário em 2026-10-16.

Cada alvo é uma leva gravada de um processo dos ciclos 3 a 7, dada como (Ação, ciclo,
processo). O gate não é chamado. Os vereditos gravados daquele processo (gate.reasoning
do JSON do ciclo) são repetidos dentro de select_evidence sobre a recuperação de HEAD,
que é a mesma desses ciclos (ADR-0074; para a Ação 45, só a partir do C6). Antes de
qualquer chamada ao scorer, a leva reconstruída (arquivo, página, trecho, produtos) é
comparada com a gravada. Um alvo que não bate é descartado e registrado.

O scorer de produção, isto é, o cliente de main.py com o esforço padrão, é chamado N
vezes sobre cada leva. A cada passada a ordem dos alvos é embaralhada com semente fixa,
para que a mesma pergunta não venha sempre depois da mesma vizinha. Cada chamada grava:
- o veredito por produto, com a justificativa;
- o campo reasoning do JSON e o canal de análise do modelo;
- o motivo de parada e os tokens;
- o hash dos dois prompts, que prova que a pergunta foi a mesma em todas as passadas.

Nada é persistido no banco, e o ledger do gate fica desligado. A opção --dry-run troca o
scorer por um stub e só confere a reconstrução das levas, sem GPU.
"""
import argparse
import hashlib
import json
import random
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

import main as app_main  # noqa: E402,F401 — wiring de produção (banco, clientes)

import evaluation.evidence_selection as es  # noqa: E402
from assessment.service import _retrieve_and_select  # noqa: E402
from evaluation import configure_gate_ledger, configure_llm_client, evaluate  # noqa: E402
from evaluation._config import get_llm_client, get_model, get_provider  # noqa: E402
from evaluation.parsing.relevance_response import RelevanceVerdict  # noqa: E402
from ingestion import get_ipmp_store  # noqa: E402

configure_gate_ledger(None)
PROCESS = "SMG-040_101607_2024"
ACC = ROOT / "scratchpad" / "acc"

# (Ação, ciclo, processo). Primeiro, as levas em que o scorer variou sobre prompt idêntico
# nos ciclos 3 a 7. Depois, levas com veredito constante, que servem de controle.
ALVOS_PADRAO = [
    (32, 7, 10), (10, 7, 10), (10, 7, 5), (35, 6, 10), (13, 6, 9), (26, 7, 8), (2, 6, 8),
    (37, 7, 6), (46, 7, 9), (22, 6, 6), (42, 6, 6),
    (26, 7, 10), (2, 7, 9), (37, 7, 8), (37, 7, 3), (22, 7, 10), (1, 7, 9), (3, 7, 10),
    (9, 7, 7), (28, 7, 10),
]

_REPLAY: dict = {}
_FALTAS: list = []


def _gate_repetido(text, evidence_intent, concepts, negative_patterns=None, acao=None,
                   product_id=None, chunk=None, process_number=None, memo=None):
    """No lugar de _gate_chunk, responde com o veredito gravado. O que não foi gravado
    vale como rejeição: são aceites que a deduplicação descartou e que, por isso,
    não mudam a leva."""
    chave = (product_id, chunk.filename, chunk.page_number, chunk.chunk_index)
    v = _REPLAY.get(chave)
    if v is None:
        _FALTAS.append(chave)
        v = False
    return es._GateCall(RelevanceVerdict(relevant=v, parse_failed=False),
                        provider="replay", model="replay")


es._gate_chunk = _gate_repetido


def _h(texto):
    return hashlib.sha256((texto or "").encode("utf-8")).hexdigest()[:16]


def _assinatura(chunks):
    return sorted([c.filename, c.page_number, c.chunk_index, sorted(c.expected_product_ids)]
                  for c in chunks)


def _carrega(acao, ciclo, proc):
    d = json.loads((ACC / f"ciclo{ciclo}_run{proc}.json").read_text(encoding="utf-8"))
    g = d["gate"][str(acao)][0] or {}
    mapa = {}
    for linha in g.get("reasoning") or []:
        f, p, c, pid, aceito = linha[:5]
        k = (pid, f, p, c)
        if k in mapa and mapa[k] != bool(aceito):
            raise SystemExit(f"veredito contraditório gravado em {k}")
        mapa[k] = bool(aceito)
    gravada = sorted([f, p, c, sorted(pids)] for f, p, c, pids in d["accepted"][str(acao)][0])
    return mapa, gravada, d["outcomes"][str(acao)][0], g.get("verdicts", {})


def _desfecho(r):
    if r.no_evidence_found:
        return "sem_evidencia"
    if r.parse_failed:
        return "parse_failed"
    return f"score={r.proposed_score}"


class _Captura:
    """Envolve o cliente do scorer: chama complete_detailed() e guarda a resposta inteira."""

    def __init__(self, inner):
        self.inner = inner
        self.ultima = None

    def complete(self, system, user, schema=None):
        self.ultima = None
        self.ultima = self.inner.complete_detailed(system, user, schema=schema)
        return self.ultima.content

    def __getattr__(self, nome):
        return getattr(self.inner, nome)


class _Stub:
    def __init__(self, pids):
        self.pids = pids

    def complete(self, system, user, schema=None):
        return json.dumps({
            "products": [{"product_id": p, "evidenced": False, "justificativa": "stub"} for p in self.pids],
            "reasoning": "stub", "score": 0, "uncertainty": False,
        })


def _grava(out, caminho):
    tmp = Path(caminho).with_suffix(".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(caminho)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--alvos", default=None, help="Ação:ciclo:processo, separados por vírgula")
    ap.add_argument("--passes", type=int, default=10)
    ap.add_argument("--semente", type=int, default=20261016)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=str(ACC / "scorer_raciocinio.json"))
    args = ap.parse_args()
    alvos = (ALVOS_PADRAO if not args.alvos
             else [tuple(int(x) for x in a.split(":")) for a in args.alvos.split(",") if a.strip()])
    ipmp = get_ipmp_store()

    levas = []
    descartados = []
    for acao, ciclo, proc in alvos:
        rotulo = f"A{acao}-C{ciclo}r{proc}"
        mapa, gravada, desfecho, verds = _carrega(acao, ciclo, proc)
        _REPLAY.clear()
        _REPLAY.update(mapa)
        _FALTAS.clear()
        accepted, rejected, reports = _retrieve_and_select(acao, PROCESS)
        refeita = _assinatura(accepted)
        ok = refeita == gravada
        situacao = "IGUAL" if ok else "DIFERENTE"
        print(f"{rotulo}: leva {situacao} à gravada ({len(accepted)} trecho(s)); "
              f"vereditos não gravados respondidos como rejeição: {len(_FALTAS)}; "
              f"gravado {desfecho} {verds}", flush=True)
        if not ok:
            print(f"   refeita: {refeita}")
            print(f"   gravada: {gravada}")
            descartados.append(rotulo)
            continue
        pids = [p.id for p in ipmp.acoes[acao].produtos_esperados if p.scored]
        levas.append({"rotulo": rotulo, "acao": acao, "ciclo": ciclo, "processo": proc,
                      "accepted": accepted, "rejected": rejected, "reports": reports, "pids": pids,
                      "gravado": {"desfecho": desfecho, "vereditos": verds}, "assinatura": refeita,
                      "faltas": [list(f) for f in _FALTAS]})

    prod, provider, model = get_llm_client(), get_provider(), get_model()
    out = {"process": PROCESS, "passes": args.passes, "semente": args.semente,
           "dry_run": args.dry_run, "descartados": descartados, "levas": {}, "chamadas": []}
    for lv in levas:
        configure_llm_client(_Stub(lv["pids"]), provider="stub", model="stub")
        r = evaluate(lv["acao"], PROCESS, lv["accepted"], rejected_chunks=lv["rejected"],
                     product_gate_reports=lv["reports"])
        reg = {k: lv[k] for k in ("acao", "ciclo", "processo", "pids", "gravado", "assinatura", "faltas")}
        reg.update({"system": r.system_prompt, "user": r.user_prompt,
                    "hash_system": _h(r.system_prompt), "hash_user": _h(r.user_prompt)})
        out["levas"][lv["rotulo"]] = reg
        print(f"  {lv['rotulo']}: prompt de sistema {len(r.system_prompt)} car. ({reg['hash_system']}), "
              f"de usuário {len(r.user_prompt)} car. ({reg['hash_user']})", flush=True)
    configure_llm_client(prod, provider=provider, model=model)
    if args.dry_run or not levas:
        _grava(out, args.out)
        print(f"gravado {args.out} (sem chamadas ao scorer)")
        return 0 if not descartados else 2

    cap = _Captura(prod)
    configure_llm_client(cap, provider=provider, model=model)
    rnd = random.Random(args.semente)
    anterior = None
    erros_seguidos = 0
    try:
        for passada in range(1, args.passes + 1):
            ordem = list(levas)
            rnd.shuffle(ordem)
            for lv in ordem:
                t0 = time.monotonic()
                item = {"passada": passada, "leva": lv["rotulo"], "anterior": anterior}
                try:
                    r = evaluate(lv["acao"], PROCESS, lv["accepted"], rejected_chunks=lv["rejected"],
                                 product_gate_reports=lv["reports"])
                    c = cap.ultima
                    item.update({
                        "desfecho": _desfecho(r), "fonte": r.score_source, "incerteza": r.uncertainty_flag,
                        "vereditos": {v.product_id: v.evidenced for v in r.product_verdicts},
                        "justificativas": {v.product_id: v.justificativa for v in r.product_verdicts},
                        "reasoning": r.reasoning,
                        "analise": c.reasoning if c else None,
                        "finish": c.finish_reason if c else None,
                        "tokens": c.completion_tokens if c else None,
                        "hash_system": _h(r.system_prompt), "hash_user": _h(r.user_prompt),
                    })
                    erros_seguidos = 0
                except Exception as exc:  # a medição segue; a falha fica registrada
                    item["erro"] = f"{type(exc).__name__}: {exc}"
                    erros_seguidos += 1
                item["segundos"] = round(time.monotonic() - t0, 1)
                out["chamadas"].append(item)
                anterior = lv["rotulo"]
                com_trecho = {p for *_, pids in lv["assinatura"] for p in pids}
                vv = " ".join(f"{k}={'T' if v else 'F'}"
                              for k, v in sorted((item.get("vereditos") or {}).items()) if k in com_trecho)
                print(f"passada {passada:2d} {lv['rotulo']:12s} {item.get('desfecho', item.get('erro'))} {vv} "
                      f"({item['segundos']} s, {item.get('tokens')} tokens)", flush=True)
                if erros_seguidos >= 3:
                    raise RuntimeError("três falhas seguidas do scorer; medição interrompida")
            _grava(out, args.out)
    finally:
        configure_llm_client(prod, provider=provider, model=model)
        _grava(out, args.out)
    print(f"gravado {args.out}: {len(out['chamadas'])} chamadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
