"""ElevenLabs voice ID mapping for Council elders."""

from council.config import load_config

# Curated mapping: elder_id -> ElevenLabs premade voice ID
# Selection criteria: gender match, accent/cultural fit, age/gravitas, uniqueness
# Voice IDs are from ElevenLabs' premade voice library.
ELEVENLABS_VOICE_MAP = {
    # Philosophers & spiritual leaders
    "aurelius": "onwK4e9ZLuTAKqWW03F9",    # Daniel — British, authoritative
    "laotzu": "ZQe5CZNOzWyzPSCn5a3c",      # James — calm, contemplative
    "buddha": "Yko7PKs96IMtcIMkMoGw",       # Ethan — gentle, warm
    "seneca": "N2lVS1w4EtoT3dr4eOWO",       # Callum — older, direct (replaces Munger)
    "epicurus": "ErXwobaYiN019PkySvjV",      # Antoni — thoughtful (replaces Naval)
    "dogen": "jsCqWAovK2LkecY7zXl4",        # Freya — soft, meditative (replaces Thich)
    "rumi": "bVMeCyTHy58xNoL34h3p",         # Jeremy — mindful, measured (replaces Kabat-Zinn)

    # Investors & business
    "graham": "TX3LPaxmHKxFdv7VOQHJ",      # Liam — warm, professorial (replaces Buffett)
    "walker": "XrExE9yKIg1WjnnlVkGX",       # Matilda — elegant, poised (replaces Lauder)

    # Strategists & warriors
    "sun_tzu": "VR6AewLTigWG4xSOukaG",      # Arnold — commanding
    "musashi": "pqHfZKP75CvOlQylNhV4",      # Bill — disciplined
    "hannibal": "EXAVITQu4vr4xnSDxMaL",     # Sarah — strong presence
    "genghis": "ODq5zmih8GrVes37Dizd",       # Patrick — powerful, deep
    "boudicca": "21m00Tcm4TlvDq8ikWAM",     # Rachel — fierce, articulate
    "machiavelli": "nPczCjzI2devNBz1zQrb",   # Brian — strategic, smooth (replaces Greene)
    "thucydides": "g5CIjZEefAph4nQFvHAz",   # Ethan (alt) — clear, methodical (replaces Tetlock)

    # Thinkers & scientists
    "franklin": "IKne3meq5aSn9XLyUdCD",     # Charlie — inventive, curious
    "davinci": "XB0fDUnXU5powFXDhCwa",      # Charlotte — creative, warm
    "jung": "GBv7mTt0atIp3Br8iCZE",         # Thomas — deep, analytical
    "bacon": "SOYHLrjzK2X1ezoPC6cr",        # Harry — intellectual, precise (replaces Kahneman)
    "william_james": "AZnzlk1XvdvUeBnXmlld", # Domi — clear, motivational (replaces Clear)
    "meadows": "ThT5KcBeYPX3keUQqHPh",      # Dorothy — systems thinker, warm

    # Leaders & cultural figures
    "tubman": "jBpfuIE2acCO8z3wKNLl",       # Gigi — strong, courageous
    "sojourner_truth": "pFZP5JQG7iQjIQuC4Bku", # Lily — warm, engaging (replaces Oprah)
    "branden": "oWAxZDx7w5VEj9dCyTzz",      # Grace — empowering
}

# Default voice for unknown elders
DEFAULT_VOICE_ID = "onwK4e9ZLuTAKqWW03F9"  # Daniel

# Narrator voice
NARRATOR_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel

# Rap Battle voices — bolder, more energetic voice selections
# Used when discussion mode is 'rap'
ELEVENLABS_RAP_VOICE_MAP = {
    "aurelius": "ODq5zmih8GrVes37Dizd",    # Patrick — powerful, deep
    "laotzu": "VR6AewLTigWG4xSOukaG",      # Arnold — commanding presence
    "buddha": "ErXwobaYiN019PkySvjV",       # Antoni — expressive
    "seneca": "N2lVS1w4EtoT3dr4eOWO",       # Callum — gruff authority
    "graham": "TX3LPaxmHKxFdv7VOQHJ",      # Liam — confident
    "epicurus": "ErXwobaYiN019PkySvjV",      # Antoni — rhythmic
    "sun_tzu": "VR6AewLTigWG4xSOukaG",      # Arnold — commanding
    "machiavelli": "nPczCjzI2devNBz1zQrb",   # Brian — smooth flow
    "jung": "GBv7mTt0atIp3Br8iCZE",         # Thomas — deep resonance
    "sojourner_truth": "pFZP5JQG7iQjIQuC4Bku", # Lily — powerful delivery
    "thucydides": "g5CIjZEefAph4nQFvHAz",   # Ethan — commanding
    "rumi": "bVMeCyTHy58xNoL34h3p",         # Jeremy — melodic
}

# Rap Battle Host voice
RAP_HOST_VOICE_ID = "VR6AewLTigWG4xSOukaG"  # Arnold — commanding MC energy

# Poetry Slam voices — more lyrical, emotional selections
# Used when discussion mode is 'poetry'
ELEVENLABS_POETRY_VOICE_MAP = {
    "aurelius": "onwK4e9ZLuTAKqWW03F9",    # Daniel — measured, dramatic
    "laotzu": "ZQe5CZNOzWyzPSCn5a3c",      # James — contemplative
    "buddha": "Yko7PKs96IMtcIMkMoGw",       # Ethan — gentle warmth
    "seneca": "N2lVS1w4EtoT3dr4eOWO",       # Callum — gravitas
    "rumi": "bVMeCyTHy58xNoL34h3p",         # Jeremy — mystical, lyrical
    "epicurus": "ErXwobaYiN019PkySvjV",      # Antoni — thoughtful
    "jung": "GBv7mTt0atIp3Br8iCZE",         # Thomas — deep, analytical
    "sojourner_truth": "pFZP5JQG7iQjIQuC4Bku", # Lily — emotional range
    "tubman": "jBpfuIE2acCO8z3wKNLl",       # Gigi — raw courage
    "dogen": "jsCqWAovK2LkecY7zXl4",        # Freya — meditative
}

# Poetry Slam MC voice
POETRY_MC_VOICE_ID = "ThT5KcBeYPX3keUQqHPh"  # Dorothy — warm, reverent


def get_elevenlabs_voice_id(elder_id: str, mode: str = "") -> str:
    """
    Get the ElevenLabs voice ID for an elder.

    Priority: user overrides > mode-specific map > curated map > default.

    Args:
        elder_id: The elder ID or special role like '__moderator__'
        mode: Discussion mode ('rap', 'poetry', or empty for standard)
    """
    config = load_config()
    overrides = config.get("elevenlabs_voice_overrides", {})

    # Check user override first
    if elder_id in overrides:
        return overrides[elder_id]

    # Mode-specific voice maps
    if mode == "rap":
        if elder_id == "__moderator__":
            return RAP_HOST_VOICE_ID
        return ELEVENLABS_RAP_VOICE_MAP.get(elder_id, ELEVENLABS_VOICE_MAP.get(elder_id, DEFAULT_VOICE_ID))

    if mode == "poetry":
        if elder_id == "__moderator__":
            return POETRY_MC_VOICE_ID
        return ELEVENLABS_POETRY_VOICE_MAP.get(elder_id, ELEVENLABS_VOICE_MAP.get(elder_id, DEFAULT_VOICE_ID))

    # Standard curated map
    return ELEVENLABS_VOICE_MAP.get(elder_id, DEFAULT_VOICE_ID)
