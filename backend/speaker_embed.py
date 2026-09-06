"""
Real speaker embeddings for the SASV-style consistency check.

The original speaker_verifier.py builds an "embedding" out of raw MFCC means +
a couple of spectral stats — that's not an actual speaker-recognition
representation. This module uses Resemblyzer, a small pretrained speaker
encoder (d-vector style), so speaker similarity is based on a real trained
model instead of hand-picked acoustic stats.

Resemblyzer bundles its pretrained weights in the pip package itself, so
there's no separate model download step required.
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

_encoder = None


def _get_encoder():
    global _encoder
    if _encoder is None:
        from resemblyzer import VoiceEncoder
        _encoder = VoiceEncoder()
        logger.info("Loaded Resemblyzer voice encoder")
    return _encoder


def embed_audio(y: np.ndarray, sr: int = 16000) -> np.ndarray:
    """Return a real speaker embedding vector (256-d) for a chunk of audio."""
    from resemblyzer import preprocess_wav
    encoder = _get_encoder()
    wav = preprocess_wav(y, source_sr=sr)
    if len(wav) == 0:
        return np.zeros(256, dtype=np.float32)
    embedding = encoder.embed_utterance(wav)
    return embedding.astype(np.float32)


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    if v1 is None or v2 is None or len(v1) == 0 or len(v2) == 0:
        return 0.0
    denom = (np.linalg.norm(v1) * np.linalg.norm(v2)) + 1e-8
    sim = float(np.dot(v1, v2) / denom)
    return max(0.0, min(1.0, sim))
