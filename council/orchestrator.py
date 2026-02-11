"""Orchestrator for managing conversations with elders."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

from council.elders import Elder, ElderRegistry
from council.llm import chat
from council.config import get_knowledge_dir, get_config_value
from council.knowledge.sources import EMBEDDED_WISDOM
from council.nomination import (
    NOMINATION_INSTRUCTION,
    parse_nomination,
    strip_nomination_tag,
    create_nominated_elder,
)


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""

    role: str  # 'user' or 'elder'
    elder_id: str | None  # None for user messages
    content: str
    elder_name: str | None = None  # For nominated elders not in the registry


@dataclass
class Conversation:
    """A conversation with one or more elders."""

    turns: list[ConversationTurn] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        self.turns.append(ConversationTurn(role="user", elder_id=None, content=content))

    def add_elder_response(self, elder_id: str, content: str, elder_name: str | None = None) -> None:
        """Add an elder response to the conversation."""
        self.turns.append(ConversationTurn(role="elder", elder_id=elder_id, content=content, elder_name=elder_name))

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
                    name = elder.name if elder else (turn.elder_name or turn.elder_id)
                    messages.append({
                        "role": "user",
                        "content": f"[{name} said]: {turn.content}"
                    })
        return messages


def _get_source_confidence(metadata: dict) -> float:
    """Derive a confidence weight from ChromaDB result metadata.

    Returns a float between 0.0 and 1.0.
    """
    source_type = metadata.get("type", "")
    vetting_confidence = metadata.get("vetting_confidence")
    audit_passed = metadata.get("audit_passed")
    quality_score = metadata.get("quality_score")

    # User-uploaded source material
    if vetting_confidence is not None:
        try:
            conf = int(vetting_confidence)
        except (ValueError, TypeError):
            conf = 50
        if conf >= 70:
            return 0.9  # Verified user source
        return 0.5  # Unvetted / low-confidence

    # YouTube transcripts
    if source_type == "youtube":
        if audit_passed is not None:
            passed = str(audit_passed).lower() in ("true", "1")
            if passed:
                return 0.8  # Audit passed
            return 0.3  # Audit failed
        return 0.7  # Default YouTube (no audit data)

    # Default for other types (e.g. Kindle books, letters)
    return 0.7


def get_elder_knowledge(elder_id: str, query: str = "", max_chars: int = 4000) -> str:
    """
    Get QUERY-RELEVANT knowledge for an elder using confidence-weighted retrieval.

    Higher-confidence sources are prioritized. Low-confidence material is
    truncated to prevent unreliable content from dominating the context.

    Args:
        elder_id: The elder ID
        query: The user's query (for semantic search)
        max_chars: Maximum characters to include

    Returns:
        Knowledge context string
    """
    # list of (confidence, text) tuples
    knowledge_parts: list[tuple[float, str]] = []

    # 1. Always include embedded wisdom (key quotes) — curated, full confidence
    if elder_id in EMBEDDED_WISDOM:
        knowledge_parts.append((1.0, EMBEDDED_WISDOM[elder_id]))

    # 2. Use ChromaDB for semantic search with confidence metadata
    if query:
        try:
            from council.knowledge.store import get_knowledge_store

            store = get_knowledge_store()
            results = store.query(elder_id, query, n_results=8)
            for result in results:
                content = result["content"]
                metadata = result.get("metadata", {})
                confidence = _get_source_confidence(metadata)
                knowledge_parts.append((confidence, content))
        except ImportError:
            pass
        except Exception:
            pass

    # 3. Fallback: If no semantic results, check downloaded knowledge files
    if len(knowledge_parts) <= 1:  # Only embedded wisdom so far
        knowledge_dir = get_knowledge_dir() / elder_id
        if knowledge_dir.exists():
            for filepath in sorted(knowledge_dir.glob("**/*.txt"))[:5]:
                try:
                    content = filepath.read_text(encoding="utf-8")
                    # Heuristic confidence from directory name
                    parts = filepath.parts
                    if "sources" in parts:
                        confidence = 0.5  # Unvetted user uploads
                    elif "youtube" in parts:
                        confidence = 0.7  # Default YouTube
                    else:
                        confidence = 0.7  # Other knowledge files
                    knowledge_parts.append((confidence, content[:2000]))
                except Exception:
                    pass

    if not knowledge_parts:
        return ""

    # Sort by confidence descending
    knowledge_parts.sort(key=lambda x: x[0], reverse=True)

    # Apply truncation limits by confidence tier
    final_parts: list[str] = []
    total_chars = 0

    for confidence, text in knowledge_parts:
        if total_chars >= max_chars:
            break

        # Apply per-item char limits based on confidence
        if confidence < 0.5:
            item_limit = 500
        elif confidence < 0.7:
            item_limit = 1500
        else:
            item_limit = max_chars  # No per-item limit for high-confidence

        truncated = text[:item_limit]
        remaining = max_chars - total_chars
        if len(truncated) > remaining:
            truncated = truncated[:remaining]

        final_parts.append(truncated)
        total_chars += len(truncated)

    combined = "\n\n---\n\n".join(final_parts)

    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[... additional knowledge available ...]"

    return f"\n\n## Your Writings and Teachings (for reference)\n\n{combined}"


def _get_tension_prompt(tension: int, role: str = "elder") -> str:
    """
    Generate a discussion-style prompt modifier based on dialectic tension (0-100).

    Args:
        tension: 0 (collaborative) to 100 (debate)
        role: "elder" or "moderator"
    """
    if role == "moderator":
        if tension <= 25:
            return (
                "\n\nDiscussion style: Encourage panelists to build on each other. "
                "Highlight areas of consensus and shared insight."
            )
        elif tension <= 50:
            return (
                "\n\nDiscussion style: Balance consensus with gentle probing. "
                "Encourage panelists to both agree and offer constructive alternatives."
            )
        elif tension <= 75:
            return (
                "\n\nDiscussion style: Encourage panelists to challenge each other. "
                "Probe where they're being too agreeable or glossing over differences."
            )
        else:
            return (
                "\n\nDiscussion style: Push for vigorous debate. Encourage panelists to "
                "take strong positions and directly challenge each other's reasoning. "
                "The questioner benefits most when ideas are stress-tested."
            )
    else:
        if tension <= 25:
            return (
                "\n\nIn this discussion, prioritize building on your fellow panelists' ideas. "
                "Look for areas of agreement and synthesis. When you have a different view, "
                "frame it as an addition rather than a contradiction."
            )
        elif tension <= 50:
            return (
                "\n\nIn this discussion, balance agreement with gentle pushback. "
                "Affirm strong ideas, but don't shy away from noting where you see "
                "things differently. Frame disagreements constructively."
            )
        elif tension <= 75:
            return (
                "\n\nIn this discussion, actively probe for weaknesses in other panelists' "
                "arguments. Play devil's advocate when you see assumptions going unchallenged. "
                "Be direct and intellectually rigorous."
            )
        else:
            return (
                "\n\nIn this discussion, take strong contrarian positions. Challenge every "
                "major claim. Point out logical flaws, missing evidence, and alternative "
                "interpretations. The questioner benefits most when ideas are stress-tested "
                "to their limits. Be sharp but not rude."
            )


import re as _re
from random import shuffle as _shuffle

_ABBREV_RE = _re.compile(
    r'\b(?:Dr|Mr|Mrs|Ms|Prof|Jr|Sr|vs|etc|i\.e|e\.g)\.',
    _re.IGNORECASE,
)

_HONORIFIC_RE = _re.compile(
    r'\b(?:Mr|Mrs|Ms|Dr|Prof|Sir|Saint|St|Lord|Lady)\b\.?\s*',
    _re.IGNORECASE,
)


def _count_sentences(text: str) -> int:
    """Count sentences using a heuristic that filters common abbreviations."""
    cleaned = _ABBREV_RE.sub('ABBR', text)
    return len(_re.findall(r'[.!?](?:\s|$)', cleaned))


def _clean_name(name_str: str) -> str:
    """Strip honorifics and punctuation from a name for fuzzy matching."""
    cleaned = _HONORIFIC_RE.sub('', name_str)
    cleaned = _re.sub(r'[.,;:!?\'"()]+', '', cleaned).strip()
    return cleaned or name_str.strip()


def _resolve_elder_name(name_str: str, name_to_id: dict[str, str]) -> str | None:
    """Resolve a (possibly noisy) name string to an elder ID.

    Tries, in order: exact full-name, last-name, first-name, substring, and
    word-overlap matching. Returns None if no unambiguous match is found.
    """
    name_lower = _clean_name(name_str).lower()
    if not name_lower:
        return None

    # 1. Exact full-name match
    if name_lower in name_to_id:
        return name_to_id[name_lower]
    # 2. Exact last-name match (unambiguous only)
    matches = [eid for c, eid in name_to_id.items()
               if c.split()[-1] == name_lower.split()[-1]]
    if len(matches) == 1:
        return matches[0]
    # 3. First-name match (unambiguous only)
    matches = [eid for c, eid in name_to_id.items()
               if c.split()[0] == name_lower.split()[0]]
    if len(matches) == 1:
        return matches[0]
    # 4. Substring match
    matches = [eid for c, eid in name_to_id.items()
               if name_lower in c or c in name_lower]
    if len(matches) == 1:
        return matches[0]
    # 5. Any word overlap
    query_words = set(name_lower.split())
    matches = [eid for c, eid in name_to_id.items()
               if query_words & set(c.split())]
    if len(matches) == 1:
        return matches[0]
    return None


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
        allow_nominations: bool | None = None,
        max_nominations: int | None = None,
    ) -> Generator[tuple[str, str], None, None]:
        """
        Conduct a roundtable discussion with multiple elders.

        Args:
            elder_ids: List of elder IDs to participate
            question: The initial question or topic
            turns: Number of rounds each elder speaks
            stream: Whether to stream responses
            allow_nominations: Whether elders can nominate guests (defaults to config)
            max_nominations: Max guest nominations (defaults to config)

        Yields:
            Tuples of (elder_id, response_chunk).
            Special: ("__nomination__", NominatedElder) signals a new guest.
        """
        # Resolve nomination settings from config if not explicitly set
        if allow_nominations is None:
            allow_nominations = get_config_value("nominations_enabled", True)
        if max_nominations is None:
            max_nominations = get_config_value("max_nominations_per_session", 2)

        # Validate all elders exist
        elders = []
        for elder_id in elder_ids:
            elder = ElderRegistry.get(elder_id)
            if not elder:
                raise ValueError(f"Elder not found: {elder_id}")
            elders.append(elder)

        self.conversation.add_user_message(question)

        nomination_count = 0
        guest_queue: list[Elder] = []  # guests to speak at end of current round

        for turn in range(turns):
            # Build the speaker list: original elders + any queued guests
            speakers = list(elders)
            if guest_queue:
                speakers.extend(guest_queue)
                guest_queue = []

            for elder in speakers:
                # Build context prompt that includes other elders' responses
                if turn == 0 and elder == elders[0]:
                    context_note = ""
                else:
                    context_note = (
                        "\n\n[Note: You are participating in a roundtable discussion. "
                        "Consider what the other council members have said and build upon, "
                        "contrast with, or complement their perspectives. "
                        "Keep your response focused and avoid repeating what others have said.]"
                    )

                messages = self.conversation.to_messages(for_elder=elder.id)

                # Append nomination instruction if enabled and under the limit
                nomination_suffix = ""
                if allow_nominations and nomination_count < max_nominations:
                    nomination_suffix = NOMINATION_INSTRUCTION

                system_prompt = elder.system_prompt + context_note + nomination_suffix
                if self.use_knowledge:
                    knowledge_context = get_elder_knowledge(elder.id, query=question)
                    if knowledge_context:
                        system_prompt += knowledge_context

                full_response = []
                for chunk in chat(messages, system=system_prompt, stream=True):
                    full_response.append(chunk)
                    yield (elder.id, chunk)

                response_text = "".join(full_response)

                # Check for nomination tag
                nomination = None
                if allow_nominations and nomination_count < max_nominations:
                    nomination = parse_nomination(response_text)

                if nomination:
                    name, expertise = nomination
                    # Strip the tag from the stored response
                    response_text = strip_nomination_tag(response_text)
                    # Create the guest elder
                    guest = create_nominated_elder(
                        name=name,
                        expertise=expertise,
                        topic=question,
                        nominated_by=elder.name,
                    )
                    nomination_count += 1
                    guest_queue.append(guest)
                    # Signal nomination to the consumer
                    yield ("__nomination__", guest)

                self.conversation.add_elder_response(
                    elder.id, response_text, elder_name=elder.name
                )

                # Signal end of this elder's turn
                yield (elder.id, None)

        # After all planned rounds, let any remaining queued guests speak
        for guest in guest_queue:
            context_note = (
                "\n\n[Note: You are a guest expert invited to this roundtable discussion. "
                "Consider what the council members have said and offer your unique perspective. "
                "Be direct and substantive.]"
            )
            messages = self.conversation.to_messages(for_elder=guest.id)
            system_prompt = guest.system_prompt + context_note
            if self.use_knowledge:
                knowledge_context = get_elder_knowledge(guest.id, query=question)
                if knowledge_context:
                    system_prompt += knowledge_context

            full_response = []
            for chunk in chat(messages, system=system_prompt, stream=True):
                full_response.append(chunk)
                yield (guest.id, chunk)

            self.conversation.add_elder_response(
                guest.id, "".join(full_response), elder_name=guest.name
            )
            yield (guest.id, None)


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


    def panel_discussion(
        self,
        elder_ids: list[str],
        question: str,
        max_turns: int = 8,
        dialectic_tension: int = 50,
        continuation: dict | None = None,
        allow_nominations: bool | None = None,
        response_length: str = "moderate",
    ) -> Generator[tuple[str, str | dict | None], None, None]:
        """
        Moderator-led expert panel discussion.

        The moderator:
        1. Opens by framing the question and directing the first panelist
        2. After each panelist, decides: direct next panelist, ask user, or wrap up
        3. Closes with memorable takeaways

        Args:
            elder_ids: List of elder IDs on the panel
            question: The topic/question for discussion
            max_turns: Maximum number of speaking turns
            continuation: If resuming after user clarification, a dict with:
                user_answer, history, speakers_so_far, turns_used

        Yields:
            ("__moderator_start__", {"phase": str}) — moderator begins speaking
            ("__moderator__", chunk_or_None) — moderator streaming/done
            ("__ask_user__", {"question": str, "state": dict}) — pause for user input
            ("__nomination__", NominatedElder) — guest nomination
            (elder_id, chunk_or_None) — elder streaming/done
        """
        import re

        DIRECT_RE = re.compile(r"\[DIRECT:\s*(.+?)\s*\]", re.IGNORECASE)
        ASK_USER_RE = re.compile(r"\[ASK_USER\]", re.IGNORECASE)
        WRAP_UP_RE = re.compile(r"\[WRAP_UP\]", re.IGNORECASE)

        MODERATOR_PERSONA = (
            "You are the Moderator of this expert panel — incisive and efficient. "
            "You call panelists by name and keep the discussion moving.\n\n"
            "CRITICAL IDENTITY RULE: You are NOT one of the panelists. You are a modern-day "
            "host and facilitator. Never say 'we' when referring to the panelists. "
            "Refer to them in the third person.\n\n"
            "BREVITY RULE: Keep all of your contributions SHORT. Openings: 1-2 sentences max. "
            "Transitions: 1 sentence. Wrap-ups: a tight bullet list. "
            "The panelists are the stars — you are the connective tissue, not the main event."
        )

        def strip_tags(text):
            text = DIRECT_RE.sub("", text)
            text = ASK_USER_RE.sub("", text)
            text = WRAP_UP_RE.sub("", text)
            return text.rstrip()

        # Build elder roster
        elders = {}
        name_to_id = {}
        for eid in elder_ids:
            elder = ElderRegistry.get(eid)
            if not elder:
                raise ValueError(f"Elder not found: {eid}")
            elders[eid] = elder
            name_to_id[elder.name.lower()] = eid

        if allow_nominations is None:
            allow_nominations = get_config_value("nominations_enabled", True)
        max_nominations = get_config_value("max_nominations_per_session", 2)
        nomination_count = 0
        nominated_elders = {}

        panelist_descriptions = "\n".join(
            f"- {e.name} ({e.title}, {e.era})" for e in elders.values()
        )

        sentence_map = {
            "brief": "1-2 sentences",
            "moderate": "3-4 sentences",
            "detailed": "5-8 sentences",
            "extended": "10-15 sentences",
            "unlimited": None,
        }
        sentence_desc = sentence_map.get(response_length, "3-4 sentences")

        # Hard cap for mechanical interruption (elder responses)
        elder_sentence_cap = {
            "brief": 3, "moderate": 5, "detailed": 9,
            "extended": 16, "unlimited": None,
        }.get(response_length, 5)

        # Moderator hard caps by phase (always concise)
        mod_cap = {"opening": 2, "transition": 1, "acknowledge": 2, "takeaways": 5}

        length_rule = (
            f"- Keep your response to EXACTLY {sentence_desc} maximum. Be substantive and concise.\n"
            if sentence_desc else
            "- Respond at whatever length serves your point best. Be thorough and substantive.\n"
        )

        panel_instruction = (
            "\n\nYou are on an expert panel discussion, like an academic seminar. "
            "The moderator is directing the conversation. Rules:\n"
            + length_rule +
            "- Directly engage with what previous panelists and the moderator have said.\n"
            "- Address other panelists by name when referencing their ideas.\n"
            "- Be professional and speak naturally, as yourself, not as a narrator.\n"
        )

        if continuation:
            # Resuming after user clarification
            speakers_so_far = set(continuation.get('speakers_so_far', []))
            turns_used = continuation.get('turns_used', 0)

            # Rebuild conversation from history
            for turn in continuation.get('history', []):
                if turn['role'] == 'user':
                    self.conversation.add_user_message(turn['text'])
                elif turn['role'] == 'moderator':
                    self.conversation.add_elder_response(
                        "__moderator__", turn['text'], elder_name="Moderator"
                    )
                elif turn['role'] == 'elder':
                    elder_obj = ElderRegistry.get(turn['elder_id'])
                    fallback_name = elder_obj.name if elder_obj else turn.get('name', turn['elder_id'])
                    self.conversation.add_elder_response(
                        turn['elder_id'], turn['text'],
                        elder_name=turn.get('name') or fallback_name
                    )

            # Add user's clarification
            user_answer = continuation['user_answer']
            self.conversation.add_user_message(user_answer)

            # Moderator acknowledges and directs next
            unseen_names = [elders[eid].name for eid in elder_ids if eid not in speakers_so_far]
            ack_prompt = (
                MODERATOR_PERSONA + "\n\n"
                "The questioner has provided clarification. In 1-2 sentences, "
                "acknowledge their answer and direct the next panelist. "
                "End with [DIRECT: Full Name].\n\n"
                f"Available panelists:\n{panelist_descriptions}\n"
                f"Panelists who haven't spoken yet: {', '.join(unseen_names) or 'all have spoken'}"
            )

            yield ("__moderator_start__", {"phase": "acknowledge"})

            messages = self.conversation.to_messages(for_elder="__moderator__")
            ack_response = []
            for chunk in chat(messages, system=ack_prompt, stream=True):
                ack_response.append(chunk)
                yield ("__moderator__", chunk)
                if _count_sentences("".join(ack_response)) > mod_cap["acknowledge"]:
                    break

            ack_text = "".join(ack_response)
            clean_ack = strip_tags(ack_text)
            self.conversation.add_elder_response(
                "__moderator__", clean_ack, elder_name="Moderator"
            )
            yield ("__moderator__", None)

            direct_match = DIRECT_RE.search(ack_text)
            if direct_match:
                next_id = _resolve_elder_name(direct_match.group(1), name_to_id)
                current_elder_id = next_id or elder_ids[0]
            else:
                unseen = [eid for eid in elder_ids if eid not in speakers_so_far]
                current_elder_id = unseen[0] if unseen else elder_ids[turns_used % len(elder_ids)]

        else:
            # Fresh panel
            speakers_so_far = set()
            turns_used = 0

            self.conversation.add_user_message(
                f"[PANEL DISCUSSION] The topic: \"{question}\"\n\n"
                f"Panelists: {', '.join(e.name for e in elders.values())}.\n"
                f"The moderator will direct the conversation."
            )

            # PHASE 1: Moderator opening
            opening_prompt = (
                MODERATOR_PERSONA + "\n\n"
                "Open this panel discussion. In 1-2 sentences: frame the question "
                "and direct the most relevant panelist to kick off.\n\n"
                f"The question: \"{question}\"\n\n"
                f"Available panelists:\n{panelist_descriptions}\n\n"
                "End with [DIRECT: Full Name]. Be brief."
            )

            yield ("__moderator_start__", {"phase": "opening"})

            messages = self.conversation.to_messages(for_elder="__moderator__")
            opening_response = []
            for chunk in chat(messages, system=opening_prompt, stream=True):
                opening_response.append(chunk)
                yield ("__moderator__", chunk)
                if _count_sentences("".join(opening_response)) > mod_cap["opening"]:
                    break

            opening_text = "".join(opening_response)
            clean_opening = strip_tags(opening_text)
            self.conversation.add_elder_response(
                "__moderator__", clean_opening, elder_name="Moderator"
            )
            yield ("__moderator__", None)

            direct_match = DIRECT_RE.search(opening_text)
            if direct_match:
                first_id = _resolve_elder_name(direct_match.group(1), name_to_id)
                current_elder_id = first_id or elder_ids[0]
            else:
                current_elder_id = elder_ids[0]

        # PHASE 2: Directed conversation loop
        remaining_turns = max_turns - turns_used

        for turn_num in range(remaining_turns):
            elder = elders.get(current_elder_id) or nominated_elders.get(current_elder_id)
            if not elder:
                break

            speakers_so_far.add(current_elder_id)

            if turn_num == 0 and not continuation:
                context_note = "\n\nThe moderator has directed you to open the discussion."
            else:
                context_note = (
                    "\n\nThe moderator has directed you to speak. "
                    "Respond to what's been said and add your perspective."
                )

            messages = self.conversation.to_messages(for_elder=elder.id)
            system_prompt = elder.system_prompt + panel_instruction + context_note
            system_prompt += _get_tension_prompt(dialectic_tension, role="elder")
            if self.use_knowledge:
                knowledge_context = get_elder_knowledge(elder.id, query=question)
                if knowledge_context:
                    system_prompt += knowledge_context

            if allow_nominations and nomination_count < max_nominations:
                system_prompt += NOMINATION_INSTRUCTION

            full_response = []
            interrupted = False
            for chunk in chat(messages, system=system_prompt, stream=True):
                full_response.append(chunk)
                yield (elder.id, chunk)
                if elder_sentence_cap is not None:
                    if _count_sentences("".join(full_response)) > elder_sentence_cap:
                        interrupted = True
                        break

            response_text = "".join(full_response)

            # Check for guest nomination (skip if interrupted)
            nomination = None
            if not interrupted and allow_nominations and nomination_count < max_nominations:
                nomination = parse_nomination(response_text)

            if nomination:
                name, expertise = nomination
                response_text = strip_nomination_tag(response_text)
                guest = create_nominated_elder(
                    name=name, expertise=expertise,
                    topic=question, nominated_by=elder.name,
                )
                nomination_count += 1
                nominated_elders[guest.id] = guest
                name_to_id[guest.name.lower()] = guest.id
                yield ("__nomination__", guest)

            self.conversation.add_elder_response(
                elder.id, response_text, elder_name=elder.name
            )
            yield (elder.id, None)

            turns_used += 1

            # MODERATOR TRANSITION: decide what happens next
            unseen_names = [elders[eid].name for eid in elder_ids if eid not in speakers_so_far]
            all_names = [e.name for e in elders.values()] + [g.name for g in nominated_elders.values()]

            all_have_spoken = len(unseen_names) == 0
            transition_prompt = (
                MODERATOR_PERSONA + "\n\n"
                f"You just heard {elder.name} speak. As moderator, decide what happens next.\n\n"
                f"Available panelists: {', '.join(all_names)}\n"
                f"Panelists who haven't spoken yet: {', '.join(unseen_names) or 'all have spoken'}\n"
                f"Turns used: {turns_used}/{max_turns}\n\n"
                "In 1 sentence, transition. You MUST end with exactly ONE of:\n"
                "- [DIRECT: Full Name] — to direct a panelist to speak next\n"
            )
            if all_have_spoken:
                transition_prompt += (
                    "- [ASK_USER] — to ask the questioner for clarification "
                    "(only if the discussion has hit a genuine ambiguity)\n"
                    "- [WRAP_UP] — to conclude the discussion\n\n"
                )
            else:
                transition_prompt += (
                    "- [WRAP_UP] — to conclude (only after ALL panelists have spoken)\n\n"
                    "IMPORTANT: Do NOT wrap up or ask the user questions yet. "
                    "Let every panelist speak first.\n"
                )
            transition_prompt += (
                "Priorities:\n"
                "- Ensure panelists who haven't spoken get their turn before wrapping up\n"
                "- Reference specific points from the previous speaker\n"
            )
            transition_prompt += _get_tension_prompt(dialectic_tension, role="moderator")

            yield ("__moderator_start__", {"phase": "transition"})

            messages = self.conversation.to_messages(for_elder="__moderator__")
            transition_response = []
            display_capped = False
            for chunk in chat(messages, system=transition_prompt, stream=True):
                transition_response.append(chunk)
                if not display_capped:
                    yield ("__moderator__", chunk)
                    if _count_sentences("".join(transition_response)) > mod_cap["transition"]:
                        display_capped = True

            transition_text = "".join(transition_response)
            clean_transition = strip_tags(transition_text)
            self.conversation.add_elder_response(
                "__moderator__", clean_transition, elder_name="Moderator"
            )
            yield ("__moderator__", None)

            # Parse moderator's decision
            if ASK_USER_RE.search(transition_text):
                state = {
                    'speakers_so_far': list(speakers_so_far),
                    'turns_used': turns_used,
                }
                yield ("__ask_user__", state)
                return  # Stream ends; client calls /api/panel-continue

            if WRAP_UP_RE.search(transition_text):
                break

            direct_match = DIRECT_RE.search(transition_text)
            if direct_match:
                next_id = _resolve_elder_name(direct_match.group(1), name_to_id)
                if next_id and next_id != current_elder_id:
                    current_elder_id = next_id
                else:
                    unseen = [eid for eid in elder_ids if eid not in speakers_so_far]
                    current_elder_id = unseen[0] if unseen else elder_ids[(elder_ids.index(current_elder_id) + 1) % len(elder_ids)]
            else:
                unseen = [eid for eid in elder_ids if eid not in speakers_so_far]
                if unseen:
                    current_elder_id = unseen[0]
                else:
                    idx = elder_ids.index(current_elder_id) if current_elder_id in elder_ids else 0
                    current_elder_id = elder_ids[(idx + 1) % len(elder_ids)]

        # PHASE 3: Nominated guests give brief closing evaluations
        if nominated_elders:
            guest_closing_instruction = (
                "\n\nThe main panel discussion has concluded. You were nominated as a guest "
                "expert during the conversation. Now give a brief closing evaluation (2-3 sentences): "
                "what was the strongest insight from the discussion, and what important angle "
                "was missed or underexplored? Be direct and substantive."
            )

            for guest_id, guest in nominated_elders.items():
                if guest_id not in speakers_so_far:
                    # This guest never got to speak — give them the floor
                    messages = self.conversation.to_messages(for_elder=guest_id)
                    system_prompt = guest.system_prompt + guest_closing_instruction

                    full_response = []
                    for chunk in chat(messages, system=system_prompt, stream=True):
                        full_response.append(chunk)
                        yield (guest_id, chunk)

                    self.conversation.add_elder_response(
                        guest_id, "".join(full_response), elder_name=guest.name
                    )
                    yield (guest_id, None)

        # PHASE 4: Moderator wrap-up with takeaways
        takeaway_prompt = (
            MODERATOR_PERSONA + "\n\n"
            "Wrap up the discussion. Give 2-3 bullet-point takeaways (one sentence each) "
            "and end with one actionable sentence. No preamble, no fluff."
        )

        yield ("__moderator_start__", {"phase": "takeaways"})

        messages = self.conversation.to_messages(for_elder="__moderator__")
        takeaway_response = []
        for chunk in chat(messages, system=takeaway_prompt, stream=True):
            takeaway_response.append(chunk)
            yield ("__moderator__", chunk)
            if _count_sentences("".join(takeaway_response)) > 12:
                break

        self.conversation.add_elder_response(
            "__moderator__", "".join(takeaway_response), elder_name="Moderator"
        )
        yield ("__moderator__", None)


    def salon_discussion(
        self,
        elder_ids: list[str],
        question: str,
        max_turns: int = 12,
        dialectic_tension: int = 50,
        continuation: dict | None = None,
        allow_nominations: bool | None = None,
        response_length: str = "moderate",
    ) -> Generator[tuple[str, str | dict | None], None, None]:
        """
        Salon-style discussion with an assertive moderator who assigns dynamic
        sentence budgets and can interrupt elders mid-stream.

        Same yield protocol as panel_discussion with one addition:
            ("__elder_interrupted__", {"elder_id": str, "name": str})

        Args:
            elder_ids: List of elder IDs
            question: Topic for discussion
            max_turns: Maximum elder speaking turns
            dialectic_tension: 0 (collaborative) to 100 (debate)
            continuation: For resuming after user clarification
        """
        import re

        DIRECT_RE = re.compile(r"\[DIRECT:\s*(.+?)(?:,\s*(\d+))?\s*\]", re.IGNORECASE)
        ASK_USER_RE = re.compile(r"\[ASK_USER\]", re.IGNORECASE)
        WRAP_UP_RE = re.compile(r"\[WRAP_UP\]", re.IGNORECASE)

        budget_max = {"brief": 3, "moderate": 5, "detailed": 8, "extended": 15, "unlimited": 30}.get(response_length, 5)
        mod_cap = {"opening": 3, "transition": 2, "acknowledge": 3, "takeaways": 6}
        SALON_MODERATOR_PERSONA = (
            "You are the Moderator of this salon — sharp, efficient, on the questioner's side.\n\n"
            "IDENTITY RULE: You are a modern-day facilitator, NOT a panelist or historical figure. "
            "Refer to panelists in the third person.\n\n"
            f"Assign sentence budgets with [DIRECT: Full Name, N] where N is 1-{budget_max}.\n\n"
            "BREVITY RULE: Keep your own contributions to 1 sentence max between speakers. "
            "You are connective tissue — the panelists are the main event."
        )

        def strip_tags(text):
            text = DIRECT_RE.sub("", text)
            text = ASK_USER_RE.sub("", text)
            text = WRAP_UP_RE.sub("", text)
            return text.rstrip()

        def parse_sentence_budget(text):
            """Extract sentence budget N from [DIRECT: Name, N]."""
            m = DIRECT_RE.search(text)
            if m and m.group(2):
                budget_max = {"brief": 3, "moderate": 5, "detailed": 8, "extended": 15, "unlimited": 30}.get(response_length, 5)
                return max(1, min(budget_max, int(m.group(2))))
            return default_budget

        # Build elder roster
        elders = {}
        name_to_id = {}
        for eid in elder_ids:
            elder = ElderRegistry.get(eid)
            if not elder:
                raise ValueError(f"Elder not found: {eid}")
            elders[eid] = elder
            name_to_id[elder.name.lower()] = eid

        if allow_nominations is None:
            allow_nominations = get_config_value("nominations_enabled", True)
        max_nominations = get_config_value("max_nominations_per_session", 2)
        nomination_count = 0
        nominated_elders = {}

        panelist_descriptions = "\n".join(
            f"- {e.name} ({e.title}, {e.era})" for e in elders.values()
        )

        # Adjust default sentence budget based on response length
        salon_budget_map = {
            "brief": 2,
            "moderate": 3,
            "detailed": 5,
            "extended": 10,
            "unlimited": 15,
        }
        default_budget = salon_budget_map.get(response_length, 3)

        salon_instruction = (
            "\n\nYou are in a salon-style discussion. The moderator is directing the "
            "conversation and has assigned you a specific number of sentences. Rules:\n"
            "- Keep your response to EXACTLY the number of sentences the moderator assigned.\n"
            "- Be substantive and concise — every sentence must earn its place.\n"
            "- Directly engage with what previous panelists and the moderator have said.\n"
            "- Address other panelists by name when referencing their ideas.\n"
            "- The moderator may cut you off if you exceed your budget.\n"
        )

        if continuation:
            speakers_so_far = set(continuation.get('speakers_so_far', []))
            turns_used = continuation.get('turns_used', 0)

            for turn in continuation.get('history', []):
                if turn['role'] == 'user':
                    self.conversation.add_user_message(turn['text'])
                elif turn['role'] == 'moderator':
                    self.conversation.add_elder_response(
                        "__moderator__", turn['text'], elder_name="Moderator"
                    )
                elif turn['role'] == 'elder':
                    elder_obj = ElderRegistry.get(turn['elder_id'])
                    fallback_name = elder_obj.name if elder_obj else turn.get('name', turn['elder_id'])
                    self.conversation.add_elder_response(
                        turn['elder_id'], turn['text'],
                        elder_name=turn.get('name') or fallback_name
                    )

            user_answer = continuation['user_answer']
            self.conversation.add_user_message(user_answer)

            unseen_names = [elders[eid].name for eid in elder_ids if eid not in speakers_so_far]
            ack_prompt = (
                SALON_MODERATOR_PERSONA + "\n\n"
                "The questioner has provided clarification. In 1 sentence, "
                "acknowledge and direct the next panelist with a sentence budget. "
                "End with [DIRECT: Full Name, N].\n\n"
                f"Available panelists:\n{panelist_descriptions}\n"
                f"Panelists who haven't spoken yet: {', '.join(unseen_names) or 'all have spoken'}"
            )
            ack_prompt += _get_tension_prompt(dialectic_tension, role="moderator")

            yield ("__moderator_start__", {"phase": "acknowledge"})

            messages = self.conversation.to_messages(for_elder="__moderator__")
            ack_response = []
            for chunk in chat(messages, system=ack_prompt, stream=True):
                ack_response.append(chunk)
                yield ("__moderator__", chunk)
                if _count_sentences("".join(ack_response)) > mod_cap["acknowledge"]:
                    break

            ack_text = "".join(ack_response)
            sentence_budget = parse_sentence_budget(ack_text)
            clean_ack = strip_tags(ack_text)
            self.conversation.add_elder_response(
                "__moderator__", clean_ack, elder_name="Moderator"
            )
            yield ("__moderator__", None)

            direct_match = DIRECT_RE.search(ack_text)
            if direct_match:
                next_id = _resolve_elder_name(direct_match.group(1), name_to_id)
                current_elder_id = next_id or elder_ids[0]
            else:
                unseen = [eid for eid in elder_ids if eid not in speakers_so_far]
                current_elder_id = unseen[0] if unseen else elder_ids[turns_used % len(elder_ids)]

        else:
            # Fresh salon
            speakers_so_far = set()
            turns_used = 0
            sentence_budget = default_budget  # based on response_length setting

            self.conversation.add_user_message(
                f"[SALON DISCUSSION] The topic: \"{question}\"\n\n"
                f"Panelists: {', '.join(e.name for e in elders.values())}.\n"
                f"The moderator will direct the conversation."
            )

            # Moderator opening
            opening_prompt = (
                SALON_MODERATOR_PERSONA + "\n\n"
                "Open this salon discussion. In 1-2 sentences:\n"
                "1. Frame the question sharply — get to the heart of what matters\n"
                "2. Direct the first panelist with a sentence budget\n\n"
                f"The question: \"{question}\"\n\n"
                f"Available panelists:\n{panelist_descriptions}\n\n"
                "End with [DIRECT: Full Name, N] where N is 1-5 sentences."
            )
            opening_prompt += _get_tension_prompt(dialectic_tension, role="moderator")

            yield ("__moderator_start__", {"phase": "opening"})

            messages = self.conversation.to_messages(for_elder="__moderator__")
            opening_response = []
            for chunk in chat(messages, system=opening_prompt, stream=True):
                opening_response.append(chunk)
                yield ("__moderator__", chunk)
                if _count_sentences("".join(opening_response)) > mod_cap["opening"]:
                    break

            opening_text = "".join(opening_response)
            sentence_budget = parse_sentence_budget(opening_text)
            clean_opening = strip_tags(opening_text)
            self.conversation.add_elder_response(
                "__moderator__", clean_opening, elder_name="Moderator"
            )
            yield ("__moderator__", None)

            direct_match = DIRECT_RE.search(opening_text)
            if direct_match:
                first_id = _resolve_elder_name(direct_match.group(1), name_to_id)
                current_elder_id = first_id or elder_ids[0]
            else:
                current_elder_id = elder_ids[0]

        # Main conversation loop
        remaining_turns = max_turns - turns_used

        for turn_num in range(remaining_turns):
            elder = elders.get(current_elder_id) or nominated_elders.get(current_elder_id)
            if not elder:
                break

            speakers_so_far.add(current_elder_id)

            if turn_num == 0 and not continuation:
                context_note = "\n\nThe moderator has directed you to open the discussion."
            else:
                context_note = (
                    "\n\nThe moderator has directed you to speak. "
                    "Respond to what's been said and add your perspective."
                )

            messages = self.conversation.to_messages(for_elder=elder.id)
            system_prompt = elder.system_prompt + salon_instruction + context_note
            system_prompt += _get_tension_prompt(dialectic_tension, role="elder")
            if self.use_knowledge:
                knowledge_context = get_elder_knowledge(elder.id, query=question)
                if knowledge_context:
                    system_prompt += knowledge_context

            if allow_nominations and nomination_count < max_nominations:
                system_prompt += NOMINATION_INSTRUCTION

            # Stream with interruption check
            full_response = []
            interrupted = False
            for chunk in chat(messages, system=system_prompt, stream=True):
                full_response.append(chunk)
                yield (elder.id, chunk)

                # Check if elder exceeded sentence budget
                current_text = "".join(full_response)
                if _count_sentences(current_text) > sentence_budget:
                    interrupted = True
                    break

            response_text = "".join(full_response)

            if interrupted:
                yield ("__elder_interrupted__", {"elder_id": elder.id, "name": elder.name})

            # Check for guest nomination (only if not interrupted)
            nomination = None
            if not interrupted and allow_nominations and nomination_count < max_nominations:
                nomination = parse_nomination(response_text)

            if nomination:
                name, expertise = nomination
                response_text = strip_nomination_tag(response_text)
                guest = create_nominated_elder(
                    name=name, expertise=expertise,
                    topic=question, nominated_by=elder.name,
                )
                nomination_count += 1
                nominated_elders[guest.id] = guest
                name_to_id[guest.name.lower()] = guest.id
                yield ("__nomination__", guest)

            self.conversation.add_elder_response(
                elder.id, response_text, elder_name=elder.name
            )
            yield (elder.id, None)

            turns_used += 1

            # Moderator transition
            unseen_names = [elders[eid].name for eid in elder_ids if eid not in speakers_so_far]
            all_names = [e.name for e in elders.values()] + [g.name for g in nominated_elders.values()]

            interrupt_note = ""
            if interrupted:
                interrupt_note = (
                    f"\nNote: You just cut off {elder.name} because they exceeded their "
                    "sentence budget. Acknowledge this briefly and move on."
                )

            all_have_spoken = len(unseen_names) == 0
            transition_prompt = (
                SALON_MODERATOR_PERSONA + "\n\n"
                f"You just heard {elder.name} speak.{interrupt_note}\n"
                "As moderator, decide what happens next.\n\n"
                f"Available panelists: {', '.join(all_names)}\n"
                f"Panelists who haven't spoken yet: {', '.join(unseen_names) or 'all have spoken'}\n"
                f"Turns used: {turns_used}/{max_turns}\n\n"
                "In 1 sentence, provide a transition. You MUST end with exactly ONE of:\n"
                "- [DIRECT: Full Name, N] — direct a panelist with N sentence budget (1-5)\n"
            )
            if all_have_spoken:
                transition_prompt += (
                    "- [ASK_USER] — ask the questioner for clarification\n"
                    "- [WRAP_UP] — conclude the discussion\n\n"
                )
            else:
                transition_prompt += (
                    "- [WRAP_UP] — conclude (only after ALL panelists have spoken)\n\n"
                    "IMPORTANT: Do NOT wrap up or ask the user questions yet. "
                    "Let every panelist speak first.\n"
                )
            transition_prompt += (
                "Priorities:\n"
                "- Ensure panelists who haven't spoken get their turn\n"
                "- Keep the pace dynamic — vary sentence budgets\n"
                "- Be punchy and direct in your transitions\n"
            )
            transition_prompt += _get_tension_prompt(dialectic_tension, role="moderator")

            yield ("__moderator_start__", {"phase": "transition"})

            messages = self.conversation.to_messages(for_elder="__moderator__")
            transition_response = []
            display_capped = False
            for chunk in chat(messages, system=transition_prompt, stream=True):
                transition_response.append(chunk)
                if not display_capped:
                    yield ("__moderator__", chunk)
                    if _count_sentences("".join(transition_response)) > mod_cap["transition"]:
                        display_capped = True

            transition_text = "".join(transition_response)
            sentence_budget = parse_sentence_budget(transition_text)
            clean_transition = strip_tags(transition_text)
            self.conversation.add_elder_response(
                "__moderator__", clean_transition, elder_name="Moderator"
            )
            yield ("__moderator__", None)

            # Parse moderator's decision
            if ASK_USER_RE.search(transition_text):
                state = {
                    'speakers_so_far': list(speakers_so_far),
                    'turns_used': turns_used,
                }
                yield ("__ask_user__", state)
                return

            if WRAP_UP_RE.search(transition_text):
                break

            direct_match = DIRECT_RE.search(transition_text)
            if direct_match:
                next_id = _resolve_elder_name(direct_match.group(1), name_to_id)
                if next_id and next_id != current_elder_id:
                    current_elder_id = next_id
                else:
                    unseen = [eid for eid in elder_ids if eid not in speakers_so_far]
                    current_elder_id = unseen[0] if unseen else elder_ids[(elder_ids.index(current_elder_id) + 1) % len(elder_ids)]
            else:
                unseen = [eid for eid in elder_ids if eid not in speakers_so_far]
                if unseen:
                    current_elder_id = unseen[0]
                else:
                    idx = elder_ids.index(current_elder_id) if current_elder_id in elder_ids else 0
                    current_elder_id = elder_ids[(idx + 1) % len(elder_ids)]

        # Nominated guests give brief closing evaluations
        if nominated_elders:
            guest_closing_instruction = (
                "\n\nThe salon discussion has concluded. You were nominated as a guest "
                "expert during the conversation. Now give a brief closing evaluation (2-3 sentences): "
                "what was the strongest insight from the discussion, and what important angle "
                "was missed or underexplored? Be direct and substantive."
            )

            for guest_id, guest in nominated_elders.items():
                if guest_id not in speakers_so_far:
                    messages = self.conversation.to_messages(for_elder=guest_id)
                    system_prompt = guest.system_prompt + guest_closing_instruction

                    full_response = []
                    for chunk in chat(messages, system=system_prompt, stream=True):
                        full_response.append(chunk)
                        yield (guest_id, chunk)

                    self.conversation.add_elder_response(
                        guest_id, "".join(full_response), elder_name=guest.name
                    )
                    yield (guest_id, None)

        # Wrap-up with takeaways
        takeaway_prompt = (
            SALON_MODERATOR_PERSONA + "\n\n"
            "The salon is concluding. Deliver punchy takeaways.\n\n"
            "Your job:\n"
            "1. Identify the 2-3 most valuable insights\n"
            "2. Make each a sharp, memorable one-liner\n"
            "3. End with one clear action item for the questioner\n\n"
            "Be concise and impactful. No fluff."
        )

        yield ("__moderator_start__", {"phase": "takeaways"})

        messages = self.conversation.to_messages(for_elder="__moderator__")
        takeaway_response = []
        for chunk in chat(messages, system=takeaway_prompt, stream=True):
            takeaway_response.append(chunk)
            yield ("__moderator__", chunk)
            if _count_sentences("".join(takeaway_response)) > 12:
                break

        self.conversation.add_elder_response(
            "__moderator__", "".join(takeaway_response), elder_name="Moderator"
        )
        yield ("__moderator__", None)


    def rap_battle(
        self,
        elder_ids: list[str],
        question: str,
        rounds: int = 3,
        response_length: str = "moderate",
    ) -> Generator[tuple[str, str | dict | None], None, None]:
        """
        Rap battle mode: two elders trade philosophical bars.

        The moderator is a battle host who introduces combatants, calls rounds,
        provides hype commentary, and declares a winner.

        Args:
            elder_ids: List of elder IDs (first two become combatants)
            question: The topic/theme for the battle
            rounds: Number of battle rounds

        Yields:
            Same protocol as panel_discussion:
            ("__moderator_start__", {"phase": str})
            ("__moderator__", chunk_or_None)
            (elder_id, chunk_or_None)
        """
        if len(elder_ids) < 2:
            raise ValueError("Rap battle requires at least 2 elders")

        combatant_ids = elder_ids[:2]
        elders = {}
        for eid in combatant_ids:
            elder = ElderRegistry.get(eid)
            if not elder:
                raise ValueError(f"Elder not found: {eid}")
            elders[eid] = elder

        mod_cap = {"opening": 2, "transition": 1, "takeaways": 3}
        BATTLE_HOST_PERSONA = (
            "You are the Battle Host — a legendary rap battle MC. High energy, witty, fun.\n\n"
            "You are NOT a combatant. You are the MC — address combatants by name. "
            "Never rap yourself.\n\n"
            "BREVITY RULE: Keep intros and transitions to 1-2 sentences. "
            "The combatants do the talking — you just set the stage."
        )

        rap_bars_map = {
            "brief": "4 to 6",
            "moderate": "6 to 10",
            "detailed": "10 to 16",
            "extended": "16 to 24",
            "unlimited": "as many as you want (go hard)",
        }
        rap_bars = rap_bars_map.get(response_length, "4 to 8")

        rap_instruction = (
            "\n\nYou are in a RAP BATTLE. Rules:\n"
            f"- Respond ONLY in rap verse — {rap_bars} bars (lines) per round\n"
            "- Your bars must RHYME (end rhyme, AABB or ABAB scheme)\n"
            "- Ground your disses in your actual philosophy and worldview\n"
            "- Reference your opponent's ideas and explain why yours are superior\n"
            "- Be clever, witty, and sharp — but not crude or hateful\n"
            "- Stay in character as yourself — rap in YOUR voice with YOUR ideas\n"
        )

        self.conversation.add_user_message(
            f"[RAP BATTLE] Topic: \"{question}\"\n\n"
            f"Combatants: {elders[combatant_ids[0]].name} vs {elders[combatant_ids[1]].name}.\n"
            f"The Battle Host will MC {rounds} rounds."
        )

        # Opening — Battle Host introduces the combatants
        opening_prompt = (
            BATTLE_HOST_PERSONA + "\n\n"
            f"Open this rap battle! In 1-2 sentences: announce the topic \"{question}\", "
            f"introduce the combatants, and call Round 1.\n\n"
            f"Combatant 1: {elders[combatant_ids[0]].name} ({elders[combatant_ids[0]].title})\n"
            f"Combatant 2: {elders[combatant_ids[1]].name} ({elders[combatant_ids[1]].title})"
        )

        yield ("__moderator_start__", {"phase": "opening"})
        messages = self.conversation.to_messages(for_elder="__moderator__")
        opening_response = []
        for chunk in chat(messages, system=opening_prompt, stream=True):
            opening_response.append(chunk)
            yield ("__moderator__", chunk)
            if _count_sentences("".join(opening_response)) > mod_cap["opening"]:
                break

        opening_text = "".join(opening_response)
        self.conversation.add_elder_response(
            "__moderator__", opening_text, elder_name="Battle Host"
        )
        yield ("__moderator__", None)

        # Battle rounds
        for round_num in range(1, rounds + 1):
            for i, eid in enumerate(combatant_ids):
                elder = elders[eid]
                opponent = elders[combatant_ids[1 - i]]

                context_note = (
                    f"\n\nThis is Round {round_num} of {rounds}. "
                    f"You are battling {opponent.name}. "
                    f"{'You are responding to their verse — hit back!' if (round_num > 1 or i > 0) else 'You go first — set the tone!'}"
                )

                messages = self.conversation.to_messages(for_elder=eid)
                system_prompt = elder.system_prompt + rap_instruction + context_note

                full_response = []
                for chunk in chat(messages, system=system_prompt, stream=True):
                    full_response.append(chunk)
                    yield (eid, chunk)

                self.conversation.add_elder_response(
                    eid, "".join(full_response), elder_name=elder.name
                )
                yield (eid, None)

            # Battle Host commentary between rounds (except after last)
            if round_num < rounds:
                transition_prompt = (
                    BATTLE_HOST_PERSONA + "\n\n"
                    f"Round {round_num} just ended! In 1 sentence, react and announce Round {round_num + 1}.\n"
                )

                yield ("__moderator_start__", {"phase": "transition"})
                messages = self.conversation.to_messages(for_elder="__moderator__")
                transition_response = []
                display_capped = False
                for chunk in chat(messages, system=transition_prompt, stream=True):
                    transition_response.append(chunk)
                    if not display_capped:
                        yield ("__moderator__", chunk)
                        if _count_sentences("".join(transition_response)) > mod_cap["transition"]:
                            display_capped = True

                self.conversation.add_elder_response(
                    "__moderator__", "".join(transition_response), elder_name="Battle Host"
                )
                yield ("__moderator__", None)

        # Battle Host declares winner
        verdict_prompt = (
            BATTLE_HOST_PERSONA + "\n\n"
            "The battle is OVER! In 1-2 sentences: declare the winner and one memorable closing line. "
            "Be decisive."
        )

        yield ("__moderator_start__", {"phase": "takeaways"})
        messages = self.conversation.to_messages(for_elder="__moderator__")
        verdict_response = []
        for chunk in chat(messages, system=verdict_prompt, stream=True):
            verdict_response.append(chunk)
            yield ("__moderator__", chunk)
            if _count_sentences("".join(verdict_response)) > 4:
                break

        self.conversation.add_elder_response(
            "__moderator__", "".join(verdict_response), elder_name="Battle Host"
        )
        yield ("__moderator__", None)


    def poetry_slam(
        self,
        elder_ids: list[str],
        question: str,
        response_length: str = "moderate",
        poetry_form: str = "spoken_word",
    ) -> Generator[tuple[str, str | dict | None], None, None]:
        """
        Poetry slam mode: elders perform spoken-word poems, MC scores and judges.

        Args:
            elder_ids: List of elder IDs to perform
            question: The theme for the slam

        Yields:
            Same protocol as panel_discussion.
        """
        elders = {}
        for eid in elder_ids:
            elder = ElderRegistry.get(eid)
            if not elder:
                raise ValueError(f"Elder not found: {eid}")
            elders[eid] = elder

        mod_cap = {"opening": 2, "transition": 1, "takeaways": 3}
        SLAM_MC_PERSONA = (
            "You are the Slam MC — a passionate poetry slam host who sets the mood "
            "and scores performances.\n\n"
            "You are NOT a poet. You are the MC and judge. Never perform poetry yourself.\n\n"
            "BREVITY RULE: Keep intros and transitions to 1 sentence. "
            "The poets are the main event."
        )

        poetry_form_instructions = {
            "spoken_word": {
                "name": "spoken-word poetry",
                "rules": "- Write in free-verse spoken-word style\n"
                         "- This is performance poetry — write for the ear, not just the page\n",
            },
            "free_verse": {
                "name": "free-verse poetry",
                "rules": "- Write in free verse — no required rhyme or meter\n"
                         "- Let rhythm emerge naturally from your ideas\n",
            },
            "haiku": {
                "name": "haiku",
                "rules": "- Write one or more haiku (5-7-5 syllable structure)\n"
                         "- Capture a single vivid moment or insight per haiku\n"
                         "- Include a seasonal or nature reference (kigo) if fitting\n",
            },
            "sonnet": {
                "name": "sonnet",
                "rules": "- Write a 14-line sonnet in iambic pentameter\n"
                         "- Use a rhyme scheme (Shakespearean ABAB CDCD EFEF GG or Petrarchan ABBAABBA CDCDCD)\n"
                         "- Build to a turn (volta) and conclude with a powerful couplet or sestet\n",
            },
            "limerick": {
                "name": "limerick",
                "rules": "- Write one or more limericks (5 lines, AABBA rhyme scheme)\n"
                         "- Lines 1, 2, 5 are longer; lines 3, 4 are shorter\n"
                         "- Be witty, clever, and rhythmic\n",
            },
            "villanelle": {
                "name": "villanelle",
                "rules": "- Write a villanelle: 19 lines, five tercets and a quatrain\n"
                         "- The first and third lines of the first tercet alternate as refrains\n"
                         "- Rhyme scheme: ABA ABA ABA ABA ABA ABAA\n",
            },
            "ballad": {
                "name": "ballad",
                "rules": "- Write in ballad form: quatrains with ABAB or ABCB rhyme\n"
                         "- Use a narrative, storytelling voice\n"
                         "- Alternating lines of iambic tetrameter and trimeter\n",
            },
            "ghazal": {
                "name": "ghazal",
                "rules": "- Write a ghazal: a series of couplets (minimum 5)\n"
                         "- Each couplet must be self-contained yet thematically linked\n"
                         "- The same word or phrase (radif) ends both lines of the first couplet and the second line of each subsequent couplet\n",
            },
            "tanka": {
                "name": "tanka",
                "rules": "- Write one or more tanka (5-7-5-7-7 syllable structure)\n"
                         "- The first three lines set a scene; the last two add personal reflection\n"
                         "- More expansive and emotional than haiku\n",
            },
            "ode": {
                "name": "ode",
                "rules": "- Write an ode — an elevated, lyrical poem of praise or deep reflection\n"
                         "- Use rich language, apostrophe (addressing the subject directly), and emotional intensity\n"
                         "- Structure in stanzas with varying line lengths\n",
            },
        }

        form_info = poetry_form_instructions.get(poetry_form, poetry_form_instructions["spoken_word"])
        form_name = form_info["name"]
        form_rules = form_info["rules"]

        poem_lines_map = {
            "brief": "4 to 8",
            "moderate": "8 to 16",
            "detailed": "16 to 24",
            "extended": "24 to 40",
            "unlimited": "as many as the poem demands",
        }
        # Some forms have fixed lengths — override
        if poetry_form == "haiku":
            poem_lines_map = {k: "3 lines per haiku" for k in poem_lines_map}
            poem_lines_map["brief"] = "1 haiku (3 lines)"
            poem_lines_map["moderate"] = "2-3 haiku (6-9 lines)"
            poem_lines_map["detailed"] = "4-5 haiku (12-15 lines)"
            poem_lines_map["extended"] = "6-8 haiku (18-24 lines)"
            poem_lines_map["unlimited"] = "as many haiku as the theme inspires"
        elif poetry_form == "tanka":
            poem_lines_map["brief"] = "1 tanka (5 lines)"
            poem_lines_map["moderate"] = "2-3 tanka (10-15 lines)"
            poem_lines_map["detailed"] = "4-5 tanka (20-25 lines)"
            poem_lines_map["extended"] = "6-8 tanka (30-40 lines)"
            poem_lines_map["unlimited"] = "as many tanka as the theme inspires"
        elif poetry_form == "limerick":
            poem_lines_map["brief"] = "1 limerick (5 lines)"
            poem_lines_map["moderate"] = "2-3 limericks (10-15 lines)"
            poem_lines_map["detailed"] = "4-5 limericks (20-25 lines)"
            poem_lines_map["extended"] = "6-8 limericks (30-40 lines)"
            poem_lines_map["unlimited"] = "as many limericks as you like"
        elif poetry_form == "sonnet":
            poem_lines_map = {k: "14 lines (one sonnet)" for k in poem_lines_map}
            poem_lines_map["unlimited"] = "a sonnet sequence (2-3 sonnets)"

        poem_lines = poem_lines_map.get(response_length, "8 to 16")

        poem_instruction = (
            f"\n\nYou are performing at a POETRY SLAM. Your form is: {form_name.upper()}. Rules:\n"
            f"- Respond ONLY in {form_name} — target {poem_lines}\n"
            + form_rules +
            "- Your poem must address the theme through your unique worldview\n"
            "- Use vivid imagery, metaphor, and emotional resonance\n"
            "- Write as yourself — let your philosophy and life experience shine through\n"
            "- Be authentic, powerful, and moving\n"
        )

        performer_names = ", ".join(elders[eid].name for eid in elder_ids)

        self.conversation.add_user_message(
            f"[POETRY SLAM] Theme: \"{question}\"\n\n"
            f"Performers: {performer_names}.\n"
            f"The Slam MC will host the event."
        )

        # MC Opening
        performer_descriptions = "\n".join(
            f"- {e.name} ({e.title}, {e.era})" for e in elders.values()
        )
        opening_prompt = (
            SLAM_MC_PERSONA + "\n\n"
            f"Open this poetry slam! Form: {form_name.upper()}. In 1-2 sentences: "
            f"announce the theme \"{question}\" and invite the first poet to the stage.\n\n"
            f"Poets:\n{performer_descriptions}"
        )

        yield ("__moderator_start__", {"phase": "opening"})
        messages = self.conversation.to_messages(for_elder="__moderator__")
        opening_response = []
        for chunk in chat(messages, system=opening_prompt, stream=True):
            opening_response.append(chunk)
            yield ("__moderator__", chunk)
            if _count_sentences("".join(opening_response)) > mod_cap["opening"]:
                break

        self.conversation.add_elder_response(
            "__moderator__", "".join(opening_response), elder_name="Slam MC"
        )
        yield ("__moderator__", None)

        # Each elder performs
        for i, eid in enumerate(elder_ids):
            elder = elders[eid]

            context_note = (
                "\n\nYou have been called to the stage. The audience is waiting. "
                "Deliver your poem on this theme with everything you have."
            )
            if i > 0:
                context_note += " You've heard the previous poets — you may reference or contrast with their themes, but make this poem wholly yours."

            messages = self.conversation.to_messages(for_elder=eid)
            system_prompt = elder.system_prompt + poem_instruction + context_note

            full_response = []
            for chunk in chat(messages, system=system_prompt, stream=True):
                full_response.append(chunk)
                yield (eid, chunk)

            self.conversation.add_elder_response(
                eid, "".join(full_response), elder_name=elder.name
            )
            yield (eid, None)

            # MC scores/transitions (except after last poet — save for final verdict)
            if i < len(elder_ids) - 1:
                next_elder = elders[elder_ids[i + 1]]
                transition_prompt = (
                    SLAM_MC_PERSONA + "\n\n"
                    f"{elder.name} just performed. In 1 sentence, react and invite {next_elder.name} to the stage.\n"
                )

                yield ("__moderator_start__", {"phase": "transition"})
                messages = self.conversation.to_messages(for_elder="__moderator__")
                transition_response = []
                display_capped = False
                for chunk in chat(messages, system=transition_prompt, stream=True):
                    transition_response.append(chunk)
                    if not display_capped:
                        yield ("__moderator__", chunk)
                        if _count_sentences("".join(transition_response)) > mod_cap["transition"]:
                            display_capped = True

                self.conversation.add_elder_response(
                    "__moderator__", "".join(transition_response), elder_name="Slam MC"
                )
                yield ("__moderator__", None)

        # MC final verdict
        verdict_prompt = (
            SLAM_MC_PERSONA + "\n\n"
            "All poets have performed. In 1-2 sentences: declare the slam champion "
            "and close with one memorable line.\n"
        )

        yield ("__moderator_start__", {"phase": "takeaways"})
        messages = self.conversation.to_messages(for_elder="__moderator__")
        verdict_response = []
        for chunk in chat(messages, system=verdict_prompt, stream=True):
            verdict_response.append(chunk)
            yield ("__moderator__", chunk)
            if _count_sentences("".join(verdict_response)) > 4:
                break

        self.conversation.add_elder_response(
            "__moderator__", "".join(verdict_response), elder_name="Slam MC"
        )
        yield ("__moderator__", None)


def get_orchestrator() -> Orchestrator:
    """Get a new orchestrator instance."""
    return Orchestrator()
