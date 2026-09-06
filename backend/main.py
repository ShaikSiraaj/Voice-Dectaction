import json
import asyncio
import uuid
import os
import datetime
import logging
import librosa
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import engine, get_db, Base
from backend.models import Call, RiskAssessment, SpeakerProfile, VerificationAction
from backend.voice_detector import VoiceDetector
from backend.speaker_verifier import SpeakerVerifier
from backend.nlp_processor import NLPProcessor
from backend.risk_engine import RiskEngine
from backend.scenarios import DEMO_SCENARIOS
from backend.twilio_stream import router as twilio_router
from backend.dashboard_ws import router as dashboard_router
from backend import speaker_embed

logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VoiceGuard Real-Time Impersonation Detection API",
    description="Multi-signal real-time decision-support and impersonation prevention system API.",
    version="1.0.0"
)

# CORS setup for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML engines
voice_detector = VoiceDetector()
speaker_verifier = SpeakerVerifier()
nlp_processor = NLPProcessor()
risk_engine = RiskEngine()

# Pydantic Schemas
class SpeakerProfileCreate(BaseModel):
    id: str
    name: str
    role: str
    department: Optional[str] = "Executive"
    sample_text: Optional[str] = None

class VerificationActionRequest(BaseModel):
    call_id: str
    action_type: str  # MFA_CHALLENGE, CALLBACK_REQUEST, SUPERVISOR_ESCALATION
    details: Optional[str] = None

app.include_router(twilio_router)
app.include_router(dashboard_router)


@app.on_event("startup")
def seed_default_speaker_data():
    """Seed default CEO speaker profile if DB is empty."""
    db = next(get_db())
    existing = db.query(SpeakerProfile).filter(SpeakerProfile.id == "spk_ceo_01").first()
    if not existing:
        ceo_profile = SpeakerProfile(
            id="spk_ceo_01",
            name="Rajesh Sharma",
            role="Chief Executive Officer",
            department="Executive Board",
            voice_print_data={
                "embedding_vector": [0.05] * 16,
                "pitch_mean": 135.2,
                "spectral_centroid": 1850.0
            }
        )
        db.add(ceo_profile)
        db.commit()

