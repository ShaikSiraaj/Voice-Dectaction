# Real-Time Voice Impersonation Detection & Prevention System
### Updated solution plan — AICTE Problem Statement 26104

---

## 1. Framing

The problem is not "classify this audio file as real or fake." It's:

> A call is happening right now. Can the system tell the person on the other end, before they act on it, that the voice may be cloned — and give them a concrete next step?

Product framing to carry into the pitch: **a real-time decision-support and prevention layer**, not a magic deepfake detector. Every detector has false positives/negatives, especially against synthesis methods it wasn't trained on — say this upfront rather than let a judge catch it.

---

## 2. Recommended architecture

```
                 LIVE CALL
                    |
              Audio Stream (2-5s chunks)
                    |
        +-----------+-----------+
        |                       |
        v                       v
  VOICE ANALYSIS           SPEECH-TO-TEXT
        |                       |
  +-----+------+                v
  |     |      |            NLP ANALYSIS
  v     v      v                |
Acoustic Prosody Speaker    (urgency, financial
Model   Model   Consistency  request, OTP request,
  |     |      |             callback avoidance)
  +-----+------+                |
        |                       |
        +-----------+-----------+
                    v
              CONTEXT ENGINE
        (caller ID, unknown number,
         transaction size, call history)
                    |
                    v
              RISK ENGINE
           (fusion of all signals)
                    |
                    v
             0-100 RISK SCORE
                    |
        +-----------+-----------+
        v           v           v
      LOW        MEDIUM       HIGH
      Allow      Warning    Alert + step-up
                             verification
                          (MFA / callback /
                           escalate to supervisor)
```

Keep the voice-authenticity model and the speaker-verification model architecturally separate from the NLP/context layer — they run on different data (audio vs. text/metadata) and fail independently, which is also a good story for "defense in depth" during Q&A.

---

## 3. Datasets — updated

**Core issue with the original plan:** ASVspoof 2021 alone trains a model that's good at catching *2019-2021-era* synthesis methods (mostly autoregressive TTS/vocoder artifacts). Most cloning tools in active use now are diffusion- or flow-matching-based, which leave different artifacts. Train and evaluate across multiple generations of attacks, not one.

| Dataset | Use it for | Why |
|---|---|---|
| **ASVspoof 5** (2024) | Primary training/eval set | ~2,000 crowdsourced speakers (vs ~100 in earlier editions), 32 attack algorithms, includes adversarial attacks for the first time — closest to a live-network scenario. |
| **DFADD** | Fine-tuning / eval | Attacks generated with diffusion and flow-matching TTS — the generation family most current cloning tools actually use. Skipping this = strong on old fakes, weak on current ones. |
| **MLAAD** (Multi-Language Audio Anti-Spoofing Dataset) | Multilingual generalization | Built explicitly for cross-language spoof detection, more relevant to the Indian-language requirement than ASVspoof alone. |
| **In-the-Wild** | Cross-domain stress test | Real deepfakes of public figures scraped from the internet — tests whether your model generalizes outside clean studio recordings, closer to the CEO-impersonation scenario. |
| **WaveFake / Fake-or-Real (FoR)** | Supplementary training data | Still useful for volume and diversity, just don't rely on them alone. |
| **AI4Bharat IndicVoices** | Genuine Indian-language speech for robustness testing/adaptation | 22 languages, large speaker pool. This is *genuine* speech, not a fake/real pair — use it to test/adapt your detector's Indian-accent robustness, not as your core spoof-detection dataset. |
| **Speech DF Arena** (benchmark, not a dataset) | Model/architecture selection | A unified leaderboard across 14 deepfake-speech datasets — use it to see which front-end/back-end combinations actually generalize instead of guessing. |

**Search keywords to use:**
```
ASVspoof5 dataset
ASVspoof 5 crowdsourced spoofing deepfake adversarial
DFADD diffusion flow-matching TTS deepfake dataset
MLAAD multilingual audio anti-spoofing dataset
In-the-Wild audio deepfake dataset
AI4Bharat IndicVoices dataset
speech deepfake detection leaderboard
AASIST speech anti-spoofing graph attention
SASV spoofing aware speaker verification
```

Avoid vague searches like "voice cloning dataset" — too generic, mixes in irrelevant TTS-training corpora that have no real/fake labels.

**Split discipline (unchanged, still correct):** split by *speaker*, not by clip. Never let the same speaker's clips appear in both train and test — the model will partially memorize speaker characteristics and give you falsely high accuracy.

---

## 4. Model architecture — updated

The original "WavLM + linear classification head" plan is a reasonable MVP but not what's competitive right now. Current strong systems (see ASVspoof5 workshop submissions) pair an SSL front-end with a dedicated spoof-detection back-end, not a bare linear layer:

```
Raw audio (16kHz, mono)
        |
        v
SSL front-end: WavLM-Base-Plus or wav2vec2-XLSR
   (frozen initially, unfreeze last layers if needed)
        |
        v
Back-end: AASIST (graph attention network)
   or ResNet + attentive pooling
        |
        v
   real / synthetic score
```

Why this matters: the front-end gives general speech representations; the back-end is what's actually tuned to catch synthesis artifacts. Linear-head-on-frozen-embeddings tends to underperform on cross-dataset generalization, which is exactly the failure mode you don't want in a live demo against an unseen cloning tool.

