from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from app.config import settings


@dataclass
class Turn:
    user: str
    intent: str
    response: str


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
        # Monta de trás pra frente (mais recente primeiro) e para de incluir
        # turnos antigos assim que o orçamento de caracteres estoura — prioriza
        # contexto recente, que é o mais relevante pra maioria dos casos de
        # debug/otimização (o problema "atual" da conversa).
        selected: list[Turn] = []
        used = 0
        for turn in reversed(self._turns):
            turn_text = f"Usuário: {turn.user}\nAXEL ({turn.intent}): {turn.response}"
            if used + len(turn_text) > self.max_chars and selected:
                break
            selected.append(turn)
            used += len(turn_text)
        selected.reverse()

        lines = []
        for turn in selected:
            lines.append(f"Usuário: {turn.user}")
            lines.append(f"AXEL ({turn.intent}): {turn.response}")
        return "\n".join(lines)

    def clear(self) -> None:
        self._turns.clear()

    def history(self) -> list[Turn]:
        return list(self._turns)


def get_memory() -> "SessionMemory":
    """Factory: escolhe o backend de memória com base em settings.memory_backend.

    Mesmo padrão do core/llm.py::get_provider — ponto de extensão único, não
    espalhado pelo código. Import local evita ciclo (persistent_memory
    importa Turn daqui).
    """
    if settings.memory_backend == "sqlite":
        from app.core.persistent_memory import PersistentSessionMemory

        return PersistentSessionMemory()  # type: ignore[return-value]
    return SessionMemory()
