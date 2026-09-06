"""
Real phone call ingestion via Twilio Media Streams.

Flow:
  1. Someone calls your Twilio number.
  2. Twilio requests TwiML from POST /twilio/voice -> we tell it to open a
     <Stream> back to our WebSocket at /ws/twilio-stream.
  3. Twilio streams raw call audio (mu-law, 8kHz, 20ms frames) as base64 JSON
     messages over that WebSocket in real time.
  4. We buffer ~3 seconds of audio, decode + resample to 16kHz, then run it
     through the REAL pipeline: voice_detector, resemblyzer speaker
     similarity, faster-whisper transcription, nlp_processor, risk_engine.
  5. Each chunk's result is saved to the DB and broadcast to any dashboard
     websocket clients watching that call_id.

This replaces the simulated/scripted path used in main.py's /ws/stream demo
endpoint (which only ever replays scenarios.py numbers) with one that
processes actual audio.
"""
import json
import base64
import logging
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import Call, RiskAssessment, SpeakerProfile
from backend.voice_detector import VoiceDetector
from backend.nlp_processor import NLPProcessor
from backend.risk_engine import RiskEngine
from backend import audio_utils, asr, speaker_embed
from backend.dashboard_ws import broadcast_to_dashboard

logger = logging.getLogger(__name__)
router = APIRouter()

voice_detector = VoiceDetector()
nlp_processor = NLPProcessor()
risk_engine = RiskEngine()

CHUNK_SECONDS = 3.0
BYTES_PER_20MS_FRAME = 160  # mu-law, 8kHz, 20ms = 160 samples = 160 bytes
FRAMES_PER_CHUNK = int((CHUNK_SECONDS * 1000) / 20)  # how many 20ms frames make one chunk


def build_twilio_twiml(request: Request) -> str:
    """Shared TwiML builder for both legacy and canonical Twilio webhook paths."""
    host = request.headers.get("host")
    stream_url = f"wss://{host}/ws/twilio-stream"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>This call is being monitored for voice security verification.</Say>
  <Connect>
    <Stream url="{stream_url}" />
  </Connect>
