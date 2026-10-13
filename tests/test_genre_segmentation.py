"""Where each document starts and ends inside a file (ADR-0074)."""

from __future__ import annotations

from retrieval.genre.classifier import INSTRUMENT, OTHER
from retrieval.genre.segmentation import page_title, pages_by_file, segment_file

PROSA = " ".join(["texto corrido do documento com frases comuns e sem marcas de titulo"] * 20)


def _segments(*pages: str):
    rows = [("f.pdf", i + 1, 0, text) for i, text in enumerate(pages)]
    return segment_file(pages_by_file(rows)["f.pdf"])


def _shape(segments):
    return [(s.page_start, s.page_end, s.start_reason, s.doc_type, s.genre) for s in segments]


def test_a_title_line_opens_a_document():
    segments = _segments(
        "ESTUDO DE VIABILIDADE ECONÔMICA\n" + PROSA,
        PROSA,
        "MINUTA DE CONTRATO DE CONCESSÃO\n" + PROSA,
    )
    assert _shape(segments) == [
        (1, 2, "title", "estudo", OTHER),
        (3, 3, "title", "minuta", INSTRUMENT),
    ]


def test_a_continuing_printed_page_number_never_opens_a_document():
    segments = _segments(
        "1\nMINUTA DE CONTRATO\n" + PROSA,
        "2\nTERMO DE REFERÊNCIA\n" + PROSA,
    )
    assert _shape(segments) == [(1, 2, "title", "minuta", INSTRUMENT)]


def test_a_title_equal_to_the_current_one_is_a_running_header():
    segments = _segments("MATRIZ DE RISCOS\n" + PROSA, "MATRIZ DE RISCOS\n" + PROSA)
    assert _shape(segments) == [(1, 2, "title", "matriz_riscos", INSTRUMENT)]


def test_a_cover_followed_by_a_table_of_contents_opens_a_document():
    segments = _segments(
        "ANEXO II - TERMO DE REFERÊNCIA\nLOTE 1",
        "SUMÁRIO\n1. OBJETO\n" + PROSA,
        "3\n" + PROSA,
    )
    assert _shape(segments) == [(1, 3, "cover", "termo_referencia", INSTRUMENT)]


def test_the_first_page_after_a_cover_with_the_same_type_is_the_same_document():
    segments = _segments(
        "ANEXO II - TERMO DE REFERÊNCIA\nLOTE 2",
        "TERMO DE REFERÊNCIA DO LOTE 2\nSUMÁRIO\n" + PROSA,
    )
    assert _shape(segments) == [(1, 2, "cover", "termo_referencia", INSTRUMENT)]


def test_an_untyped_cover_takes_the_title_of_the_next_page():
    segments = _segments(
        "PREFEITURA MUNICIPAL\nLOTE 3\nVOLUME I",
        "2\nMATRIZ DE RISCOS\n" + PROSA,
    )
    assert _shape(segments) == [(1, 2, "cover", "matriz_riscos", INSTRUMENT)]


def test_the_printed_numbering_restarting_at_1_opens_a_document():
    segments = _segments(
        "1\nRELATÓRIO TÉCNICO\n" + PROSA,
        "2\n" + PROSA,
        "3\n" + PROSA,
        "1\n" + PROSA,
    )
    assert _shape(segments) == [
        (1, 3, "title", "relatorio", OTHER),
        (4, 4, "restart", None, None),
    ]


def test_a_mixed_case_title_needs_an_identifier():
    assert page_title(["Parecer nº 123/2024", PROSA], cover=False)[:2] == ("parecer", OTHER)
    assert page_title(["Parecer favorável à contratação", PROSA], cover=False) is None


def test_a_sentence_is_not_a_title():
    """A line ending in punctuation is running prose ("...nos termos do TERMO
    DE REFERÊNCIA."), not a heading."""
    assert page_title(["TERMO DE REFERÊNCIA.", PROSA], cover=False) is None


def test_the_letterhead_is_skipped_before_the_title():
    lines = ["PREFEITURA MUNICIPAL DE EXEMPLO", "SECRETARIA MUNICIPAL DE OBRAS", "EDITAL DE LICITAÇÃO"]
    assert page_title(lines + [PROSA], cover=False)[:2] == ("edital", INSTRUMENT)


def test_a_generic_heading_leaves_the_genre_to_the_chunk_labels():
    """DECLARAÇÃO, CRONOGRAMA, PLANO... are untyped on purpose: a declaration of
    the ordenador de despesas must not be filtered because a contract annex may
    carry the same heading."""
    segments = _segments("DECLARAÇÃO\n" + PROSA)
    assert segments[0].doc_type is None and segments[0].genre is None


def test_a_study_is_not_mistaken_for_its_prefix():
    """ESTUDO TÉCNICO PRELIMINAR is the ETP, matched before the bare ESTUDO."""
    segments = _segments("ESTUDO TÉCNICO PRELIMINAR\n" + PROSA)
    assert (segments[0].doc_type, segments[0].genre) == ("etp", OTHER)
