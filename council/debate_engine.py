"""
Multi-Agent Debate Engine

A structured debate system with:
- Moderator agent that guides discussion and identifies disagreements
- Multiple debate phases (opening, cross-examination, rebuttal, closing)
- Forced engagement between elders on points of disagreement
- Tracking of positions and arguments
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Generator

from council.elders import Elder, ElderRegistry
from council.llm import chat
from council.config import get_config_value
from council.nomination import (
    NOMINATION_INSTRUCTION,
    parse_nomination,
    strip_nomination_tag,
    create_nominated_elder,
)


class DebatePhase(Enum):
    OPENING = "opening"
    CROSS_EXAMINATION = "cross_examination"
    REBUTTAL = "rebuttal"
    FREE_DEBATE = "free_debate"
    CLOSING = "closing"


@dataclass
class Position:
    """An elder's position on a topic."""
    elder_id: str
    stance: str  # Their core position
    key_arguments: list[str] = field(default_factory=list)
    points_challenged: list[str] = field(default_factory=list)


@dataclass
class Disagreement:
    """A point of disagreement between elders."""
    topic: str
    elder_a: str
    position_a: str
    elder_b: str
    position_b: str
    resolved: bool = False


MODERATOR_SYSTEM_PROMPT = """You are a skilled debate moderator for the Council of Elders.

Your role is to:
1. Ensure productive, substantive debate
2. Identify points of agreement and disagreement
3. Push debaters to engage with each other's arguments directly
4. Ask probing follow-up questions
5. Prevent debaters from talking past each other
6. Keep the debate focused and moving forward

You are neutral and do not take sides. You facilitate rigorous intellectual exchange.

Be concise. Your interventions should be brief and purposeful."""