</Response>"""


@router.post("/voice")
@router.post("/twilio/voice")
async def twilio_voice_webhook(request: Request):
    """
    TwiML instructions Twilio follows when your number is called.
    Accepts both /voice and /twilio/voice for compatibility with older configs.
    """
    twiml = build_twilio_twiml(request)
    return Response(content=twiml, media_type="application/xml")


@router.websocket("/ws/twilio-stream")
async def twilio_media_stream(websocket: WebSocket):
    await websocket.accept()
    db: Session = SessionLocal()

    call_id = None
    mulaw_buffer = bytearray()
    frame_count = 0
    chunk_index = 0
    enrolled_embedding = None  # loaded once we know which speaker profile to check against

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            event = msg.get("event")

            if event == "connected":
                logger.info("Twilio media stream connected")

            elif event == "start":
                start_data = msg["start"]
                call_id = start_data["callSid"]
                from_number = start_data.get("customParameters", {}).get("from", "Unknown")

                db_call = Call(
                    id=call_id,
                    caller_id=from_number,
                    caller_name="Live Phone Call",
                    status="ACTIVE",
                    fused_risk_score=0.0,
                    risk_level="LOW",
                )
                db.merge(db_call)
                db.commit()
                logger.info(f"Call started: {call_id}")

                # Load the enrolled reference speaker (default: CEO profile) for comparison
                enrolled = db.query(SpeakerProfile).filter(SpeakerProfile.id == "spk_ceo_01").first()
                if enrolled and enrolled.voice_print_data and "real_embedding" in enrolled.voice_print_data:
                    enrolled_embedding = np.array(enrolled.voice_print_data["real_embedding"], dtype=np.float32)

            elif event == "media":
                payload_b64 = msg["media"]["payload"]
                mulaw_buffer.extend(base64.b64decode(payload_b64))
                frame_count += 1

                if frame_count >= FRAMES_PER_CHUNK:
                    chunk_index += 1
                    await _process_chunk(
                        db, call_id, chunk_index, bytes(mulaw_buffer),
                        enrolled_embedding
                    )
                    mulaw_buffer = bytearray()
                    frame_count = 0

            elif event == "stop":
                logger.info(f"Call ended: {call_id}")
                if call_id:
                    db_call = db.query(Call).filter(Call.id == call_id).first()
                    if db_call:
                        db_call.status = "COMPLETED"
                        db.commit()
                break

    except WebSocketDisconnect:
        logger.info(f"Twilio stream disconnected for call {call_id}")
    except Exception as e:
        logger.error(f"Twilio stream error: {e}", exc_info=True)
    finally:
        db.close()


async def _process_chunk(db: Session, call_id: str, chunk_index: int, mulaw_bytes: bytes, enrolled_embedding):
    """Decode, run the real pipeline, save, and broadcast one ~3s chunk of real call audio."""
    # 1. Decode mu-law bytes -> float32 PCM, resample 8kHz -> 16kHz
    b64_payload = base64.b64encode(mulaw_bytes).decode("ascii")
    y_8k = audio_utils.decode_mulaw_b64_to_pcm8k(b64_payload)
    y_16k = audio_utils.resample_8k_to_16k(y_8k)

    # 2. Real voice authenticity heuristic (actual audio now, not an empty array)
    voice_res = voice_detector.analyze_audio_chunk(y_16k, sr=16000)
    v_prob = voice_res["synthetic_probability"]

    # 3. Real speaker similarity via Resemblyzer, if a reference voice is enrolled
    if enrolled_embedding is not None:
        current_embedding = speaker_embed.embed_audio(y_16k, sr=16000)
        similarity = speaker_embed.cosine_similarity(current_embedding, enrolled_embedding)
        spk_anomaly = 1.0 - similarity
    else:
        spk_anomaly = 0.45  # unknown/unenrolled speaker baseline, same default as speaker_verifier.py

    # 4. Real transcription of this chunk
    transcript = asr.transcribe_chunk(y_16k, sr=16000)

    # 5. Real NLP intent scoring on the real transcript
    nlp_res = nlp_processor.process_transcript(transcript)

    # 6. Fuse into one risk score
    risk_res = risk_engine.fuse_signals(
        voice_synthetic_prob=v_prob,
        speaker_anomaly_score=spk_anomaly,
        financial_intent_score=nlp_res["financial_intent_score"],
        urgency_score=nlp_res["urgency_score"],
        callback_avoidance_score=nlp_res["callback_avoidance_score"],
        is_unknown_caller=True,
    )

    # 7. Persist
    db_call = db.query(Call).filter(Call.id == call_id).first()
    if db_call:
        db_call.fused_risk_score = risk_res["fused_risk_score"]
        db_call.risk_level = risk_res["risk_level"]
        db.commit()

    assessment = RiskAssessment(
        call_id=call_id,
        chunk_index=chunk_index,
        voice_synthetic_prob=v_prob,
        speaker_anomaly_score=spk_anomaly,
        financial_intent_score=nlp_res["financial_intent_score"],
        urgency_score=nlp_res["urgency_score"],
        unknown_caller_score=1.0,
        callback_avoidance_score=nlp_res["callback_avoidance_score"],
        fused_risk_score=risk_res["fused_risk_score"],
        risk_level=risk_res["risk_level"],
        transcript_snippet=transcript,
        explainability_breakdown=risk_res["explainability_breakdown"],
    )
    db.add(assessment)
    db.commit()

    # 8. Push live update to any dashboard clients watching this call
    await broadcast_to_dashboard(call_id, {
        "call_id": call_id,
        "chunk_index": chunk_index,
        "transcript": transcript,
        "fused_risk_score": risk_res["fused_risk_score"],
        "risk_level": risk_res["risk_level"],
        "recommended_action": risk_res["recommended_action"],
        "voice_analysis": voice_res,
        "speaker_anomaly_score": spk_anomaly,
        "nlp_analysis": nlp_res,
        "explainability_breakdown": risk_res["explainability_breakdown"],
    })

    logger.info(f"[{call_id}] chunk {chunk_index}: risk={risk_res['fused_risk_score']} transcript='{transcript}'")
