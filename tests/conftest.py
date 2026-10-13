"""
Pytest root configuration.

Sets up environment-level configuration that cannot be expressed in pytest.ini.
"""
import os

import pytest


def pytest_configure(config):
    cmd = os.environ.get("TESSERACT_CMD")
    if cmd:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = cmd
        except ImportError:
            pass


@pytest.fixture(autouse=True)
def _empty_retrieval_profile_store(monkeypatch):
    """Patch the retrieval profile store singleton to empty for every test.

    Without this, tests that exercise the full cascade (retrieve_for_acao /
    AssessmentService) fall through to the vector fallback when the real
    acao_01.json profile terms don't match generic test chunk text, which
    triggers a HuggingFace model download and fails under a corporate proxy.

    Tests that need a specific profile (e.g. test_retrieval_profile.py) call
    monkeypatch.setattr(...) themselves after this fixture runs, overriding it.
    Tests that need _load() to execute (store-loading tests) also set
    _store=None themselves, which forces a fresh load despite this fixture.
    """
    import ingestion.retrieval_profile as _rp
    from ingestion.retrieval_profile import RetrievalProfileStore

    monkeypatch.setattr(_rp, "_store", RetrievalProfileStore(acoes={}))


@pytest.fixture(autouse=True)
def _stub_vector_search(monkeypatch):
    """Patch search_vector to return [] for every test.

    The vector fallback (LanceDB + sentence-transformers) makes a network
    request to HuggingFace on startup to check for model updates.  Under the
    corporate proxy, that request fails with an SSL error when pip-system-certs
    cannot inject the truststore.  Tests that specifically exercise vector
    retrieval patch this themselves; all other tests should not trigger the
    network call.
    """
    from retrieval.query import vector as _vec

    monkeypatch.setattr(_vec, "search_vector", lambda *args, **kwargs: [])


@pytest.fixture(autouse=True)
def _stub_gate_llm_client(monkeypatch):
    """Configure the relevance gate (ADR-0050) with a client object for every test.

    AssessmentService.run_assessment() calls get_gate_llm_client() unconditionally
    and raises RuntimeError if it was never configured. Constructing an
    OllamaClient does not itself make a network call (only .complete() does),
    and the empty-profile fixture above means most tests never reach a product
    with an evidence_intent to gate against, so .complete() is rarely invoked.
    Tests that specifically exercise select_evidence() with a real profile
    patch evaluation._config._gate_client directly with a stub.
    """
    import evaluation._config as _eval_cfg
    from evaluation.llm.ollama import OllamaClient

    monkeypatch.setattr(_eval_cfg, "_gate_client", OllamaClient(model="mistral"))


@pytest.fixture(autouse=True)
def _stub_document_genres_and_neighbors(monkeypatch):
    """No genre map and no neighbours unless a test asks for them (ADR-0074).

    select_evidence() reads the canonical document index once per Ação and,
    with neighbour expansion on by default, fetches the neighbours of every
    accepted chunk -- both from the retrieval DB, which most unit tests never
    configure. The empty map means "no chunk is known to be instrument text",
    so nothing is filtered; tests of the filter pass their own map, and
    tests/test_genre_index.py builds the real index on a real DB. Tests of the
    expansion patch fetch_neighbor_chunks themselves, after this fixture.
    """
    import evaluation.evidence_selection as _es

    monkeypatch.setattr(_es, "_chunk_genres", lambda process_number: {})
    monkeypatch.setattr(_es, "fetch_neighbor_chunks", lambda *args, **kwargs: (None, None))
