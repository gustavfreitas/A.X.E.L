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
    """Histórico curto em memória — reseta a cada execução do CLI.

    Deliberadamente simples na v1: nada de persistência em disco/DB ainda.
    Isso é uma limitação declarada no product brief, não um esquecimento.
    """

    max_turns: int = settings.max_history_turns
    _turns: deque[Turn] = field(default_factory=deque)

    def __post_init__(self) -> None:
        self._turns = deque(maxlen=self.max_turns)

    def add(self, user: str, intent: str, response: str) -> None:
        self._turns.append(Turn(user=user, intent=intent, response=response))

    def as_context(self) -> str:
        if not self._turns:
            return ""
        lines = []
        for turn in self._turns:
            lines.append(f"Usuário: {turn.user}")
            lines.append(f"AXEL ({turn.intent}): {turn.response}")
        return "\n".join(lines)
