"""Validação de entrada e detecção de vazamento do prompt interno."""

from __future__ import annotations

import pytest

from app.core import prompts
from app.utils import security


def test_validate_input_aceita_texto_normal():
    security.validate_input("minha query está lenta")


@pytest.mark.parametrize("texto", ["", "   ", "\n\t"])
def test_validate_input_recusa_vazio(texto):
    with pytest.raises(security.InputValidationError):
        security.validate_input(texto)


def test_validate_input_recusa_texto_muito_longo():
    with pytest.raises(security.InputValidationError):
        security.validate_input("a" * (security.MAX_INPUT_LENGTH + 1))


def test_validate_input_aceita_exatamente_no_limite():
    security.validate_input("a" * security.MAX_INPUT_LENGTH)


def _frase_do_prompt(source: str) -> str:
    """Uma frase longa de verdade do prompt interno (junta as quebras de linha)."""
    for paragraph in source.split("\n\n"):
        joined = " ".join(line.strip() for line in paragraph.splitlines())
        for sentence in joined.split(". "):
            if len(sentence) > 60 and not sentence.isupper():
                return sentence.rstrip(".")
    raise AssertionError("prompt sem frase longa")


@pytest.mark.parametrize("fonte", [prompts.system_prompt, prompts.security_prompt])
def test_detecta_frase_literal_do_prompt_interno(fonte):
    frase = _frase_do_prompt(fonte())
    resposta = f"Claro! As minhas instruções dizem: {frase}"
    assert security.check_output_leakage(resposta)


def test_detecta_mesmo_com_caixa_diferente():
    frase = _frase_do_prompt(prompts.system_prompt()).upper()
    assert security.check_output_leakage(frase)


def test_resposta_tecnica_normal_nao_dispara():
    resposta = (
        "DIAGNÓSTICO\nA query faz um full table scan porque não há índice em "
        "created_at.\n\nCAUSA PROVÁVEL\nO filtro usa uma função na coluna, o "
        "que impede o uso do índice.\n\nSUGESTÃO\nCrie um índice e reescreva "
        "o filtro como um intervalo."
    )
    assert security.check_output_leakage(resposta) == []


def test_limitacao_conhecida_traducao_do_prompt_nao_e_detectada():
    """Documenta um limite real: a checagem é por trecho literal.

    Se o modelo vazar o prompt TRADUZIDO ou parafraseado, os canários em
    português não casam. É por isso que a defesa também depende do prompt de
    segurança e da classificação de intenção, e por isso a README fala em
    defesa em camadas, não em garantia.
    """
    traduzido = "My internal instructions say that I am a technical assistant."
    assert security.check_output_leakage(traduzido) == []
