"""
Problem Refinement Engine

A structured conversation to clarify and refine the user's question/problem
before the debate begins. Each elder asks clarifying questions from their
unique perspective.

Structure:
1. User states initial topic
2. Each elder asks 0-2 clarifying questions
3. User responds
4. Optional second round of questions
5. Synthesizer summarizes the refined problem
6. User confirms or adjusts
7. Debate begins with well-defined topic
"""

from dataclasses import dataclass, field
from typing import Generator

from council.elders import Elder, ElderRegistry
from council.llm import chat


@dataclass
class RefinedProblem:
    """The output of the refinement process."""
    original_topic: str
    refined_topic: str
    key_aspects: list[str]
    user_context: dict[str, str]  # Elder ID -> user's answer to their questions
    areas_of_tension: list[str]
    debate_framing: str


QUESTION_GENERATOR_PROMPT = """You are {elder_name}, participating in a pre-debate clarification session.

Your philosophical framework:
{framework_summary}

The user wants to discuss: "{topic}"

Your task: Ask 1-2 clarifying questions that would help you understand the problem better
from YOUR unique perspective. Your questions should:

1. Probe the aspects most relevant to your philosophy
2. Help uncover hidden assumptions or context
3. Clarify what the user really wants to understand

{previous_context}

Respond with ONLY your questions (1-2), numbered. Be concise but thoughtful.
If the topic is already clear enough for your purposes, you may ask just one question
or state "I have sufficient clarity to proceed."

Questions:"""


FRAMEWORK_SUMMARIES = {
    "munger": "Mental models, inversion, incentives, circle of competence, avoiding stupidity",
    "buffett": "Long-term value, margin of safety, understanding what you own, temperament over intellect",
    "aurelius": "Stoicism, what is within your control, virtue, accepting fate, present moment",
    "franklin": "Practical wisdom, systematic self-improvement, finding win-win solutions, experimentation",
    "bruce_lee": "Adaptation, breaking limitations, honest self-expression, being like water",
    "musashi": "Strategy, discipline, the Way, perceiving what cannot be seen, timing",
    "sun_tzu": "Strategic positioning, knowing yourself and your enemy, winning without fighting",
    "buddha": "Suffering and its causes, attachment, impermanence, the middle way, mindfulness",
    "branden": "Self-esteem, living consciously, self-responsibility, personal integrity",
    "peterson": "Meaning through responsibility, order and chaos, confronting fears, telling the truth",
}


SYNTHESIZER_PROMPT = """You are a skilled facilitator helping to synthesize a problem definition.

Original topic: {original_topic}

Clarifying questions asked and user's responses:
{qa_summary}

Your task: Create a refined problem statement that captures:
1. The core question/issue (1-2 sentences)
2. Key aspects that emerged from clarification (3-5 bullet points)
3. Potential areas of tension or disagreement between perspectives (2-3 points)
4. A suggested framing for the debate (1-2 sentences)

Be concise and precise. Format your response as:

## Refined Problem
[The core question restated with more precision]

## Key Aspects
- [Aspect 1]
- [Aspect 2]
- [Aspect 3]

## Likely Areas of Tension
- [Tension 1]
- [Tension 2]

## Suggested Debate Framing
[How the debate should be framed given what we learned]"""


