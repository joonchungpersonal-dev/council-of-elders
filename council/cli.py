"""Command-line interface for Council of Elders."""

from typing import Optional
import sys

import typer
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt
from rich.markdown import Markdown

from council.elders import ElderRegistry
from council.orchestrator import get_orchestrator
from council.llm import check_ollama_available, list_available_models
from council.config import load_config, save_config, get_config_value, set_config_value
from council.ui import (
    console,
    print_error,
    print_success,
    print_info,
    print_elders_list,
    print_welcome,
    print_elder_header,
    create_elder_panel,
)
from council.history import save_session, list_sessions, load_session
from council.formats.html_formatter import save_html_response

app = typer.Typer(
    name="council",
    help="Council of Elders - Local AI Advisory System",
    no_args_is_help=True,
)


@app.command()
def ask(
    elder: str = typer.Argument(..., help="Elder ID to consult (e.g., munger, aurelius)"),
    question: str = typer.Argument(..., help="Your question for the elder"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming output"),
):
    """Ask a specific elder a question."""
    # Validate elder exists
    elder_obj = ElderRegistry.get(elder)
    if not elder_obj:
        print_error(f"Elder '{elder}' not found. Use 'council elders' to see available elders.")
        raise typer.Exit(1)

    # Check Ollama
    available, msg = check_ollama_available()
    if not available:
        print_error(msg)
        raise typer.Exit(1)

    orchestrator = get_orchestrator()

    print_elder_header(elder_obj)

    if no_stream:
        response_text = "".join(orchestrator.ask_elder(elder, question, stream=True))
        console.print(f"[{elder_obj.color}]│[/]")
        console.print(create_elder_panel(elder_obj, response_text))
    else:
        full_response = []
        with Live(console=console, refresh_per_second=10, transient=True) as live:
            for chunk in orchestrator.ask_elder(elder, question, stream=True):
                full_response.append(chunk)
                current = "".join(full_response)
                live.update(Text(f"│ {current}", style=f"{elder_obj.color}"))

        console.print(f"[{elder_obj.color}]│[/]")
        response_text = "".join(full_response)
        console.print(create_elder_panel(elder_obj, response_text))

    # Save to history
    save_session(
        [elder],
        [
            {"role": "user", "content": question},
            {"role": "elder", "elder_id": elder, "content": response_text},
        ],
    )


@app.command()
def roundtable(
    question: str = typer.Argument(..., help="Topic or question for the roundtable"),
    elders: str = typer.Option(
        "munger,aurelius,franklin",
        "--elders", "-e",
        help="Comma-separated list of elder IDs",
    ),
    turns: int = typer.Option(1, "--turns", "-t", help="Number of discussion rounds"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output HTML file path"),
    html: bool = typer.Option(False, "--html", help="Force HTML output"),
    no_html: bool = typer.Option(False, "--no-html", help="Disable HTML output"),
    no_nominations: bool = typer.Option(False, "--no-nominations", help="Disable elder nominations"),
):
    """Convene a roundtable discussion with multiple elders."""
    import webbrowser
    from pathlib import Path

    elder_ids = [e.strip() for e in elders.split(",")]

    # Validate all elders
    for elder_id in elder_ids:
        if not ElderRegistry.get(elder_id):
            print_error(f"Elder '{elder_id}' not found. Use 'council elders' to see available.")
            raise typer.Exit(1)

    # Check Ollama
    available, msg = check_ollama_available()
    if not available:
        print_error(msg)
        raise typer.Exit(1)

    console.print()
    console.print(f"[bold]Roundtable Discussion[/bold]")
    console.print(f"[dim]Elders: {', '.join(elder_ids)} | Rounds: {turns}[/dim]")
    console.print()

    orchestrator = get_orchestrator()
    conversation = [{"role": "user", "content": question}]

    current_elder = None
    current_response = []
    responses_for_html = []
    nominated_elders: dict[str, object] = {}  # id -> NominatedElder

    allow_nominations = not no_nominations

    for elder_id, chunk in orchestrator.roundtable(
        elder_ids, question, turns=turns, allow_nominations=allow_nominations
    ):
        # Handle nomination events
        if elder_id == "__nomination__":
            guest = chunk  # chunk is the NominatedElder object
            nominated_elders[guest.id] = guest
            console.print()
            console.print(
                f"[bold bright_magenta]>> {guest._nominated_by} nominates "
                f"{guest.name} ({guest._expertise})[/bold bright_magenta]"
            )
            console.print()
            continue

        if chunk is None:
            # End of this elder's turn
            if current_elder and current_response:
                console.print(f"[{current_elder.color}]│[/]")
                console.print(create_elder_panel(current_elder, "".join(current_response)))
                full_content = "".join(current_response)
                conversation.append({
                    "role": "elder",
                    "elder_id": current_elder.id,
                    "content": full_content,
                })
                responses_for_html.append({
                    "elder_id": current_elder.id,
                    "content": full_content,
                })
            current_response = []
            current_elder = None
        else:
            # New elder starting or continuing
            elder_obj = ElderRegistry.get(elder_id) or nominated_elders.get(elder_id)
            if current_elder != elder_obj:
                current_elder = elder_obj
                print_elder_header(elder_obj)
            current_response.append(chunk)
            # Print incrementally
            sys.stdout.write(chunk)
            sys.stdout.flush()

    # Save to history
    save_session(elder_ids, conversation)
    console.print()

    # Check if we should output HTML
    output_format = get_config_value("output_format", "terminal")
    should_output_html = (
        html or
        output is not None or
        (output_format in ("html", "both") and not no_html)
    )

    if should_output_html and responses_for_html:
        output_path = output or f"council_roundtable_{len(elder_ids)}elders.html"
        html_path = save_html_response(
            question=question,
            responses=responses_for_html,
            output_path=output_path,
            title="Roundtable Discussion"
        )
        print_success(f"HTML output saved to: {html_path}")

        # Auto-open if configured
        if get_config_value("auto_open_html", True):
            webbrowser.open(f"file://{html_path}")


@app.command()
def chat(
    elder: str = typer.Argument(..., help="Elder ID for interactive chat"),
):
    """Start an interactive chat session with an elder."""
    elder_obj = ElderRegistry.get(elder)
    if not elder_obj:
        print_error(f"Elder '{elder}' not found.")
        raise typer.Exit(1)

    available, msg = check_ollama_available()
    if not available:
        print_error(msg)
        raise typer.Exit(1)

    console.print()
    console.print(f"[bold]Interactive Session with {elder_obj.name}[/bold]")
    console.print(f"[dim]{elder_obj.title} ({elder_obj.era})[/dim]")
    console.print()
    console.print(f"[{elder_obj.color}]{elder_obj.get_greeting()}[/]")
    console.print()
    console.print("[dim]Type 'quit' or 'exit' to end the session. Press Ctrl+C to interrupt.[/dim]")
    console.print()

    orchestrator = get_orchestrator()
    conversation = []

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")

            if user_input.lower() in ("quit", "exit", "q"):
                console.print()
                print_info("Session ended. May their wisdom guide you.")
                break

            if not user_input.strip():
                continue

            conversation.append({"role": "user", "content": user_input})
            print_elder_header(elder_obj)

            full_response = []
            for chunk in orchestrator.ask_elder(elder, user_input, stream=True):
                full_response.append(chunk)
                sys.stdout.write(chunk)
                sys.stdout.flush()

            console.print()
            response_text = "".join(full_response)
            conversation.append({"role": "elder", "elder_id": elder, "content": response_text})
            console.print()

        except KeyboardInterrupt:
            console.print()
            print_info("Session interrupted.")
            break
        except EOFError:
            console.print()
            break

    # Save session
    if conversation:
        save_session([elder], conversation)


@app.command(name="elders")
def list_elders(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show mental models"),
):
    """List all available elders in the council."""
    print_elders_list(verbose=verbose)


@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="Config key to view or set"),
    value: Optional[str] = typer.Argument(None, help="Value to set"),
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all config values"),
):
    """View or modify configuration."""
    if show_all or (key is None and value is None):
        cfg = load_config()
        console.print()
        console.print("[bold]Current Configuration[/bold]")
        console.print()
        for k, v in cfg.items():
            console.print(f"  [cyan]{k}[/cyan]: {v}")
        console.print()
        console.print(f"[dim]Config file: ~/.council/config.yaml[/dim]")
        console.print()
        return

    if key and value is None:
        # Show single value
        val = get_config_value(key)
        if val is not None:
            console.print(f"{key}: {val}")
        else:
            print_error(f"Config key '{key}' not found.")
            raise typer.Exit(1)
    elif key and value:
        # Set value
        # Try to parse as appropriate type
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        else:
            try:
                value = float(value)
            except ValueError:
                pass  # Keep as string

        set_config_value(key, value)
        print_success(f"Set {key} = {value}")


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of sessions to show"),
    session_id: Optional[str] = typer.Argument(None, help="Session ID to view"),
):
    """View conversation history."""
    if session_id:
        session = load_session(session_id)
        if not session:
            print_error(f"Session '{session_id}' not found.")
            raise typer.Exit(1)

        console.print()
        console.print(f"[bold]Session: {session['id']}[/bold]")
        console.print(f"[dim]Date: {session.get('timestamp', 'Unknown')}[/dim]")
        console.print(f"[dim]Elders: {', '.join(session.get('elders', []))}[/dim]")
        console.print()

        for turn in session.get("conversation", []):
            if turn["role"] == "user":
                console.print(f"[bold cyan]You:[/bold cyan] {turn['content']}")
                console.print()
            else:
                elder = ElderRegistry.get(turn.get("elder_id", ""))
                name = elder.name if elder else turn.get("elder_id", "Elder")
                color = elder.color if elder else "white"
                console.print(f"[bold {color}]{name}:[/bold {color}]")
                console.print(Markdown(turn["content"]))
                console.print()
        return

    sessions = list_sessions(limit=limit)

    if not sessions:
        print_info("No conversation history yet.")
        return

    console.print()
    console.print("[bold]Recent Sessions[/bold]")
    console.print()

    for s in sessions:
        elders_str = ", ".join(s.get("elders", []))[:30]
        date_str = s.get("timestamp", "")[:10]
        console.print(
            f"  [cyan]{s['id']}[/cyan]  "
            f"[dim]{date_str}[/dim]  "
            f"[dim]({elders_str})[/dim]  "
            f"{s.get('topic', 'Untitled')[:40]}"
        )

    console.print()
    console.print("[dim]Use 'council history <session_id>' to view a session.[/dim]")


