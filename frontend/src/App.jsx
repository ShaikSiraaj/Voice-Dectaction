import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { LiveCallMonitor } from './components/LiveCallMonitor';
import { SignalExplainability } from './components/SignalExplainability';
import { VerificationActions } from './components/VerificationActions';
import { SpeakerManager } from './components/SpeakerManager';
import { CallAuditLog } from './components/CallAuditLog';

export default function App() {
  const [scenarios, setScenarios] = useState({});
  const [activeScenarioId, setActiveScenarioId] = useState('cloned_ceo_attack');
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [callId, setCallId] = useState(null);

  // Real-time risk state
  const [currentRiskScore, setCurrentRiskScore] = useState(15);
  const [currentRiskLevel, setCurrentRiskLevel] = useState('LOW');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [flaggedKeywords, setFlaggedKeywords] = useState([]);
  const [explainabilityBreakdown, setExplainabilityBreakdown] = useState(null);

  const wsRef = useRef(null);
  const chunkIndexRef = useRef(1);
  const streamIntervalRef = useRef(null);

  // Fetch preset scenarios on mount
  useEffect(() => {
    fetch('/api/scenarios')
      .then((res) => res.json())
      .then((data) => setScenarios(data))
      .catch((err) => console.error('Failed to load scenarios:', err));
  }, []);

  // Setup WebSocket connection
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/stream`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket stream connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.call_id) setCallId(data.call_id);
        setCurrentRiskScore(data.fused_risk_score || 0);
        setCurrentRiskLevel(data.risk_level || 'LOW');
        setLiveTranscript(data.transcript || '');
        setFlaggedKeywords(data.flagged_keywords || []);
        setExplainabilityBreakdown(data.explainability_breakdown || null);
      } catch (err) {
        console.error('Error parsing WS message:', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    wsRef.current = ws;

    return () => {
      if (ws) ws.close();
      if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
    };
  }, []);

  const handleToggleStreaming = () => {
    if (isStreaming) {
      setIsStreaming(false);
      if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
    } else {
      setIsStreaming(true);
      chunkIndexRef.current = 1;

      const activeSc = scenarios[activeScenarioId];
      if (!activeSc) return;

      const chunks = activeSc.chunks || [];

      // Stream chunks sequentially over interval
      streamIntervalRef.current = setInterval(() => {
        const idx = (chunkIndexRef.current - 1) % chunks.length;
        const chunkData = chunks[idx];

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          const payload = {
            chunk_index: chunkIndexRef.current,
            transcript: chunkData.transcript,
            voice_synthetic_prob: chunkData.voice_synthetic_prob,
            speaker_anomaly_score: chunkData.speaker_anomaly_score,
            financial_intent_score: chunkData.financial_intent_score,
            urgency_score: chunkData.urgency_score,
            callback_avoidance_score: chunkData.callback_avoidance_score,
            is_unknown_caller: activeSc.is_unknown_caller
          };
          wsRef.current.send(JSON.stringify(payload));
          chunkIndexRef.current += 1;
        }
      }, 3000);
    }
  };

  const handleSelectScenario = (scId) => {
    setActiveScenarioId(scId);
    if (isStreaming) {
      // Restart streaming with new scenario
      if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
      chunkIndexRef.current = 1;
      const activeSc = scenarios[scId];
      if (activeSc && activeSc.chunks) {
        const chunks = activeSc.chunks;
        streamIntervalRef.current = setInterval(() => {
          const idx = (chunkIndexRef.current - 1) % chunks.length;
          const chunkData = chunks[idx];
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              chunk_index: chunkIndexRef.current,
              transcript: chunkData.transcript,
              voice_synthetic_prob: chunkData.voice_synthetic_prob,
              speaker_anomaly_score: chunkData.speaker_anomaly_score,
              financial_intent_score: chunkData.financial_intent_score,
              urgency_score: chunkData.urgency_score,
              callback_avoidance_score: chunkData.callback_avoidance_score,
              is_unknown_caller: activeSc.is_unknown_caller
            }));
            chunkIndexRef.current += 1;
          }
        }, 3000);
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <Header isConnected={isConnected} isStreaming={isStreaming} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        <LiveCallMonitor
          scenarios={scenarios}
          activeScenarioId={activeScenarioId}
          onSelectScenario={handleSelectScenario}
          isStreaming={isStreaming}
          onToggleStreaming={handleToggleStreaming}
          currentRiskScore={currentRiskScore}
          currentRiskLevel={currentRiskLevel}
          liveTranscript={liveTranscript}
          flaggedKeywords={flaggedKeywords}
        />

        {explainabilityBreakdown && (
          <SignalExplainability explainabilityBreakdown={explainabilityBreakdown} />
        )}

        <VerificationActions
          callId={callId}
          currentRiskLevel={currentRiskLevel}
          onVerificationTriggered={() => {}}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SpeakerManager />
          <CallAuditLog />
        </div>
      </main>

      <footer className="bg-white border-t border-slate-200 py-4 px-6 text-center text-xs text-slate-500 font-medium">
        VoiceGuard AI • Real-Time Decision-Support & Prevention System • AICTE Hackathon Solution
      </footer>
    </div>
  );
}
