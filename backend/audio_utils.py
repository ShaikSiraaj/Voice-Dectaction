"""
Audio decoding utilities for Twilio Media Streams.

Twilio sends call audio as base64-encoded mu-law (G.711) PCM at 8kHz, 20ms frames.
Our models expect 16-bit linear PCM float32 at 16kHz, so we decode + resample here.

Implemented with plain numpy (no `audioop`, which is deprecated/removed in newer
Python versions) so this stays portable regardless of Python version.
"""
import base64
import numpy as np
import librosa

# Standard mu-law decode table (ITU-T G.711)
_MULAW_BIAS = 0x84
_MULAW_CLIP = 32635


def _mulaw_decode_sample(u_val: int) -> int:
    u_val = ~u_val & 0xFF
    sign = u_val & 0x80
    exponent = (u_val >> 4) & 0x07
    mantissa = u_val & 0x0F
    sample = ((mantissa << 3) + _MULAW_BIAS) << exponent
    sample -= _MULAW_BIAS
    if sign != 0:
        sample = -sample
    return sample


# Precompute the full 256-entry lookup table once (fast vectorized decode)
_MULAW_TABLE = np.array([_mulaw_decode_sample(i) for i in range(256)], dtype=np.int16)


def decode_mulaw_b64_to_pcm8k(b64_payload: str) -> np.ndarray:
    """Decode a base64 mu-law payload (as sent by Twilio) into float32 PCM at 8kHz, range [-1, 1]."""
    raw_bytes = base64.b64decode(b64_payload)
    u_vals = np.frombuffer(raw_bytes, dtype=np.uint8)
    pcm16 = _MULAW_TABLE[u_vals]
    pcm_float = pcm16.astype(np.float32) / 32768.0
    return pcm_float


def resample_8k_to_16k(y_8k: np.ndarray) -> np.ndarray:
    """Resample 8kHz audio to 16kHz to match what our detection models expect."""
    if len(y_8k) == 0:
        return y_8k
    return librosa.resample(y_8k, orig_sr=8000, target_sr=16000)
