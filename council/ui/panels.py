"""Rich UI panels and display components."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.markdown import Markdown

from council.elders import Elder, ElderRegistry

console = Console()


def create_elder_panel(elder: Elder, content: str, title: str | None = None) -> Panel:
    """Create a styled panel for an elder's response."""
    panel_title = title or f"[bold]{elder.name}[/bold]"
    return Panel(
        Markdown(content),
        title=panel_title,
        title_align="left",
        border_style=elder.color,
        padding=(1, 2),
    )


def print_elder_header(elder: Elder) -> None:
    """Print an elder's header."""
    console.print()
    console.print(f"[bold {elder.color}]┌─ {elder.name} ─[/]")
    console.print(f"[dim {elder.color}]│  {elder.title} ({elder.era})[/]")
    console.print(f"[{elder.color}]│[/]")


def print_elder_response(elder: Elder, content: str) -> None:
    """Print an elder's complete response in a panel."""
    console.print()
    console.print(create_elder_panel(elder, content))


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[dim]{message}[/dim]")


def print_elders_list(verbose: bool = False) -> None:
    """Print a table of available elders."""
    table = Table(title="Council of Elders", show_header=True, header_style="bold")

    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Title")
    table.add_column("Era", style="dim")

    if verbose:
        table.add_column("Key Mental Models", style="italic")

    for elder in ElderRegistry.get_all():
        if verbose:
            models = ", ".join(elder.mental_models[:3])
            if len(elder.mental_models) > 3:
                models += f" (+{len(elder.mental_models) - 3} more)"
            table.add_row(elder.id, elder.name, elder.title, elder.era, models)
        else:
            table.add_row(elder.id, elder.name, elder.title, elder.era)

    console.print()
    console.print(table)
    console.print()


def print_welcome() -> None:
    """Print welcome message."""
    welcome_text = """
[bold]Welcome to the Council of Elders[/bold]

A local AI advisory system embodying the wisdom of great thinkers.
All processing happens locally on your machine using Ollama.

[dim]Commands:[/dim]
  [cyan]council ask <elder> "<question>"[/cyan]  - Ask a specific elder
  [cyan]council roundtable "<question>"[/cyan]   - Convene multiple elders
  [cyan]council chat <elder>[/cyan]              - Interactive chat session
  [cyan]council elders[/cyan]                    - List available elders
  [cyan]council config[/cyan]                    - View/edit configuration

[dim]Examples:[/dim]
  council ask munger "Should I invest in this opportunity?"
  council ask buddha "How do I find peace with uncertainty?"
  council roundtable --elders munger,buffett "How should I evaluate a business?"
  council chat aurelius
"""
    console.print(Panel(welcome_text, border_style="blue", padding=(1, 2)))


def stream_elder_response(elder: Elder, response_generator) -> str:
    """Stream an elder's response with live updating."""
    full_response = []

    print_elder_header(elder)

    with Live(console=console, refresh_per_second=10, transient=True) as live:
        for chunk in response_generator:
            full_response.append(chunk)
            current_text = "".join(full_response)
            # Show streaming text with elder color
            live.update(Text(f"│ {current_text}", style=elder.color))

    # Print final response
    final_text = "".join(full_response)
    console.print(f"[{elder.color}]│[/]")
    console.print(create_elder_panel(elder, final_text, title=None))

    return final_text
