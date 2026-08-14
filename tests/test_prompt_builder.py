from retrieval import RetrievedChunk

from evaluation.prompt.builder import build_system_prompt, build_user_prompt


def _chunk(**kwargs) -> RetrievedChunk:
    defaults = dict(
        process_number="0023.001234/2024-01",
        filename="EVTEA.pdf",
        page_number=1,
        chunk_index=0,
        char_offset=0,
        page_total=10,
        ocr_used=False,
        source_type="text",
        text="Texto de exemplo.",
        cascade_step="bm25",
        expected_product_ids=["1a"],
        bm25_score=3.5,
        rank=1,
    )
    return RetrievedChunk(**{**defaults, **kwargs})


# --- System prompt ---

def test_system_prompt_contains_descricao_acao():
    prompt = build_system_prompt(1)
    assert "Descrever o motivo pelo qual o projeto é necessário" in prompt


def test_system_prompt_contains_o_que_esperar():
    prompt = build_system_prompt(1)
    assert "o_que_esperar" not in prompt  # field name never exposed
    assert "Descrição clara e interconectada" in prompt


def test_system_prompt_contains_example_labels():
    prompt = build_system_prompt(1)
    assert "Atendido" in prompt
    assert "Parcialmente Atendido" in prompt
    assert "Não Atendido" in prompt


def test_system_prompt_contains_illustrative_framing():
    prompt = build_system_prompt(1)
    assert "ilustram os níveis de pontuação" in prompt
    assert "independente do setor ou domínio" in prompt


def test_system_prompt_contains_json_field_names():
    prompt = build_system_prompt(1)
    assert '"reasoning"' in prompt
    assert '"score"' in prompt
    assert '"uncertainty"' in prompt


def test_system_prompt_contains_uncertainty_criterion():
    prompt = build_system_prompt(1)
    assert '"uncertainty": true' in prompt


def test_system_prompt_contains_produtos_esperados():
    prompt = build_system_prompt(1)
    assert "1a" in prompt
    assert "1b" in prompt
    assert "1c" in prompt
    assert "1d" in prompt


def test_system_prompt_deterministic():
    assert build_system_prompt(1) == build_system_prompt(1)


# --- User prompt ordering ---

def test_user_prompt_filename_match_before_bm25():
    fm = _chunk(cascade_step="filename_match", filename="A.pdf", page_number=1, bm25_score=None, rank=None, expected_product_ids=[], text="filename text here")
    bm = _chunk(cascade_step="bm25", filename="A.pdf", page_number=1, bm25_score=5.0, rank=1, text="bm25 text here")
    prompt = build_user_prompt([bm, fm])
    assert prompt.index("filename text here") < prompt.index("bm25 text here")


def test_user_prompt_bm25_score_desc_order():
    high = _chunk(cascade_step="bm25", bm25_score=9.0, rank=1, chunk_index=0, text="high score")
    low = _chunk(cascade_step="bm25", bm25_score=2.0, rank=2, chunk_index=1, text="low score")
    prompt = build_user_prompt([low, high])
    assert prompt.index("high score") < prompt.index("low score")


def test_user_prompt_non_bm25_filename_asc():
    b_chunk = _chunk(cascade_step="filename_match", filename="B.pdf", bm25_score=None, rank=None, expected_product_ids=[], text="B file")
    a_chunk = _chunk(cascade_step="filename_match", filename="A.pdf", bm25_score=None, rank=None, expected_product_ids=[], text="A file")
    prompt = build_user_prompt([b_chunk, a_chunk])
    assert prompt.index("A file") < prompt.index("B file")


def test_user_prompt_deterministic():
    chunks = [
        _chunk(cascade_step="bm25", bm25_score=5.0, rank=1, chunk_index=0, text="first"),
        _chunk(cascade_step="bm25", bm25_score=3.0, rank=2, chunk_index=1, text="second"),
    ]
    assert build_user_prompt(chunks) == build_user_prompt(chunks)


def test_user_prompt_contains_filename_and_page():
    chunk = _chunk(filename="ContratoPPP.pdf", page_number=7)
    prompt = build_user_prompt([chunk])
    assert "ContratoPPP.pdf" in prompt
    assert "7" in prompt


def test_user_prompt_contains_summary_line():
    chunk = _chunk(text="abc")
    prompt = build_user_prompt([chunk])
    assert "1 trecho" in prompt or "trecho(s)" in prompt


def test_user_prompt_cascade_order_all_steps():
    # Chunks without expected_product_id (document-focused steps) are grouped
    # under "Documentos Focais" and appear before per-product blocks.
    # Within that section, cascade priority is filename < variant < regex.
    # bm25 chunk has expected_product_id="1a" so it appears in its product block,
    # always after the ungrouped section — regardless of cascade priority.
    regex_c = _chunk(cascade_step="regex", filename="A.pdf", bm25_score=None, rank=None, expected_product_ids=[], text="regex text")
    bm_c = _chunk(cascade_step="bm25", bm25_score=8.0, rank=1, text="bm25 text")
    variant_c = _chunk(cascade_step="variant_match", filename="A.pdf", bm25_score=None, rank=None, expected_product_ids=[], text="variant text")
    filename_c = _chunk(cascade_step="filename_match", filename="A.pdf", bm25_score=None, rank=None, expected_product_ids=[], text="filename text")
    prompt = build_user_prompt([regex_c, bm_c, variant_c, filename_c])
    positions = {
        "filename": prompt.index("filename text"),
        "variant": prompt.index("variant text"),
        "bm25": prompt.index("bm25 text"),
        "regex": prompt.index("regex text"),
    }
    # Within ungrouped section: filename < variant < regex (cascade priority)
    assert positions["filename"] < positions["variant"] < positions["regex"]
    # Product block always after ungrouped section
    assert positions["regex"] < positions["bm25"]
