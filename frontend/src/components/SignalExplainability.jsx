import React from 'react';
import { HelpCircle, Layers, CheckCircle2, AlertCircle } from 'lucide-react';

export function SignalExplainability({ explainabilityBreakdown }) {
  if (!explainabilityBreakdown) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <Layers className="h-5 w-5 text-sky-600" />
          <h2 className="text-base font-bold text-slate-900">
            Signal Explainability Breakdown
          </h2>
        </div>
        <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md">
          Transparent Weighted Fusion
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold">
              <th className="py-2.5 px-3">SIGNAL METRIC</th>
              <th className="py-2.5 px-3">RAW SCORE</th>
              <th className="py-2.5 px-3">FUSION WEIGHT</th>
              <th className="py-2.5 px-3">RISK CONTRIBUTION</th>
              <th className="py-2.5 px-3 text-right">STATUS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-medium">
            {Object.entries(explainabilityBreakdown).map(([key, item]) => {
              const contrib = item.score_contribution;
              const isHigh = item.raw_value > 0.6;
              return (
                <tr key={key} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-3 font-semibold text-slate-900">
                    {item.label}
                  </td>
                  <td className="py-3 px-3 text-slate-700">
                    {(item.raw_value * 100).toFixed(0)}%
                  </td>
                  <td className="py-3 px-3 text-slate-500">
                    {(item.weight * 100).toFixed(0)}%
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            isHigh ? 'bg-rose-500' : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min(100, (contrib / (item.weight * 100)) * 100)}%` }}
                        />
                      </div>
                      <span className="font-bold text-slate-800">+{contrib} pts</span>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-right">
                    {isHigh ? (
                      <span className="inline-flex items-center gap-1 text-rose-600 font-bold bg-rose-50 px-2 py-0.5 rounded">
                        <AlertCircle className="h-3.5 w-3.5" /> High Risk
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Normal
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
