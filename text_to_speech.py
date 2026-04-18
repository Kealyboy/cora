"""Text-to-speech via Piper (subprocess) and WAV playback on Windows."""

from __future__ import annotations

import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import wake_word
from state_manager import ConversationState, StateManager

_BASE = Path(__file__).resolve().parent
_PIPER_DIR = _BASE / "piper"
PIPER_EXE = _PIPER_DIR / "piper.exe"
VOICE_MODEL = _PIPER_DIR / "en_US-lessac-medium.onnx"


def speak(text: str, state: StateManager) -> bool:
    """
    Synthesize with Piper, play WAV, then remove the temp file.

    Wake-word detection runs on a background thread during synthesis and playback
    so the user can interrupt TTS. If the wake word fires, Piper/playback is
    killed, state returns to IDLE, and this function returns False.

    Returns True if TTS finished normally, False if interrupted by wake word.
    """
    if not text.strip():
        return True

    stop_monitor = threading.Event()
    wake_detected = threading.Event()

    def wake_worker() -> None:
        try:
            if wake_word.listen_until_wake_or_stop(stop_monitor):
                wake_detected.set()
        except Exception:
            pass

    wt = threading.Thread(target=wake_worker, daemon=True)
    wt.start()

    fd, wav_path_str = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    wav_path = Path(wav_path_str)

    try:
        proc = subprocess.Popen(
            [
                str(PIPER_EXE),
                "--model",
                str(VOICE_MODEL),
                "--output_file",
                str(wav_path.resolve()),
            ],
            cwd=str(_PIPER_DIR),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            if proc.stdin is not None:
                proc.stdin.write(text.encode("utf-8"))
                proc.stdin.close()
        except BrokenPipeError:
            pass

        while proc.poll() is None:
            if wake_detected.is_set():
                proc.kill()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                state.set_state(ConversationState.IDLE)
                stop_monitor.set()
                wt.join(timeout=3)
                return False
            time.sleep(0.02)

        if wake_detected.is_set():
            state.set_state(ConversationState.IDLE)
            stop_monitor.set()
            wt.join(timeout=3)
            return False

        path_ps = str(wav_path.resolve()).replace("'", "''")
        play = subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                f"(New-Object System.Media.SoundPlayer('{path_ps}')).PlaySync()",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        while play.poll() is None:
            if wake_detected.is_set():
                play.kill()
                try:
                    play.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    play.kill()
                state.set_state(ConversationState.IDLE)
                stop_monitor.set()
                wt.join(timeout=3)
                return False
            time.sleep(0.02)

        try:
            play.wait(timeout=5)
        except subprocess.TimeoutExpired:
            play.kill()

        stop_monitor.set()
        wt.join(timeout=3)
        return True
    finally:
        stop_monitor.set()
        wt.join(timeout=2)
        try:
            wav_path.unlink(missing_ok=True)
        except OSError:
            pass
