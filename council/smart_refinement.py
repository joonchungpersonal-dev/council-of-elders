"""
Smart Problem Refinement Engine

An intelligent refinement system that:
1. Analyzes the user's problem to identify the most relevant elders
2. Selects 2-4 elders whose perspectives are most valuable
3. Uses a two-phase approach: categorization then targeted questioning
4. Produces a focused, high-quality problem definition

This replaces the brute-force approach where every elder asks questions.
"""

from dataclasses import dataclass, field
from typing import Generator, Callable

from council.elders import Elder, ElderRegistry
from council.llm import chat


@dataclass
class RefinedProblem:
    """The output of the refinement process."""
    original_topic: str
    refined_topic: str
    key_aspects: list[str]
    user_context: dict[str, str]
    areas_of_tension: list[str]
    debate_framing: str
    selected_elders: list[str]  # IDs of elders chosen for the debate


# Elder expertise categories for intelligent selection
ELDER_EXPERTISE = {
    "munger": {
        "domains": ["investing", "business", "decision-making", "mental models", "psychology", "avoiding mistakes"],
        "style": "analytical, systematic, contrarian",
    },
    "buffett": {
        "domains": ["investing", "business", "long-term thinking", "value", "patience", "wealth"],
        "style": "folksy wisdom, long-term focus",
    },
    "aurelius": {
        "domains": ["emotions", "adversity", "control", "duty", "death", "acceptance", "virtue"],
        "style": "stoic, reflective, philosophical",
    },
    "franklin": {
        "domains": ["productivity", "self-improvement", "diplomacy", "practical problems", "habits", "relationships"],
        "style": "practical, experimental, balanced",
    },
    "bruce_lee": {
        "domains": ["self-expression", "adaptability", "limitations", "mastery", "philosophy", "identity"],
        "style": "direct, energetic, transformative",
    },
    "musashi": {
        "domains": ["strategy", "discipline", "combat", "mastery", "timing", "focus"],
        "style": "austere, warrior, focused",
    },
    "sun_tzu": {
        "domains": ["strategy", "competition", "conflict", "positioning", "leadership", "planning"],
        "style": "strategic, indirect, calculating",
    },
    "buddha": {
        "domains": ["suffering", "attachment", "peace", "mindfulness", "desires", "liberation"],
        "style": "gentle, paradoxical, liberating",
    },
    "branden": {
        "domains": ["self-esteem", "confidence", "psychology", "relationships", "authenticity", "self-worth"],
        "style": "therapeutic, empowering, direct",
    },
    "peterson": {
        "domains": ["meaning", "responsibility", "chaos", "order", "truth", "suffering", "psychology"],
        "style": "intense, challenging, archetypal",
    },
    "clear": {
        "domains": ["habits", "behavior change", "systems", "productivity", "consistency", "improvement"],
        "style": "practical, evidence-based, systematic",
    },
    "greene": {
        "domains": ["power", "strategy", "human nature", "seduction", "mastery", "social dynamics"],
        "style": "historical, strategic, unflinching",
    },
    "naval": {
        "domains": ["wealth", "happiness", "startups", "leverage", "philosophy", "freedom"],
        "style": "aphoristic, first-principles, modern"],
    },
    "rubin": {
        "domains": ["creativity", "art", "process", "intuition", "presence", "inspiration"],
        "style": "zen-like, minimalist, observational",
    },
    "oprah": {
        "domains": ["purpose", "authenticity", "transformation", "relationships", "communication", "healing"],
        "style": "warm, direct, empowering",
    },
    "thich": {
        "domains": ["mindfulness", "peace", "presence", "compassion", "breathing", "emotions"],
        "style": "gentle, poetic, practice-oriented",
    },
    "jung": {
        "domains": ["unconscious", "dreams", "archetypes", "shadow", "integration", "meaning"],
        "style": "depth, symbolic, integrative",
    },
    "kinrys": {
        "domains": ["dating", "attraction", "communication", "confidence", "relationships"],
        "style": "practical, insider perspective, direct",
    },
    "noble": {
        "domains": ["attraction", "dating", "confidence", "approach", "relationships"],
        "style": "direct, tactical, empowering",
    },
    "quinn": {
        "domains": ["dating", "connection", "confidence", "communication", "authenticity"],
        "style": "warm, practical, encouraging",
    },
    "ryan": {
        "domains": ["dating", "relationships", "standards", "self-worth", "modern dating"],
        "style": "direct, supportive, boundary-focused",
    },
}


