"""Text-to-speech via Piper (subprocess) and WAV playback on Windows."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_PIPER_DIR = _BASE / "piper"
PIPER_EXE = _PIPER_DIR / "piper.exe"
VOICE_MODEL = _PIPER_DIR / "en_US-lessac-medium.onnx"


def speak(text: str) -> None:
    """Synthesize ``text`` with Piper to a WAV file, play it, then remove the temp file."""
    if not text.strip():
        return

    fd, wav_path_str = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    wav_path = Path(wav_path_str)

    try:
        subprocess.run(
            [
                str(PIPER_EXE),
                "--model",
                str(VOICE_MODEL),
                "--output_file",
                str(wav_path.resolve()),
            ],
            cwd=str(_PIPER_DIR),
            input=text.encode("utf-8"),
            check=True,
        )

        path_ps = str(wav_path.resolve()).replace("'", "''")
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                f"(New-Object System.Media.SoundPlayer('{path_ps}')).PlaySync()",
            ],
            check=True,
        )
    finally:
        try:
            wav_path.unlink(missing_ok=True)
        except OSError:
            pass
