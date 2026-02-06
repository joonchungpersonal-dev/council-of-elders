#!/usr/bin/env python3
"""
Council of Elders - Structured Debate with Problem Refinement

Flow:
1. REFINEMENT PHASE - Elders ask clarifying questions to understand the problem
2. SYNTHESIS - Problem is refined and framed
3. DEBATE PHASE - Structured debate with moderator

Usage: python debate.py
"""

import sys
import os
import asyncio
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from council.elders import ElderRegistry, Elder
from council.llm import check_ollama_available
from council.config import get_config_dir
from council.debate_engine import DebateEngine, DebatePhase
from council.refinement_engine import RefinementEngine, RefinedProblem
from council.smart_refinement import SmartRefinementEngine, RefinedProblem as SmartRefinedProblem

console = Console()

# Voice assignments
ELDER_VOICES = {
    "munger": "en-US-GuyNeural",
    "buffett": "en-US-RogerNeural",
    "aurelius": "en-GB-RyanNeural",
    "franklin": "en-US-ChristopherNeural",
    "bruce_lee": "en-US-JasonNeural",
    "musashi": "en-US-GuyNeural",
    "sun_tzu": "en-US-GuyNeural",
    "buddha": "en-IN-PrabhatNeural",
    "branden": "en-US-DavisNeural",
    "peterson": "en-CA-LiamNeural",
    "clear": "en-US-AndrewNeural",
    "kinrys": "en-US-JennyNeural",
    "noble": "en-GB-LibbyNeural",
    "quinn": "en-GB-SoniaNeural",
    "ryan": "en-US-MichelleNeural",
    "greene": "en-US-TonyNeural",
    "naval": "en-US-BrandonNeural",
    "rubin": "en-US-EricNeural",
    "oprah": "en-US-AriaNeural",
    "thich": "en-US-GuyNeural",
    "jung": "de-DE-ConradNeural",
}
MODERATOR_VOICE = "en-US-AriaNeural"
FALLBACK_VOICE = "en-US-GuyNeural"

PHASE_NAMES = {
    "opening": "Opening Statements",
    "cross_examination": "Cross-Examination",
    "rebuttal": "Rebuttals",
    "free_debate": "Open Debate",
    "closing": "Closing Statements",
}

ELDER_COLORS = {}


def get_debates_dir() -> Path:
    debates_dir = get_config_dir() / "debates"
    debates_dir.mkdir(parents=True, exist_ok=True)
    return debates_dir


def print_elders():
    elders = ElderRegistry.get_all()
    for elder in elders:
        console.print(f"  [cyan]{elder.id:12}[/cyan] {elder.name}")


def select_debaters() -> list[Elder]:
    console.print("\n[bold]Available Elders:[/bold]")
    print_elders()
    console.print()

    selection = Prompt.ask(
        "Select 2-4 elders (comma-separated)",
        default="munger,peterson,aurelius"
    )

    elder_ids = [e.strip().lower() for e in selection.split(",")]
    elders = []

    for eid in elder_ids:
        elder = ElderRegistry.get(eid)
        if elder:
            elders.append(elder)
            ELDER_COLORS[elder.name] = elder.color
        else:
            console.print(f"[yellow]'{eid}' not found, skipping.[/yellow]")

    if len(elders) < 2:
        console.print("[red]Need at least 2 elders. Using defaults.[/red]")
        elders = [ElderRegistry.get("munger"), ElderRegistry.get("aurelius")]
        for e in elders:
            ELDER_COLORS[e.name] = e.color

    return elders[:4]


