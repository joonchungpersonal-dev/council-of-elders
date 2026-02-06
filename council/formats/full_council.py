"""
Full Council Debate Format

A structured format for maximum exposure to diverse wisdom perspectives.
Uses a 3-phase approach:

Phase 1: DOMAIN PERSPECTIVES (5 voices)
  - One elder from each major domain gives initial take
  - Business, Philosophy, Psychology, Creativity, Systems

Phase 2: DIALECTIC PAIRS (2-3 pairs)
  - Opposing viewpoints debate specific tensions
  - e.g., Action vs Non-action, Risk vs Safety, Individual vs Collective

Phase 3: SYNTHESIS (1-2 elders)
  - Integrative thinkers weave threads together
  - Usually Munger (mental models) or Aurelius (practical wisdom)

Total: 8-12 perspectives, structured for coherence
"""

from dataclasses import dataclass
from typing import Generator

# Domain representatives - one voice per major area
DOMAIN_REPRESENTATIVES = {
    "business": ["munger", "buffett", "naval", "greene"],
    "philosophy": ["aurelius", "seneca", "lao", "confucius"],
    "psychology": ["jung", "peterson", "branden", "frankl"],
    "creativity": ["rubin", "lee", "oprah", "franklin"],
    "systems": ["taleb", "feynman"],
}

# Dialectic pairs - opposing perspectives that create productive tension
DIALECTIC_PAIRS = [
    ("aurelius", "lao", "Action vs Wu Wei"),           # Stoic duty vs Taoist flow
    ("greene", "thich", "Strategy vs Compassion"),     # Power vs Peace
    ("taleb", "buffett", "Antifragility vs Patience"), # Volatility vs Steadiness
    ("peterson", "naval", "Responsibility vs Freedom"),# Order vs Liberation
    ("jung", "franklin", "Depth vs Pragmatism"),       # Inner work vs Outer results
    ("munger", "rubin", "Analysis vs Intuition"),      # Rational vs Creative
]

# Synthesizers - elders good at integrating multiple viewpoints
SYNTHESIZERS = ["munger", "aurelius", "naval", "frankl"]


@dataclass
class CouncilDebateConfig:
    """Configuration for a full council debate."""
    question: str
    # Which domains to include (default: all 5)
    domains: list[str] | None = None
    # How many dialectic pairs to run (0-3)
    dialectic_rounds: int = 2
    # Who synthesizes at the end
    synthesizer: str = "munger"
    # Include dissent/devil's advocate
    include_dissent: bool = True


def select_domain_representatives(domains: list[str] | None = None) -> dict[str, str]:
    """Select one elder from each domain based on the question context."""
    if domains is None:
        domains = list(DOMAIN_REPRESENTATIVES.keys())

    # For now, select first from each domain
    # Could be made smarter based on question analysis
    selected = {}
    for domain in domains:
        if domain in DOMAIN_REPRESENTATIVES:
            selected[domain] = DOMAIN_REPRESENTATIVES[domain][0]

    return selected


def select_dialectic_pairs(question: str, count: int = 2) -> list[tuple[str, str, str]]:
    """Select relevant dialectic pairs based on question themes."""
    # Simple keyword matching for now
    question_lower = question.lower()

    scored_pairs = []
    for elder1, elder2, theme in DIALECTIC_PAIRS:
        score = 0
        theme_words = theme.lower().split()
        for word in theme_words:
            if word in question_lower:
                score += 2
        # Add some variety
        scored_pairs.append((score, (elder1, elder2, theme)))

    # Sort by relevance, take top N
    scored_pairs.sort(key=lambda x: x[0], reverse=True)
    return [pair for _, pair in scored_pairs[:count]]


def get_phase1_prompt(question: str, domain: str, elder_id: str) -> str:
    """Generate prompt for Phase 1: Domain Perspectives."""
    return f"""You are participating in a council debate on this question:

"{question}"

You are representing the {domain.upper()} perspective. Give your initial take in 2-3 paragraphs.
Focus on what your domain uniquely contributes to this question.
Be direct and substantive - this is the opening round."""


def get_phase2_prompt(question: str, elder_id: str, opponent_id: str,
                      opponent_response: str, theme: str) -> str:
    """Generate prompt for Phase 2: Dialectic."""
    return f"""The council is debating: "{question}"

The theme of this dialectic round is: {theme}

Your counterpart {opponent_id} has argued:
---
{opponent_response}
---

Engage with their perspective. Where do you agree? Where do you see it differently?
What crucial insight might they be missing? Be respectful but direct.
2-3 paragraphs."""


def get_phase3_prompt(question: str, all_perspectives: list[dict]) -> str:
    """Generate prompt for Phase 3: Synthesis."""
    perspectives_text = "\n\n".join([
        f"**{p['elder']}** ({p['phase']}): {p['content'][:500]}..."
        for p in all_perspectives
    ])

    return f"""The council has debated: "{question}"

Here are the perspectives shared:
{perspectives_text}

As the synthesizer, weave these threads together:
1. What are the key agreements across perspectives?
2. What tensions remain unresolved, and why might that be valuable?
3. What practical wisdom emerges for someone facing this question?

Provide an integrative summary in 3-4 paragraphs."""


# Preset council configurations for common question types
COUNCIL_PRESETS = {
    "career": {
        "domains": ["business", "psychology", "philosophy"],
        "dialectic_pairs": [("greene", "thich", "Ambition vs Peace"),
                           ("peterson", "naval", "Responsibility vs Freedom")],
        "synthesizer": "munger",
    },
    "relationship": {
        "domains": ["psychology", "philosophy", "creativity"],
        "dialectic_pairs": [("jung", "confucius", "Individual vs Collective"),
                           ("branden", "thich", "Self-esteem vs Compassion")],
        "synthesizer": "aurelius",
    },
    "creative": {
        "domains": ["creativity", "psychology", "systems"],
        "dialectic_pairs": [("rubin", "munger", "Intuition vs Analysis"),
                           ("lee", "peterson", "Flow vs Structure")],
        "synthesizer": "naval",
    },
    "financial": {
        "domains": ["business", "systems", "philosophy"],
        "dialectic_pairs": [("taleb", "buffett", "Antifragility vs Patience"),
                           ("munger", "lao", "Action vs Non-action")],
        "synthesizer": "munger",
    },
    "existential": {
        "domains": ["philosophy", "psychology", "creativity"],
        "dialectic_pairs": [("aurelius", "lao", "Duty vs Flow"),
                           ("frankl", "naval", "Meaning vs Happiness")],
        "synthesizer": "frankl",
    },
    "full": {
        "domains": ["business", "philosophy", "psychology", "creativity", "systems"],
        "dialectic_pairs": DIALECTIC_PAIRS[:3],
        "synthesizer": "munger",
    },
}
