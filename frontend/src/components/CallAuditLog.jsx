import React, { useState, useEffect } from 'react';
import { History, ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react';

export function CallAuditLog() {
  const [calls, setCalls] = useState([]);

  const fetchCalls = async () => {
    try {
      const res = await fetch('/api/calls');
      const data = await res.json();
      setCalls(data);
    } catch (err) {
      console.error('Failed to fetch call history:', err);
    }
  };

  useEffect(() => {
    fetchCalls();
    const interval = setInterval(fetchCalls, 5000);
    return () => clearInterval(interval);
  }, []);

  const getBadgeStyle = (level) => {
    switch (level) {
      case 'HIGH':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <History className="h-5 w-5 text-sky-600" />
          <h2 className="text-base font-bold text-slate-900">
            Real-Time Call History & Impersonation Audit Logs
          </h2>
        </div>
        <span className="text-xs font-semibold text-slate-500">
          Auto-refreshing (5s)
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
              <th className="py-2.5 px-3">CALL SESSION ID</th>
              <th className="py-2.5 px-3">PURPORTED CALLER</th>
              <th className="py-2.5 px-3">START TIME</th>
              <th className="py-2.5 px-3">FUSED RISK</th>
              <th className="py-2.5 px-3">THREAT LEVEL</th>
              <th className="py-2.5 px-3 text-right">SESSION STATUS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-medium">
            {calls.length === 0 ? (
              <tr>
                <td colSpan="6" className="py-6 text-center text-slate-400">
                  No previous call records recorded.
                </td>
              </tr>
            ) : (
              calls.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-3 font-mono text-slate-800 font-bold">
                    {c.id}
                  </td>
                  <td className="py-3 px-3">
                    <div className="font-semibold text-slate-900">{c.caller_name || 'Unknown'}</div>
                    <div className="text-[10px] text-slate-500">{c.caller_id}</div>
                  </td>
                  <td className="py-3 px-3 text-slate-600">
                    {c.start_time ? new Date(c.start_time).toLocaleTimeString() : 'N/A'}
                  </td>
                  <td className="py-3 px-3 font-bold text-slate-900">
                    {Math.round(c.fused_risk_score)} / 100
                  </td>
                  <td className="py-3 px-3">
                    <span className={`px-2.5 py-0.5 rounded-full border text-[10px] font-bold ${getBadgeStyle(c.risk_level)}`}>
                      {c.risk_level}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right font-semibold text-slate-700 uppercase">
                    {c.status}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
