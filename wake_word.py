"""Wake-word detection for CORA using openWakeWord."""

from __future__ import annotations

import numpy as np
import sounddevice as sd
from openwakeword.model import Model

SAMPLE_RATE = 16000
INPUT_DEVICE_INDEX = 1
CHUNK_SAMPLES = 1280
DETECTION_THRESHOLD = 0.5


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

            scores = model.predict(samples)
            if not isinstance(scores, dict):
                continue

            for model_name, score in scores.items():
                if "jarvis" in model_name.lower() and float(score) >= DETECTION_THRESHOLD:
                    print("Wake word detected!")
                    return True
