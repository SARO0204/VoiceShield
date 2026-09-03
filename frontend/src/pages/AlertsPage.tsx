import React, { useState, useEffect } from 'react';
import { BellRing, AlertOctagon, CheckCircle2, Filter, Ban } from 'lucide-react';
import { api } from '../services/api';
import type { AlertRecord } from '../types';
import { RiskBadge } from '../components/common/RiskBadge';

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.getAlerts(severityFilter || undefined);
      setAlerts(res.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [severityFilter]);

  const handleResolve = async (alertId: string, resolution: string) => {
    try {
      await api.resolveAlert(alertId, resolution);
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId ? { ...a, resolved: true, resolution } : a
        )
      );
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <BellRing className="w-4 h-4" />
            Security Operations Incident Response
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Incident Alerts & Fraud Response Center
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Triage, disposition, and resolve critical voice cloning security alerts and impersonation events.
          </p>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical Alerts</option>
            <option value="HIGH">High Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="LOW">Low Risk</option>
          </select>
        </div>
      </div>

      {/* Alerts Stream */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center text-xs font-mono text-cyan-400">Loading incident alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="p-12 text-center text-xs font-mono text-slate-500 rounded-2xl bg-slate-900/40 border border-slate-800">
            No incident alerts found. Protection active and systems operating normally.
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-5 rounded-2xl border transition-all ${
                alert.resolved
                  ? 'bg-slate-900/40 border-slate-800/80 opacity-75'
                  : alert.severity === 'CRITICAL'
                  ? 'bg-rose-500/10 border-rose-500/40 shadow-lg shadow-rose-500/10'
                  : 'bg-slate-900/70 border-slate-800'
              }`}
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl ${alert.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' : 'bg-orange-500/20 text-orange-400'}`}>
                    <AlertOctagon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      {alert.title}
                    </h3>
                    <span className="text-[11px] font-mono text-slate-400">
                      ID: {alert.id} | Timestamp: {alert.created_at?.replace('T', ' ').substring(0, 19)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <RiskBadge level={alert.severity as any} score={alert.risk_score} />
                  {alert.resolved && (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                      RESOLVED ({alert.resolution})
                    </span>
                  )}
                </div>
              </div>

              <div className="py-3 space-y-2 text-xs">
                <p className="text-slate-200 font-medium">{alert.message}</p>
                {alert.reasons && alert.reasons.length > 0 && (
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1 text-[11px] text-slate-300">
                    <span className="font-bold text-slate-400 block mb-1">Detection Evidence:</span>
                    {alert.reasons.map((r, i) => (
                      <div key={i} className="flex items-center gap-1.5">
                        <span className="text-cyan-400 font-bold">✓</span>
                        <span>{r}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Disposition Action Buttons */}
              {!alert.resolved && (
                <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-slate-800/80">
                  <button
                    onClick={() => handleResolve(alert.id, 'FALSE_POSITIVE')}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    Mark False Positive
                  </button>

                  <button
                    onClick={() => handleResolve(alert.id, 'CONFIRM_SCAM')}
                    className="px-3 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/40 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <Ban className="w-3.5 h-3.5" />
                    Confirm Voice Scam
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

    </div>
  );
};
