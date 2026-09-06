import React, { useState } from 'react';
import { KeyRound, PhoneForwarded, ShieldAlert, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

export function VerificationActions({ callId, currentRiskLevel, onVerificationTriggered }) {
  const [loadingAction, setLoadingAction] = useState(null);
  const [lastActionResult, setLastActionResult] = useState(null);

  const handleAction = async (actionType, detailsText) => {
    setLoadingAction(actionType);
    setLastActionResult(null);

    try {
      const response = await fetch('/api/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          call_id: callId || 'live_call_session',
          action_type: actionType,
          details: detailsText
        })
      });
      const data = await response.json();
      setLastActionResult(data);
      if (onVerificationTriggered) {
        onVerificationTriggered(data);
      }
    } catch (err) {
      console.error("Verification action error:", err);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-rose-600" />
          Step-Up Verification & Prevention Protocol
        </h2>
        <span className="text-xs font-semibold text-slate-500">
          Recommended Decision Support Layer
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Action 1: MFA Challenge */}
        <button
          disabled={loadingAction !== null}
          onClick={() => handleAction('MFA_CHALLENGE', 'Trigger real-time biometric/push MFA verification')}
          className="p-4 rounded-xl border border-sky-200 bg-sky-50 hover:bg-sky-100 text-sky-900 transition-all flex flex-col items-start space-y-2 text-left group"
        >
          <div className="flex justify-between w-full items-center">
            <KeyRound className="h-5 w-5 text-sky-600 group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-bold bg-sky-200 text-sky-800 px-2 py-0.5 rounded">
              Fastest
            </span>
          </div>
          <div>
            <div className="font-bold text-xs">Trigger MFA Challenge</div>
            <div className="text-[11px] text-sky-700 font-normal">
              Send instant mobile push token / biometric verification to enrolled CEO device.
            </div>
          </div>
        </button>

        {/* Action 2: Registered Callback */}
        <button
          disabled={loadingAction !== null}
          onClick={() => handleAction('CALLBACK_REQUEST', 'Trigger official corporate PBX callback')}
          className="p-4 rounded-xl border border-amber-200 bg-amber-50 hover:bg-amber-100 text-amber-900 transition-all flex flex-col items-start space-y-2 text-left group"
        >
          <div className="flex justify-between w-full items-center">
            <PhoneForwarded className="h-5 w-5 text-amber-600 group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-bold bg-amber-200 text-amber-800 px-2 py-0.5 rounded">
              Standard
            </span>
          </div>
          <div>
            <div className="font-bold text-xs">Request Official Callback</div>
            <div className="text-[11px] text-amber-700 font-normal">
              Instruct line to hang up and originate outbound call to registered corporate number.
            </div>
          </div>
        </button>

        {/* Action 3: Escalate to Supervisor */}
        <button
          disabled={loadingAction !== null}
          onClick={() => handleAction('SUPERVISOR_ESCALATION', 'Escalate incident to Security Operations Center')}
          className="p-4 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-900 transition-all flex flex-col items-start space-y-2 text-left group"
        >
          <div className="flex justify-between w-full items-center">
            <ShieldAlert className="h-5 w-5 text-rose-600 group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-bold bg-rose-200 text-rose-800 px-2 py-0.5 rounded">
              High Priority
            </span>
          </div>
          <div>
            <div className="font-bold text-xs">Escalate to Supervisor / SOC</div>
            <div className="text-[11px] text-rose-700 font-normal">
              Flag live incident, preserve recording, and immediately block further wire action.
            </div>
          </div>
        </button>
      </div>

      {/* Action Execution Feedback Result */}
      {lastActionResult && (
        <div className={`p-4 rounded-xl border flex items-start space-x-3 ${
          lastActionResult.status === 'PASSED'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
            : 'bg-rose-50 border-rose-200 text-rose-900'
        }`}>
          {lastActionResult.status === 'PASSED' ? (
            <CheckCircle className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <XCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
          )}
          <div className="text-xs space-y-1">
            <div className="font-bold uppercase tracking-wider">
              Verification Result: {lastActionResult.status}
            </div>
            <p>{lastActionResult.details}</p>
            <div className="text-[11px] font-semibold text-slate-600">
              Call Session Status Updated: <span className="underline">{lastActionResult.call_status}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
