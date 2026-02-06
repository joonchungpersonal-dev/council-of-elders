#!/usr/bin/env python3
"""
Council of Elders - Interactive Chatbot

Just run: python chat.py
"""

import sys
import os

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt

from council.elders import ElderRegistry
from council.llm import check_ollama_available
from council.orchestrator import get_orchestrator

console = Console()


def print_elders():
    """Print available elders in a compact format."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column()

    elders = ElderRegistry.get_all()
    # Display in two columns
    mid = (len(elders) + 1) // 2
    for i in range(mid):
        left = elders[i]
        left_text = f"[cyan]{left.id}[/cyan] - {left.name}"
        if i + mid < len(elders):
            right = elders[i + mid]
            right_text = f"[cyan]{right.id}[/cyan] - {right.name}"
        else:
            right_text = ""
        table.add_row(left_text, right_text)

    console.print(table)


def main():
    console.clear()
    console.print(Panel.fit(
        "[bold]Council of Elders[/bold]\n"
        "[dim]Wisdom from history's greatest thinkers[/dim]",
        border_style="blue"
    ))
    console.print()

    # Check Ollama
    available, msg = check_ollama_available()
    if not available:
        console.print(f"[red]Error:[/red] {msg}")
        console.print("[dim]Make sure Ollama is running: ollama serve[/dim]")
        return

    console.print("[bold]Available Elders:[/bold]")
    print_elders()
    console.print()

    console.print("[dim]Commands: 'switch' to change elder, 'elders' to list, 'clear' to reset, 'quit' to exit[/dim]")
    console.print()

    # Select initial elder
    elder_id = Prompt.ask(
        "Who would you like to consult?",
        default="munger"
    ).strip().lower()

    elder = ElderRegistry.get(elder_id)
    if not elder:
        console.print(f"[yellow]Elder '{elder_id}' not found. Starting with Munger.[/yellow]")
        elder = ElderRegistry.get("munger")
        elder_id = "munger"

    console.print()
    console.print(f"[bold {elder.color}]── {elder.name} ──[/bold {elder.color}]")
    console.print(f"[{elder.color}]{elder.get_greeting()}[/{elder.color}]")
    console.print()

    orchestrator = get_orchestrator()

    while True:
        try:
            # Get user input
            user_input = Prompt.ask(f"[bold]You[/bold]").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ('quit', 'exit', 'q'):
                console.print("\n[dim]May their wisdom guide you.[/dim]")
                break

            if user_input.lower() == 'clear':
                orchestrator = get_orchestrator()
                console.clear()
                console.print(f"[bold {elder.color}]── {elder.name} ──[/bold {elder.color}]")
                console.print(f"[{elder.color}]{elder.get_greeting()}[/{elder.color}]")
                console.print()
                continue

            if user_input.lower() in ('switch', 'change', 'elders'):
                console.print()
                print_elders()
                new_elder_id = Prompt.ask(
                    "\nWho would you like to consult?",
                    default=elder_id
                ).strip().lower()

                new_elder = ElderRegistry.get(new_elder_id)
                if new_elder:
                    elder = new_elder
                    elder_id = new_elder_id
                    orchestrator = get_orchestrator()  # Reset conversation
                    console.print()
                    console.print(f"[bold {elder.color}]── {elder.name} ──[/bold {elder.color}]")
                    console.print(f"[{elder.color}]{elder.get_greeting()}[/{elder.color}]")
                else:
                    console.print(f"[yellow]Elder '{new_elder_id}' not found.[/yellow]")
                console.print()
                continue

            # Check for @mention to switch elder inline
            if user_input.startswith('@'):
                parts = user_input.split(' ', 1)
                mentioned_elder_id = parts[0][1:].lower()
                mentioned_elder = ElderRegistry.get(mentioned_elder_id)
                if mentioned_elder:
                    elder = mentioned_elder
                    elder_id = mentioned_elder_id
                    orchestrator = get_orchestrator()
                    user_input = parts[1] if len(parts) > 1 else ""
                    console.print(f"[dim]Switching to {elder.name}...[/dim]")
                    if not user_input:
                        console.print(f"[{elder.color}]{elder.get_greeting()}[/{elder.color}]")
                        console.print()
                        continue

            # Get response from elder
            console.print()
            response_parts = []

            # Print elder name
            console.print(f"[bold {elder.color}]{elder.name}[/bold {elder.color}]")

            # Stream response
            for chunk in orchestrator.ask_elder(elder_id, user_input, stream=True):
                response_parts.append(chunk)
                print(chunk, end='', flush=True)

            console.print("\n")

        except KeyboardInterrupt:
            console.print("\n\n[dim]Session interrupted. May their wisdom guide you.[/dim]")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
