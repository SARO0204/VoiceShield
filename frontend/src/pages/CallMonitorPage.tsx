import React, { useState, useEffect } from "react";
import {
  PhoneCall,
  Search,
  Activity,
  ArrowLeft,
  FileText,
  FileDown,
  RefreshCw,
} from "lucide-react";
import { api } from "../services/api";
import type { CallRecord, AnalysisRecord } from "../types";
import { RiskBadge } from "../components/common/RiskBadge";

export const CallMonitorPage: React.FC = () => {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  const [callDetail, setCallDetail] = useState<{
    call: CallRecord;
    analyses: AnalysisRecord[];
    timeline_events: any[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchCalls = async () => {
    setLoading(true);
    try {
      const res = await api.getCalls(50);
      setCalls(res.items);
      setError(null);
    } catch (e) {
      const message =
        e instanceof Error ? e.message : "Call records are unavailable.";
      setError(message);
      console.error("Error fetching calls:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, []);

  const openCallDetail = async (callId: string) => {
    setSelectedCallId(callId);
    setDetailError(null);
    try {
      const detail = await api.getCallDetail(callId);
      setCallDetail(detail);
    } catch (e) {
      const message =
        e instanceof Error ? e.message : "Call details are unavailable.";
      setDetailError(message);
      console.error("Error fetching call details:", e);
    }
  };

  const filteredCalls = calls.filter(
    (c) =>
      c.caller_label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.id.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <PhoneCall className="w-4 h-4" />
            Continuous Voice Stream Auditing
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Monitored Voice Calls & Streams
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Inspect call timelines, chunk-by-chunk deepfake probability
            evolution, and flagged scam transcripts.
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search caller or ID..."
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {selectedCallId && callDetail ? (
        /* Detailed Call View */
        <div className="space-y-6 animate-fadeIn">
          <button
            onClick={() => {
              setSelectedCallId(null);
              setCallDetail(null);
            }}
            className="inline-flex items-center gap-2 text-xs text-cyan-400 hover:text-cyan-300 font-semibold"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to All Calls
          </button>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Call Profile */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex items-start justify-between pb-3 border-b border-slate-800">
                <div>
                  <h3 className="text-lg font-bold font-display text-white">
                    {callDetail.call.caller_label}
                  </h3>
                  <span className="text-xs font-mono text-slate-400">
                    ID: {callDetail.call.id}
                  </span>
                </div>
                <RiskBadge
                  level={callDetail.call.risk_level}
                  score={callDetail.call.overall_risk}
                />
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between p-2 rounded-lg bg-slate-950/40">
                  <span className="text-slate-400">Started At:</span>
                  <span className="font-mono text-slate-200">
                    {callDetail.call.started_at}
                  </span>
                </div>
                <div className="flex justify-between p-2 rounded-lg bg-slate-950/40">
                  <span className="text-slate-400">Duration:</span>
                  <span className="font-mono text-slate-200">
                    {callDetail.call.duration_sec.toFixed(1)} seconds
                  </span>
                </div>
                <div className="flex justify-between p-2 rounded-lg bg-slate-950/40">
                  <span className="text-slate-400">Classification:</span>
                  <RiskBadge
                    classification={callDetail.call.overall_classification}
                  />
                </div>
                <div className="flex justify-between p-2 rounded-lg bg-slate-950/40">
                  <span className="text-slate-400">Status:</span>
                  <span className="font-bold text-cyan-400">
                    {callDetail.call.status}
                  </span>
                </div>
              </div>

              {callDetail.call.transcript && (
                <div className="pt-2">
                  <span className="text-xs font-bold text-slate-300 block mb-1.5 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-cyan-400" />
                    Transcript Record:
                  </span>
                  <p className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                    "{callDetail.call.transcript}"
                  </p>
                </div>
              )}

              {/* PDF Report Download */}
              <button
                onClick={async () => {
                  const targetId =
                    callDetail.analyses[0]?.id || callDetail.call.id;
                  try {
                    setIsDownloadingPdf(true);
                    await api.downloadReportPdf(targetId);
                  } catch (e) {
                    console.error(e);
                  } finally {
                    setIsDownloadingPdf(false);
                  }
                }}
                disabled={isDownloadingPdf}
                className="w-full mt-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-cyan-300 hover:text-cyan-200 border border-cyan-500/30 font-semibold text-xs flex items-center justify-center gap-2 transition-all shadow-md"
              >
                {isDownloadingPdf ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                    <span>Generating PDF...</span>
                  </>
                ) : (
                  <>
                    <FileDown className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Download Forensic PDF</span>
                  </>
                )}
              </button>
            </div>

            {/* Right: Chunk-by-Chunk Progression & Timeline */}
            <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold font-display text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                Chunk-by-Chunk Risk Evolution
              </h3>

              <div className="space-y-3">
                {callDetail.analyses.map((ana, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200">
                        Segment #{idx + 1} ({ana.audio_duration_sec.toFixed(1)}
                        s)
                      </span>
                      <RiskBadge
                        level={ana.risk.level}
                        score={ana.risk.score}
                        size="sm"
                      />
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="p-2 rounded bg-slate-900/50">
                        <span className="text-[10px] text-slate-400 block">
                          AI Probability
                        </span>
                        <span className="font-mono font-bold text-rose-400">
                          {(ana.prediction.ai_probability * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-900/50">
                        <span className="text-[10px] text-slate-400 block">
                          Confidence
                        </span>
                        <span className="font-mono font-bold text-cyan-400">
                          {(ana.prediction.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-900/50">
                        <span className="text-[10px] text-slate-400 block">
                          Scam Context
                        </span>
                        <span className="font-mono font-bold text-amber-400">
                          {(ana.scam_context.score * 100).toFixed(0)}/100
                        </span>
                      </div>
                    </div>

                    {ana.explanation.length > 0 && (
                      <p className="text-[11px] text-slate-400 italic">
                        {ana.explanation[0]}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Calls Table */
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          {loading ? (
            <div className="p-12 text-center text-xs font-mono text-cyan-400">
              Loading call records...
            </div>
          ) : error ? (
            <div className="p-12 text-center text-xs font-mono text-rose-400">
              {error}
            </div>
          ) : filteredCalls.length === 0 ? (
            <div className="p-12 text-center text-xs font-mono text-slate-500">
              No calls matching filter.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-slate-400 bg-slate-950/60 border-b border-slate-800 font-mono uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Session Start</th>
                    <th className="p-3">Caller Identity</th>
                    <th className="p-3">Duration</th>
                    <th className="p-3">Classification</th>
                    <th className="p-3">Threat Risk</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Inspect</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredCalls.map((c) => (
                    <tr
                      key={c.id}
                      className="hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="p-3 font-mono text-slate-400">
                        {c.started_at
                          ? c.started_at.replace("T", " ").substring(0, 19)
                          : "-"}
                      </td>
                      <td className="p-3 font-semibold text-slate-200">
                        {c.caller_label}
                      </td>
                      <td className="p-3 font-mono text-slate-400">
                        {c.duration_sec.toFixed(1)}s
                      </td>
                      <td className="p-3">
                        <RiskBadge classification={c.overall_classification} />
                      </td>
                      <td className="p-3">
                        <RiskBadge
                          level={c.risk_level}
                          score={c.overall_risk}
                        />
                      </td>
                      <td className="p-3 font-mono font-bold text-cyan-400">
                        {c.status}
                      </td>
                      <td className="p-3 text-right">
                        <button
                          onClick={() => openCallDetail(c.id)}
                          className="px-2.5 py-1 rounded-lg bg-cyan-600/20 hover:bg-cyan-600 text-cyan-300 hover:text-white transition-colors"
                        >
                          Deep Inspect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {detailError && selectedCallId && !callDetail && (
        <div className="p-12 text-center text-xs font-mono text-rose-400">
          {detailError}
        </div>
      )}
    </div>
  );
};
