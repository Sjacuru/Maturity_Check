import sys
import time

sys.path.insert(0, "src")
from evaluation.llm.ollama import OllamaClient
from evaluation.prompt.relevance_builder import build_relevance_system_prompt, build_relevance_user_prompt
from evaluation.parsing.relevance_response import parse_relevance_response
from evaluation.evidence_selection import _is_verbatim_subsequence

EVIDENCE_INTENT = (
    "Descrição concisa dos motivos pelo qual o projeto é necessário: diagnóstico "
    "de deficiências operacionais, problemas de capacidade, demanda pública não "
    "atendida, fragmentação ou encerramento contratual."
)

NOISE_CHUNK = (
    "PREFEITURA DA CIDADE DO RIO DE JANEIRO Secretaria Municipal de Coordenacao "
    "Governamental R. Afonso Cavalcanti, 455"
)

REAL_RELEVANT_CHUNK = (
    "Atualmente, apos aditivos, os referidos contratos compreendem apenas "
    "abrigos de onibus, MUPIs e relogios eletronicos, que somados totalizam "
    "cerca de 8.500 equipamentos."
)

MODELS = [
    "splitpierre/bode-alpaca-pt-br:latest",
    "cnmoro/Qwen2.5-0.5B-Portuguese-v2:fp16",
]


def probe(model_name: str, label: str, chunk_text: str, expected: str) -> None:
    client = OllamaClient(model=model_name, num_predict=600, timeout=180)
    system = build_relevance_system_prompt(EVIDENCE_INTENT)
    user = build_relevance_user_prompt(chunk_text)
    t0 = time.time()
    try:
        raw = client.complete(system, user)
    except Exception as exc:
        print(f"[{model_name}] {label}: ERROR after {time.time()-t0:.1f}s: {exc}")
        return
    elapsed = time.time() - t0
    verdict = parse_relevance_response(raw)

    verbatim_ok = None
    if verdict.relevant and verdict.cleaned_text:
        verbatim_ok = _is_verbatim_subsequence(verdict.cleaned_text, chunk_text)

    got = "yes" if verdict.relevant else "no"
    correct = "OK" if got == expected else "MISMATCH"
    print(f"\n=== [{model_name}] {label} ({elapsed:.1f}s) — expected={expected} got={got} [{correct}] ===")
    print(f"parse_failed={verdict.parse_failed} verbatim_subsequence_ok={verbatim_ok}")
    print("RAW:", repr(raw)[:400])


for model in MODELS:
    probe(model, "NOISE_CHUNK (header/address)", NOISE_CHUNK, expected="no")
    probe(model, "REAL_RELEVANT_CHUNK (top 1a evidence)", REAL_RELEVANT_CHUNK, expected="yes")
