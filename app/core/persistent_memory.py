"""
Memória persistente (opt-in) via SQLite.

Implementa a mesma interface pública de SessionMemory (add, as_context,
clear, history) de propósito: o resto do código (Assistant) não sabe nem
precisa saber qual backend está por trás — é só trocar qual classe o
factory em core/memory.py::get_memory retorna.

Trade-off declarado, não escondido: persistir em disco significa guardar
trechos de código e mensagens do usuário em texto puro no arquivo .db.
Por isso isso é OPT-IN (AXEL_MEMORY_BACKEND=sqlite), não o padrão — o
padrão continua sendo RAM, que não deixa rastro em disco.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass

from app.config import settings
from app.core.memory import Turn, format_context


@dataclass
class PersistentSessionMemory:
    db_path: str = settings.history_db_path
    max_turns: int = settings.max_history_turns
    max_chars: int = settings.max_history_chars

    def __post_init__(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def add(self, user: str, intent: str, response: str) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO turns (user_input, intent, response) VALUES (?, ?, ?)",
                (user, intent, response),
            )
            conn.commit()

    def _recent_turns(self) -> list[Turn]:
        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT user_input, intent, response FROM turns "
                "ORDER BY id DESC LIMIT ?",
                (self.max_turns,),
            ).fetchall()
        # veio mais recente -> mais antigo; devolve na ordem cronológica normal
        return [Turn(user=r[0], intent=r[1], response=r[2]) for r in reversed(rows)]

    def as_context(self) -> str:
        turns = self._recent_turns()
        if not turns:
            return ""
        return format_context(turns, self.max_chars)

    def clear(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("DELETE FROM turns")
            conn.commit()

    def history(self) -> list[Turn]:
        return self._recent_turns()