@app.command()
def models():
    """List available Ollama models."""
    available_models = list_available_models()

    if not available_models:
        print_error("No models found. Make sure Ollama is running.")
        console.print("[dim]Install a model with: ollama pull qwen2.5:14b[/dim]")
        raise typer.Exit(1)

    current_model = get_config_value("model", "qwen2.5:14b")

    console.print()
    console.print("[bold]Available Ollama Models[/bold]")
    console.print()

    for model in available_models:
        if model == current_model:
            console.print(f"  [green]● {model}[/green] [dim](current)[/dim]")
        else:
            console.print(f"  [dim]○[/dim] {model}")

    console.print()
    console.print("[dim]Change model with: council config model <model_name>[/dim]")


@app.command()
def checklist(
    question: str = typer.Argument(..., help="Decision or problem to analyze"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output HTML file path"),
):
    """Run Munger's comprehensive mental model checklist on a decision.

    This systematically applies Charlie Munger's full latticework of mental models
    to analyze a decision or problem from multiple angles - the way Munger himself
    would approach important decisions.
    """
    import webbrowser
    from pathlib import Path

    available, msg = check_ollama_available()
    if not available:
        print_error(msg)
        raise typer.Exit(1)

    elder_obj = ElderRegistry.get("munger")

    console.print()
    console.print("[bold dark_orange]Munger's Mental Model Checklist[/bold dark_orange]")
    console.print(f"[dim]Systematic analysis using the latticework of mental models[/dim]")
    console.print()
    console.print(f"[bold]Decision/Problem:[/bold] {question}")
    console.print()

    # The comprehensive checklist prompt
    checklist_prompt = f"""You are running your comprehensive mental model checklist on this decision. This is the systematic approach you use for important decisions - walking through your full latticework of models to ensure nothing is missed.

The decision/problem to analyze:
"{question}"

Please work through each category of mental models systematically, noting what each reveals about this decision. Be thorough but practical - if a model doesn't apply, say so briefly and move on.

## CHECKLIST STRUCTURE

### 1. INVERSION (What would guarantee failure?)
- Invert the question: What would make this fail spectacularly?
- What am I trying to avoid at all costs?
- "All I want to know is where I'm going to die, so I never go there."

### 2. CIRCLE OF COMPETENCE
- Is this within my circle of competence?
- What do I NOT know that I need to know?
- Who knows more about this than I do?

### 3. FIRST PRINCIPLES THINKING
- What are the fundamental truths here?
- What assumptions am I making that might be wrong?
- Strip away the complexity - what's really going on?

### 4. INCENTIVES ("Show me the incentive...")
- Who benefits from what outcome?
- What incentives are at play that I might be missing?
- Are incentives aligned or misaligned?

### 5. SECOND AND THIRD ORDER EFFECTS
- What happens next? And then what?
- What are the unintended consequences?
- Play out the scenario over time.

### 6. PROBABILISTIC THINKING
- What are the base rates for this type of decision?
- Am I overweighting recent or vivid examples?
- What's the expected value calculation?

### 7. OPPORTUNITY COST
- What am I giving up by choosing this path?
- What else could I do with this time/money/energy?
- Is there a better alternative I'm not considering?

### 8. MARGIN OF SAFETY
- What's my buffer for being wrong?
- How bad is the worst case, and can I survive it?
- Am I leaving enough room for error?

### 9. PSYCHOLOGY OF HUMAN MISJUDGMENT
Run through the key biases:
- Confirmation bias: Am I seeking only supporting evidence?
- Commitment/consistency: Am I doubling down on a prior decision?
- Social proof: Am I following the crowd?
- Authority: Am I deferring too much to experts?
- Liking/disliking: Are my feelings about people clouding judgment?
- Envy/jealousy: Is this driving the decision?
- Reciprocity: Do I feel obligated in a way that distorts thinking?
- Over-optimism: Am I being too hopeful?
- Loss aversion: Am I avoiding action due to fear of loss?
- Availability cascade: Is something vivid/recent distorting my view?

### 10. LOLLAPALOOZA EFFECTS
- Are multiple biases or forces combining here?
- What feedback loops might amplify effects?
- Where might things go nonlinear?

### 11. MR. MARKET / CONTRARIAN THINKING
- What does the crowd believe? Are they right?
- Is there value in going against consensus?
- Am I being contrarian just to be different, or is there logic?

### 12. FINAL SYNTHESIS
- What's the clear-eyed summary?
- What's my recommendation?
- What would make me change my mind?

---

Work through each section with your characteristic directness. Don't pad or flatter - give the hard truth. Use analogies and examples where helpful. End with a clear, actionable conclusion."""

    orchestrator = get_orchestrator()

    print_elder_header(elder_obj)

    full_response = []
    for chunk in orchestrator.ask_elder("munger", checklist_prompt, stream=True):
        full_response.append(chunk)
        sys.stdout.write(chunk)
        sys.stdout.flush()

    console.print()
    console.print()
    response_text = "".join(full_response)

    # Save to history
    save_session(
        ["munger"],
        [
            {"role": "user", "content": f"[MENTAL MODEL CHECKLIST] {question}"},
            {"role": "elder", "elder_id": "munger", "content": response_text},
        ],
    )

    # HTML output
    output_format = get_config_value("output_format", "terminal")
    should_output_html = output is not None or output_format in ("html", "both")

    if should_output_html:
        import webbrowser
        output_path = output or "munger_checklist.html"
        html_path = save_html_response(
            question=f"Mental Model Checklist: {question}",
            responses=[{"elder_id": "munger", "content": response_text}],
            output_path=output_path,
            title="Munger's Mental Model Checklist"
        )
        print_success(f"HTML output saved to: {html_path}")

        if get_config_value("auto_open_html", True):
            webbrowser.open(f"file://{html_path}")


@app.command()
def status():
    """Check system status and configuration."""
    console.print()
    console.print("[bold]Council of Elders - Status[/bold]")
    console.print()

    # Ollama status
    available, msg = check_ollama_available()
    if available:
        console.print(f"  [green]●[/green] Ollama: Connected")
    else:
        console.print(f"  [red]●[/red] Ollama: {msg}")

    # Current model
    model = get_config_value("model", "qwen2.5:14b")
    console.print(f"  [dim]Model:[/dim] {model}")

    # Available elders
    elders = ElderRegistry.get_all()
    console.print(f"  [dim]Elders:[/dim] {len(elders)} available")

    # History
    sessions = list_sessions(limit=1000)
    console.print(f"  [dim]History:[/dim] {len(sessions)} sessions")

    console.print()


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(5000, "--port", "-p", help="Port to bind to"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """Launch the beautiful web interface."""
    import webbrowser
    from threading import Timer

    # Check Ollama first
    available, msg = check_ollama_available()
    if not available:
        print_error(msg)
        print_info("The web interface will still launch, but you'll need Ollama running to use it.")

    console.print()
    console.print("[bold]Council of Elders - Web Interface[/bold]")
    console.print()
    console.print(f"Starting server at [cyan]http://{host}:{port}[/cyan]")
    console.print("[dim]Press Ctrl+C to stop the server.[/dim]")
    console.print()

    # Open browser after short delay
    def open_browser():
        webbrowser.open(f"http://{host}:{port}")

    if not debug:
        Timer(1.5, open_browser).start()

    from council.web.app import run_server
    run_server(host=host, port=port, debug=debug)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """Council of Elders - Local AI Advisory System."""
    if version:
        from council import __version__
        console.print(f"Council of Elders v{__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        print_welcome()


if __name__ == "__main__":
    app()
