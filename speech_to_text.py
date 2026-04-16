"""Microphone speech-to-text using faster-whisper (base model)."""

from __future__ import annotations

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
# Input device index 1: Elgato Wave:3 (see `python -m sounddevice` for your list).
INPUT_DEVICE_INDEX = 1
CHUNK_S = 0.03
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_S)
# End utterance after this many consecutive silent chunks (~0.6s at 30ms/chunk).
SILENCE_CHUNKS_TO_STOP = 20
# Hard cap on capture length (~45s at 30ms/chunk).
MAX_CHUNKS = 1500

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def _rms(chunk: np.ndarray) -> float:
    if chunk.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(chunk.astype(np.float64)))))


def _record_chunk() -> np.ndarray:
    block = sd.rec(
        CHUNK_SAMPLES,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.float32,
        device=INPUT_DEVICE_INDEX,
    )
    sd.wait()
    return np.squeeze(block, axis=-1)


def _estimate_noise_floor() -> float:
    levels: list[float] = []
    for _ in range(15):
        levels.append(_rms(_record_chunk()))
    return float(np.median(levels))


def listen() -> str:
    """Record from the mic until post-speech silence, then return transcribed text."""
    print("Listening...")
    noise = _estimate_noise_floor()
    speech_on = max(noise * 4.0, 0.018)
    speech_off = max(noise * 2.2, 0.010)

    buffer: list[np.ndarray] = []
    speech_started = False
    silent_run = 0

    for _ in range(MAX_CHUNKS):
        chunk = _record_chunk()
        level = _rms(chunk)

        if not speech_started:
            if level >= speech_on:
                speech_started = True
                buffer.append(chunk)
            continue

        buffer.append(chunk)
        if level <= speech_off:
            silent_run += 1
            if silent_run >= SILENCE_CHUNKS_TO_STOP:
                break
        else:
            silent_run = 0

    if not buffer:
        return ""

    print("Processing...")
    audio = np.concatenate(buffer, axis=0)
    segments, _info = _get_model().transcribe(
        audio,
        language="en",
        vad_filter=True,
    )
    parts: list[str] = []
    for seg in segments:
        t = seg.text.strip()
        if t:
            parts.append(t)
    return " ".join(parts).strip()
