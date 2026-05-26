# publish_issues.ps1
# Prerequisites: gh auth login (https://cli.github.com/)
# Run: pwsh -File docs\publish_issues.ps1
# Issues are created in dependency order so blockers can reference real issue numbers.

$REPO = "Sjacuru/Maturity_Check"

# --- Ensure label exists ---
function Ensure-Label($name, $color, $desc) {
    $existing = gh label list --repo $REPO --json name | ConvertFrom-Json | Where-Object { $_.name -eq $name }
    if (-not $existing) {
        gh label create $name --repo $REPO --color $color --description $desc
        Write-Host "Created label: $name"
    }
}
Ensure-Label "ready-for-agent" "0075ca" "AFK slice — can be implemented without human interaction"
Ensure-Label "hitl"            "e4e669" "Human-in-the-loop — requires human review before proceeding"
Ensure-Label "module:ingestion" "d93f0b" "Module 1 — Ingestion layer"

# --- Issue 1: Package scaffold ---
$issue1 = gh issue create `
  --repo $REPO `
  --title "Ingestion: package scaffold" `
  --label "ready-for-agent,module:ingestion" `
  --body @'
**What to build**

Create the `src/ingestion/` Python package so it is installable and importable. This slice has no application logic — it is purely structural setup that all subsequent ingestion slices depend on.

Deliver: `src/ingestion/__init__.py` as an empty (or stub) public surface. Verify the package is importable after `pip install -e .` without errors.

**Acceptance criteria**

- [ ] `src/ingestion/` directory exists with `__init__.py`
- [ ] `pip install -e .` succeeds in the project's Python environment
- [ ] `from ingestion import get_ipmp_store` raises `ImportError` with a clear message (or `AttributeError` if `__init__.py` is empty) — not a module-not-found error
- [ ] No application logic in `__init__.py` at this stage

**Blocked by**

None — can start immediately
'@

$issue1_num = ($issue1 -split '/')[-1]
Write-Host "Created Issue #$issue1_num: Package scaffold"

# --- Issue 2: IPMP singleton ---
$issue2 = gh issue create `
  --repo $REPO `
  --title "Ingestion: IPMP singleton (get_ipmp_store)" `
  --label "ready-for-agent,module:ingestion" `
  --body @"
**What to build**

Implement `ingestion/ipmp.py` end-to-end: Pydantic models, glob-based file discovery, tolerant loader (ADR-0010 fatal/non-fatal split), and the `get_ipmp_store()` singleton. Export `get_ipmp_store` from `__init__.py` as the only public symbol added by this slice.

Pydantic model shapes (finalized in grill-me session):

``````python
class Exemplo(BaseModel):
    nivel: str
    score: int          # 0, 1, or 3
    texto: str

class ProdutoEsperado(BaseModel):
    id: str             # validated: r"^\d+[a-z]?\$"  — canonical id, not a query label
    texto: str

class AcaoIPMP(BaseModel):
    acao_id: int
    titulo: str
    dimensao: str
    por_que_importante: str
    descricao_acao: str
    o_que_esperar: str
    produtos_esperados: list[ProdutoEsperado]
    momento_ideal: str
    excecoes: list[str]
    exemplos: list[Exemplo]

class IPMPStore(BaseModel):
    acoes: dict[int, AcaoIPMP]
``````

Tolerant loading rules (ADR-0010):
- **Fatal** (crash immediately): data directory not found; JSON syntax error or unreadable file; filename numeric suffix does not match internal `acao_id`
- **Non-fatal** (skip + structured log): Pydantic validation failure on an individual file
- Every skipped file emits: filename, error detail, reason for skip
- Every load ends with a count log: e.g. `Loaded 1/1 IPMP action files. Skipped: 0`

**Acceptance criteria**

- [ ] `from ingestion import get_ipmp_store` works after this slice
- [ ] `store = get_ipmp_store(); assert store.acoes[1].titulo` passes against `data/ipmp/acao_01.json`
- [ ] Calling `get_ipmp_store()` twice returns the same cached object (singleton)
- [ ] Missing `data/ipmp/` directory raises a fatal exception immediately
- [ ] A file whose filename suffix does not match internal `acao_id` raises a fatal exception
- [ ] A file with a JSON syntax error raises a fatal exception
- [ ] A file with a Pydantic validation failure is skipped with a structured log entry; other files still load
- [ ] `ProdutoEsperado.id` is validated against `r"^\d+[a-z]?\$"`
- [ ] `ingestion.ipmp` is never imported directly by any other module — only `ingestion` (the package) is the import surface

**Blocked by**

#$issue1_num
"@

$issue2_num = ($issue2 -split '/')[-1]
Write-Host "Created Issue #$issue2_num: IPMP singleton"

# --- Issue 3: AcaoRioManual model review (HITL) ---
$issue3 = gh issue create `
  --repo $REPO `
  --title "Ingestion [HITL]: enumerate and review AcaoRioManual Pydantic model tree" `
  --label "hitl,module:ingestion" `
  --body @"
**What to build**

This is a human-in-the-loop review slice. The full Pydantic model tree for `AcaoRioManual` was intentionally deferred from the grill-me session because it requires enumerating all nested types directly from `data/rio_manual/acao_01.json`.

The agent must:
1. Read `data/rio_manual/acao_01.json` in full
2. Enumerate every field and nested object into a proposed Pydantic type-shape specification
3. Present the proposed model tree to the human for review before any code is written

