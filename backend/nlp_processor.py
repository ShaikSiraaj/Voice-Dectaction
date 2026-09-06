import re
from typing import Dict, Any, List

class NLPProcessor:
    """
    Speech-to-Text conversation intelligence & social engineering intent classifier.
    Detects scam patterns: financial requests, OTP/password demands, urgency, threats,
    callback avoidance, and impersonation claims.
    """

    PATTERNS = {
        "financial_request": [
            r"wire transfer", r"transfer \$?\d+", r"send money", r"bank details",
            r"immediate payment", r"gift cards", r"crypto", r"bitcoin", r"swift code",
            r"account number", r"vendor payment", r"unpaid invoice", r"routing number"
        ],
        "otp_request": [
            r"otp", r"one[- ]time password", r"verification code", r"2fa code",
            r"read me the code", r"security code", r"pin number", r"authentication code"
        ],
        "password_request": [
            r"password", r"login credentials", r"access code", r"user id", r"master key"
        ],
        "urgency": [
            r"urgent", r"immediately", r"right now", r"asap", r"within 10 minutes",
            r"don't wait", r"emergency", r"critical", r"time[- ]sensitive", r"before it's too late"
        ],
        "threat": [
            r"police", r"legal action", r"arrest", r"account frozen", r"lawsuit",
            r"terminate your employment", r"fire you", r"court warrant", r"suspended"
        ],
        "callback_avoidance": [
            r"don't call me back", r"do not call me back", r"can't talk on my regular line", r"phone line is busy",
            r"private line", r"do not reach out", r"in a quiet meeting", r"boarding a flight"
        ],
        "impersonation_claim": [
            r"this is the ceo", r"calling from headquarters", r"i am your executive",
            r"it's me director", r"calling from IT department", r"bank fraud division"
        ]
    }

    def process_transcript(self, transcript: str, context_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze transcript text for social engineering intent indicators.
        Returns risk scores per category and list of flagged phrases.
        """
        if context_metadata is None:
            context_metadata = {}

        text_lower = transcript.lower()
        detected_intents: Dict[str, float] = {}
        matched_snippets: List[str] = []

        for category, patterns in self.PATTERNS.items():
            category_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    category_matches.extend(matches)

            if category_matches:
                score = min(1.0, 0.60 + 0.20 * len(category_matches))
                detected_intents[category] = round(score, 2)
                matched_snippets.extend(category_matches)
            else:
                detected_intents[category] = 0.0

        # High level intent aggregates
        financial_score = max(detected_intents.get("financial_request", 0.0), detected_intents.get("otp_request", 0.0))
        urgency_score = detected_intents.get("urgency", 0.0)
        callback_avoidance_score = detected_intents.get("callback_avoidance", 0.0)

        # Handle simulation overrides for scenario testing
        if "simulated_financial_intent_score" in context_metadata:
            financial_score = float(context_metadata["simulated_financial_intent_score"])
        if "simulated_urgency_score" in context_metadata:
            urgency_score = float(context_metadata["simulated_urgency_score"])
        if "simulated_callback_avoidance_score" in context_metadata:
            callback_avoidance_score = float(context_metadata["simulated_callback_avoidance_score"])

        return {
            "financial_intent_score": round(financial_score, 2),
            "urgency_score": round(urgency_score, 2),
            "callback_avoidance_score": round(callback_avoidance_score, 2),
            "category_scores": detected_intents,
            "flagged_keywords": list(set(matched_snippets)),
            "transcript_text": transcript
        }
