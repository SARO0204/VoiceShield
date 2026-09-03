import React from 'react';
import { AlertOctagon, ShieldAlert, XCircle, CheckCircle, Lock, PhoneOff, HelpCircle } from 'lucide-react';

interface EmergencyAlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  aiProbability: number;
  riskScore: number;
  reasons: string[];
  callerLabel?: string;
  onTriggerVerification: () => void;
  onMarkSafe: () => void;
  onBlockCall: () => void;
}

export const EmergencyAlertModal: React.FC<EmergencyAlertModalProps> = ({
  isOpen,
  onClose,
  aiProbability,
  riskScore,
  reasons,
  callerLabel = 'Unknown Caller',
  onTriggerVerification,
  onMarkSafe,
  onBlockCall,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-2xl rounded-2xl bg-slate-900 border-2 border-rose-600 shadow-[0_0_60px_rgba(225,29,72,0.45)] overflow-hidden animate-scaleUp">
        
        {/* Top Emergency Header */}
        <div className="bg-gradient-to-r from-rose-700 via-red-600 to-rose-800 p-5 flex items-center justify-between text-white">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-black/30 rounded-xl animate-bounce">
              <AlertOctagon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-display tracking-tight flex items-center gap-2">
                POTENTIAL VOICE CLONE SCAM DETECTED
              </h2>
              <p className="text-xs text-rose-100 font-mono">
                Target Caller: <span className="font-bold underline">{callerLabel}</span> | Threat Score: <span className="font-bold text-white">{riskScore}/100</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-black/20 hover:bg-black/40 text-rose-100 transition-colors"
          >
            <XCircle className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          
          {/* Probability & Risk meter */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/70 border border-rose-500/30 text-center">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                AI Voice Synthetic Probability
              </span>
              <span className="text-3xl font-extrabold font-mono-numbers text-rose-400">
                {(aiProbability * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-rose-300/70 block mt-0.5">AASIST Graph Model Confidence</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/70 border border-rose-500/30 text-center">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Composite Scam Risk Level
              </span>
              <span className="text-3xl font-extrabold font-mono-numbers text-rose-400">
                CRITICAL ({riskScore})
              </span>
              <span className="text-[10px] text-rose-300/70 block mt-0.5">Voice + NLP Context Escalation</span>
            </div>
          </div>

          {/* Explainability Evidence */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              Forensic Detection Evidence
            </h4>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5 text-xs text-slate-200">
              {reasons.length > 0 ? (
                reasons.map((r, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-rose-400 font-bold">✓</span>
                    <span>{r}</span>
                  </div>
                ))
              ) : (
                <div className="flex items-start gap-2">
                  <span className="text-rose-400 font-bold">✓</span>
                  <span>Acoustic artifacts characteristic of synthetic neural vocoder detected</span>
                </div>
              )}
            </div>
          </div>

          {/* Recommended Fraud Prevention Steps */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-2 flex items-center gap-2">
              <Lock className="w-4 h-4 text-amber-400" />
              Mandatory Action Directives
            </h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-200 flex items-center gap-2">
                <span className="text-amber-400 font-bold text-sm">⛔</span>
                <span>Do NOT transfer money or wire funds</span>
              </div>
              <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-200 flex items-center gap-2">
                <span className="text-amber-400 font-bold text-sm">🔑</span>
                <span>Do NOT share OTP or passwords</span>
              </div>
              <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-200 flex items-center gap-2">
                <span className="text-amber-400 font-bold text-sm">📞</span>
                <span>Call person back on trusted number</span>
              </div>
              <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/25 text-amber-200 flex items-center gap-2">
                <span className="text-amber-400 font-bold text-sm">👥</span>
                <span>Contact family / mutual person</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800">
            <button
              onClick={onTriggerVerification}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition-colors shadow-lg shadow-cyan-600/30"
            >
              <HelpCircle className="w-4 h-4" />
              Ask Secret Question Challenge
            </button>

            <button
              onClick={onBlockCall}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs transition-colors shadow-lg shadow-rose-600/30"
            >
              <PhoneOff className="w-4 h-4" />
              End Call & Flag Threat
            </button>

            <button
              onClick={onMarkSafe}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-colors"
            >
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              Mark Safe
            </button>
          </div>

        </div>

      </div>
    </div>
  );
};
