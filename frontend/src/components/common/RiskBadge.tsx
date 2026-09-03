import React from 'react';
import { ShieldCheck, AlertTriangle, ShieldAlert, AlertOctagon, HelpCircle, Bot } from 'lucide-react';
import type { RiskLevel, ClassificationType } from '../../types';

interface RiskBadgeProps {
  level?: RiskLevel;
  score?: number;
  classification?: ClassificationType;
  showScore?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  score,
  classification,
  showScore = true,
  size = 'md',
}) => {
  // If classification is passed
  if (classification) {
    if (classification === 'GENUINE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          GENUINE HUMAN
        </span>
      );
    }
    if (classification === 'SYNTHETIC') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
          <Bot className="w-3.5 h-3.5 text-rose-400" />
          SYNTHETIC / AI CLONE
        </span>
      );
    }
    if (classification === 'UNCERTAIN') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
          <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
          UNCERTAIN / VERIFY
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-700/40 text-slate-400 border border-slate-600/40">
        MODEL UNAVAILABLE
      </span>
    );
  }

  // If Risk Level is passed
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5 font-bold',
  }[size];

  switch (level) {
    case 'LOW':
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 ${sizeClasses}`}>
          <ShieldCheck className="w-3.5 h-3.5" />
          LOW {showScore && score !== undefined && <span className="font-mono-numbers opacity-80">({score})</span>}
        </span>
      );
    case 'MEDIUM':
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 ${sizeClasses}`}>
          <AlertTriangle className="w-3.5 h-3.5" />
          MEDIUM {showScore && score !== undefined && <span className="font-mono-numbers opacity-80">({score})</span>}
        </span>
      );
    case 'HIGH':
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-orange-500/20 text-orange-300 border border-orange-500/40 ${sizeClasses}`}>
          <ShieldAlert className="w-3.5 h-3.5" />
          HIGH {showScore && score !== undefined && <span className="font-mono-numbers opacity-80">({score})</span>}
        </span>
      );
    case 'CRITICAL':
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-rose-500/25 text-rose-300 border border-rose-500/50 animate-pulse ${sizeClasses}`}>
          <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
          CRITICAL {showScore && score !== undefined && <span className="font-mono-numbers opacity-90 font-bold">({score}/100)</span>}
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold bg-slate-700/30 text-slate-300 border border-slate-600/30 ${sizeClasses}`}>
          UNKNOWN
        </span>
      );
  }
};
