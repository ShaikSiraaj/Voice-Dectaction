import numpy as np
import logging
from typing import Dict, Any, Optional
from backend.voice_detector import VoiceDetector

logger = logging.getLogger(__name__)

class SpeakerVerifier:
    """
    Spoofing-Aware Speaker Verification (SASV) module.
    Compares incoming stream audio features with enrolled speaker reference profiles.
    Calculates cosine similarity and detects voice print mismatch/anomaly.
    """

    def __init__(self):
        self.voice_detector = VoiceDetector()

    def create_speaker_embedding(self, audio_data: np.ndarray, sr: int = 16000) -> Dict[str, Any]:
        """Generate voice print signature profile from reference audio clip."""
        features = self.voice_detector.extract_acoustic_features(audio_data, sr)

        # Construct compact vector: 13 MFCC means + spectral centroid + bandwidth + pitch_mean
        embedding = np.array(
            features["mfcc_means"] + [
                features["spectral_centroid"],
                features["spectral_bandwidth"],
                features["pitch_mean"]
            ],
            dtype=np.float32
        )

        # Normalize vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return {
            "embedding_vector": embedding.tolist(),
            "pitch_mean": features["pitch_mean"],
            "spectral_centroid": features["spectral_centroid"]
        }

    def verify_speaker_identity(
        self,
        audio_chunk: np.ndarray,
        enrolled_profile: Optional[Dict[str, Any]] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
        sr: int = 16000
    ) -> Dict[str, Any]:
        """
        Verify incoming audio against enrolled speaker profile.
        Returns speaker anomaly score (0.0 = exact match, 1.0 = total mismatch/anomaly).
        """
        if context_metadata is None:
            context_metadata = {}

        # Allow context simulation override for scenario testing
        if "simulated_speaker_anomaly_score" in context_metadata:
            anomaly_score = float(context_metadata["simulated_speaker_anomaly_score"])
            return {
                "speaker_anomaly_score": round(anomaly_score, 4),
                "is_anomaly": anomaly_score > 0.50,
                "similarity_score": round(1.0 - anomaly_score, 4),
                "enrolled_speaker_found": True
            }

        if not enrolled_profile or "voice_print_data" not in enrolled_profile or not enrolled_profile["voice_print_data"]:
            # If no reference profile enrolled for caller, treat as baseline unknown speaker anomaly
            return {
                "speaker_anomaly_score": 0.45,  # Moderate score for unknown/unenrolled speaker
                "is_anomaly": False,
                "similarity_score": 0.55,
                "enrolled_speaker_found": False
            }

        # Extract current chunk embedding
        current_profile = self.create_speaker_embedding(audio_chunk, sr)
        v1 = np.array(current_profile["embedding_vector"], dtype=np.float32)

        ref_data = enrolled_profile["voice_print_data"]
        v2 = np.array(ref_data.get("embedding_vector", []), dtype=np.float32)

        if len(v1) != len(v2) or len(v2) == 0:
            return {
                "speaker_anomaly_score": 0.50,
                "is_anomaly": True,
                "similarity_score": 0.50,
                "enrolled_speaker_found": True
            }

        # Cosine similarity
        similarity = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8))
        similarity = max(0.0, min(1.0, similarity))

        anomaly_score = float(np.clip(1.0 - similarity, 0.0, 1.0))

        return {
            "speaker_anomaly_score": round(anomaly_score, 4),
            "is_anomaly": anomaly_score > 0.50,
            "similarity_score": round(similarity, 4),
            "enrolled_speaker_found": True
        }
