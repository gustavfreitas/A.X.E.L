"""Memória de sessão (RAM) e persistente (SQLite)."""

from __future__ import annotations

from app.core.memory import SessionMemory, format_context
from app.core.persistent_memory import PersistentSessionMemory


def test_ram_limita_por_numero_de_turnos():
    memoria = SessionMemory(max_turns=2, max_chars=10_000)
    for i in range(4):
        memoria.add(f"pergunta {i}", "CODE_DEBUG", f"resposta {i}")
    assert [t.user for t in memoria.history()] == ["pergunta 2", "pergunta 3"]


def test_contexto_vazio_quando_nao_ha_historico():
    assert SessionMemory().as_context() == ""


def test_contexto_respeita_orcamento_de_caracteres_e_prioriza_o_recente():
    memoria = SessionMemory(max_turns=10, max_chars=120)
    memoria.add("a" * 60, "CODE_DEBUG", "b" * 60)
    memoria.add("ultima pergunta", "CODE_DEBUG", "ultima resposta")
    contexto = memoria.as_context()
    assert "ultima pergunta" in contexto
    assert "a" * 60 not in contexto


def test_turno_mais_recente_entra_mesmo_acima_do_orcamento():
    memoria = SessionMemory(max_turns=10, max_chars=10)
    memoria.add("x" * 200, "CODE_DEBUG", "y" * 200)
    assert "x" * 200 in memoria.as_context()


def test_clear_apaga_tudo():
    memoria = SessionMemory()
    memoria.add("p", "CODE_DEBUG", "r")
    memoria.clear()
    assert memoria.history() == []


def test_sqlite_persiste_entre_instancias(tmp_path):
    caminho = str(tmp_path / "h.db")
    PersistentSessionMemory(db_path=caminho).add("p1", "SQL_OPTIMIZATION", "r1")
    reaberta = PersistentSessionMemory(db_path=caminho)
    assert [t.user for t in reaberta.history()] == ["p1"]


def test_sqlite_e_ram_geram_o_mesmo_contexto(tmp_path):
    ram = SessionMemory(max_turns=6, max_chars=3000)
    sql = PersistentSessionMemory(
        db_path=str(tmp_path / "h.db"), max_turns=6, max_chars=3000
    )
    for i in range(3):
        ram.add(f"p{i}", "CODE_DEBUG", f"r{i}")
        sql.add(f"p{i}", "CODE_DEBUG", f"r{i}")
    assert ram.as_context() == sql.as_context()


def test_sqlite_clear(tmp_path):
    memoria = PersistentSessionMemory(db_path=str(tmp_path / "h.db"))
    memoria.add("p", "CODE_DEBUG", "r")
    memoria.clear()
    assert memoria.history() == []


def test_format_context_ordem_cronologica():
    ram = SessionMemory()
    ram.add("primeiro", "CODE_DEBUG", "r1")
    ram.add("segundo", "CODE_DEBUG", "r2")
    texto = format_context(ram.history(), 3000)
    assert texto.index("primeiro") < texto.index("segundo")
