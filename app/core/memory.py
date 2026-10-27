from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from app.config import settings


@dataclass
class Turn:
    user: str
    intent: str
    response: str


def format_context(turns: list[Turn], max_chars: int) -> str:
    """Monta o contexto de histórico respeitando o orçamento de caracteres.

    Percorre do turno mais recente para o mais antigo e para de incluir assim
    que o orçamento estoura (sempre mantém pelo menos o turno mais recente).
    Compartilhada pelos dois backends de memória para não duplicar a regra.
    """
    selected: list[Turn] = []
    used = 0
    for turn in reversed(turns):
        turn_text = f"Usuário: {turn.user}\nAXEL ({turn.intent}): {turn.response}"
        if used + len(turn_text) > max_chars and selected:
            break
        selected.append(turn)
        used += len(turn_text)
    selected.reverse()

    lines = []
    for turn in selected:
        lines.append(f"Usuário: {turn.user}")
        lines.append(f"AXEL ({turn.intent}): {turn.response}")
    return "\n".join(lines)


@dataclass
class SessionMemory:
    """Histórico curto em memória — reseta a cada execução do CLI por padrão
    (ver core/persistent_memory.py para a alternativa com SQLite).

    Corta por DOIS critérios, não só um: número de turnos (max_turns) E
    tamanho total em caracteres (max_chars). Só limitar por turno não basta —
    um turno com diagnóstico longo pode sozinho estourar o contexto útil de
    um modelo pequeno como qwen2.5:1.5b, que degrada mais rápido com prompts
    grandes do que um modelo de fronteira.
    """

    max_turns: int = settings.max_history_turns
    max_chars: int = settings.max_history_chars
    _turns: deque[Turn] = field(default_factory=deque)

    def __post_init__(self) -> None:
        self._turns = deque(maxlen=self.max_turns)

    def add(self, user: str, intent: str, response: str) -> None:
        self._turns.append(Turn(user=user, intent=intent, response=response))

    def as_context(self) -> str:
        if not self._turns:
            return ""
        return format_context(list(self._turns), self.max_chars)

    def clear(self) -> None:
        self._turns.clear()

    def history(self) -> list[Turn]:
        return list(self._turns)


def get_memory() -> SessionMemory:
    """Factory: escolhe o backend de memória com base em settings.memory_backend.

    Mesmo padrão do core/llm.py::get_provider — ponto de extensão único, não
    espalhado pelo código. Import local evita ciclo (persistent_memory
    importa Turn daqui).
    """
    if settings.memory_backend == "sqlite":
        from app.core.persistent_memory import PersistentSessionMemory

        return PersistentSessionMemory()  # type: ignore[return-value]
    return SessionMemory()
