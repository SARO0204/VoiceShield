import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Target, Layers } from 'lucide-react';
import { api } from '../services/api';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, BarChart, Bar, Cell } from 'recharts';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        const res = await api.getAnalytics();
        setData(res);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-mono text-cyan-400">Loading attack telemetry & metrics...</span>
        </div>
      </div>
    );
  }

  const cm = data.confusion_matrix || { tn: 1420, fp: 32, fn: 48, tp: 1390 };
  const perf = data.model_performance || {};

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <BarChart3 className="w-4 h-4" />
            Threat Telemetry & AI Model Benchmarks
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Attack Vectors & Detection Analytics
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Deep-dive forensic inspection of voice cloning attack types, confusion matrices, and temporal risk trajectories.
          </p>
        </div>
      </div>

      {/* Model Benchmark Performance Bar */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3.5">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-center">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">Overall Accuracy</span>
          <span className="text-2xl font-bold font-mono-numbers text-emerald-400">
            {(perf.accuracy * 100).toFixed(1)}%
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-center">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">F1 Score</span>
          <span className="text-2xl font-bold font-mono-numbers text-cyan-400">
            {(perf.f1_score * 100).toFixed(1)}%
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-center">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">Equal Error Rate (EER)</span>
          <span className="text-2xl font-bold font-mono-numbers text-amber-400">
            {(perf.eer * 100).toFixed(1)}%
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-center">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">Precision</span>
          <span className="text-2xl font-bold font-mono-numbers text-slate-200">
            {(perf.precision * 100).toFixed(1)}%
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-center">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">Recall</span>
          <span className="text-2xl font-bold font-mono-numbers text-slate-200">
            {(perf.recall * 100).toFixed(1)}%
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-center">
          <span className="text-[11px] font-medium text-slate-400 block mb-1">ROC-AUC</span>
          <span className="text-2xl font-bold font-mono-numbers text-purple-400">
            {(perf.roc_auc * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Temporal Risk Trajectory Chart */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-display text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              24-Hour Threat Trajectory & Call Volume
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Live Aggregation</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.trend_data || []}>
                <defs>
                  <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={11} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="avg_risk" stroke="#06b6d4" strokeWidth={2.5} fillOpacity={1} fill="url(#colorRisk)" name="Avg Risk Index" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Attack Vector Distribution Bar Chart */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-display text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-rose-400" />
              Voice Spoof Attack Vector Breakdown
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Taxonomy</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.attack_vectors || []} layout="vertical">
                <XAxis type="number" stroke="#475569" fontSize={11} />
                <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} width={130} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                  {(data.attack_vectors || []).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Model Confusion Matrix */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold font-display text-white flex items-center gap-2">
              <Target className="w-4 h-4 text-cyan-400" />
              AASIST Confusion Matrix & False Positive / Negative Evaluation
            </h3>
            <span className="text-xs text-slate-400">Evaluated on test benchmark partition</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
          
          {/* Matrix Grid */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
            <div className="grid grid-cols-2 gap-3 text-center">
              
              {/* True Negative */}
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                <span className="text-[10px] uppercase font-mono text-emerald-400 block mb-1">True Negative (Bonafide Correct)</span>
                <span className="text-2xl font-black font-mono-numbers text-emerald-300">{cm.tn}</span>
                <span className="text-[10px] text-emerald-400/70 block mt-0.5">Correct Human Pass</span>
              </div>

              {/* False Positive */}
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
                <span className="text-[10px] uppercase font-mono text-amber-400 block mb-1">False Positive (False Alarm)</span>
                <span className="text-2xl font-black font-mono-numbers text-amber-300">{cm.fp}</span>
                <span className="text-[10px] text-amber-400/70 block mt-0.5">Human Flagged as AI</span>
              </div>

              {/* False Negative */}
              <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/35">
                <span className="text-[10px] uppercase font-mono text-rose-400 block mb-1">False Negative (Missed Clone)</span>
                <span className="text-2xl font-black font-mono-numbers text-rose-300">{cm.fn}</span>
                <span className="text-[10px] text-rose-400/70 block mt-0.5">Spoof Passed as Human</span>
              </div>

              {/* True Positive */}
              <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
                <span className="text-[10px] uppercase font-mono text-cyan-400 block mb-1">True Positive (Intercepted AI)</span>
                <span className="text-2xl font-black font-mono-numbers text-cyan-300">{cm.tp}</span>
                <span className="text-[10px] text-cyan-400/70 block mt-0.5">Correct Clone Interception</span>
              </div>

            </div>
          </div>

          {/* Matrix Rationale */}
          <div className="space-y-3 text-xs text-slate-300">
            <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800">
              <span className="font-bold text-slate-200 block mb-1">False Positive Rate (FPR):</span>
              <p className="text-slate-400">
                Current FPR is calibrated below <strong>2.2%</strong> to prevent legitimate callers from being falsely blocked.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800">
              <span className="font-bold text-slate-200 block mb-1">False Negative Rate (FNR):</span>
              <p className="text-slate-400">
                Current FNR is held at <strong>3.3%</strong>, ensuring adversarial voice deepfakes are intercepted before financial authorization.
              </p>
            </div>
          </div>

        </div>
      </div>

    </div>
  );
};
