"""Abstract base class for TTS providers."""

from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Interface for text-to-speech providers."""

    @abstractmethod
    def synthesize(self, text: str, voice_key: str, role: str = "elder", mode: str = "") -> bytes:
        """
        Convert text to audio bytes.

        Args:
            text: The text to speak.
            voice_key: Elder ID or role identifier for voice selection.
            role: 'elder', 'narrator', or 'user'.
            mode: Discussion mode ('rap', 'poetry', or '' for standard).

        Returns:
            Raw audio bytes in the provider's native format.
        """

    @abstractmethod
    def get_audio_format(self) -> str:
        """Return the audio format string, e.g. 'wav' or 'mp3'."""

    @abstractmethod
    def get_mime_type(self) -> str:
        """Return the MIME type, e.g. 'audio/wav' or 'audio/mpeg'."""

    @abstractmethod
    def get_file_extension(self) -> str:
        """Return the file extension including dot, e.g. '.wav' or '.mp3'."""

    @abstractmethod
    def generate_silence(self, duration_ms: int) -> bytes:
        """Generate silent audio of the given duration."""
