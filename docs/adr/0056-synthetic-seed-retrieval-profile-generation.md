# Synthetic seed retrieval-profile generation, scoped to Query Terms only

**Status:** accepted

Scaling retrieval profiles from Ação 1 (hand-curated against a real case) to the remaining 45
requires either repeating that manual, per-case process 45 times, or a way to seed a profile
before any real document exists. `docs/prompts/04_retrieval-profile-synthesis.md` is the latter:
an LLM-reasoning-only process (no code, no `.claude/skills/`) that produces a
`profile_maturity: "seed"` profile from `data/ipmp/acao_NN.json` and general domain knowledge —
never from a real case document.

## Why not fully-automated generation, and why this doesn't violate DAN-0002

DAN-0002 (closed by ADR-0047+0048) explicitly rejected "fully automated LLM-assisted query
generation without real-document grounding," reasoning that an LLM reading only IPMP text would
reproduce governance-framing language at a different level of indirection. This process avoids
that failure mode by construction, not by exception: every term it adds under
`provenance: "synthetic"` defaults to `status: "experimental"`, which `build_query_from_terms`
already excludes from the active BM25 query — the same mechanism already protecting Ação 1's own
experimental terms. A seed profile is a hypothesis register, not a certified retrieval
configuration — DAN-0002's target (untrusted LLM vocabulary silently driving retrieval) cannot
occur, because nothing this process writes is active by default.

## Why `.claude/skills/` was rejected

`.claude/` is gitignored (root `.gitignore`). A skill placed there would never be committed,
never reach GitHub, and would vanish if the machine changed — directly contradicting the
project's reproducibility requirement (the professor's core constraint). `docs/prompts/04_...md`
follows the convention already established by `01_grill-me.md` / `02_To-PRD.md` /
`03_To_issues.md` / `05_retrieval-profile-validation.md`: a plain, versioned markdown procedure
invoked by pointing Claude at the file, not a slash-command-registered skill.

## Scope limits (deliberate)

- **Never reads a real case document.** Real-document grounding (Stage B) stays entirely in
  `05_retrieval-profile-validation.md`.
- **Only Layer C (Query Terms) gets the new provenance/sector machinery.** Layers B
  (`retrieval_signal_concepts`) and D (`evidence_logic_patterns` / `negative_evidence_patterns`)
  are generated at the same Stage-A quality but get no per-item provenance tracking — retrofitting
  it would require converting Ação 1's existing plain-string lists into structured objects, a
  breaking migration disproportionate to layers that don't drive retrieval (CONTEXT.md: "Layers
  A, B, and D are never FTS5 inputs").
- **Sector vocabulary comes from a versioned reference list** (`data/sector_taxonomy.json`, 15
  entries — 7 from the domain expert, 8 from consolidated LLM knowledge, both tagged by
  `source`), never invented ad hoc — keeps `sector_hint` values comparable across Ações and
  prevents scope creep into arbitrary vocabulary generation.
- **Not every product gets sector terms.** The process explicitly judges, per Expected Product,
  whether cross-sector variation is even plausible before adding sector-tagged terms — avoids
  padding procedural/structural products with irrelevant vocabulary.
- **Additive merge only.** Re-running against an Ação with an existing profile never touches an
  item whose `status` is `"validated"`/`"deprecated"`; it only adds new `"experimental"`
  candidates. `profile_maturity` is never advanced by this process — only a real-document
  population session does that.

## Consequences

- `PhraseQueryTerm` / `NearQueryTerm` (`src/ingestion/retrieval_profile.py`): `provenance` gains a
  third value, `"synthetic"`; both gain an optional `sector_hint: str | None` field.
- New reference artifact `data/sector_taxonomy.json`, exempted in `.gitignore`.
- New cross-Ação overlap convention: a Query Term/Concept judged genuinely pertinent to more than
  one Ação carries `shared_with_acao` plus a short justification, decided once at generation time
  — not a runtime chunk-tracking mechanism.
- CONTEXT.md gained: Provenance (promoted to its own entry, was previously only referenced inline),
  Sector Taxonomy.
- `05_retrieval-profile-validation.md` updated to document `synthetic` as a third provenance value
  and to point to `04` when no profile exists yet for the target Ação.