SELECTOR_PROMPT = """You are an expert facilitator for the Council of Elders.

The user wants to explore: "{topic}"

Available elders and their expertise:
{elder_summaries}

Your task:
1. Analyze the user's topic/question
2. Identify which 2-4 elders would provide the MOST VALUABLE and DIVERSE perspectives
3. Explain briefly why each selected elder is relevant

Consider:
- Choose elders whose expertise directly relates to the topic
- Include at least one elder who might offer a contrasting/unexpected viewpoint
- Don't just pick the obvious choices - think about unique angles
- For personal/emotional topics, include psychology-focused elders
- For strategic/career topics, include business/strategy elders
- For existential/meaning topics, include philosophical elders

Respond in this format:
SELECTED: [elder_id_1], [elder_id_2], [elder_id_3]
RATIONALE:
- [elder_id_1]: [1 sentence why]
- [elder_id_2]: [1 sentence why]
- [elder_id_3]: [1 sentence why]
"""


QUESTION_PROMPT = """You are {elder_name}, about to participate in a council debate.

Your expertise: {expertise}
Your communication style: {style}

The user wants to discuss: "{topic}"

{context}

Ask 1-2 FOCUSED clarifying questions that will help you give the best possible advice.
Your questions should:
1. Probe the aspects most relevant to YOUR unique expertise
2. Uncover key context that would change your advice
3. Be specific and actionable (not generic "tell me more")

If the topic is already clear enough, you may say "I have enough context to proceed."

Your questions (be concise):"""


SYNTHESIS_PROMPT = """You are synthesizing a refined problem definition for a Council debate.

Original topic: {original_topic}

Selected elders: {selected_elders}

Questions and answers:
{qa_summary}

Create a refined problem statement:

## Core Question
[1-2 sentences capturing the essential question]

## Key Context
- [3-4 bullet points of important context from the Q&A]

## Debate Focus Areas
- [2-3 specific aspects the elders should address]

## Potential Tensions
- [2-3 areas where elders may disagree]

## Recommended Framing
[1-2 sentences on how to approach the debate]

Be precise and actionable."""


