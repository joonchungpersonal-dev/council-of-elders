"""ElevenLabs TTS provider for premium voices."""

import io
import struct
import time
import wave

from council.config import load_config
from council.tts.base import TTSProvider
from council.tts.voices import get_elevenlabs_voice_id, NARRATOR_VOICE_ID


class ElevenLabsTTSProvider(TTSProvider):
    """Premium TTS using ElevenLabs API."""

    def __init__(self):
        from elevenlabs import ElevenLabs

        config = load_config()
        api_key = config.get("elevenlabs_api_key", "")
        self._model = config.get("elevenlabs_model", "eleven_multilingual_v2")
        self._client = ElevenLabs(api_key=api_key)

    def synthesize(self, text: str, voice_key: str, role: str = "elder", mode: str = "") -> bytes:
        if role in ("narrator", "user"):
            voice_id = NARRATOR_VOICE_ID
        else:
            voice_id = get_elevenlabs_voice_id(voice_key, mode=mode)

        return self._synthesize_with_retry(text, voice_id)

    def get_audio_format(self) -> str:
        return "mp3"

    def get_mime_type(self) -> str:
        return "audio/mpeg"

    def get_file_extension(self) -> str:
        return ".mp3"

    def generate_silence(self, duration_ms: int) -> bytes:
        """Generate a silent MP3 frame sequence of approximately the given duration.

        Uses a minimal valid MP3 frame (MPEG1 Layer3, 128kbps, 44100Hz, mono)
        filled with silence. Each frame is ~26ms, so we repeat as needed.
        """
        # Minimal silent MP3 frame: MPEG1 Layer3 128kbps 44100Hz mono
        # Frame header: 0xFFFB9004, followed by zeros to fill 417 bytes
        frame_header = b"\xff\xfb\x90\x04"
        frame_size = 417  # bytes per frame at 128kbps/44100Hz
        frame_duration_ms = 26.122  # ms per frame

        num_frames = max(1, int(duration_ms / frame_duration_ms))
        silent_frame = frame_header + b"\x00" * (frame_size - len(frame_header))

        return silent_frame * num_frames

    def _synthesize_with_retry(self, text: str, voice_id: str, max_retries: int = 3) -> bytes:
        """Call ElevenLabs API with exponential backoff on rate limits."""
        for attempt in range(max_retries):
            try:
                audio_generator = self._client.text_to_speech.convert(
                    voice_id=voice_id,
                    text=text,
                    model_id=self._model,
                    output_format="mp3_44100_128",
                )
                # Collect all chunks from the generator
                chunks = []
                for chunk in audio_generator:
                    chunks.append(chunk)
                return b"".join(chunks)

            except Exception as e:
                error_str = str(e)
                # Retry on rate limit (429) errors
                if "429" in error_str or "rate" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait = 2 ** (attempt + 1)
                        print(f"[elevenlabs] Rate limited, retrying in {wait}s...")
                        time.sleep(wait)
                        continue
                raise