class DebateEngine:
    """Multi-agent debate engine with moderator and structured phases."""

    def __init__(
        self,
        elders: list[Elder],
        topic: str,
        allow_nominations: bool | None = None,
        max_nominations: int | None = None,
    ):
        self.elders = elders
        self.topic = topic
        self.transcript: list[dict] = []
        self.positions: dict[str, Position] = {}
        self.disagreements: list[Disagreement] = []
        self.current_phase = DebatePhase.OPENING

        # Nomination state
        if allow_nominations is None:
            allow_nominations = get_config_value("nominations_enabled", True)
        if max_nominations is None:
            max_nominations = get_config_value("max_nominations_per_session", 2)
        self.allow_nominations = allow_nominations
        self.max_nominations = max_nominations
        self.nomination_count = 0
        self.guest_elders: list[Elder] = []

    def _add_to_transcript(self, speaker: str, speaker_type: str, content: str, phase: DebatePhase, elder_id: str | None = None):
        """Add a statement to the transcript."""
        self.transcript.append({
            "speaker": speaker,
            "speaker_type": speaker_type,  # "elder" or "moderator"
            "content": content,
            "phase": phase.value,
            "elder_id": elder_id,
        })

    def _get_debate_context(self, for_elder: str | None = None, last_n: int = 10) -> str:
        """Get recent debate context as a string."""
        recent = self.transcript[-last_n:] if len(self.transcript) > last_n else self.transcript

        if not recent:
            return ""

        context = "Recent debate:\n\n"
        for entry in recent:
            if entry["speaker_type"] == "moderator":
                prefix = "[MODERATOR]"
            elif for_elder and entry.get("elder_id") == for_elder:
                prefix = "[You]"
            else:
                prefix = f"[{entry['speaker']}]"
            context += f"{prefix}: {entry['content']}\n\n"

        return context

    def _call_moderator(self, instruction: str, stream: bool = True) -> Generator[str, None, None] | str:
        """Get moderator input."""
        context = self._get_debate_context()

        prompt = f"""Topic: {self.topic}

Debaters: {', '.join(e.name for e in self.elders)}

{context}

{instruction}"""

        messages = [{"role": "user", "content": prompt}]

        if stream:
            full_response = []
            for chunk in chat(messages, system=MODERATOR_SYSTEM_PROMPT, stream=True):
                full_response.append(chunk)
                yield chunk
            self._add_to_transcript("Moderator", "moderator", "".join(full_response), self.current_phase)
        else:
            response = "".join(chat(messages, system=MODERATOR_SYSTEM_PROMPT, stream=True))
            self._add_to_transcript("Moderator", "moderator", response, self.current_phase)
            return response

    def _call_elder(self, elder: Elder, instruction: str, stream: bool = True) -> Generator[str, None, None] | str:
        """Get an elder's response."""
        context = self._get_debate_context(for_elder=elder.id)

        prompt = f"""You are participating in a formal debate.

Topic: {self.topic}

Other debaters: {', '.join(e.name for e in self.elders if e.id != elder.id)}

{context}

{instruction}

Remember: This is a debate. Engage directly with the other debaters' arguments.
If you disagree, say so clearly and explain why. If you agree, acknowledge it and build upon it.
Do not simply give a monologue - this is a conversation."""

        messages = [{"role": "user", "content": prompt}]

        if stream:
            full_response = []
            for chunk in chat(messages, system=elder.system_prompt, stream=True):
                full_response.append(chunk)
                yield chunk
            self._add_to_transcript(elder.name, "elder", "".join(full_response), self.current_phase, elder_id=elder.id)
        else:
            response = "".join(chat(messages, system=elder.system_prompt, stream=True))
            self._add_to_transcript(elder.name, "elder", response, self.current_phase, elder_id=elder.id)
            return response

    def _analyze_positions(self) -> str:
        """Have moderator analyze current positions and identify disagreements."""
        prompt = f"""Analyze the debate so far on: {self.topic}

For each debater, identify:
1. Their core position/stance
2. Their key arguments
3. Points where they disagree with others

Then identify the most significant disagreements that should be explored further.

Format your response as:

## Positions
[Elder Name]: [Core stance]
- Key argument 1
- Key argument 2

## Key Disagreements
1. [Elder A] vs [Elder B] on [specific point]
2. ...

## Recommended Focus
[What the debate should focus on next to be most productive]"""

        messages = [{"role": "user", "content": self._get_debate_context() + "\n\n" + prompt}]
        return "".join(chat(messages, system=MODERATOR_SYSTEM_PROMPT, stream=True))

    def run_opening_statements(self) -> Generator[tuple[str, str, str], None, None]:
        """
        Run opening statements phase.

        Yields: (speaker_name, speaker_type, chunk)
        """
        self.current_phase = DebatePhase.OPENING

        # Moderator introduces
        yield ("Moderator", "moderator", "")
        intro_prompt = f"Briefly introduce this debate on '{self.topic}' and invite the first speaker to give their opening statement. Be concise (2-3 sentences)."
        for chunk in self._call_moderator(intro_prompt):
            yield ("Moderator", "moderator", chunk)
        yield ("Moderator", "moderator", None)  # Signal end of turn

        # Each elder gives opening statement
        for i, elder in enumerate(self.elders):
            yield (elder.name, "elder", "")

            instruction = f"""Give your opening statement on: {self.topic}

In 2-3 paragraphs:
1. State your core position clearly
2. Present your main arguments
3. If you're not the first speaker, briefly acknowledge what others have said

Be direct and substantive."""

            for chunk in self._call_elder(elder, instruction):
                yield (elder.name, "elder", chunk)
            yield (elder.name, "elder", None)  # Signal end of turn

    def run_cross_examination(self, rounds: int = 2) -> Generator[tuple[str, str, str], None, None]:
        """
        Run cross-examination phase where elders question each other.

        Yields: (speaker_name, speaker_type, chunk)
        """
        self.current_phase = DebatePhase.CROSS_EXAMINATION

        # Moderator analyzes and identifies key disagreements
        yield ("Moderator", "moderator", "")
        analysis_prompt = """Based on the opening statements, identify the key points of disagreement.
Then pose a direct question to one debater about another's argument.
Format: "[Elder A], [Elder B] argued [X]. How do you respond to this?"
Be specific and pointed."""

        for chunk in self._call_moderator(analysis_prompt):
            yield ("Moderator", "moderator", chunk)
        yield ("Moderator", "moderator", None)

        for round_num in range(rounds):
            for i, elder in enumerate(self.elders):
                yield (elder.name, "elder", "")

                # Get the other elders
                other_elders = [e for e in self.elders if e.id != elder.id]
                other_names = ", ".join(e.name for e in other_elders)

                instruction = f"""The moderator or another debater has raised points you should address.

Your task:
1. Directly respond to any challenges to your position
2. Then pose a pointed question to one of the other debaters ({other_names})
3. Your question should challenge their argument or expose a weakness in their reasoning

Be direct. This is cross-examination - be intellectually aggressive but respectful."""

                for chunk in self._call_elder(elder, instruction):
                    yield (elder.name, "elder", chunk)
                yield (elder.name, "elder", None)

            # Moderator intervention between rounds
            if round_num < rounds - 1:
                yield ("Moderator", "moderator", "")
                intervention_prompt = """The cross-examination continues.
Identify an argument that hasn't been adequately addressed or a contradiction that should be explored.
Push one of the debaters to clarify or defend their position. Be specific and probing."""

                for chunk in self._call_moderator(intervention_prompt):
                    yield ("Moderator", "moderator", chunk)
                yield ("Moderator", "moderator", None)

    def run_rebuttal(self) -> Generator[tuple[str, str, str], None, None]:
        """
        Run rebuttal phase where elders respond to challenges.

        Yields: (speaker_name, speaker_type, chunk)
        """
        self.current_phase = DebatePhase.REBUTTAL

        # Moderator frames the rebuttal
        yield ("Moderator", "moderator", "")
        frame_prompt = """Summarize the key points of contention that have emerged.
Then invite the debaters to give their rebuttals, focusing on the strongest challenges to their positions."""

        for chunk in self._call_moderator(frame_prompt):
            yield ("Moderator", "moderator", chunk)
        yield ("Moderator", "moderator", None)

        for elder in self.elders:
            yield (elder.name, "elder", "")

            instruction = f"""Give your rebuttal.

In 2-3 paragraphs:
1. Address the strongest challenge that was raised against your position
2. Reinforce your argument with additional reasoning or examples
3. Point out any weaknesses in the other positions that haven't been addressed

This is your chance to defend your view and strengthen your case."""

            for chunk in self._call_elder(elder, instruction):
                yield (elder.name, "elder", chunk)
            yield (elder.name, "elder", None)

    def _nominations_available(self) -> bool:
        """Check if nominations are still allowed."""
        return self.allow_nominations and self.nomination_count < self.max_nominations

    def _handle_nomination(
        self, elder: Elder, response_text: str
    ) -> tuple[str, Elder | None]:
        """Check for and handle a nomination in an elder's response.

        Returns (cleaned_response, guest_elder_or_none).
        """
        if not self._nominations_available():
            return response_text, None

        nomination = parse_nomination(response_text)
        if not nomination:
            return response_text, None

        name, expertise = nomination
        cleaned = strip_nomination_tag(response_text)
        guest = create_nominated_elder(
            name=name,
            expertise=expertise,
            topic=self.topic,
            nominated_by=elder.name,
        )
        self.nomination_count += 1
        self.guest_elders.append(guest)
        return cleaned, guest

    def run_free_debate(self, exchanges: int = 3) -> Generator[tuple[str, str, str], None, None]:
        """
        Run a free-form debate section with moderator guidance.

        Yields: (speaker_name, speaker_type, chunk)
        Special: ("__nomination__", "nomination", guest_elder) signals a new guest.
        """
        self.current_phase = DebatePhase.FREE_DEBATE

        yield ("Moderator", "moderator", "")
        intro_prompt = """We now move to open debate.
Identify the most important unresolved question and direct it to the debater best positioned to address it."""

        for chunk in self._call_moderator(intro_prompt):
            yield ("Moderator", "moderator", chunk)
        yield ("Moderator", "moderator", None)

        guest_queue: list[Elder] = []

        for exchange in range(exchanges):
            # Pick an elder to respond (rotate through original elders)
            elder = self.elders[exchange % len(self.elders)]

            yield (elder.name, "elder", "")

            nomination_suffix = ""
            if self._nominations_available():
                nomination_suffix = NOMINATION_INSTRUCTION

            instruction = """Respond to the moderator's question or the previous speaker's point.
Be concise but substantive. Then either:
- Pose a follow-up question to another debater, OR
- Make a new argument that advances your position

Keep the debate moving forward.""" + nomination_suffix

            full_response = []
            for chunk in self._call_elder(elder, instruction):
                full_response.append(chunk)
                yield (elder.name, "elder", chunk)

            response_text = "".join(full_response)

            # Check for nomination
            cleaned, guest = self._handle_nomination(elder, response_text)
            if guest:
                # Fix the transcript entry (replace last one with cleaned text)
                if self.transcript and self.transcript[-1]["speaker"] == elder.name:
                    self.transcript[-1]["content"] = cleaned
                guest_queue.append(guest)
                yield ("__nomination__", "nomination", guest)

            yield (elder.name, "elder", None)

            # Moderator keeps things on track every 2 exchanges
            if exchange % 2 == 1 and exchange < exchanges - 1:
                yield ("Moderator", "moderator", "")
                guide_prompt = """Briefly redirect the debate if needed.
Either: probe deeper on a point, highlight an overlooked disagreement, or ask a debater to respond to something they've avoided."""

                for chunk in self._call_moderator(guide_prompt):
                    yield ("Moderator", "moderator", chunk)
                yield ("Moderator", "moderator", None)

        # Let queued guests speak
        for guest in guest_queue:
            yield (guest.name, "elder", "")

            guest_instruction = (
                f"You are {guest.name}, a guest expert invited to this debate. "
                "Consider the arguments made so far and offer your unique perspective. "
                "Be direct and substantive. Engage with the points that have been raised."
            )

            for chunk in self._call_elder(guest, guest_instruction):
                yield (guest.name, "elder", chunk)
            yield (guest.name, "elder", None)

    def run_closing_statements(self) -> Generator[tuple[str, str, str], None, None]:
        """
        Run closing statements.

        Yields: (speaker_name, speaker_type, chunk)
        """
        self.current_phase = DebatePhase.CLOSING

        yield ("Moderator", "moderator", "")
        close_prompt = """Briefly summarize the key points of agreement and disagreement that emerged.
Then invite each debater to give their closing statement."""

        for chunk in self._call_moderator(close_prompt):
            yield ("Moderator", "moderator", chunk)
        yield ("Moderator", "moderator", None)

        # Include guest elders in closing statements
        all_speakers = list(self.elders) + self.guest_elders

        for elder in all_speakers:
            yield (elder.name, "elder", "")

            is_guest = elder in self.guest_elders
            if is_guest:
                instruction = f"""Give a brief closing statement on: {self.topic}

As a guest expert, summarize your key contribution to this debate in 1-2 paragraphs.
What perspective did you bring that was missing? What is your takeaway?"""
            else:
                instruction = f"""Give your closing statement on: {self.topic}

In 1-2 paragraphs:
1. Restate your core position
2. Acknowledge the strongest point made by an opponent
3. Explain why your view should still prevail
4. End with your key takeaway for the audience

Be memorable and persuasive."""

            for chunk in self._call_elder(elder, instruction):
                yield (elder.name, "elder", chunk)
            yield (elder.name, "elder", None)

        # Moderator closes
        yield ("Moderator", "moderator", "")
        final_prompt = """Thank the debaters and give a brief (2-3 sentence) closing that highlights what made this debate valuable, without declaring a winner."""

        for chunk in self._call_moderator(final_prompt):
            yield ("Moderator", "moderator", chunk)
        yield ("Moderator", "moderator", None)

    def run_full_debate(
        self,
        cross_exam_rounds: int = 2,
        free_debate_exchanges: int = 4
    ) -> Generator[tuple[str, str, str, str], None, None]:
        """
        Run a complete structured debate.

        Yields: (phase, speaker_name, speaker_type, chunk)
        """
        # Opening
        for speaker, speaker_type, chunk in self.run_opening_statements():
            yield (DebatePhase.OPENING.value, speaker, speaker_type, chunk)

        # Cross-examination
        for speaker, speaker_type, chunk in self.run_cross_examination(rounds=cross_exam_rounds):
            yield (DebatePhase.CROSS_EXAMINATION.value, speaker, speaker_type, chunk)

        # Rebuttal
        for speaker, speaker_type, chunk in self.run_rebuttal():
            yield (DebatePhase.REBUTTAL.value, speaker, speaker_type, chunk)

        # Free debate
        for speaker, speaker_type, chunk in self.run_free_debate(exchanges=free_debate_exchanges):
            yield (DebatePhase.FREE_DEBATE.value, speaker, speaker_type, chunk)

        # Closing
        for speaker, speaker_type, chunk in self.run_closing_statements():
            yield (DebatePhase.CLOSING.value, speaker, speaker_type, chunk)

    def get_transcript(self) -> list[dict]:
        """Get the full transcript."""
        return self.transcript