class RefinementEngine:
    """Engine for refining problems through elder clarification."""

    def __init__(self, elders: list[Elder], initial_topic: str):
        self.elders = elders
        self.initial_topic = initial_topic
        self.questions: dict[str, list[str]] = {}  # elder_id -> list of questions
        self.answers: dict[str, str] = {}  # elder_id -> user's consolidated answer
        self.transcript: list[dict] = []

    def _add_to_transcript(self, speaker: str, role: str, content: str):
        self.transcript.append({
            "speaker": speaker,
            "role": role,
            "content": content
        })

    def generate_questions(self, elder: Elder, previous_qa: str = "") -> Generator[str, None, str]:
        """
        Generate clarifying questions from an elder.

        Yields chunks, returns full response.
        """
        previous_context = ""
        if previous_qa:
            previous_context = f"\nPrevious questions and answers in this session:\n{previous_qa}\n"

        prompt = QUESTION_GENERATOR_PROMPT.format(
            elder_name=elder.name,
            framework_summary=FRAMEWORK_SUMMARIES.get(elder.id, ""),
            topic=self.initial_topic,
            previous_context=previous_context
        )

        messages = [{"role": "user", "content": prompt}]

        full_response = []
        for chunk in chat(messages, system=elder.system_prompt, stream=True):
            full_response.append(chunk)
            yield chunk

        response = "".join(full_response)
        self._add_to_transcript(elder.name, "elder", response)

        # Parse questions
        questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering/bullets
                q = line.lstrip('0123456789.-) ').strip()
                if q and '?' in q:
                    questions.append(q)

        self.questions[elder.id] = questions
        return response

    def record_answer(self, elder_id: str, answer: str):
        """Record user's answer to an elder's questions."""
        self.answers[elder_id] = answer
        elder = ElderRegistry.get(elder_id)
        elder_name = elder.name if elder else elder_id
        self._add_to_transcript("User", "user", f"[In response to {elder_name}] {answer}")

    def get_qa_summary(self) -> str:
        """Get a summary of all questions and answers."""
        summary = ""
        for elder in self.elders:
            if elder.id in self.questions:
                summary += f"\n### {elder.name}'s Questions:\n"
                for i, q in enumerate(self.questions[elder.id], 1):
                    summary += f"{i}. {q}\n"
                if elder.id in self.answers:
                    summary += f"\nUser's response: {self.answers[elder.id]}\n"
        return summary

    def synthesize(self) -> Generator[str, None, str]:
        """
        Synthesize the refined problem from all Q&A.

        Yields chunks, returns full response.
        """
        qa_summary = self.get_qa_summary()

        prompt = SYNTHESIZER_PROMPT.format(
            original_topic=self.initial_topic,
            qa_summary=qa_summary
        )

        messages = [{"role": "user", "content": prompt}]

        full_response = []
        for chunk in chat(messages, stream=True):
            full_response.append(chunk)
            yield chunk

        response = "".join(full_response)
        self._add_to_transcript("Synthesizer", "system", response)
        return response

    def parse_synthesis(self, synthesis: str) -> RefinedProblem:
        """Parse the synthesis into a structured RefinedProblem."""
        # Extract sections (basic parsing)
        refined_topic = self.initial_topic
        key_aspects = []
        tensions = []
        framing = ""

        lines = synthesis.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if '## Refined Problem' in line:
                current_section = 'problem'
            elif '## Key Aspects' in line:
                current_section = 'aspects'
            elif '## Likely Areas of Tension' in line or '## Areas of Tension' in line:
                current_section = 'tensions'
            elif '## Suggested Debate Framing' in line or '## Debate Framing' in line:
                current_section = 'framing'
            elif line:
                if current_section == 'problem' and not line.startswith('#'):
                    refined_topic = line
                elif current_section == 'aspects' and line.startswith('-'):
                    key_aspects.append(line.lstrip('- '))
                elif current_section == 'tensions' and line.startswith('-'):
                    tensions.append(line.lstrip('- '))
                elif current_section == 'framing' and not line.startswith('#'):
                    framing += line + " "

        return RefinedProblem(
            original_topic=self.initial_topic,
            refined_topic=refined_topic.strip(),
            key_aspects=key_aspects,
            user_context=self.answers,
            areas_of_tension=tensions,
            debate_framing=framing.strip()
        )

    def run_full_refinement(self, get_user_input) -> Generator[tuple[str, str, str], None, RefinedProblem]:
        """
        Run the complete refinement process.

        Args:
            get_user_input: Callable that takes (elder_name, questions) and returns user's answer

        Yields:
            (stage, speaker, content) tuples

        Returns:
            RefinedProblem
        """
        # Stage 1: Each elder asks questions
        yield ("intro", "System", "Let's clarify your question before the debate begins.\n")

        previous_qa = ""

        for elder in self.elders:
            yield ("questions", elder.name, "")  # Signal start

            # Generate questions
            full_response = ""
            for chunk in self.generate_questions(elder, previous_qa):
                yield ("questions", elder.name, chunk)
                full_response += chunk

            yield ("questions", elder.name, None)  # Signal end

            # Get user input (this will be handled by the UI)
            if self.questions.get(elder.id):
                answer = get_user_input(elder.name, self.questions[elder.id])
                if answer:
                    self.record_answer(elder.id, answer)
                    previous_qa += f"\n{elder.name} asked: {self.questions[elder.id]}\nUser answered: {answer}\n"
                    yield ("answer", "User", answer)

        # Stage 2: Synthesize
        yield ("synthesis", "Synthesizer", "")

        synthesis_text = ""
        for chunk in self.synthesize():
            yield ("synthesis", "Synthesizer", chunk)
            synthesis_text += chunk

        yield ("synthesis", "Synthesizer", None)

        # Parse and return
        refined = self.parse_synthesis(synthesis_text)
        return refined
