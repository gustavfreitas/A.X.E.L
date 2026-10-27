"""Estatística da avaliação: intervalo de confiança e quebra por intenção."""

from __future__ import annotations

from collections import defaultdict
from math import sqrt


def wilson_interval(acertos: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confiança de Wilson (95%) para uma proporção.

    Com poucos casos (aqui, 16), a accuracy tem uma margem de erro grande, e o
    intervalo de Wilson é mais honesto que a aproximação normal nessa faixa.
    """
    if total == 0:
        return 0.0, 0.0
    p = acertos / total
    denominador = 1 + z**2 / total
    centro = (p + z**2 / (2 * total)) / denominador
    margem = z * sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denominador
    return max(0.0, centro - margem), min(1.0, centro + margem)


def por_intencao(linhas: list[dict]) -> dict[str, tuple[int, int]]:
    """{intenção esperada: (acertos, total)}."""
    contagem: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for linha in linhas:
        contagem[linha["expected"]][1] += 1
        contagem[linha["expected"]][0] += int(linha["passed"])
    return {k: (v[0], v[1]) for k, v in sorted(contagem.items())}
