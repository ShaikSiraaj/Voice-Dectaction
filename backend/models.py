import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.database import Base


class SpeakerProfile(Base):
    __tablename__ = "speaker_profiles"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    department = Column(String, nullable=True)
    voice_print_data = Column(JSON, nullable=True)  # Spectral/pitch features centroid
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    calls = relationship("Call", back_populates="speaker")


class Call(Base):
    __tablename__ = "calls"

    id = Column(String, primary_key=True, index=True)
    caller_id = Column(String, nullable=False)
    caller_name = Column(String, nullable=True)
    speaker_id = Column(String, ForeignKey("speaker_profiles.id"), nullable=True)
    scenario_id = Column(String, nullable=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="ACTIVE")  # ACTIVE, COMPLETED, INTERRUPTED, BLOCKED
    fused_risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH

    speaker = relationship("SpeakerProfile", back_populates="calls")
    assessments = relationship("RiskAssessment", back_populates="call", cascade="all, delete-orphan")
    verifications = relationship("VerificationAction", back_populates="call", cascade="all, delete-orphan")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, ForeignKey("calls.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    chunk_index = Column(Integer, nullable=False)

    # Signal scores (0.0 to 1.0)
    voice_synthetic_prob = Column(Float, nullable=False)
    speaker_anomaly_score = Column(Float, nullable=False)
    financial_intent_score = Column(Float, nullable=False)
    urgency_score = Column(Float, nullable=False)
    unknown_caller_score = Column(Float, nullable=False)
    callback_avoidance_score = Column(Float, nullable=False)

    # Fused aggregate score (0 to 100)
    fused_risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)

    transcript_snippet = Column(Text, nullable=True)
    explainability_breakdown = Column(JSON, nullable=True)

    call = relationship("Call", back_populates="assessments")


class VerificationAction(Base):
    __tablename__ = "verification_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String, ForeignKey("calls.id"), nullable=False)
    action_type = Column(String, nullable=False)  # MFA_CHALLENGE, CALLBACK_REQUEST, SUPERVISOR_ESCALATION
    status = Column(String, nullable=False)  # PENDING, PASSED, FAILED, BYPASSED
    triggered_at = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(Text, nullable=True)

    call = relationship("Call", back_populates="verifications")
