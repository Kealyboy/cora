"""Wake-word detection for CORA using openWakeWord."""

from __future__ import annotations

from threading import Event

import numpy as np
import sounddevice as sd
from openwakeword.model import Model

SAMPLE_RATE = 16000
INPUT_DEVICE_INDEX = 1
CHUNK_SAMPLES = 1280
DETECTION_THRESHOLD = 0.5

# When True, mic audio is discarded for wake-word scoring (e.g. during TTS playback).
_mic_muted: bool = False


def set_microphone_muted(muted: bool) -> None:
    """Mute wake-word detection while keeping the stream open (discards audio)."""
    global _mic_muted
    _mic_muted = muted


def is_microphone_muted() -> bool:
    return _mic_muted


def _score_wake(model: Model, samples: np.ndarray) -> bool:
    scores = model.predict(samples)
    if not isinstance(scores, dict):
        return False
    for model_name, score in scores.items():
        if "jarvis" in model_name.lower() and float(score) >= DETECTION_THRESHOLD:
            print("Wake word detected!")
            return True
    return False


def listen_until_wake_or_stop(stop: Event) -> bool:
    """
    Block until wake word is detected (return True) or ``stop`` is set (return False).
    Used while TTS runs on another thread so the mic can still hear the wake word.
    """
    model = Model(inference_framework="tflite")
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=CHUNK_SAMPLES,
        device=INPUT_DEVICE_INDEX,
    ) as stream:
        while not stop.is_set():
            audio_chunk, _overflowed = stream.read(CHUNK_SAMPLES)
            samples = np.squeeze(audio_chunk, axis=-1).astype(np.int16)

            if _mic_muted:
                continue

            if _score_wake(model, samples):
                return True
    return False


def listen_for_wake_word() -> bool:
    """Block until the Hey Jarvis wake word is detected, then return True."""
    model = Model(inference_framework="tflite")
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=CHUNK_SAMPLES,
        device=INPUT_DEVICE_INDEX,
    ) as stream:
        while True:
            audio_chunk, _overflowed = stream.read(CHUNK_SAMPLES)
            samples = np.squeeze(audio_chunk, axis=-1).astype(np.int16)

            if _mic_muted:
                continue

            if _score_wake(model, samples):
                return True
