"""TTS provider factory."""

from council.config import load_config
from council.tts.base import TTSProvider


def get_tts_provider() -> TTSProvider:
    """
    Return the configured TTS provider.

    Fallback chain:
      1. If tts_provider != "elevenlabs" → macOS
      2. If no API key set → macOS (silent fallback)
      3. If elevenlabs package not installed → macOS (log warning)
      4. Otherwise → ElevenLabs
    """
    config = load_config()

    if config.get("tts_provider") == "elevenlabs":
        api_key = config.get("elevenlabs_api_key", "")
        if not api_key:
            # Silent fallback — no key configured
            from council.tts.macos import MacOSTTSProvider
            return MacOSTTSProvider()

        try:
            from council.tts.elevenlabs import ElevenLabsTTSProvider
            return ElevenLabsTTSProvider()
        except ImportError:
            print("[tts] elevenlabs package not installed, falling back to macOS. "
                  "Install with: pip install council-of-elders[tts]")
            from council.tts.macos import MacOSTTSProvider
            return MacOSTTSProvider()

    from council.tts.macos import MacOSTTSProvider
    return MacOSTTSProvider()