def run_smart_refinement(initial_topic: str) -> RefinedProblem | None:
    """
    Run SMART refinement: automatically selects 2-4 most relevant elders
    instead of having all elders ask questions.
    """
    console.print(Panel.fit(
        "[bold]Smart Problem Refinement[/bold]\n"
        "[dim]The system will select the most relevant advisors for your question[/dim]",
        border_style="cyan"
    ))
    console.print()

    engine = SmartRefinementEngine(initial_topic)

    # Phase 1: Select elders
    console.print("[bold]Analyzing your question...[/bold]\n")

    for chunk in engine.select_elders():
        print(chunk, end='', flush=True)

    console.print(f"\n\n[green]Selected {len(engine.selected_elders)} advisors:[/green]")
    for elder in engine.selected_elders:
        rationale = engine.selection_rationale.get(elder.id, "")
        console.print(f"  [cyan]{elder.name}[/cyan] - {rationale}")
    console.print()

    # Phase 2: Each selected elder asks questions
    for elder in engine.selected_elders:
        color = getattr(elder, 'color', 'white')
        console.print(f"[bold {color}]{elder.name}[/bold {color}]:")

        full_response = []
        for chunk in engine.generate_questions(elder):
            full_response.append(chunk)
            print(chunk, end='', flush=True)
        console.print("\n")

        questions = engine.questions.get(elder.id, [])

        if questions and "sufficient clarity" not in "".join(full_response).lower():
            console.print(f"[dim]Answer {elder.name}'s questions (or Enter to skip):[/dim]")
            answer = Prompt.ask("[bold cyan]Your response[/bold cyan]", default="")

            if answer.strip():
                engine.record_answer(elder.id, answer)
            console.print()

    # Phase 3: Synthesize
    if engine.answers:
        console.print(Panel.fit("[bold]Synthesizing...[/bold]", border_style="green"))
        console.print()

        synthesis_text = []
        for chunk in engine.synthesize():
            synthesis_text.append(chunk)
            print(chunk, end='', flush=True)
        console.print("\n")

        refined = engine.parse_synthesis("".join(synthesis_text))

        # Convert to standard RefinedProblem
        return RefinedProblem(
            original_topic=refined.original_topic,
            refined_topic=refined.refined_topic,
            key_aspects=refined.key_aspects,
            user_context=refined.user_context,
            areas_of_tension=refined.areas_of_tension,
            debate_framing=refined.debate_framing
        )
    else:
        return RefinedProblem(
            original_topic=initial_topic,
            refined_topic=initial_topic,
            key_aspects=[],
            user_context={},
            areas_of_tension=[],
            debate_framing=initial_topic
        )


def run_refinement_phase(elders: list[Elder], initial_topic: str) -> RefinedProblem | None:
    """
    Run the problem refinement phase where elders ask clarifying questions.
    (Original approach: ALL selected elders ask questions)

    Returns RefinedProblem or None if user skips.
    """
    console.print(Panel.fit(
        "[bold]Phase 1: Problem Refinement[/bold]\n"
        "[dim]Each elder will ask 1-2 clarifying questions from their perspective[/dim]",
        border_style="cyan"
    ))
    console.print()

    engine = RefinementEngine(elders, initial_topic)
    all_questions_answers = []

    # Each elder asks questions
    for elder in elders:
        color = ELDER_COLORS.get(elder.name, "white")
        console.print(f"[bold {color}]{elder.name}[/bold {color}] is considering your question...")
        console.print()

        # Generate questions
        full_response = []
        for chunk in engine.generate_questions(elder):
            full_response.append(chunk)
            print(chunk, end='', flush=True)
        console.print("\n")

        questions = engine.questions.get(elder.id, [])

        if questions and "sufficient clarity" not in "".join(full_response).lower():
            # Get user's response
            console.print(f"[dim]Answer {elder.name}'s questions (or press Enter to skip):[/dim]")
            answer = Prompt.ask("[bold cyan]Your response[/bold cyan]", default="")

            if answer.strip():
                engine.record_answer(elder.id, answer)
                all_questions_answers.append({
                    "elder": elder.name,
                    "questions": questions,
                    "answer": answer
                })
            console.print()
        else:
            console.print(f"[dim]{elder.name} has sufficient clarity.[/dim]\n")

    # Synthesize if we got any answers
    if engine.answers:
        console.print(Panel.fit(
            "[bold]Synthesizing Refined Problem[/bold]",
            border_style="green"
        ))
        console.print()

        synthesis_text = []
        for chunk in engine.synthesize():
            synthesis_text.append(chunk)
            print(chunk, end='', flush=True)
        console.print("\n")

        refined = engine.parse_synthesis("".join(synthesis_text))

        # Show refined problem and confirm
        console.print(Panel(
            f"[bold]Original:[/bold] {refined.original_topic}\n\n"
            f"[bold]Refined:[/bold] {refined.refined_topic}\n\n"
            f"[bold]Debate Framing:[/bold] {refined.debate_framing}",
            title="Refined Problem",
            border_style="green"
        ))

        if Confirm.ask("\nProceed with this refined framing?", default=True):
            return refined
        else:
            # Let user adjust
            new_topic = Prompt.ask("Enter adjusted topic", default=refined.refined_topic)
            refined.refined_topic = new_topic
            refined.debate_framing = new_topic
            return refined
    else:
        console.print("[dim]No clarifications provided. Proceeding with original topic.[/dim]\n")
        return RefinedProblem(
            original_topic=initial_topic,
            refined_topic=initial_topic,
            key_aspects=[],
            user_context={},
            areas_of_tension=[],
            debate_framing=initial_topic
        )


