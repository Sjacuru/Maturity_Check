"""Tests for evaluation.parsing.relevance_response.parse_relevance_response (ADR-0050)."""

from evaluation.parsing.relevance_response import parse_relevance_response


def test_relevant_with_cleaned_text():
    raw = "Algum raciocínio.\n\nRELEVANT: yes\nCLEANED:\nTexto limpo aqui."
    result = parse_relevance_response(raw)
    assert result.relevant is True
    assert result.cleaned_text == "Texto limpo aqui."
    assert result.parse_failed is False


def test_not_relevant_has_no_cleaned_text():
    raw = "Raciocínio.\n\nRELEVANT: no"
    result = parse_relevance_response(raw)
    assert result.relevant is False
    assert result.cleaned_text is None
    assert result.parse_failed is False


def test_case_insensitive_sentinel():
    raw = "relevant: YES\ncleaned:\ntexto"
    result = parse_relevance_response(raw)
    assert result.relevant is True
    assert result.cleaned_text == "texto"


def test_missing_sentinel_is_parse_failed():
    raw = "Resposta sem sentinela nenhuma."
    result = parse_relevance_response(raw)
    assert result.parse_failed is True
    assert result.relevant is False


def test_relevant_yes_without_cleaned_block_is_parse_failed():
    raw = "RELEVANT: yes"
    result = parse_relevance_response(raw)
    assert result.relevant is True
    assert result.cleaned_text is None
    assert result.parse_failed is True


def test_multiline_cleaned_text_preserved():
    raw = "RELEVANT: yes\nCLEANED:\nLinha um.\nLinha dois.\nLinha três."
    result = parse_relevance_response(raw)
    assert result.cleaned_text == "Linha um.\nLinha dois.\nLinha três."
