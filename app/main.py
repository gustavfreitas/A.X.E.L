from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from app.core.llm import get_provider
from app.services.assistant import Assistant
from app.utils.preflight import check_ollama
from app.utils.security import InputValidationError

console = Console()

BANNER = """
[bold cyan]A.X.E.L.[/bold cyan] — Automated X-electronic Engineering Link
Especialista em debug e otimização de Python/SQL.
Digite 'sair' para encerrar.
"""


def main() -> None:
    console.print(Panel.fit(BANNER, border_style="cyan"))

    preflight = check_ollama()
    if not preflight.ok:
        console.print(f"[bold red]Pré-requisito faltando:[/bold red] {preflight.message}")
        return

    try:
        provider = get_provider()
    except ValueError as exc:
        console.print(f"[bold red]Erro de configuração:[/bold red] {exc}")
        return

    assistant = Assistant(provider=provider)

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