@app.get("/api/health")
def health_check():
    return {"status": "HEALTHY", "system": "VoiceGuard Impersonation Prevention Engine", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.get("/api/scenarios")
def get_scenarios():
    """Returns preset demo scenarios."""
    return DEMO_SCENARIOS

@app.get("/api/calls")
def list_calls(db: Session = Depends(get_db)):
    """Returns call history audit log."""
    calls = db.query(Call).order_by(Call.start_time.desc()).all()
    result = []
    for c in calls:
        assessments_count = len(c.assessments)
        verifications_count = len(c.verifications)
        result.append({
            "id": c.id,
            "caller_id": c.caller_id,
            "caller_name": c.caller_name,
            "start_time": c.start_time.isoformat() if c.start_time else None,
            "status": c.status,
            "fused_risk_score": c.fused_risk_score,
            "risk_level": c.risk_level,
            "assessments_count": assessments_count,
            "verifications_count": verifications_count,
        })
    return result

@app.get("/api/calls/{call_id}")
def get_call_details(call_id: str, db: Session = Depends(get_db)):
    """Returns detailed call audit record with risk assessments and verifications."""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    assessments = db.query(RiskAssessment).filter(RiskAssessment.call_id == call_id).order_by(RiskAssessment.chunk_index.asc()).all()
    verifications = db.query(VerificationAction).filter(VerificationAction.call_id == call_id).order_by(VerificationAction.triggered_at.desc()).all()

    return {
        "call": {
            "id": call.id,
            "caller_id": call.caller_id,
            "caller_name": call.caller_name,
            "start_time": call.start_time.isoformat() if call.start_time else None,
            "status": call.status,
            "fused_risk_score": call.fused_risk_score,
            "risk_level": call.risk_level,
        },
        "assessments": [
            {
                "chunk_index": a.chunk_index,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                "voice_synthetic_prob": a.voice_synthetic_prob,
                "speaker_anomaly_score": a.speaker_anomaly_score,
                "financial_intent_score": a.financial_intent_score,
                "urgency_score": a.urgency_score,
                "fused_risk_score": a.fused_risk_score,
                "risk_level": a.risk_level,
                "transcript_snippet": a.transcript_snippet,
                "explainability_breakdown": a.explainability_breakdown
            } for a in assessments
        ],
        "verifications": [
            {
                "id": v.id,
                "action_type": v.action_type,
                "status": v.status,
                "triggered_at": v.triggered_at.isoformat() if v.triggered_at else None,
                "details": v.details
            } for v in verifications
        ]
    }

@app.get("/api/speakers")
def list_speakers(db: Session = Depends(get_db)):
    speakers = db.query(SpeakerProfile).all()
    return [{
        "id": s.id,
        "name": s.name,
        "role": s.role,
        "department": s.department,
        "created_at": s.created_at.isoformat() if s.created_at else None
    } for s in speakers]

@app.post("/api/speakers")
def create_speaker(profile: SpeakerProfileCreate, db: Session = Depends(get_db)):
    existing = db.query(SpeakerProfile).filter(SpeakerProfile.id == profile.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Speaker ID already exists")

    new_speaker = SpeakerProfile(
        id=profile.id,
        name=profile.name,
        role=profile.role,
        department=profile.department,
        voice_print_data={
            "embedding_vector": [0.04] * 16,
            "pitch_mean": 140.0,
            "spectral_centroid": 1900.0
        }
    )
    db.add(new_speaker)
    db.commit()
    return {"message": "Speaker enrolled successfully", "id": profile.id}

@app.post("/api/speakers/{speaker_id}/enroll-audio")
async def enroll_speaker_audio(speaker_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Enroll a REAL reference voice sample for a speaker (e.g. an actual recording
    of the CEO saying a few sentences). Replaces the placeholder embedding with
    a genuine Resemblyzer voice-print, used later to compare against live call audio.
    Upload a clean ~10-30 second WAV/MP3 of the person speaking normally.
    """
    speaker = db.query(SpeakerProfile).filter(SpeakerProfile.id == speaker_id).first()
    if not speaker:
        raise HTTPException(status_code=404, detail="Speaker not found")

    audio_bytes = await file.read()
    tmp_path = f"/tmp/{uuid.uuid4().hex}.wav"
    with open(tmp_path, "wb") as f:
        f.write(audio_bytes)

    y, sr = librosa.load(tmp_path, sr=16000, mono=True)
    os.remove(tmp_path)

    embedding = speaker_embed.embed_audio(y, sr=16000)

    speaker.voice_print_data = {
        **(speaker.voice_print_data or {}),
        "real_embedding": embedding.tolist(),
    }
    db.commit()

    return {"message": f"Real voice print enrolled for {speaker_id}", "embedding_dim": len(embedding)}


@app.post("/api/verify")
def trigger_verification_action(payload: VerificationActionRequest, db: Session = Depends(get_db)):
    """Simulates a step-up verification action (MFA Challenge, Callback, Escalation)."""
    call = db.query(Call).filter(Call.id == payload.call_id).first()
    if not call:
        call = Call(id=payload.call_id, caller_id="Unknown", caller_name="Live Stream Call", fused_risk_score=75.0, risk_level="HIGH")
        db.add(call)
        db.commit()

    if call.fused_risk_score > 70.0:
        action_status = "FAILED" if payload.action_type == "MFA_CHALLENGE" else "FLAGGED"
        details_str = payload.details or "MFA Verification failed - Voice biometric mismatch and caller failed push token."
        call.status = "BLOCKED"
    else:
        action_status = "PASSED"
        details_str = payload.details or "MFA Verification successful - Identity confirmed."
        call.status = "COMPLETED"

    action = VerificationAction(
        call_id=payload.call_id,
        action_type=payload.action_type,
        status=action_status,
        details=details_str
    )
    db.add(action)
    db.commit()

    return {
        "call_id": payload.call_id,
        "action_type": payload.action_type,
        "status": action_status,
        "details": details_str,
        "call_status": call.status
    }


@app.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for live 2-5s audio chunk streaming and real-time risk score broadcasts.
    """
    await _handle_ws_connection(websocket, db)

async def _handle_ws_connection(websocket: WebSocket, db: Session):
    await websocket.accept()
    call_id = f"call_{uuid.uuid4().hex[:8]}"

    # Initialize DB call session
    db_call = Call(
        id=call_id,
        caller_id="Live Audio Stream",
        caller_name="Inbound Streaming Call",
        status="ACTIVE",
        fused_risk_score=0.0,
        risk_level="LOW"
    )
    db.add(db_call)
    db.commit()

    try:
        while True:
            data_text = await websocket.receive_text()
            payload = json.loads(data_text)

            chunk_index = payload.get("chunk_index", 1)
            transcript = payload.get("transcript", "")

            sim_synthetic_prob = payload.get("voice_synthetic_prob")
            sim_speaker_anomaly = payload.get("speaker_anomaly_score")
            sim_financial = payload.get("financial_intent_score")
            sim_urgency = payload.get("urgency_score")
            sim_callback = payload.get("callback_avoidance_score")
            is_unknown_caller = payload.get("is_unknown_caller", True)

            # 1. Voice Analysis
            voice_context = {}
            if sim_synthetic_prob is not None:
                voice_context["simulated_voice_synthetic_prob"] = sim_synthetic_prob

            voice_res = voice_detector.analyze_audio_chunk(
                y=[], sr=16000,
                context_metadata=voice_context
            )
            v_prob = voice_res["synthetic_probability"]

            # 2. Speaker Verification (SASV)
            enrolled = db.query(SpeakerProfile).filter(SpeakerProfile.id == "spk_ceo_01").first()
            enrolled_dict = {"voice_print_data": enrolled.voice_print_data} if enrolled else None

            speaker_context = {}
            if sim_speaker_anomaly is not None:
                speaker_context["simulated_speaker_anomaly_score"] = sim_speaker_anomaly

            spk_res = speaker_verifier.verify_speaker_identity(
                audio_chunk=[],
                enrolled_profile=enrolled_dict,
                context_metadata=speaker_context
            )
            spk_anomaly = spk_res["speaker_anomaly_score"]

            # 3. NLP Intent Processing
            nlp_context = {}
            if sim_financial is not None:
                nlp_context["simulated_financial_intent_score"] = sim_financial
            if sim_urgency is not None:
                nlp_context["simulated_urgency_score"] = sim_urgency
            if sim_callback is not None:
                nlp_context["simulated_callback_avoidance_score"] = sim_callback

            nlp_res = nlp_processor.process_transcript(
                transcript,
                context_metadata=nlp_context
            )
            fin_score = nlp_res["financial_intent_score"]
            urg_score = nlp_res["urgency_score"]
            cb_score = nlp_res["callback_avoidance_score"]

            # 4. Risk Fusion Engine
            risk_res = risk_engine.fuse_signals(
                voice_synthetic_prob=v_prob,
                speaker_anomaly_score=spk_anomaly,
                financial_intent_score=fin_score,
                urgency_score=urg_score,
                callback_avoidance_score=cb_score,
                is_unknown_caller=is_unknown_caller
            )

            # Update call DB state
            db_call.fused_risk_score = risk_res["fused_risk_score"]
            db_call.risk_level = risk_res["risk_level"]
            db.commit()

            # Save assessment chunk
            assessment = RiskAssessment(
                call_id=call_id,
                chunk_index=chunk_index,
                voice_synthetic_prob=v_prob,
                speaker_anomaly_score=spk_anomaly,
                financial_intent_score=fin_score,
                urgency_score=urg_score,
                unknown_caller_score=1.0 if is_unknown_caller else 0.0,
                callback_avoidance_score=cb_score,
                fused_risk_score=risk_res["fused_risk_score"],
                risk_level=risk_res["risk_level"],
                transcript_snippet=transcript,
                explainability_breakdown=risk_res["explainability_breakdown"]
            )
            db.add(assessment)
            db.commit()

            # Send real-time risk payload back
            response_payload = {
                "call_id": call_id,
                "chunk_index": chunk_index,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "fused_risk_score": risk_res["fused_risk_score"],
                "risk_level": risk_res["risk_level"],
                "recommended_action": risk_res["recommended_action"],
                "transcript": transcript,
                "flagged_keywords": nlp_res["flagged_keywords"],
                "voice_analysis": voice_res,
                "speaker_verification": spk_res,
                "nlp_analysis": nlp_res,
                "explainability_breakdown": risk_res["explainability_breakdown"]
            }

            await websocket.send_text(json.dumps(response_payload))

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for call {call_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
