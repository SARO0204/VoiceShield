import React from 'react';
import {
  ShieldAlert,
  PhoneCall,
  Bot,
  AlertOctagon,
  Percent,
  CheckCircle2,
  Cpu,
  ArrowUpRight,
  TrendingUp,
  Activity,
} from 'lucide-react';
import type { DashboardSummary } from '../types';
import { RiskBadge } from '../components/common/RiskBadge';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface DashboardPageProps {
  data: DashboardSummary | null;
  isLoading: boolean;
  onNavigate: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  data,
  isLoading,
  onNavigate,
}) => {
  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-mono text-cyan-400">Loading SOC Live Intelligence...</span>
        </div>
      </div>
    );
  }

  const kpis = [
    {
      title: 'Total Analyzed Calls',
      value: data.total_calls_analyzed,
      subtext: 'Monitored speech sessions',
      icon: PhoneCall,
      color: 'text-cyan-400',
      border: 'border-cyan-500/30',
      bg: 'bg-cyan-500/10',
    },
    {
      title: 'AI Voice Clones Intercepted',
      value: data.ai_voice_detected,
      subtext: 'Synthetic voice signatures',
      icon: Bot,
      color: 'text-rose-400',
      border: 'border-rose-500/30',
      bg: 'bg-rose-500/10',
    },
    {
      title: 'High / Critical Risk Calls',
      value: data.high_risk_calls,
      subtext: 'Escalated security threats',
      icon: ShieldAlert,
      color: 'text-orange-400',
      border: 'border-orange-500/30',
      bg: 'bg-orange-500/10',
    },
    {
      title: 'Active Critical Alerts',
      value: data.critical_alerts,
      subtext: 'Requiring immediate action',
      icon: AlertOctagon,
      color: 'text-red-400',
      border: 'border-red-500/40',
      bg: 'bg-red-500/15',
    },
    {
      title: 'Average Threat Score',
      value: `${data.average_risk_score}/100`,
      subtext: 'Multi-factor risk index',
      icon: Percent,
      color: 'text-amber-400',
      border: 'border-amber-500/30',
      bg: 'bg-amber-500/10',
    },
    {
      title: 'Model Anti-Spoof EER',
      value: `${(data.model_health.eer * 100).toFixed(1)}%`,
      subtext: `AASIST (${data.model_health.version})`,
      icon: CheckCircle2,
      color: 'text-emerald-400',
      border: 'border-emerald-500/30',
      bg: 'bg-emerald-500/10',
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1627] to-slate-900 border border-slate-800 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            Active Real-Time Threat Intelligence
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Cybersecurity Command & Voice Defense Center
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Real-time deepfake acoustic inspection (AASIST), social engineering heuristic scoring, and fraud interception.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('live')}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-lg shadow-cyan-600/30 transition-colors"
          >
            <Activity className="w-4 h-4" />
            Launch Live Monitor
          </button>
          <button
            onClick={() => onNavigate('analyze')}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
          >
            Upload Audio File
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-2xl bg-slate-900/60 backdrop-blur-md border ${kpi.border} flex flex-col justify-between hover:scale-[1.02] transition-transform`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-medium text-slate-400 leading-tight line-clamp-2">
                  {kpi.title}
                </span>
                <div className={`p-1.5 rounded-lg ${kpi.bg}`}>
                  <Icon className={`w-4 h-4 ${kpi.color}`} />
                </div>
              </div>
              <div>
                <span className={`text-2xl font-black font-mono-numbers ${kpi.color}`}>
                  {kpi.value}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5 truncate">
                  {kpi.subtext}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Charts & Overview Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Risk Distribution Donut */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 font-display">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              Risk Tier Distribution
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Total: {data.total_calls_analyzed}</span>
          </div>

          <div className="h-48 w-full flex items-center justify-center">
            {data.total_calls_analyzed === 0 ? (
              <div className="text-center text-xs text-slate-500 font-mono">
                No calls recorded yet.
                <br />
                <span className="text-cyan-400 cursor-pointer underline" onClick={() => onNavigate('live')}>
                  Start live monitoring
                </span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.risk_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="count"
                  >
                    {data.risk_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                    itemStyle={{ color: '#f8fafc' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800">
            {data.risk_distribution.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-1.5 rounded-lg bg-slate-950/40">
                <span className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                  {item.name}
                </span>
                <span className="font-mono-numbers font-bold text-slate-200">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Model Architecture & Quality Health Card */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 font-display">
              <Cpu className="w-4 h-4 text-cyan-400" />
              Active AASIST Neural Engine
            </h3>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              {data.model_health.mode}
            </span>
          </div>

          <div className="space-y-3 my-auto py-2">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-xs text-slate-400">Architecture</span>
              <span className="text-xs font-mono font-bold text-slate-200">Spectro-Temporal Graph Attention</span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 block">Accuracy</span>
                <span className="text-base font-bold font-mono-numbers text-emerald-400">
                  {(data.model_health.accuracy * 100).toFixed(1)}%
                </span>
              </div>

              <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 block">F1 Score</span>
                <span className="text-base font-bold font-mono-numbers text-cyan-400">
                  {(data.model_health.f1_score * 100).toFixed(1)}%
                </span>
              </div>

              <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 block">EER Benchmark</span>
                <span className="text-base font-bold font-mono-numbers text-amber-400">
                  {(data.model_health.eer * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-400">Execution Hardware:</span>
              <span className="font-mono text-cyan-300 font-semibold">{data.model_health.device}</span>
            </div>
          </div>

          <button
            onClick={() => onNavigate('training')}
            className="w-full mt-2 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
          >
            <span>Open Model Training Studio</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Live Protection Status Card */}
        <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900/80 to-cyan-950/30 border border-cyan-500/30 flex flex-col justify-between relative overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 font-display">
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
              Live Defense Shield
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse">
              PROTECTION ACTIVE
            </span>
          </div>

          <div className="space-y-2.5 my-auto">
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-1">
              <div className="flex items-center justify-between text-slate-300 font-semibold">
                <span>Microphone & Call Stream</span>
                <span className="text-emerald-400 font-mono">READY</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Continuous 2-4 second sliding window inference with sub-100ms response.
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs space-y-1">
              <div className="flex items-center justify-between text-slate-300 font-semibold">
                <span>Scam Context NLP Heuristics</span>
                <span className="text-cyan-400 font-mono">ENABLED</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Detects urgent wire transfers, OTP requests, and impersonation claims.
              </p>
            </div>
          </div>

          <button
            onClick={() => onNavigate('live')}
            className="w-full mt-3 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-cyan-600/30 flex items-center justify-center gap-2 transition-all"
          >
            <Activity className="w-4 h-4" />
            <span>Open Real-Time Monitor</span>
          </button>
        </div>

      </div>

      {/* Recent Monitored Calls Table */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold font-display text-white flex items-center gap-2">
              <PhoneCall className="w-4 h-4 text-cyan-400" />
              Recent Monitored Voice Calls
            </h3>
            <span className="text-xs text-slate-400">Dynamic log of analyzed speech audio</span>
          </div>

          <button
            onClick={() => onNavigate('calls')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
          >
            <span>View All Calls</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {data.recent_calls.length === 0 ? (
          <div className="p-8 text-center rounded-xl bg-slate-950/40 border border-slate-800 text-slate-400 text-xs font-mono">
            No voice analyses recorded yet. Use 'Analyze Audio' or 'Live Protection' to run the first detection.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 bg-slate-950/60 border-b border-slate-800 font-mono uppercase text-[10px]">
                <tr>
                  <th className="p-3">Time</th>
                  <th className="p-3">Caller Identity</th>
                  <th className="p-3">Duration</th>
                  <th className="p-3">Classification</th>
                  <th className="p-3">Risk Level</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data.recent_calls.map((call) => (
                  <tr key={call.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-3 font-mono text-slate-400">
                      {call.started_at ? call.started_at.split('T')[1]?.substring(0, 8) : '--:--:--'}
                    </td>
                    <td className="p-3 font-semibold text-slate-200">
                      {call.caller_label}
                    </td>
                    <td className="p-3 font-mono text-slate-400">
                      {call.duration_sec ? `${call.duration_sec.toFixed(1)}s` : '0.0s'}
                    </td>
                    <td className="p-3">
                      <RiskBadge classification={call.overall_classification} />
                    </td>
                    <td className="p-3">
                      <RiskBadge level={call.risk_level} score={call.overall_risk} />
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => onNavigate('calls')}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-cyan-600 text-slate-300 hover:text-white transition-colors"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
};
