"""
Real speech-to-text for live call chunks.

Uses faster-whisper (CTranslate2-optimized Whisper) so it runs fast on CPU,
which matters for keeping up with a live 2-4 second chunk cadence on a laptop.

First run downloads the model weights (one-time, needs internet). After that
it runs fully offline. Start with the "tiny" or "base" model for speed;
upgrade to "small" if your laptop can keep up and you want better accuracy.
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        # "tiny" = fastest, lowest accuracy. "base"/"small" = slower, better.
        # int8 compute_type keeps CPU inference fast.
        _model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.info("Loaded faster-whisper 'base' model on CPU")
    return _model


def transcribe_chunk(y: np.ndarray, sr: int = 16000, language: str = None) -> str:
    """
    Transcribe a short audio chunk (numpy float32, mono, `sr` Hz) to text.
    `language` can be set to e.g. "en", "hi", "te" to skip language auto-detection
    and speed things up if you know the call language in advance.
    """
    if y is None or len(y) < sr * 0.3:  # skip near-empty chunks
        return ""

    model = _get_model()
    segments, _info = model.transcribe(
        y,
        language=language,
        beam_size=1,          # greedy decoding = faster, fine for short chunks
        vad_filter=True,      # skip silent stretches within the chunk
        condition_on_previous_text=False,
    )
    text = " ".join(seg.text.strip() for seg in segments)
    return text.strip()
