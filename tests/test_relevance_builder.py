"""Tests for evaluation.prompt.relevance_builder (ADR-0050 gate prompt)."""

from __future__ import annotations

from evaluation.prompt.relevance_builder import build_relevance_system_prompt, build_relevance_user_prompt


def test_system_prompt_without_concepts_contains_only_evidence_intent():
    prompt = build_relevance_system_prompt("evidência de X")
    assert "evidência de X" in prompt
    assert "Qualquer um dos elementos abaixo" not in prompt


def test_system_prompt_with_empty_concepts_list_matches_no_concepts():
    with_none = build_relevance_system_prompt("evidência de X", None)
    with_empty = build_relevance_system_prompt("evidência de X", [])
    assert with_none == with_empty
    assert "Qualquer um dos elementos abaixo" not in with_empty


def test_system_prompt_with_concepts_lists_each_as_a_bullet():
    prompt = build_relevance_system_prompt(
        "evidência de X", ["Matriz de riscos e alocação de responsabilidades", "Metas de interesse público"]
    )
    assert "evidência de X" in prompt
    assert "Qualquer um dos elementos abaixo também conta como evidência válida" in prompt
    assert "- Matriz de riscos e alocação de responsabilidades" in prompt
    assert "- Metas de interesse público" in prompt


def test_user_prompt_wraps_chunk_text():
    prompt = build_relevance_user_prompt("texto do trecho")
    assert prompt == "[Trecho a avaliar]\ntexto do trecho"
