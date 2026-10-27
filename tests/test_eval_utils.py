from __future__ import annotations

import pytest

from scripts.eval_utils import por_intencao, wilson_interval


def test_wilson_14_de_16_tem_intervalo_largo():
    baixo, alto = wilson_interval(14, 16)
    assert baixo == pytest.approx(0.640, abs=0.01)
    assert alto == pytest.approx(0.965, abs=0.01)


def test_wilson_extremos_ficam_entre_0_e_1():
    assert wilson_interval(0, 10)[0] == 0.0
    assert wilson_interval(10, 10)[1] == 1.0
    assert wilson_interval(0, 0) == (0.0, 0.0)


def test_por_intencao_agrupa_acertos_e_totais():
    linhas = [
        {"expected": "A", "passed": True},
        {"expected": "A", "passed": False},
        {"expected": "B", "passed": True},
    ]
    assert por_intencao(linhas) == {"A": (1, 2), "B": (1, 1)}
