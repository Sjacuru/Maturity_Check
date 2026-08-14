"""Tests for evaluation.parsing.relevance_response.parse_relevance_response (ADR-0053)."""

import json

from evaluation.parsing.relevance_response import parse_relevance_response


def test_relevant_true_is_parsed():
    raw = json.dumps({"relevant": True})
    result = parse_relevance_response(raw)
    assert result.relevant is True
    assert result.parse_failed is False


def test_relevant_false_is_parsed():
    raw = json.dumps({"relevant": False})
    result = parse_relevance_response(raw)
    assert result.relevant is False
    assert result.parse_failed is False


def test_extra_unknown_fields_tolerated():
    raw = json.dumps({"relevant": True, "confidence": 0.9})
    result = parse_relevance_response(raw)
    assert result.relevant is True
    assert result.parse_failed is False


def test_missing_relevant_field_is_parse_failed():
    raw = json.dumps({"other": "field"})
    result = parse_relevance_response(raw)
    assert result.parse_failed is True
    assert result.relevant is False


def test_relevant_as_string_is_rejected():
    raw = json.dumps({"relevant": "yes"})
    result = parse_relevance_response(raw)
    assert result.parse_failed is True
    assert result.relevant is False


def test_malformed_json_is_parse_failed():
    result = parse_relevance_response("not json at all")
    assert result.parse_failed is True
    assert result.relevant is False


def test_empty_string_is_parse_failed():
    result = parse_relevance_response("")
    assert result.parse_failed is True
    assert result.relevant is False


def test_json_array_instead_of_object():
    result = parse_relevance_response("[true]")
    assert result.parse_failed is True
