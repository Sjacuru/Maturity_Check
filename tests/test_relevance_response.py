"""Tests for evaluation.parsing.relevance_response.parse_relevance_response (ADR-0050)."""

from evaluation.parsing.relevance_response import parse_relevance_response


def test_relevant_yes_is_parsed():
    raw = "Algum raciocínio.\n\nRELEVANT: yes"
    result = parse_relevance_response(raw)
    assert result.relevant is True
    assert result.parse_failed is False


def test_relevant_no_is_parsed():
    raw = "Raciocínio.\n\nRELEVANT: no"
    result = parse_relevance_response(raw)
    assert result.relevant is False
    assert result.parse_failed is False


def test_case_insensitive_sentinel():
    raw = "relevant: YES"
    result = parse_relevance_response(raw)
    assert result.relevant is True
    assert result.parse_failed is False


def test_missing_sentinel_is_parse_failed():
    raw = "Resposta sem sentinela nenhuma."
    result = parse_relevance_response(raw)
    assert result.parse_failed is True
    assert result.relevant is False


def test_portuguese_affirmative_tolerated():
    raw = "RELEVANT: sim"
    result = parse_relevance_response(raw)
    assert result.relevant is True
    assert result.parse_failed is False


def test_portuguese_negative_tolerated():
    raw = "RELEVANT: não"
    result = parse_relevance_response(raw)
    assert result.relevant is False
    assert result.parse_failed is False


def test_leading_whitespace_tolerated():
    raw = " RELEVANT: yes"
    result = parse_relevance_response(raw)
    assert result.relevant is True
    assert result.parse_failed is False
