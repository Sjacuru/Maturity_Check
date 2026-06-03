# Module 5 configures independently; main.py owns startup sequencing

## Independent module configuration

Module 5 stores its own `db_path` at module level via `assessment.configure(db_path)`, independently of Module 3's `retrieval.configure(db_path)`. Both modules are called from `main.py` with the same physical path. This is consistent with the pattern established in Modules 3 and 4.

Cross-module configuration access — e.g., `assessment` importing and reading `retrieval._config.get_db_path()` — is prohibited. The physical database file is shared (ADR-0024); module configuration ownership is not.

The distinction:
- **Shared physical database:** one SQLite file; both modules read and write it.
- **Independent configuration ownership:** each module owns its own module-level config; no module reads another module's private `_config` to derive its own.

## Startup sequencing in main.py

`main.py` owns runtime bootstrap order:

```python
from retrieval import configure as configure_retrieval, init_db as retrieval_init_db
from assessment import configure as configure_assessment, init_db as assessment_init_db, create_app

db_path = "data/app.db"
configure_retrieval(db_path)
retrieval_init_db(db_path)

configure_assessment(db_path)
assessment_init_db(db_path)

configure_llm(provider=..., model=...)

app = create_app()
```

Responsibilities:
- `main.py`: runtime bootstrap sequencing (configure → init_db → create_app).
- `create_app()`: FastAPI application construction only.
- `init_db()` functions: schema initialisation for their own tables only.

`create_app()` must not call `init_db()` internally — that would hide a startup side effect inside a function whose name implies only application construction. Tests that call `create_app()` without a database would behave differently from production.

## Consequences

- Adding a new module that uses the shared DB requires adding one more `configure()` + `init_db()` line to `main.py` — no changes to existing modules.
- `main.py` is the single place to audit startup order and configuration values.
- Module packages remain importable as libraries without triggering database initialisation side effects.
