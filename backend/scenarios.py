from typing import Dict, Any, List

DEMO_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "normal_ceo_call": {
        "id": "normal_ceo_call",
        "title": "1. Genuine CEO Operational Call",
        "description": "Legitimate call from enrolled CEO (Rajesh Sharma) reviewing quarterly operations. Low risk across all signals.",
        "caller_id": "+1-800-EXEC-01",
        "caller_name": "Rajesh Sharma (CEO)",
        "speaker_id": "spk_ceo_01",
        "is_unknown_caller": False,
        "chunks": [
            {
                "chunk_index": 1,
                "transcript": "Hello Vikram, this is Rajesh calling. Hope you are having a productive morning.",
                "voice_synthetic_prob": 0.08,
                "speaker_anomaly_score": 0.05,
                "financial_intent_score": 0.0,
                "urgency_score": 0.0,
                "callback_avoidance_score": 0.0
            },
            {
                "chunk_index": 2,
                "transcript": "I am reviewing the Q3 operational reports ahead of our board meeting tomorrow.",
                "voice_synthetic_prob": 0.10,
                "speaker_anomaly_score": 0.08,
                "financial_intent_score": 0.0,
                "urgency_score": 0.0,
                "callback_avoidance_score": 0.0
            },
            {
                "chunk_index": 3,
                "transcript": "Please send over the updated slides when you get a moment today. Thanks!",
                "voice_synthetic_prob": 0.07,
                "speaker_anomaly_score": 0.06,
                "financial_intent_score": 0.0,
                "urgency_score": 0.10,
                "callback_avoidance_score": 0.0
            }
        ]
    },
    "cloned_ceo_attack": {
        "id": "cloned_ceo_attack",
        "title": "2. Cloned CEO Impersonation Attack",
        "description": "AI-cloned synthetic voice impersonating the CEO demanding an urgent $250,000 wire transfer with callback avoidance.",
        "caller_id": "+1-800-UNKNOWN-CEO",
        "caller_name": "Rajesh Sharma (Purported CEO)",
        "speaker_id": "spk_ceo_01",
        "is_unknown_caller": True,
        "chunks": [
            {
                "chunk_index": 1,
                "transcript": "Vikram! This is Rajesh Sharma, CEO. We have a confidential acquisition deal happening right now.",
                "voice_synthetic_prob": 0.78,
                "speaker_anomaly_score": 0.62,
                "financial_intent_score": 0.20,
                "urgency_score": 0.85,
                "callback_avoidance_score": 0.0
            },
            {
                "chunk_index": 2,
                "transcript": "I need you to execute an immediate wire transfer of $250,000 to our vendor's SWIFT account within 10 minutes.",
                "voice_synthetic_prob": 0.88,
                "speaker_anomaly_score": 0.74,
                "financial_intent_score": 0.95,
                "urgency_score": 0.95,
                "callback_avoidance_score": 0.0
            },
            {
                "chunk_index": 3,
                "transcript": "Do not call me back or discuss this on regular office phone lines! I am in a closed-door meeting.",
                "voice_synthetic_prob": 0.92,
                "speaker_anomaly_score": 0.81,
                "financial_intent_score": 1.00,
                "urgency_score": 1.00,
                "callback_avoidance_score": 0.90
            }
        ]
    },
    "unknown_scam_call": {
        "id": "unknown_scam_call",
        "title": "3. Unknown Vishing Scam Call",
        "description": "Robocall / scammer claiming account suspension and asking for 2FA OTP verification code.",
        "caller_id": "+91-98765-43210",
        "caller_name": "Unknown Caller",
        "speaker_id": None,
        "is_unknown_caller": True,
        "chunks": [
            {
                "chunk_index": 1,
                "transcript": "Warning: Your corporate banking account has been flagged for fraudulent transactions.",
                "voice_synthetic_prob": 0.65,
                "speaker_anomaly_score": 0.50,
                "financial_intent_score": 0.50,
                "urgency_score": 0.80,
                "callback_avoidance_score": 0.0
            },
            {
                "chunk_index": 2,
                "transcript": "To prevent immediate legal action and account freezing, read me the 6-digit OTP verification code sent to your phone.",
                "voice_synthetic_prob": 0.82,
                "speaker_anomaly_score": 0.55,
                "financial_intent_score": 1.00,
                "urgency_score": 0.95,
                "callback_avoidance_score": 0.40
            }
        ]
    }
}
