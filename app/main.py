from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from app.config import settings
from app.core.llm import get_provider
from app.core.memory import get_memory
from app.services.assistant import Assistant
from app.utils.preflight import check_ollama
from app.utils.security import InputValidationError

console = Console()

BANNER = """
[bold cyan]A.X.E.L.[/bold cyan] — Automated X-electronic Engineering Link
Especialista em debug e otimização de Python/SQL.
Comandos: 'sair', '/historico', '/limpar'.
"""


def main() -> None:
    console.print(Panel.fit(BANNER, border_style="cyan"))

    preflight = check_ollama()
    if not preflight.ok:
        console.print(
            f"[bold red]Pré-requisito faltando:[/bold red] {preflight.message}"
        )
        return

    try:
        provider = get_provider()
    except ValueError as exc:
        console.print(f"[bold red]Erro de configuração:[/bold red] {exc}")
        return

    memory = get_memory()
    if settings.memory_backend == "sqlite":
        console.print(
            f"[dim]Memória persistente ativa ({settings.history_db_path}). "
            "Trechos de código e mensagens ficam salvos em disco entre "
            "execuções. Use /limpar para apagar.[/dim]"
        )

    assistant = Assistant(provider=provider, memory=memory)

    while True:
        try:
            user_input = console.input("[bold green]você >[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Encerrando.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in {"sair", "exit", "quit"}:
            console.print("[dim]Até mais.[/dim]")
            break
        if user_input.lower() == "/limpar":
            memory.clear()
            console.print("[dim]Histórico apagado.[/dim]")
            continue
        if user_input.lower() == "/historico":
            turns = memory.history()
            if not turns:
                console.print("[dim](sem histórico nesta sessão)[/dim]")
            for i, turn in enumerate(turns, 1):
                console.print(f"[dim]{i}. [{turn.intent}] {turn.user[:70]}[/dim]")
            continue

        try:
            answer = assistant.handle(user_input)
        except InputValidationError as exc:
            console.print(f"[yellow]Entrada inválida:[/yellow] {exc}")
            continue
        except RuntimeError as exc:
            console.print(f"[bold red]AXEL:[/bold red] {exc}")
            continue

        console.print(Markdown(f"**AXEL:**\n\n{answer}"))


if __name__ == "__main__":
    main()
