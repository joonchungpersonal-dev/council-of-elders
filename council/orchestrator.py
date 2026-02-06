"""Orchestrator for managing conversations with elders."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

from council.elders import Elder, ElderRegistry
from council.llm import chat
from council.config import get_knowledge_dir
from council.knowledge.sources import EMBEDDED_WISDOM


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""

    role: str  # 'user' or 'elder'
    elder_id: str | None  # None for user messages
    content: str


@dataclass
class Conversation:
    """A conversation with one or more elders."""

    turns: list[ConversationTurn] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        self.turns.append(ConversationTurn(role="user", elder_id=None, content=content))

    def add_elder_response(self, elder_id: str, content: str) -> None:
        """Add an elder response to the conversation."""
        self.turns.append(ConversationTurn(role="elder", elder_id=elder_id, content=content))

    def to_messages(self, for_elder: str | None = None) -> list[dict]:
        """Convert conversation to message format for LLM."""
        messages = []
        for turn in self.turns:
            if turn.role == "user":
                messages.append({"role": "user", "content": turn.content})
            elif turn.role == "elder":
                # For the current elder, their messages are "assistant"
                # For other elders, include them as context in user message
                if turn.elder_id == for_elder:
                    messages.append({"role": "assistant", "content": turn.content})
                else:
                    elder = ElderRegistry.get(turn.elder_id)
                    elder_name = elder.name if elder else turn.elder_id
                    messages.append({
                        "role": "user",
                        "content": f"[{elder_name} said]: {turn.content}"
                    })
        return messages


def get_elder_knowledge(elder_id: str, query: str = "", max_chars: int = 4000) -> str:
    """
    Get QUERY-RELEVANT knowledge for an elder using semantic search.

    Args:
        elder_id: The elder ID
        query: The user's query (for semantic search)
        max_chars: Maximum characters to include

    Returns:
        Knowledge context string
    """
    knowledge_parts = []

    # 1. Always include embedded wisdom (key quotes) - these are curated
    if elder_id in EMBEDDED_WISDOM:
        knowledge_parts.append(EMBEDDED_WISDOM[elder_id])

    # 2. Use ChromaDB for semantic search of additional knowledge (if available)
    if query:
        try:
            from council.knowledge.store import get_knowledge_store

            store = get_knowledge_store()
            context = store.get_context(elder_id, query, max_tokens=2000)
            if context:
                knowledge_parts.append(context)
        except ImportError:
            # ChromaDB not installed, fall back to file-based approach
            pass
        except Exception:
            # ChromaDB query failed, fall back to file-based approach
            pass

    # 3. Fallback: If no semantic results, check downloaded knowledge files
    if len(knowledge_parts) <= 1:  # Only embedded wisdom so far
        knowledge_dir = get_knowledge_dir() / elder_id
        if knowledge_dir.exists():
            for filepath in sorted(knowledge_dir.glob("**/*.txt"))[:5]:  # Limit files
                try:
                    content = filepath.read_text(encoding="utf-8")
                    # Take first portion of each file
                    knowledge_parts.append(content[:2000])
                except Exception:
                    pass

    if not knowledge_parts:
        return ""

    combined = "\n\n---\n\n".join(knowledge_parts)

    # Truncate if too long
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[... additional knowledge available ...]"

    return f"\n\n## Your Writings and Teachings (for reference)\n\n{combined}"


class Orchestrator:
    """Manages conversations with the council of elders."""

    def __init__(self, use_knowledge: bool = True):
        self.conversation = Conversation()
        self.use_knowledge = use_knowledge

    def reset_conversation(self) -> None:
        """Start a fresh conversation."""
        self.conversation = Conversation()

    def ask_elder(
        self,
        elder_id: str,
        question: str,
        stream: bool = True,
    ) -> Generator[str, None, None] | str:
        """
        Ask a single elder a question.

        Args:
            elder_id: The ID of the elder to ask
            question: The user's question
            stream: Whether to stream the response

        Yields/Returns:
            Response chunks if streaming, full response if not
        """
        elder = ElderRegistry.get(elder_id)
        if not elder:
            raise ValueError(f"Elder not found: {elder_id}")

        self.conversation.add_user_message(question)
        messages = self.conversation.to_messages(for_elder=elder_id)

        # Build system prompt with knowledge context
        system_prompt = elder.system_prompt
        if self.use_knowledge:
            knowledge_context = get_elder_knowledge(elder_id, query=question)
            if knowledge_context:
                system_prompt = system_prompt + knowledge_context

        if stream:
            full_response = []
            for chunk in chat(messages, system=system_prompt, stream=True):
                full_response.append(chunk)
                yield chunk
            self.conversation.add_elder_response(elder_id, "".join(full_response))
        else:
            response = chat(messages, system=system_prompt, stream=False)
            self.conversation.add_elder_response(elder_id, response)
            return response

    def roundtable(
        self,
        elder_ids: list[str],
        question: str,
        turns: int = 1,
        stream: bool = True,
    ) -> Generator[tuple[str, str], None, None]:
        """
        Conduct a roundtable discussion with multiple elders.

        Args:
            elder_ids: List of elder IDs to participate
            question: The initial question or topic
            turns: Number of rounds each elder speaks
            stream: Whether to stream responses

        Yields:
            Tuples of (elder_id, response_chunk)
        """
        # Validate all elders exist
        elders = []
        for elder_id in elder_ids:
            elder = ElderRegistry.get(elder_id)
            if not elder:
                raise ValueError(f"Elder not found: {elder_id}")
            elders.append(elder)

        self.conversation.add_user_message(question)

        for turn in range(turns):
            for elder in elders:
                # Build context prompt that includes other elders' responses
                if turn == 0 and elder == elders[0]:
                    # First elder, first turn - just respond to the question
                    context_note = ""
                else:
                    # Subsequent - acknowledge the ongoing discussion
                    context_note = (
                        "\n\n[Note: You are participating in a roundtable discussion. "
                        "Consider what the other council members have said and build upon, "
                        "contrast with, or complement their perspectives. "
                        "Keep your response focused and avoid repeating what others have said.]"
                    )

                messages = self.conversation.to_messages(for_elder=elder.id)

                full_response = []
                system_prompt = elder.system_prompt + context_note

                for chunk in chat(messages, system=system_prompt, stream=True):
                    full_response.append(chunk)
                    yield (elder.id, chunk)

                self.conversation.add_elder_response(elder.id, "".join(full_response))

                # Signal end of this elder's turn
                yield (elder.id, None)


    def debate_intake_questions(
        self,
        elder_ids: list[str],
        question: str,
        num_questions: int = 3,
        stream: bool = True,
    ) -> Generator[tuple[str, str], None, None]:
        """
        Have elders debate what clarifying questions to ask before giving advice.

        Args:
            elder_ids: List of elder IDs to participate in the debate
            question: The user's initial question
            num_questions: Target number of clarifying questions to generate
            stream: Whether to stream responses

        Yields:
            Tuples of (elder_id, response_chunk) - final elder is "synthesis"
        """
        # Validate elders
        elders = []
        for elder_id in elder_ids:
            elder = ElderRegistry.get(elder_id)
            if not elder:
                raise ValueError(f"Elder not found: {elder_id}")
            elders.append(elder)

        # Special system prompt for intake question debate
        intake_debate_prompt = """
