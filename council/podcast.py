"""Podcast generation — converts council responses to audio using pluggable TTS."""

import io
import os
import tempfile
import wave

from council.tts import get_tts_provider


def _concat_wavs(wav_parts: list[bytes], output_path: str):
    """Concatenate multiple WAV byte buffers into one WAV file."""
    if not wav_parts:
        return

    with wave.open(output_path, "w") as out:
        params_set = False
        for data in wav_parts:
            with wave.open(io.BytesIO(data), "r") as w:
                if not params_set:
                    out.setparams(w.getparams())
                    params_set = True
                out.writeframes(w.readframes(w.getnframes()))


def _concat_mp3s(mp3_parts: list[bytes], output_path: str):
    """Concatenate MP3 parts into a clean, browser-compatible MP3 via ffmpeg.

    Raw binary append of MP3 chunks from different sources (ElevenLabs API
    + generated silence frames) produces files with invalid frame boundaries
    that trip up browser <audio> decoders. Re-encoding through ffmpeg fixes this.
    """
    import subprocess
    import shutil

    # Fallback to raw append if ffmpeg is not available
    if not shutil.which("ffmpeg"):
        with open(output_path, "wb") as out:
            for data in mp3_parts:
                out.write(data)
        return

    tmpdir = tempfile.mkdtemp(prefix="podcast_")
    try:
        # Write each part to a temp file
        part_paths = []
        for i, data in enumerate(mp3_parts):
            p = os.path.join(tmpdir, f"part_{i:04d}.mp3")
            with open(p, "wb") as f:
                f.write(data)
            part_paths.append(p)

        # Build ffmpeg concat list
        list_path = os.path.join(tmpdir, "concat.txt")
        with open(list_path, "w") as f:
            for p in part_paths:
                f.write(f"file '{p}'\n")

        # Re-encode into a single clean MP3
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", list_path, "-codec:a", "libmp3lame",
                "-b:a", "128k", "-ar", "44100", "-ac", "2",
                output_path,
            ],
            check=True, capture_output=True,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def count_tts_segments(segments: list[dict]) -> int:
    """Count segments that require TTS API calls (for progress estimates)."""
    count = 0
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        seg_type = seg.get("type", "narrator")
        if seg_type == "elder":
            count += 2  # name intro + speech
        else:
            count += 1
    return count


def generate_podcast(
    segments: list[dict],
    output_path: str,
    mode: str = "",
    on_progress: callable = None,
) -> tuple[str, str]:
    """
    Generate a podcast from conversation segments.

    Args:
        segments: List of dicts with keys:
            - type: 'narrator' | 'elder' | 'user'
            - text: The text to speak
            - elder_id: (for 'elder' type) the elder's ID
            - name: (for 'elder' type) the elder's display name
        output_path: Base path for the output file (extension will be adjusted)
        mode: Discussion mode ('rap', 'poetry', or '' for standard).
        on_progress: Optional callback(current, total) called after each TTS call.

    Returns:
        Tuple of (actual_output_path, audio_format) where format is 'wav' or 'mp3'.
    """
    provider = get_tts_provider()
    fmt = provider.get_audio_format()
    ext = provider.get_file_extension()

    # Adjust output path to match the provider's format
    base = os.path.splitext(output_path)[0]
    actual_path = base + ext

    total_calls = count_tts_segments(segments)
    current_call = 0
    audio_parts = []

    def _progress():
        nonlocal current_call
        current_call += 1
        if on_progress:
            on_progress(current_call, total_calls)

    for seg in segments:
        seg_type = seg.get("type", "narrator")
        text = seg.get("text", "").strip()
        if not text:
            continue

        try:
            if seg_type == "elder":
                elder_id = seg.get("elder_id", "")
                name = seg.get("name", "Elder")

                # Intro: narrator says the elder's name
                intro_audio = provider.synthesize(f"{name}.", "", role="narrator", mode=mode)
                audio_parts.append(intro_audio)
                _progress()

                # Brief pause
                pause_audio = provider.generate_silence(600)
                audio_parts.append(pause_audio)

                # Elder speaks
                elder_audio = provider.synthesize(text, elder_id, role="elder", mode=mode)
                audio_parts.append(elder_audio)
                _progress()

            elif seg_type == "narrator":
                nar_audio = provider.synthesize(text, "", role="narrator", mode=mode)
                audio_parts.append(nar_audio)
                _progress()

            elif seg_type == "user":
                user_audio = provider.synthesize(text, "", role="user", mode=mode)
                audio_parts.append(user_audio)
                _progress()

            # Pause between segments
            gap_audio = provider.generate_silence(1000)
            audio_parts.append(gap_audio)

        except Exception as e:
            import traceback
            print(f"[podcast] Error synthesizing segment ({seg_type}): {e}")
            traceback.print_exc()
            # Add silence placeholder so the podcast continues
            audio_parts.append(provider.generate_silence(500))
            continue

    # Concatenate all parts
    print(f"[podcast] Concatenating {len(audio_parts)} parts, sizes: {[len(p) for p in audio_parts]}")
    if fmt == "wav":
        _concat_wavs(audio_parts, actual_path)
    else:
        _concat_mp3s(audio_parts, actual_path)
    print(f"[podcast] Written to {actual_path} ({os.path.getsize(actual_path)} bytes)")

    return actual_path, fmt
