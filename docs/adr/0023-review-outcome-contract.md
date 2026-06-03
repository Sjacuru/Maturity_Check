# Review Outcome Contract — accept/override with final score persistence

The Auditor review of an EvaluationResult always produces a Review Outcome carrying an authoritative Final Score in {0, 1, 3}. The minimum action set is: accept the proposed_score as-is, or override to any of {0, 1, 3}. Both proposed_score and final_score are persisted, along with an is_override boolean and a mandatory justification note when overriding. All original EvaluationResult status flags (uncertainty_flag, parse_failed, no_evidence_found) are preserved unchanged in the stored record regardless of the Auditor's decision. For special states (no_evidence_found, parse_failed), manual score assignment is permitted; the Review Outcome records that final_score was produced through Auditor intervention. Evidence references (pointers to chunks already in retrieved_chunks) are included as an optional field on overrides — implementation is in scope only if it requires no new retrieval, chunk discovery, or retrieval-repair workflow.

## Considered Options

- **Accept/reject only:** The Auditor marks accepted or rejected, with no direct score assignment on rejection. Rejected: leaves the score unresolved when the Auditor's judgment differs from the LLM's proposal, requiring a second pass or out-of-band resolution.
- **Full evidence correction:** Auditor selects new evidence chunks not in retrieved_chunks. Rejected: introduces re-retrieval and evidence-repair workflows out of scope for Phase 1.
- **Evidence references scoped to retrieved_chunks:** Auditor can optionally reference existing chunks to support an override. Accepted with Phase 1 condition: in scope only if trivially implementable; otherwise deferred.

## Consequences

- Every Review Outcome carries a Final Score — no open/pending evaluation state after review.
- proposed_score and final_score coexist in storage — divergences are auditable without referring to LLM logs.
- is_override + justification create a human audit trail that the academic reviewer can inspect.
- Preserving all three status flags even after override means the LLM's original assessment is never silently rewritten by the Auditor.
- Manual score assignment on no_evidence_found/parse_failed states allows the Auditor to close evaluations that the system cannot resolve automatically.
