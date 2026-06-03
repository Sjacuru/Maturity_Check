# Shared SQLite database with schema-level table ownership

All modules that require persistent storage use a single SQLite database file in Phase 1. Table ownership is enforced at the schema level, not the file level.

Ownership boundaries:

- **Retrieval module:** `chunks`, `chunks_fts` (and any future retrieval-layer tables)
- **Module 5 (assessment/review):** `evaluation_results`, `review_outcomes` (and any future assessment-layer tables)

Constraints:
- Retrieval migrations must not read, write, or alter Module 5-owned tables.
- Module 5 migrations must not read, write, or alter retrieval-owned tables.
- Each module initialises its own tables via its own `init_db()` / DDL entry point.

## Considered Options

- **Separate SQLite file for Module 5:** Keeps rebuildable retrieval data physically separate from durable Auditor decisions. Rejected: current requirements do not justify the operational overhead of a second file. The distinction between rebuildable and durable data is a real concern, but it is enforced by table-ownership rules and migration discipline — not by a second database.

## Consequences

- Single file to back up, restore, and pass around in Phase 1 development.
- Schema-level ownership prevents accidental cross-module coupling during migrations.
- If future requirements emerge (independent backup policies, index rebuilding without touching review history, scaling), physical separation can be introduced at that point without changing module APIs — the ownership boundary is already encoded in the schema.