Key structural constraints already decided (must be reflected in the model):
- `_meta.known_gaps: list[str]` — sole gap registry; Pydantic does not validate domain completeness
- `law_references[*].regex_variants: list[str]` — may be `[]` (intentional incompleteness, not a defect)
- `law_references[*].law_number: str` — may be `"UNKNOWN"` (intentional incompleteness, not a defect)
- `acao_id: int` — must match filename suffix (same fatal-error rule as IPMP)

**Acceptance criteria**

- [ ] Agent reads `data/rio_manual/acao_01.json` fully and enumerates all nested types
- [ ] Proposed model tree is presented to the human before any implementation code is written
- [ ] Human approves (or requests changes to) the proposed model tree
- [ ] Output of this slice is an approved type-shape specification — not working code

**Blocked by**

#$issue1_num
"@

$issue3_num = ($issue3 -split '/')[-1]
Write-Host "Created Issue #$issue3_num: AcaoRioManual model review (HITL)"

# --- Issue 4: Acronym singleton ---
$issue4 = gh issue create `
  --repo $REPO `
  --title "Ingestion: acronym singleton (get_acronym_store)" `
  --label "ready-for-agent,module:ingestion" `
  --body @"
**What to build**

Implement `ingestion/acronyms.py` end-to-end: load `data/acronyms/acronyms.json`, validate that all keys and values are non-empty strings, return a `dict[str, str]` singleton via `get_acronym_store()`. Export `get_acronym_store` from `__init__.py`.

The acronym store is a flat canonical dataset — all derived views (reverse mappings, contextual expansion) belong to retrieval/orchestration layers. Ingestion returns the flat structure exactly as represented in the source artifact.

Tolerant loading rules (same as IPMP, ADR-0010):
- **Fatal**: `data/acronyms/acronyms.json` not found; JSON syntax error
- **Non-fatal**: individual key/value pair fails validation (non-string or empty) — skip entry + structured log

**Acceptance criteria**

- [ ] `from ingestion import get_acronym_store` works after this slice
- [ ] `store = get_acronym_store(); assert isinstance(store, dict) and len(store) > 0` passes
- [ ] All keys and values in the returned dict are non-empty strings
- [ ] Calling `get_acronym_store()` twice returns the same cached object (singleton)
- [ ] Missing `data/acronyms/acronyms.json` raises a fatal exception immediately
- [ ] `ingestion.acronyms` is never imported directly by any other module

**Blocked by**

#$issue1_num
"@

$issue4_num = ($issue4 -split '/')[-1]
Write-Host "Created Issue #$issue4_num: Acronym singleton"

# --- Issue 5: Rio Manual singleton (blocked by HITL review) ---
$issue5 = gh issue create `
  --repo $REPO `
  --title "Ingestion: Rio Manual singleton (get_rio_manual_store)" `
  --label "ready-for-agent,module:ingestion" `
  --body @"
**What to build**

Implement `ingestion/rio_manual.py` end-to-end using the `AcaoRioManual` Pydantic model tree approved in the HITL review issue. Deliver glob-based file discovery, tolerant loader (ADR-0010), and the `get_rio_manual_store()` singleton. Export `get_rio_manual_store` from `__init__.py`.

The approved model tree from #$issue3_num is the source-of-truth for this implementation — do not deviate from it.

Tolerant loading rules (ADR-0010, same pattern as IPMP):
- **Fatal**: `data/rio_manual/` not found; JSON syntax error; filename suffix does not match internal `acao_id`
- **Non-fatal**: Pydantic validation failure on individual file — skip + structured log
- Empty `regex_variants` and `"UNKNOWN"` law numbers are valid states — must not trigger validation failure

**Acceptance criteria**

- [ ] `from ingestion import get_rio_manual_store` works after this slice
- [ ] `store = get_rio_manual_store(); assert store.acoes[1].acao_id == 1` passes against `data/rio_manual/acao_01.json`
- [ ] Calling `get_rio_manual_store()` twice returns the same cached object (singleton)
- [ ] `AcaoRioManual` with `regex_variants: []` and `law_number: "UNKNOWN"` loads without error
- [ ] Missing `data/rio_manual/` directory raises a fatal exception immediately
- [ ] Filename suffix mismatch raises a fatal exception
- [ ] Pydantic validation failure on an individual file is non-fatal — skip + log
- [ ] `ingestion.rio_manual` is never imported directly by any other module
- [ ] After all three singletons are implemented, `from ingestion import get_ipmp_store, get_rio_manual_store, get_acronym_store` is the complete public surface

**Blocked by**

#$issue3_num (HITL model review must be approved before implementation begins)
"@

$issue5_num = ($issue5 -split '/')[-1]
Write-Host "Created Issue #$issue5_num: Rio Manual singleton"

Write-Host ""
Write-Host "All 5 issues created. Summary:"
Write-Host "  #$issue1_num — Package scaffold (AFK)"
Write-Host "  #$issue2_num — IPMP singleton (AFK, blocked by #$issue1_num)"
Write-Host "  #$issue3_num — AcaoRioManual model review (HITL, blocked by #$issue1_num)"
Write-Host "  #$issue4_num — Acronym singleton (AFK, blocked by #$issue1_num)"
Write-Host "  #$issue5_num — Rio Manual singleton (AFK, blocked by #$issue3_num)"
