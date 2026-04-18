"""Microphone speech-to-text using faster-whisper (base model)."""

from __future__ import annotations

import math

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
        _model = WhisperModel("medium", device="cpu", compute_type="int8")
    return _model


def _rms(chunk: np.ndarray) -> float:
    if chunk.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(chunk.astype(np.float64)))))


def _create_input_stream() -> sd.InputStream:
    sd.check_input_settings(
        device=INPUT_DEVICE_INDEX,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    stream = sd.InputStream(
        device=INPUT_DEVICE_INDEX,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK_SAMPLES,
    )
    stream.start()
    actual_sample_rate = int(round(float(stream.samplerate)))
    if actual_sample_rate != SAMPLE_RATE:
        stream.stop()
        stream.close()
        raise RuntimeError(
            f"Microphone sample rate mismatch: expected {SAMPLE_RATE} Hz, "
            f"got {actual_sample_rate} Hz."
        )
    return stream


def _record_chunk(stream: sd.InputStream) -> np.ndarray:
    block, _overflowed = stream.read(CHUNK_SAMPLES)
    return np.squeeze(block, axis=-1)


def _estimate_noise_floor(stream: sd.InputStream) -> float:
    levels: list[float] = []
    for _ in range(15):
        levels.append(_rms(_record_chunk(stream)))
    return float(np.median(levels))


def listen(max_wait_seconds: float | None = None, verbose: bool = True) -> str:
    """Record from the mic until post-speech silence, then return transcribed text."""
    if verbose:
        print("Listening...")
    stream = _create_input_stream()
    try:
        noise = _estimate_noise_floor(stream)
        speech_on = max(noise * 4.0, 0.018)
        speech_off = max(noise * 2.2, 0.010)
        max_chunks = (
            min(MAX_CHUNKS, max(1, int(math.ceil(max_wait_seconds / CHUNK_S))))
            if max_wait_seconds is not None
            else MAX_CHUNKS
        )

        buffer: list[np.ndarray] = []
        speech_started = False
        silent_run = 0

        for _ in range(max_chunks):
            chunk = _record_chunk(stream)
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
    finally:
        stream.stop()
        stream.close()

    if not buffer:
        return ""

    if verbose:
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
