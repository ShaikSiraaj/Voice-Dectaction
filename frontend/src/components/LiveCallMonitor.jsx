import React from 'react';
import { Play, Pause, AlertTriangle, UserCheck, ShieldCheck, PhoneCall, Radio, Volume2 } from 'lucide-react';

export function LiveCallMonitor({
  scenarios,
  activeScenarioId,
  onSelectScenario,
  isStreaming,
  onToggleStreaming,
  currentRiskScore,
  currentRiskLevel,
  liveTranscript,
  flaggedKeywords
}) {
  const getRiskColorClass = (level) => {
    switch (level) {
      case 'HIGH':
        return 'bg-rose-500 text-white shadow-rose-200';
      case 'MEDIUM':
        return 'bg-amber-500 text-white shadow-amber-200';
      default:
        return 'bg-emerald-500 text-white shadow-emerald-200';
    }
  };

  const getRiskGaugeBorder = (level) => {
    switch (level) {
      case 'HIGH':
        return 'border-rose-500 bg-rose-50';
      case 'MEDIUM':
        return 'border-amber-500 bg-amber-50';
      default:
        return 'border-emerald-500 bg-emerald-50';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
      {/* Top Bar: Scenario Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
            Simulate Attack Scenario
          </label>
          <div className="flex flex-wrap gap-2">
            {Object.values(scenarios).map((sc) => (
              <button
                key={sc.id}
                onClick={() => onSelectScenario(sc.id)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 border ${
                  activeScenarioId === sc.id
                    ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <PhoneCall className="h-3.5 w-3.5" />
                {sc.title}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={onToggleStreaming}
          className={`px-5 py-2.5 rounded-xl text-sm font-bold shadow-md transition-all flex items-center justify-center gap-2 ${
            isStreaming
              ? 'bg-rose-600 hover:bg-rose-700 text-white shadow-rose-100'
              : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-100'
          }`}
        >
          {isStreaming ? (
            <>
              <Pause className="h-4 w-4" /> Stop Live Call Stream
            </>
          ) : (
            <>
              <Play className="h-4 w-4" /> Start Live Call Stream
            </>
          )}
        </button>
      </div>

      {/* Main Grid: Waveform & Live Risk Score Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
        {/* Waveform Visualizer & Call Details */}
        <div className="lg:col-span-2 bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
          <div className="flex justify-between items-center text-xs font-bold text-slate-600">
            <span className="flex items-center gap-2">
              <Volume2 className="h-4 w-4 text-sky-600" />
              INBOUND AUDIO STREAM CHUNK (16kHz Mono)
            </span>
            <span className={`px-2.5 py-0.5 rounded-md text-[10px] uppercase font-bold ${
              isStreaming ? 'bg-rose-100 text-rose-700 animate-pulse' : 'bg-slate-200 text-slate-600'
            }`}>
              {isStreaming ? 'Live Sampling 3.2s Chunks' : 'Stream Paused'}
            </span>
          </div>

          {/* Animated Audio Waveform */}
          <div className="h-20 bg-white border border-slate-200 rounded-lg p-3 flex items-center justify-between gap-1 overflow-hidden">
            {Array.from({ length: 32 }).map((_, idx) => {
              const heightPct = isStreaming
                ? Math.min(100, Math.max(15, Math.sin(idx + Date.now() / 200) * 50 + 50))
                : 15;
              return (
                <div
                  key={idx}
                  className={`w-1.5 rounded-full transition-all duration-150 ${
                    isStreaming ? 'bg-sky-500' : 'bg-slate-300'
                  }`}
                  style={{ height: `${heightPct}%` }}
                />
              );
            })}
          </div>

          {/* Live Transcript Display */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-bold text-slate-500">
              <span>REAL-TIME TRANSCRIPT (AI4Bharat Indic ASR / Whisper)</span>
              {flaggedKeywords.length > 0 && (
                <span className="text-rose-600 text-[11px] font-bold">
                  {flaggedKeywords.length} Trigger Phrase(s) Detected
                </span>
              )}
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-3 min-h-[60px] text-xs font-medium text-slate-800 leading-relaxed shadow-inner">
              {liveTranscript ? (
                <span>{liveTranscript}</span>
              ) : (
                <span className="text-slate-400 italic">Waiting for incoming voice stream chunks...</span>
              )}
            </div>
          </div>
        </div>

        {/* Dynamic Risk Gauge */}
        <div className={`border-2 rounded-2xl p-5 flex flex-col items-center justify-center text-center space-y-3 transition-all ${getRiskGaugeBorder(currentRiskLevel)}`}>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
            Fused Impersonation Risk Score
          </span>

          <div className="relative flex items-center justify-center">
            <div className="text-5xl font-black tracking-tight text-slate-900">
              {Math.round(currentRiskScore)}
              <span className="text-lg font-bold text-slate-400">/100</span>
            </div>
          </div>

          <div className={`px-4 py-1.5 rounded-full text-xs font-bold shadow-sm ${getRiskColorClass(currentRiskLevel)}`}>
            {currentRiskLevel} RISK THREAT
          </div>

          <p className="text-[11px] font-medium text-slate-600 max-w-[200px]">
            {currentRiskLevel === 'HIGH'
              ? 'Critical synthetic voice or social engineering anomaly detected.'
              : currentRiskLevel === 'MEDIUM'
              ? 'Suspicious conversational or voice indicators present.'
              : 'Voice authentic and conversation parameters low risk.'}
          </p>
        </div>
      </div>
    </div>
  );
}
