import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.voice_detector import VoiceDetector
from backend.speaker_verifier import SpeakerVerifier
from backend.nlp_processor import NLPProcessor
from backend.risk_engine import RiskEngine
from backend.scenarios import DEMO_SCENARIOS

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"

def test_scenarios_endpoint():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "normal_ceo_call" in data
    assert "cloned_ceo_attack" in data
    assert "unknown_scam_call" in data

def test_voice_detector_analysis():
    vd = VoiceDetector()
    audio_sample = np.random.randn(16000 * 2)  # 2 seconds white noise
    res = vd.analyze_audio_chunk(audio_sample)
    assert "synthetic_probability" in res
    assert 0.0 <= res["synthetic_probability"] <= 1.0
    assert "acoustic_features" in res
    assert "mfcc_means" in res["acoustic_features"]

def test_speaker_verifier():
    sv = SpeakerVerifier()
    audio1 = np.random.randn(16000 * 2)
    profile = sv.create_speaker_embedding(audio1)
    assert "embedding_vector" in profile
    assert len(profile["embedding_vector"]) == 16

    # Verify against own embedding
    match_res = sv.verify_speaker_identity(audio1, {"voice_print_data": profile})
    assert match_res["similarity_score"] > 0.80
    assert match_res["speaker_anomaly_score"] < 0.20

def test_nlp_processor():
    nlp = NLPProcessor()
    text = "Please initiate an urgent wire transfer of $10000 to SWIFT account immediately. Do not call me back."
    res = nlp.process_transcript(text)
    assert res["financial_intent_score"] >= 0.60
    assert res["urgency_score"] >= 0.60
    assert res["callback_avoidance_score"] >= 0.60
    assert "wire transfer" in res["flagged_keywords"]

def test_risk_engine_fusion():
    re = RiskEngine()
    # High risk inputs
    high_risk_fused = re.fuse_signals(
        voice_synthetic_prob=0.90,
        speaker_anomaly_score=0.85,
        financial_intent_score=1.00,
        urgency_score=0.90,
        callback_avoidance_score=0.80,
        is_unknown_caller=True
    )
    assert high_risk_fused["fused_risk_score"] >= 70.0
    assert high_risk_fused["risk_level"] == "HIGH"
    assert "explainability_breakdown" in high_risk_fused

    # Low risk inputs
    low_risk_fused = re.fuse_signals(
        voice_synthetic_prob=0.05,
        speaker_anomaly_score=0.05,
        financial_intent_score=0.0,
        urgency_score=0.0,
        callback_avoidance_score=0.0,
        is_unknown_caller=False
    )
    assert low_risk_fused["fused_risk_score"] < 40.0
    assert low_risk_fused["risk_level"] == "LOW"

def test_verification_api():
    payload = {
        "call_id": "test_call_001",
        "action_type": "MFA_CHALLENGE",
        "details": "Trigger push MFA token"
    }
    response = client.post("/api/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["call_id"] == "test_call_001"
    assert "status" in data

def test_speakers_api():
    response = client.get("/api/speakers")
    assert response.status_code == 200
    speakers = response.json()
    assert isinstance(speakers, list)
