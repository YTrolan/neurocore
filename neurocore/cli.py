import os

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent.loop import Agent
from .tools.builtin.files import ListDirTool, ReadFileTool, WriteFileTool
from .tools.builtin.image import GenerateImageTool
from .tools.builtin.shell import ShellTool
from .tools.builtin.web import WebFetchTool, WebSearchTool
from .tools.registry import ToolRegistry

app = typer.Typer(add_completion=False)
console = Console()


def _print_event(event: str, **data):
    if event == "thinking":
        console.print("[dim]· итерация " + str(data["iteration"]) + "[/dim]")
    elif event == "tool_call":
        console.print(
            Panel.fit(
                "[bold]" + data["name"] + "[/bold]\n" + str(data["arguments"]),
                title="tool call",
                border_style="yellow",
            )
        )
    elif event == "tool_result":
        console.print(
            Panel.fit(
                data["result"][:800],
                title="<- " + data["name"],
                border_style="cyan",
            )
        )
    elif event == "assistant":
        pass


def _build_agent(model: str, thinking: bool, cwd: str) -> Agent:
    token = os.getenv("DEEPSEEK_TOKEN")
    if not token:
        console.print("[red]Установи переменную окружения DEEPSEEK_TOKEN[/red]")
        raise typer.Exit(1)

    from .core.opendeep_provider import OpenDeepProvider

    provider = OpenDeepProvider(token=token, model=model, thinking=thinking)

    tools = (
        ToolRegistry()
        .register(ShellTool(cwd=cwd))
        .register(ReadFileTool())
        .register(WriteFileTool())
        .register(ListDirTool())
        .register(GenerateImageTool())
        .register(WebFetchTool())
        .register(WebSearchTool())
    )

    return Agent(provider=provider, tools=tools, on_event=_print_event)


@app.command()
def run(
    model: str = typer.Option("deepseek-v4-pro", help="Имя модели"),
    thinking: bool = typer.Option(False, "--think", help="Включить DeepThink"),
    cwd: str = typer.Option(".", help="Рабочая директория для shell"),
):
    """NeuroCore — интерактивный harness. Ctrl+C для выхода."""
    agent = _build_agent(model, thinking, cwd)

    console.print(
        Panel.fit(
            "[bold]NeuroCore[/bold] · модель: " + model + " · think=" + str(thinking),
            border_style="green",
        )
    )

    while True:
        try:
            user_input = console.input("\n[bold blue]>[/bold blue] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]пока[/dim]")
            break

        if not user_input.strip():
            continue

        try:
            answer = agent.run(user_input)
            console.print()
            console.print(Markdown(answer))
        except Exception as e:
            console.print("[red]Ошибка: " + str(e) + "[/red]")


def main():
    """Точка входа для neurocore.exe."""
    app()


if __name__ == "__main__":
    main()
