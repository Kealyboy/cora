import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
OUTPUT_DEVICE = None

def _tone(freq, duration, volume=0.3):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.sin(2 * np.pi * freq * t)
    envelope = np.ones_like(wave)
    fade = int(SAMPLE_RATE * 0.01)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    return (wave * envelope * volume).astype(np.float32)

def _play(audio):
    sd.play(audio, samplerate=SAMPLE_RATE, device=OUTPUT_DEVICE)
    sd.wait()

def wake_chime():
    first = _tone(880, 0.12)
    gap = np.zeros(int(SAMPLE_RATE * 0.04), dtype=np.float32)
    second = _tone(1100, 0.18)
    _play(np.concatenate([first, gap, second]))

def thinking_tone():
    tone = _tone(440, 0.15, volume=0.15)
    gap = np.zeros(int(SAMPLE_RATE * 0.1), dtype=np.float32)
    _play(np.concatenate([tone, gap, tone]))

def error_tone():
    _play(_tone(300, 0.3, volume=0.25))
