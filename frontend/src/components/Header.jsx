import React from 'react';
import { ShieldAlert, Activity, CheckCircle, Radio } from 'lucide-react';

export function Header({ isConnected, isStreaming }) {
  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-sky-600 text-white p-2.5 rounded-xl shadow-md">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              VoiceGuard AI
              <span className="text-xs bg-sky-100 text-sky-800 font-semibold px-2.5 py-0.5 rounded-full border border-sky-200">
                Live Impersonation Defense
              </span>
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              AICTE Problem Statement 26104 • Real-Time Voice Cloning Detection & Prevention
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700">
            <Radio className={`h-4 w-4 ${isStreaming ? 'text-rose-500 animate-pulse' : 'text-slate-400'}`} />
            <span>{isStreaming ? 'CALL STREAMING ACTIVE' : 'CALL IDLE'}</span>
          </div>

          <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600">
            <Activity className="h-4 w-4 text-emerald-500" />
            <span>Engine: WavLM + SASV + XLM-R</span>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-ping' : 'bg-amber-400'}`}></span>
            <span className="text-xs font-semibold text-slate-600">
              {isConnected ? 'WS Connected' : 'WS Reconnecting...'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
