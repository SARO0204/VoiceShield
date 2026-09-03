import React from 'react';
import {
  LayoutDashboard,
  Radio,
  FileAudio,
  PhoneCall,
  ShieldQuestion,
  BellRing,
  History,
  BarChart3,
  Cpu,
  Activity,
  Settings,
  Shield,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  criticalAlertCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  criticalAlertCount = 0,
}) => {
  const menuItems = [
    { id: 'dashboard', label: 'SOC Dashboard', icon: LayoutDashboard },
    { id: 'live', label: 'Live Protection', icon: Radio, pulse: true },
    { id: 'analyze', label: 'Analyze Audio', icon: FileAudio },
    { id: 'calls', label: 'Call Monitor', icon: PhoneCall },
    { id: 'verification', label: 'Identity Verification', icon: ShieldQuestion },
    { id: 'alerts', label: 'Alerts & Response', icon: BellRing, badge: criticalAlertCount },
    { id: 'history', label: 'Forensic History', icon: History },
    { id: 'analytics', label: 'Attack Analytics', icon: BarChart3 },
    { id: 'training', label: 'Model & Training Studio', icon: Cpu },
    { id: 'health', label: 'System Health', icon: Activity },
    { id: 'settings', label: 'Privacy & Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 bg-[#0a101d]/90 backdrop-blur-xl border-r border-slate-800/80 flex flex-col justify-between p-4 z-30 select-none">
      
      {/* Brand Logo */}
      <div>
        <div className="flex items-center gap-3 px-3 py-3 mb-6 border-b border-slate-800/60">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-display font-black text-lg tracking-wider text-white flex items-center gap-1.5">
              VOICE<span className="text-cyan-400">SHIELD</span>
            </h1>
            <span className="text-[10px] font-mono tracking-widest text-slate-400 block uppercase">
              AI Anti-Spoofing SOC
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-600/25 to-blue-600/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>

                {item.pulse && (
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                  </span>
                )}

                {item.badge !== undefined && item.badge > 0 && (
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/30 text-rose-300 border border-rose-500/50">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status Badge */}
      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
        <div className="flex items-center justify-between text-[11px] mb-1.5">
          <span className="text-slate-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Core Model Engine
          </span>
          <span className="font-mono text-cyan-400 font-semibold">AASIST-v1.0</span>
        </div>
        <div className="text-[10px] text-slate-500 font-mono truncate">
          Active Mode: <span className="text-slate-300">NEURAL INFERENCE</span>
        </div>
      </div>

    </aside>
  );
};
