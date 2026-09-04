import React, { useState, useEffect } from "react";
import {
  Activity,
  Server,
  Database,
  Cpu,
  Radio,
  HardDrive,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { api } from "../services/api";
import type { SystemStatus } from "../types";

export const SystemHealthPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      const res = await api.getSystemStatus();
      setStatus(res);
      setError(null);
    } catch (e) {
      const message =
        e instanceof Error ? e.message : "System health data is unavailable.";
      setError(message);
      console.error("Error fetching system health:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-mono text-cyan-400">
            Pinging infrastructure nodes...
          </span>
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <div className="text-center text-sm font-mono text-rose-400">
          {error || "System health data is unavailable."}
        </div>
      </div>
    );
  }

  const nodes = [
    {
      name: "FastAPI Backend Core",
      status: status.backend,
      subtext: `v${status.version} REST & Async Core`,
      icon: Server,
      isHealthy: status.backend === "ONLINE",
    },
    {
      name: "MongoDB Database",
      status: status.mongodb,
      subtext: "Atlas / Local Engine",
      icon: Database,
      isHealthy: status.mongodb === "CONNECTED",
    },
    {
      name: "AASIST Neural Model Engine",
      status: status.ml_model,
      subtext: `Mode: ${status.model_mode}`,
      icon: Cpu,
      isHealthy: status.ml_model === "LOADED",
    },
    {
      name: "Compute Hardware Accelerator",
      status: status.gpu.available ? "CUDA GPU" : "CPU FALLBACK",
      subtext: status.gpu.name || "CPU Host",
      icon: Activity,
      isHealthy: true,
    },
    {
      name: "WebSocket Live Stream Hub",
      status: status.websocket,
      subtext: "Sub-100ms Ingestion Hub",
      icon: Radio,
      isHealthy: status.websocket === "ONLINE",
    },
    {
      name: "Forensic Storage Partition",
      status: status.storage.status,
      subtext: `${status.storage.free_space_gb} GB Free Storage`,
      icon: HardDrive,
      isHealthy: status.storage.status === "HEALTHY",
    },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <Activity className="w-4 h-4" />
            Infrastructure Health & Telemetry
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            System & Component Health Status
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Live diagnostic health checks of database clusters, GPU
            accelerators, ML inference workers, and storage partitions.
          </p>
        </div>
      </div>

      {/* Nodes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {nodes.map((node, i) => {
          const Icon = node.icon;
          return (
            <div
              key={i}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-cyan-400">
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-200">
                      {node.name}
                    </h3>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {node.subtext}
                    </span>
                  </div>
                </div>

                <div
                  className={`p-1 rounded-full ${node.isHealthy ? "text-emerald-400" : "text-amber-400"}`}
                >
                  {node.isHealthy ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <AlertCircle className="w-5 h-5" />
                  )}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
                <span className="text-slate-400">Node Status:</span>
                <span
                  className={`font-mono font-bold ${node.isHealthy ? "text-emerald-400" : "text-amber-400"}`}
                >
                  {node.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
