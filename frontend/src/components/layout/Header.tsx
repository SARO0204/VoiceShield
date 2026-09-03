import React from 'react';
import { ShieldCheck, ShieldAlert, Cpu, Database, Bell, User } from 'lucide-react';
import type { SystemStatus, UserProfile } from '../../types';

interface HeaderProps {
  systemStatus?: SystemStatus | null;
  user?: UserProfile | null;
  activeProtection: boolean;
  onToggleProtection: () => void;
  criticalAlertsCount: number;
  onOpenAlerts: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  systemStatus,
  user,
  activeProtection,
  onToggleProtection,
  criticalAlertsCount,
  onOpenAlerts,
}) => {
  return (
    <header className="h-16 shrink-0 bg-[#080d17]/80 backdrop-blur-md border-b border-slate-800/80 px-6 flex items-center justify-between z-20">
      
      {/* Left Protection Radar */}
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleProtection}
          className={`flex items-center gap-2.5 px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all duration-300 ${
            activeProtection
              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
              : 'bg-slate-800/50 text-slate-400 border-slate-700'
          }`}
        >
          {activeProtection ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>SHIELD ACTIVE</span>
            </>
          ) : (
            <>
              <ShieldAlert className="w-4 h-4 text-slate-400" />
              <span>SHIELD STANDBY</span>
            </>
          )}
        </button>

        {/* Hardware Status Tag */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] font-mono text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span>Device:</span>
          <span className="text-cyan-300 font-bold">
            {systemStatus?.gpu?.available ? 'NVIDIA CUDA' : 'CPU FALLBACK'}
          </span>
        </div>

        {/* DB Status Tag */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] font-mono text-slate-300">
          <Database className="w-3.5 h-3.5 text-emerald-400" />
          <span>MongoDB:</span>
          <span className={systemStatus?.mongodb === 'CONNECTED' ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
            {systemStatus?.mongodb || 'CONNECTED'}
          </span>
        </div>
      </div>

      {/* Right User & Alert Center */}
      <div className="flex items-center gap-4">
        {/* Notification Bell */}
        <button
          onClick={onOpenAlerts}
          className="relative p-2 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors"
          title="Incident Alerts"
        >
          <Bell className="w-4 h-4" />
          {criticalAlertsCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[9px] font-bold text-white animate-pulse">
              {criticalAlertsCount}
            </span>
          )}
        </button>

        {/* User Profile Chip */}
        <div className="flex items-center gap-2.5 pl-3 border-l border-slate-800 text-xs">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-600 to-blue-700 flex items-center justify-center text-white font-bold shadow-md shadow-cyan-600/20">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden sm:block text-left">
            <span className="font-semibold text-slate-200 block leading-tight">
              {user?.name || 'Security Analyst'}
            </span>
            <span className="text-[10px] text-slate-400 font-mono">
              {user?.role || 'SOC Level 3'}
            </span>
          </div>
        </div>
      </div>

    </header>
  );
};
