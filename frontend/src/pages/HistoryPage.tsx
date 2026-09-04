import React, { useState, useEffect } from "react";
import { History, Search, Download } from "lucide-react";
import { api } from "../services/api";
import type { AnalysisRecord } from "../types";
import { RiskBadge } from "../components/common/RiskBadge";

export const HistoryPage: React.FC = () => {
  const [analyses, setAnalyses] = useState<AnalysisRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [classFilter, setClassFilter] = useState("");
  const [selectedAnalysis, setSelectedAnalysis] =
    useState<AnalysisRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalyses = async () => {
    setLoading(true);
    try {
      const res = await api.getAnalyses(
        100,
        0,
        riskFilter || undefined,
        classFilter || undefined,
      );
      setAnalyses(res.items);
      setError(null);
    } catch (e) {
      const message =
        e instanceof Error ? e.message : "Forensic history is unavailable.";
      setError(message);
      console.error("Error fetching forensic history:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
  }, [riskFilter, classFilter]);

  const filtered = analyses.filter(
    (a) =>
      a.caller_label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.id.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(analyses, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `voiceshield_forensic_export_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <History className="w-4 h-4" />
            Forensic Audit & Historical Logs
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Forensic Analysis History
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Complete immutable ledger of voice anti-spoofing analyses,
            probability scores, and evidence reasoning.
          </p>
        </div>

        <button
          onClick={exportJSON}
          className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-colors"
        >
          <Download className="w-4 h-4 text-cyan-400" />
          Export Forensic JSON
        </button>
      </div>

      {/* Filters Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by analysis ID, caller, or file..."
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Risk Tiers</option>
            <option value="CRITICAL">Critical Risk</option>
            <option value="HIGH">High Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="LOW">Low Risk</option>
          </select>

          <select
            value={classFilter}
            onChange={(e) => setClassFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Classifications</option>
            <option value="SYNTHETIC">Synthetic / AI Clones</option>
            <option value="GENUINE">Genuine Human</option>
            <option value="UNCERTAIN">Uncertain Evidence</option>
          </select>
        </div>
      </div>

      {/* History Table */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
        {loading ? (
          <div className="p-12 text-center text-xs font-mono text-cyan-400">
            Loading historical forensic logs...
          </div>
        ) : error ? (
          <div className="p-12 text-center text-xs font-mono text-rose-400">
            {error}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-xs font-mono text-slate-500">
            No forensic records found matching filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 bg-slate-950/60 border-b border-slate-800 font-mono uppercase text-[10px]">
                <tr>
                  <th className="p-3">Analysis Time</th>
                  <th className="p-3">Target Subject</th>
                  <th className="p-3">Duration</th>
                  <th className="p-3">AI Likelihood</th>
                  <th className="p-3">Classification</th>
                  <th className="p-3">Risk Score</th>
                  <th className="p-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filtered.map((a) => (
                  <tr
                    key={a.id}
                    className="hover:bg-slate-800/30 transition-colors"
                  >
                    <td className="p-3 font-mono text-slate-400">
                      {a.timestamp
                        ? a.timestamp.replace("T", " ").substring(0, 19)
                        : "-"}
                    </td>
                    <td className="p-3 font-semibold text-slate-200">
                      {a.caller_label}
                    </td>
                    <td className="p-3 font-mono text-slate-400">
                      {a.audio_duration_sec?.toFixed(1)}s
                    </td>
                    <td className="p-3 font-mono font-bold text-rose-400">
                      {((a.prediction?.ai_probability || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="p-3">
                      <RiskBadge
                        classification={a.prediction?.classification}
                      />
                    </td>
                    <td className="p-3">
                      <RiskBadge level={a.risk?.level} score={a.risk?.score} />
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => setSelectedAnalysis(a)}
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

      {/* Forensic Detail Modal */}
      {selectedAnalysis && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
          <div className="w-full max-w-xl p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-start justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-white font-display">
                  Forensic Analysis #{selectedAnalysis.id}
                </h3>
                <span className="text-xs font-mono text-slate-400">
                  {selectedAnalysis.timestamp}
                </span>
              </div>
              <button
                onClick={() => setSelectedAnalysis(null)}
                className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-slate-400 block mb-1">
                  AI Voice Synthetic Prob:
                </span>
                <span className="text-xl font-bold font-mono text-rose-400">
                  {(
                    (selectedAnalysis.prediction.ai_probability || 0) * 100
                  ).toFixed(1)}
                  %
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-slate-400 block mb-1">
                  Risk Score / Level:
                </span>
                <RiskBadge
                  level={selectedAnalysis.risk.level}
                  score={selectedAnalysis.risk.score}
                />
              </div>
            </div>

            {selectedAnalysis.explanation.length > 0 && (
              <div className="space-y-1.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Evidence Points:
                </h4>
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1 text-xs text-slate-300">
                  {selectedAnalysis.explanation.map((e, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      <span className="text-cyan-400 font-bold">✓</span>
                      <span>{e}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="p-3 rounded-xl bg-slate-950/70 border border-amber-500/30 text-xs">
              <span className="font-bold text-amber-300 block mb-1">
                Recommended Action:
              </span>
              <p className="text-slate-300">
                {selectedAnalysis.risk.recommended_action}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