class SmartRefinementEngine:
    """
    Intelligent refinement that selects the best elders for the topic
    and asks targeted questions.
    """

    def __init__(self, initial_topic: str, available_elders: list[Elder] | None = None):
        self.initial_topic = initial_topic
        self.available_elders = available_elders or list(ElderRegistry.list_all())
        self.selected_elder_ids: list[str] = []
        self.selected_elders: list[Elder] = []
        self.questions: dict[str, list[str]] = {}
        self.answers: dict[str, str] = {}
        self.selection_rationale: dict[str, str] = {}
        self.transcript: list[dict] = []

    def _build_elder_summaries(self) -> str:
        """Build a summary of available elders for the selector."""
        summaries = []
        for elder in self.available_elders:
            if elder.id in ELDER_EXPERTISE:
                exp = ELDER_EXPERTISE[elder.id]
                domains = ", ".join(exp["domains"])
                summaries.append(f"- {elder.id} ({elder.name}): {domains} | Style: {exp['style']}")
            else:
                summaries.append(f"- {elder.id} ({elder.name}): General wisdom")
        return "\n".join(summaries)

    def select_elders(self) -> Generator[str, None, list[str]]:
        """
        Use LLM to select the most relevant elders for this topic.
        Yields progress, returns list of elder IDs.
        """
        prompt = SELECTOR_PROMPT.format(
            topic=self.initial_topic,
            elder_summaries=self._build_elder_summaries()
        )

        messages = [{"role": "user", "content": prompt}]
        full_response = []

        for chunk in chat(messages, stream=True):
            full_response.append(chunk)
            yield chunk

        response = "".join(full_response)

        # Parse response
        selected_ids = []
        rationales = {}

        for line in response.split('\n'):
            if line.startswith('SELECTED:'):
                ids_part = line.replace('SELECTED:', '').strip()
                selected_ids = [id.strip() for id in ids_part.split(',')]
            elif line.strip().startswith('-') and ':' in line:
                # Parse rationale
                parts = line.strip().lstrip('- ').split(':', 1)
                if len(parts) == 2:
                    eid = parts[0].strip()
                    rationale = parts[1].strip()
                    rationales[eid] = rationale

        # Validate and store
        valid_ids = []
        for eid in selected_ids:
            elder = ElderRegistry.get(eid)
            if elder:
                valid_ids.append(eid)
                self.selected_elders.append(elder)
                if eid in rationales:
                    self.selection_rationale[eid] = rationales[eid]

        self.selected_elder_ids = valid_ids[:4]  # Max 4 elders
        self.selected_elders = self.selected_elders[:4]

        return self.selected_elder_ids

    def generate_questions(self, elder: Elder, previous_qa: str = "") -> Generator[str, None, str]:
        """Generate clarifying questions from a selected elder."""
        expertise = ELDER_EXPERTISE.get(elder.id, {})
        domains = ", ".join(expertise.get("domains", ["general wisdom"]))
        style = expertise.get("style", "thoughtful")

        context = ""
        if previous_qa:
            context = f"Previous questions and answers:\n{previous_qa}\n"

        prompt = QUESTION_PROMPT.format(
            elder_name=elder.name,
            expertise=domains,
            style=style,
            topic=self.initial_topic,
            context=context
        )

        messages = [{"role": "user", "content": prompt}]
        full_response = []

        for chunk in chat(messages, system=elder.system_prompt, stream=True):
            full_response.append(chunk)
            yield chunk

        response = "".join(full_response)

        # Parse questions
        questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and '?' in line:
                # Clean up numbering
                q = line.lstrip('0123456789.-) ').strip()
                if q and len(q) > 10:
                    questions.append(q)

        self.questions[elder.id] = questions
        self.transcript.append({"speaker": elder.name, "content": response})

        return response

    def record_answer(self, elder_id: str, answer: str):
        """Record user's answer."""
        self.answers[elder_id] = answer
        self.transcript.append({"speaker": "User", "content": answer})

    def get_qa_summary(self) -> str:
        """Get summary of all Q&A."""
        summary = ""
        for elder in self.selected_elders:
            if elder.id in self.questions:
                summary += f"\n### {elder.name}:\n"
                for q in self.questions[elder.id]:
                    summary += f"Q: {q}\n"
                if elder.id in self.answers:
                    summary += f"A: {self.answers[elder.id]}\n"
        return summary

    def synthesize(self) -> Generator[str, None, str]:
        """Synthesize the refined problem."""
        elder_names = ", ".join(e.name for e in self.selected_elders)

        prompt = SYNTHESIS_PROMPT.format(
            original_topic=self.initial_topic,
            selected_elders=elder_names,
            qa_summary=self.get_qa_summary()
        )

        messages = [{"role": "user", "content": prompt}]
        full_response = []

        for chunk in chat(messages, stream=True):
            full_response.append(chunk)
            yield chunk

        return "".join(full_response)

    def parse_synthesis(self, synthesis: str) -> RefinedProblem:
        """Parse synthesis into structured output."""
        refined_topic = self.initial_topic
        key_aspects = []
        tensions = []
        framing = ""

        current_section = None
        for line in synthesis.split('\n'):
            line = line.strip()
            if '## Core Question' in line:
                current_section = 'problem'
            elif '## Key Context' in line:
                current_section = 'aspects'
            elif '## Debate Focus' in line:
                current_section = 'focus'
            elif '## Potential Tensions' in line:
                current_section = 'tensions'
            elif '## Recommended Framing' in line:
                current_section = 'framing'
            elif line and not line.startswith('#'):
                if current_section == 'problem':
                    refined_topic = line
                elif current_section in ('aspects', 'focus') and line.startswith('-'):
                    key_aspects.append(line.lstrip('- '))
                elif current_section == 'tensions' and line.startswith('-'):
                    tensions.append(line.lstrip('- '))
                elif current_section == 'framing':
                    framing += line + " "

        return RefinedProblem(
            original_topic=self.initial_topic,
            refined_topic=refined_topic.strip(),
            key_aspects=key_aspects,
            user_context=self.answers,
            areas_of_tension=tensions,
            debate_framing=framing.strip(),
            selected_elders=self.selected_elder_ids
        )

    def run_refinement(
        self,
        get_user_input: Callable[[str, list[str]], str],
        on_progress: Callable[[str, str, str], None] | None = None
    ) -> RefinedProblem:
        """
        Run the complete smart refinement process.

        Args:
            get_user_input: Callable(elder_name, questions) -> answer
            on_progress: Callable(stage, speaker, content) for streaming

        Returns:
            RefinedProblem
        """
        def emit(stage, speaker, content):
            if on_progress:
                on_progress(stage, speaker, content)

        # Phase 1: Select elders
        emit("selection", "System", "Analyzing your question to select the most relevant advisors...\n")

        selection_text = ""
        for chunk in self.select_elders():
            selection_text += chunk
            emit("selection", "System", chunk)

        emit("selection", "System", f"\n\nSelected {len(self.selected_elders)} elders: " +
             ", ".join(e.name for e in self.selected_elders) + "\n")

        # Phase 2: Each selected elder asks questions
        previous_qa = ""

        for elder in self.selected_elders:
            if elder.id in self.selection_rationale:
                emit("questions", "System",
                     f"\n{elder.name} ({self.selection_rationale[elder.id]}):\n")

            for chunk in self.generate_questions(elder, previous_qa):
                emit("questions", elder.name, chunk)

            # Get user input
            if self.questions.get(elder.id):
                answer = get_user_input(elder.name, self.questions[elder.id])
                if answer and answer.strip():
                    self.record_answer(elder.id, answer)
                    previous_qa += f"\n{elder.name}: {self.questions[elder.id]}\nUser: {answer}\n"
                    emit("answer", "User", answer)

        # Phase 3: Synthesize
        emit("synthesis", "System", "\n\nSynthesizing refined problem definition...\n")

        synthesis_text = ""
        for chunk in self.synthesize():
            synthesis_text += chunk
            emit("synthesis", "Synthesizer", chunk)

        return self.parse_synthesis(synthesis_text)


def quick_refinement(topic: str, max_questions: int = 3) -> Generator[str, None, RefinedProblem]:
    """
    Simplified refinement for when you just want quick clarification.

    Args:
        topic: The user's initial topic
        max_questions: Maximum total questions across all elders

    Yields:
        Progress text

    Returns:
        RefinedProblem
    """
    engine = SmartRefinementEngine(topic)

    # Select elders
    yield "Selecting advisors...\n"
    for chunk in engine.select_elders():
        yield chunk

    yield f"\n\nSelected: {', '.join(e.name for e in engine.selected_elders)}\n"

    # Limit questions per elder
    questions_per_elder = max(1, max_questions // len(engine.selected_elders))

    # In quick mode, we just show what questions would be asked
    yield "\nKey questions to consider:\n"

    for elder in engine.selected_elders[:2]:  # Limit to 2 elders in quick mode
        yield f"\n**{elder.name}**:\n"
        for chunk in engine.generate_questions(elder):
            yield chunk
        yield "\n"

    # Return basic refined problem
    return RefinedProblem(
        original_topic=topic,
        refined_topic=topic,
        key_aspects=[],
        user_context={},
        areas_of_tension=[],
        debate_framing="",
        selected_elders=engine.selected_elder_ids
    )
