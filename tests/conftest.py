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