**Speaker consistency — reframe as SASV, not two separate scores.** Rather than computing "voice authenticity" and "speaker match" as independent numbers you average later, look at the **SASV (Spoofing-Aware Speaker Verification)** framework, which jointly decides "is this the right speaker AND is it genuine speech" as one combined task. It's the more principled version of what Layer 1 + Layer 3 in the original plan were trying to do separately, and it's a stronger thing to cite in your report than an ad hoc weighted average.

**Real-time latency caveat:** WavLM-Base-Plus is ~94M parameters. On modest hardware, this can be slower than expected for continuous 2-5s chunk inference. Have a lighter fallback ready — a distilled SSL model or an end-to-end lightweight architecture like RawNet2 — so the live demo's rolling risk score doesn't visibly lag.

---

## 5. Fine-tuning process (unchanged, still correct — keep this part)

1. Normalize all audio to 16kHz mono WAV, trim excess silence, chunk into 2-5s segments.
2. Label REAL=0, FAKE=1, split by speaker (not by clip).
3. Freeze the SSL backbone first, train only the back-end classifier.
4. Evaluate. If insufficient, unfreeze the last few SSL layers and fine-tune with a small learning rate.
5. Measure precision, recall, F1, ROC-AUC, and **Equal Error Rate (EER)** — the standard metric in this literature — not just accuracy. For a security system, false negatives (missed clones) matter more than false positives.
6. Test on completely unseen speakers *and*, ideally, an unseen synthesis method (e.g., train mostly on ASVspoof5 + WaveFake, hold out DFADD entirely for final testing) — this is the generalization check that separates a real system from a dataset-overfit demo.

---

## 6. Second pipeline: conversation intelligence (unchanged direction, still solid)

```
Audio -> ASR (multilingual/Indic) -> Transcript -> NLP classifier
```

Categories to detect: `financial_request`, `otp_request`, `password_request`, `urgency`, `threat`, `callback_avoidance`, `impersonation_claim`, `normal`.

- Use AI4Bharat's Indic ASR ecosystem for Indian-language transcription rather than training your own.
- Fine-tune a pretrained multilingual transformer (e.g. XLM-R family) on a small, self-labeled domain dataset of scam/social-engineering phrases — you don't need thousands of real recorded calls, synthetic/labeled transcripts are fine for a prototype, just say so explicitly to the judges.

---

## 7. Risk engine

Start with a transparent, explainable weighted fusion — judges respond well to a system that can show *why* it flagged something, not just a number:

```
Voice synthetic probability     0.82
Speaker anomaly                 0.65
Financial/OTP request           1.00
Urgency language                0.90
Unknown caller                  1.00
Callback avoidance              0.80
---------------------------------------
Fused risk score                 91/100  -> CRITICAL
```

You can later replace the hand-set weights with a trained fusion model (logistic regression or small MLP) once you have enough labeled multi-signal examples — but a transparent rule-based fusion is actually a stronger demo choice for a hackathon than a black-box fusion model, since you can narrate every number on screen.

---

## 8. Tech stack

| Component | Choice |
|---|---|
| Voice deepfake front-end | WavLM-Base-Plus or wav2vec2-XLSR |
| Voice deepfake back-end | AASIST or ResNet + attentive pooling |
| Speaker verification framing | SASV-style joint scoring |
| ML framework | PyTorch |
| Model/dataset tooling | Hugging Face Transformers + Datasets |
| Audio processing | librosa, torchaudio |
| Speech-to-text | AI4Bharat Indic ASR / multilingual ASR |
| NLP intent classifier | Fine-tuned multilingual transformer (XLM-R) |
| Risk engine | Python, transparent weighted fusion |
| API | FastAPI |
| Real-time streaming | WebSocket |
| Frontend dashboard | React |
| Database | PostgreSQL |

---

## 9. Phased build order

1. **Phase 1** — Core voice-authenticity detector: ASVspoof5 + DFADD, WavLM/wav2vec2 front-end + AASIST back-end.
2. **Phase 2** — Real-time chunked streaming inference with a rolling risk score.
3. **Phase 3** — Speaker verification / SASV-style consistency check against enrolled reference voice.
4. **Phase 4** — Speech-to-text + NLP social-engineering intent classifier.
5. **Phase 5** — Risk fusion engine with explainable signal breakdown.
6. **Phase 6** — Alert/verification dashboard: risk score, explanation table, recommended action (MFA / callback / escalate).

---

## 10. Demo narrative (unchanged — this framing is genuinely strong)

1. **Normal call** — genuine CEO call, risk score stays low, system stays quiet.
2. **Cloned-voice attack** — simulated cloned CEO call requesting an urgent fund transfer; risk score climbs live across the call as voice + context signals accumulate; system fires a high-risk alert with a signal-by-signal explanation.
3. **Prevention** — employee clicks "Verify Caller," system offers MFA / registered-number callback / supervisor escalation; the fake CEO fails MFA; system confirms a fraud attempt.

This "detection -> explanation -> decision -> prevention" arc is a stronger story than "detection -> prediction" alone — keep it as the spine of the presentation.

---

## 11. What to say (and not say) to judges

- Say: *"a real-time, multi-signal impersonation risk assessment system that supports human decision-making."*
- Don't say: *"an AI that detects every cloned voice with 100% accuracy."* Every detector has blind spots against unseen synthesis methods, compressed/noisy audio, and adversarial attacks (which ASVspoof5 now explicitly tests for) — acknowledging this is a stronger position than overclaiming, and it preempts the question a technically sharp judge will ask.