def run_debate_ui(engine: DebateEngine, intensity: str = "standard") -> list[dict]:
    """Run the debate with live UI output."""

    if intensity == "quick":
        cross_rounds, free_exchanges = 1, 2
    elif intensity == "thorough":
        cross_rounds, free_exchanges = 3, 6
    else:
        cross_rounds, free_exchanges = 2, 4

    console.print(f"\n[bold]{'═' * 60}[/bold]")
    console.print(f"[bold]  DEBATE: {engine.topic}[/bold]")
    console.print(f"[bold]{'═' * 60}[/bold]\n")
    console.print(f"[dim]Debaters: {', '.join(e.name for e in engine.elders)}[/dim]")
    console.print(f"[dim]Format: Opening → Cross-Examination → Rebuttal → Free Debate → Closing[/dim]\n")

    current_phase = None
    current_speaker = None

    for phase, speaker, speaker_type, chunk in engine.run_full_debate(
        cross_exam_rounds=cross_rounds,
        free_debate_exchanges=free_exchanges
    ):
        if phase != current_phase:
            current_phase = phase
            phase_name = PHASE_NAMES.get(phase, phase)
            console.print(f"\n[bold magenta]{'─' * 20} {phase_name} {'─' * 20}[/bold magenta]\n")

        if speaker != current_speaker:
            current_speaker = speaker
            if chunk == "":
                if speaker_type == "moderator":
                    console.print(f"[bold bright_white]Moderator:[/bold bright_white]")
                else:
                    color = ELDER_COLORS.get(speaker, "white")
                    console.print(f"[bold {color}]{speaker}:[/bold {color}]")
                continue

        if chunk is None:
            console.print("\n")
            continue

        print(chunk, end='', flush=True)

    console.print(f"\n[bold]{'═' * 60}[/bold]")
    console.print(f"[bold]  END OF DEBATE[/bold]")
    console.print(f"[bold]{'═' * 60}[/bold]\n")

    return engine.get_transcript()


