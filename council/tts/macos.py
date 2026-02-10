"""macOS TTS provider using the `say` command."""

import io
import os
import subprocess
import tempfile
import wave

from council.tts.base import TTSProvider

# Map elder IDs to macOS voice names for distinct character
VOICE_MAP = {
    # Philosophers & spiritual leaders
    "aurelius": "Daniel",      # British — gravitas
    "laotzu": "Rishi",         # Indian English — contemplative
    "buddha": "Rishi",
    "thich": "Rishi",
    "kabatzinn": "Albert",

    # Investors & business
    "munger": "Fred",          # Older American — wise, blunt
    "buffett": "Fred",
    "naval": "Samantha",

    # Strategists & warriors
    "sun_tzu": "Aman",         # Indian English — measured
    "musashi": "Aman",
    "hannibal": "Daniel",
    "genghis": "Daniel",
    "boudicca": "Karen",       # Australian — fierce

    # Thinkers & scientists
    "franklin": "Albert",      # American — inventive
    "davinci": "Moira",        # Irish — creative
    "jung": "Daniel",
    "kahneman": "Albert",
    "tetlock": "Albert",
    "klein": "Fred",
    "meadows": "Tessa",        # South African
    "clear": "Samantha",

    # Leaders & cultural figures
    "tubman": "Karen",
    "oprah": "Samantha",
    "lauder": "Tessa",
    "bruce_lee": "Aman",
    "greene": "Fred",
    "branden": "Moira",
    "rubin": "Samantha",
}

NARRATOR_VOICE = "Samantha"
NARRATOR_RATE = 180
ELDER_RATE = 175

SAMPLE_RATE = 22050
SAMPLE_WIDTH = 2  # 16-bit
CHANNELS = 1


class MacOSTTSProvider(TTSProvider):
    """Free TTS using macOS `say` command."""

    def synthesize(self, text: str, voice_key: str, role: str = "elder", mode: str = "") -> bytes:
        if role == "narrator" or role == "user":
            voice = NARRATOR_VOICE
            rate = NARRATOR_RATE
        else:
            voice = VOICE_MAP.get(voice_key, "Daniel")
            rate = ELDER_RATE

        return _say_to_wav_bytes(text, voice, rate)

    def get_audio_format(self) -> str:
        return "wav"

    def get_mime_type(self) -> str:
        return "audio/wav"

    def get_file_extension(self) -> str:
        return ".wav"

    def generate_silence(self, duration_ms: int) -> bytes:
        n_frames = int(SAMPLE_RATE * duration_ms / 1000)
        buf = io.BytesIO()
        with wave.open(buf, "w") as w:
            w.setnchannels(CHANNELS)
            w.setsampwidth(SAMPLE_WIDTH)
            w.setframerate(SAMPLE_RATE)
            w.writeframes(b"\x00\x00" * n_frames)
        return buf.getvalue()


def _say_to_wav_bytes(text: str, voice: str, rate: int) -> bytes:
    """Use macOS `say` to generate WAV bytes."""
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp_aiff:
        aiff_path = tmp_aiff.name
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        wav_path = tmp_wav.name

    try:
        subprocess.run(
            ["say", "-v", voice, "-r", str(rate), "-o", aiff_path, text],
            check=True,
            capture_output=True,
            timeout=120,
        )
        subprocess.run(
            [
                "afconvert", "-f", "WAVE", "-d", "LEI16@22050",
                "-c", "1", aiff_path, wav_path,
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        for p in (aiff_path, wav_path):
            try:
                os.unlink(p)
            except OSError:
                pass