You are participating in a preliminary council discussion. Before giving advice on the user's question, the council is debating what CLARIFYING QUESTIONS would help you all give better guidance.

Your task in this round:
1. Consider what information is MISSING from the user's question
2. Think about what YOUR unique perspective needs to know
3. Propose 1-2 specific clarifying questions that would help
4. Briefly explain WHY each question matters from your viewpoint
5. If other council members have spoken, you may agree with their questions, disagree, or propose alternatives

Be concise. Focus on questions that will genuinely improve the advice you can give.
Format your questions clearly, like:
- **Question 1**: [Your question here]
  *Why this matters*: [Brief explanation]
"""

        synthesis_prompt = f"""
You are synthesizing the council's debate about clarifying questions.

Review what each elder proposed and create a FINAL LIST of exactly {num_questions} clarifying questions to ask the user.

Choose the most valuable questions that:
1. Cover different important dimensions of the problem
2. Will genuinely help the council give better advice
3. Are specific and answerable

Format your response EXACTLY like this:
---
Based on the council's deliberation, we would like to understand your situation better:

1. [First question]

2. [Second question]

3. [Third question]
---

Be direct and clear. These questions will be shown to the user.
"""

        # Store the original question
        self.conversation.add_user_message(
            f"[INTAKE PHASE] The user is seeking counsel on: \"{question}\"\n\n"
            f"Before we advise, let us discuss what clarifying questions would help us give better guidance."
        )

        # Each elder proposes questions
        for i, elder in enumerate(elders):
            if i > 0:
                context_note = (
                    "\n\n[Consider what your fellow council members have proposed. "
                    "Build on good ideas, offer alternatives where you disagree, "
                    "and add questions from your unique perspective.]"
                )
            else:
                context_note = ""

            messages = self.conversation.to_messages(for_elder=elder.id)
            system_prompt = elder.system_prompt + intake_debate_prompt + context_note

            full_response = []
            for chunk in chat(messages, system=system_prompt, stream=True):
                full_response.append(chunk)
                yield (elder.id, chunk)

            self.conversation.add_elder_response(elder.id, "".join(full_response))
            yield (elder.id, None)

        # Synthesis phase - use the first elder to synthesize
        synthesizer = elders[0]
        self.conversation.add_user_message(
            "[SYNTHESIS] Now synthesize the council's proposals into a final list of clarifying questions."
        )

        messages = self.conversation.to_messages(for_elder=synthesizer.id)

        full_response = []
        for chunk in chat(messages, system=synthesis_prompt, stream=True):
            full_response.append(chunk)
            yield ("synthesis", chunk)

        self.conversation.add_elder_response("synthesis", "".join(full_response))
        yield ("synthesis", None)


def get_orchestrator() -> Orchestrator:
    """Get a new orchestrator instance."""
    return Orchestrator()