def save_transcript(
    topic: str,
    elders: list[Elder],
    transcript: list[dict],
    refined_problem: RefinedProblem | None = None
) -> Path:
    """Save the complete debate transcript including refinement."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debate_{timestamp}.md"
    filepath = get_debates_dir() / filename

    with open(filepath, "w") as f:
        f.write(f"# Council of Elders Debate\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Debaters:** {', '.join(e.name for e in elders)}\n\n")

        if refined_problem:
            f.write(f"## Problem Refinement\n\n")
            f.write(f"**Original Topic:** {refined_problem.original_topic}\n\n")
            f.write(f"**Refined Topic:** {refined_problem.refined_topic}\n\n")
            if refined_problem.key_aspects:
                f.write(f"**Key Aspects:**\n")
                for aspect in refined_problem.key_aspects:
                    f.write(f"- {aspect}\n")
                f.write("\n")
            if refined_problem.areas_of_tension:
                f.write(f"**Areas of Tension:**\n")
                for tension in refined_problem.areas_of_tension:
                    f.write(f"- {tension}\n")
                f.write("\n")
            f.write(f"**Debate Framing:** {refined_problem.debate_framing}\n\n")

        f.write("---\n\n")
        f.write(f"## Debate\n\n")
        f.write(f"**Topic:** {topic}\n\n")

        current_phase = None
        for entry in transcript:
            phase = entry.get("phase", "")
            if phase != current_phase:
                current_phase = phase
                phase_name = PHASE_NAMES.get(phase, phase)
                f.write(f"### {phase_name}\n\n")

            speaker = entry["speaker"]
            if entry["speaker_type"] == "moderator":
                f.write(f"**Moderator:** {entry['content']}\n\n")
            else:
                f.write(f"#### {speaker}\n\n{entry['content']}\n\n")

    return filepath


async def generate_debate_audio(transcript: list[dict], output_path: Path, progress_callback=None):
    """Generate audio for the debate."""
    import edge_tts

    temp_files = []

    try:
        for i, entry in enumerate(transcript):
            speaker = entry["speaker"]
            speaker_type = entry["speaker_type"]
            content = entry["content"]

            if speaker_type == "moderator":
                voice = MODERATOR_VOICE
            else:
                elder_id = None
                for eid, elder in [(e.id, e) for e in ElderRegistry.get_all()]:
                    if elder.name == speaker:
                        elder_id = eid
                        break
                voice = ELDER_VOICES.get(elder_id, FALLBACK_VOICE)

            temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            temp_files.append(temp_file.name)
            temp_file.close()

            full_text = f"{speaker} says: {content}"
            communicate = edge_tts.Communicate(full_text, voice)
            await communicate.save(temp_file.name)

            if progress_callback:
                progress_callback(i + 1, len(transcript))

        if len(temp_files) > 1:
            list_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            for tf in temp_files:
                list_file.write(f"file '{tf}'\n")
            list_file.close()

            try:
                subprocess.run([
                    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', list_file.name, '-c', 'copy', str(output_path)
                ], capture_output=True, check=True)
                os.unlink(list_file.name)
            except (subprocess.CalledProcessError, FileNotFoundError):
                for i, tf in enumerate(temp_files):
                    segment_path = output_path.parent / f"{output_path.stem}_part{i+1:02d}.mp3"
                    os.rename(tf, segment_path)
                temp_files = []
                console.print(f"[yellow]Audio saved as separate files (install ffmpeg to combine)[/yellow]")
                return
        elif temp_files:
            os.rename(temp_files[0], output_path)
            temp_files = []

    finally:
        for tf in temp_files:
            try:
                os.unlink(tf)
            except:
                pass


def play_audio(filepath: Path):
    if sys.platform == "darwin":
        subprocess.run(["afplay", str(filepath)])
    elif sys.platform == "linux":
        subprocess.run(["mpv", str(filepath)], capture_output=True)
    elif sys.platform == "win32":
        os.startfile(str(filepath))


def main():
    console.clear()
    console.print(Panel.fit(
        "[bold]Council of Elders[/bold]\n"
        "[dim]Structured Debate with Problem Refinement[/dim]",
        border_style="blue"
    ))

    # Check Ollama
    available, msg = check_ollama_available()
    if not available:
        console.print(f"[red]Error:[/red] {msg}")
        return

    # Select debaters
    elders = select_debaters()
    console.print(f"\n[green]Debaters:[/green] {', '.join(e.name for e in elders)}")

    # Get initial topic
    console.print()
    topic = Prompt.ask("[bold]What would you like the council to debate?[/bold]")
    if not topic.strip():
        topic = "What is the key to living a meaningful life?"

    # Ask about refinement
    console.print()
    console.print("[bold]Problem Refinement Options:[/bold]")
    console.print("  [cyan]smart[/cyan]    - AI selects 2-4 most relevant elders (recommended)")
    console.print("  [cyan]all[/cyan]      - All selected elders ask questions")
    console.print("  [cyan]skip[/cyan]     - Skip refinement, go straight to debate")
    refinement_mode = Prompt.ask(
        "Choose refinement mode",
        default="smart",
        choices=["smart", "all", "skip"]
    )

    refined_problem = None
    debate_topic = topic

    if refinement_mode == "smart":
        console.print()
        refined_problem = run_smart_refinement(topic)
        if refined_problem:
            debate_topic = refined_problem.refined_topic or refined_problem.debate_framing or topic
    elif refinement_mode == "all":
        console.print()
        refined_problem = run_refinement_phase(elders, topic)
        if refined_problem:
            debate_topic = refined_problem.refined_topic or refined_problem.debate_framing or topic

    # Debate intensity
    console.print("\n[bold]Debate intensity:[/bold]")
    console.print("  [cyan]quick[/cyan]    - Faster (~5 min)")
    console.print("  [cyan]standard[/cyan] - Balanced (~10 min)")
    console.print("  [cyan]thorough[/cyan] - Deep dive (~20 min)")
    intensity = Prompt.ask("Choose intensity", default="standard", choices=["quick", "standard", "thorough"])

    # Run debate
    console.print()
    console.print(Panel.fit(
        "[bold]Phase 2: Structured Debate[/bold]",
        border_style="red"
    ))

    engine = DebateEngine(elders, debate_topic)
    transcript = run_debate_ui(engine, intensity)

    # Save transcript
    transcript_path = save_transcript(debate_topic, elders, transcript, refined_problem)
    console.print(f"[green]✓ Transcript saved:[/green] {transcript_path}")

    # Generate audio
    if Confirm.ask("\nGenerate audio?", default=True):
        audio_path = transcript_path.with_suffix('.mp3')

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating audio...", total=len(transcript))

            def update_progress(current, total):
                progress.update(task, completed=current)

            asyncio.run(generate_debate_audio(transcript, audio_path, update_progress))

        if audio_path.exists():
            console.print(f"[green]✓ Audio saved:[/green] {audio_path}")

            if Confirm.ask("Play now?", default=False):
                console.print("[dim]Playing... (Ctrl+C to stop)[/dim]")
                try:
                    play_audio(audio_path)
                except KeyboardInterrupt:
                    pass
        else:
            part_files = list(audio_path.parent.glob(f"{audio_path.stem}_part*.mp3"))
            if part_files:
                console.print(f"[green]✓ Audio saved as {len(part_files)} parts[/green]")

    console.print(f"\n[dim]All debates saved in: ~/.council/debates/[/dim]")


if __name__ == "__main__":
    main()
