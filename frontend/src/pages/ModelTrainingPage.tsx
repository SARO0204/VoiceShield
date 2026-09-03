import React, { useState, useEffect } from 'react';
import { Cpu, Play, RefreshCw, Terminal, Layers } from 'lucide-react';
import { api } from '../services/api';
import type { TrainingState, SystemStatus } from '../types';

export const ModelTrainingPage: React.FC = () => {
  const [trainingState, setTrainingState] = useState<TrainingState | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [epochs, setEpochs] = useState(20);
  const [batchSize, setBatchSize] = useState(16);
  const [learningRate, setLearningRate] = useState(0.0001);
  const [isStarting, setIsStarting] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  const fetchStatus = async () => {
    try {
      const [tState, sStatus] = await Promise.all([
        api.getTrainingStatus(),
        api.getSystemStatus(),
      ]);
      setTrainingState(tState);
      setSystemStatus(sStatus);
      if (tState.logs) {
        setLogs(tState.logs);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2500);
    return () => clearInterval(interval);
  }, []);

  const handleStartTraining = async () => {
    setIsStarting(true);
    try {
      await api.startTraining(epochs, batchSize, learningRate);
      await fetchStatus();
    } catch (e: any) {
      alert(e.message || 'Failed to start training');
    } finally {
      setIsStarting(false);
    }
  };

  const isTrainingActive = trainingState?.status === 'TRAINING' || trainingState?.status === 'PREPARING_DATA';

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <Cpu className="w-4 h-4" />
            Automated MLOps & Anti-Spoofing Training Supervisor
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Model & Training Studio
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Train, fine-tune, evaluate, and promote AASIST neural architectures with speaker-disjoint isolation and model quality gates.
          </p>
        </div>

        <button
          onClick={handleStartTraining}
          disabled={isTrainingActive || isStarting}
          className={`px-5 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 shadow-lg transition-all ${
            isTrainingActive || isStarting
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-600/30'
          }`}
        >
          {isTrainingActive ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin text-cyan-300" />
              <span>Training In Progress...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Start AASIST Training</span>
            </>
          )}
        </button>
      </div>

      {/* Model & Hardware Telemetry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 block mb-1">Active Neural Architecture</span>
          <span className="text-xl font-bold font-display text-cyan-400">AASIST v1.0</span>
          <span className="text-[10px] text-slate-500 block font-mono mt-0.5">SincNet + GAT Modules</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 block mb-1">Compute Execution Device</span>
          <span className="text-xl font-bold font-mono text-emerald-400">
            {systemStatus?.gpu?.available ? 'NVIDIA CUDA' : 'CPU FALLBACK'}
          </span>
          <span className="text-[10px] text-slate-500 block font-mono mt-0.5">
            {systemStatus?.gpu?.name || 'Multi-thread CPU'}
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 block mb-1">Dataset Status</span>
          <span className="text-xl font-bold font-mono text-slate-200">
            {trainingState?.dataset_status === 'READY' ? 'VALIDATED' : 'STANDBY'}
          </span>
          <span className="text-[10px] text-slate-500 block font-mono mt-0.5">Speaker-Disjoint Manifests</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 block mb-1">Current Training Status</span>
          <span className={`text-xl font-bold font-mono ${isTrainingActive ? 'text-amber-400 animate-pulse' : 'text-slate-300'}`}>
            {trainingState?.status || 'NOT_STARTED'}
          </span>
          <span className="text-[10px] text-slate-500 block font-mono mt-0.5">
            {trainingState?.message || 'Ready'}
          </span>
        </div>
      </div>

      {/* Training Progress Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left: Hyperparameter Configuration */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold font-display text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            Training Hyperparameters
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Epochs:</label>
              <input
                type="number"
                value={epochs}
                onChange={(e) => setEpochs(Number(e.target.value))}
                disabled={isTrainingActive}
                className="w-full px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Batch Size:</label>
              <input
                type="number"
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                disabled={isTrainingActive}
                className="w-full px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Learning Rate:</label>
              <input
                type="number"
                step="0.00001"
                value={learningRate}
                onChange={(e) => setLearningRate(Number(e.target.value))}
                disabled={isTrainingActive}
                className="w-full px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-slate-200"
              />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <span className="font-bold text-slate-300 block mb-1">Automated Quality Gate:</span>
            <p>New model is promoted only if validation F1 &gt; active F1 and EER &lt; active EER.</p>
          </div>
        </div>

        {/* Right: Live Training Logs & Progress Monitor (Span 2) */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-display text-white flex items-center gap-2">
              <Terminal className="w-4 h-4 text-cyan-400" />
              Live Epoch Telemetry & Logs
            </h3>

            {isTrainingActive && (
              <span className="text-xs font-mono text-cyan-400 animate-pulse">
                Epoch {trainingState?.current_epoch} / {trainingState?.total_epochs}
              </span>
            )}
          </div>

          {/* Progress Bar */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-mono text-slate-400">
              <span>Overall Training Progress</span>
              <span>{trainingState?.progress_percent?.toFixed(1) || '0.0'}%</span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 transition-all duration-300"
                style={{ width: `${trainingState?.progress_percent || 0}%` }}
              />
            </div>
          </div>

          {/* Epoch Metrics */}
          <div className="grid grid-cols-4 gap-2 text-center text-xs pt-1">
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Train Loss</span>
              <span className="font-mono font-bold text-slate-200">{trainingState?.train_loss?.toFixed(4) || '0.0000'}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Val Loss</span>
              <span className="font-mono font-bold text-slate-200">{trainingState?.val_loss?.toFixed(4) || '0.0000'}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Best F1</span>
              <span className="font-mono font-bold text-cyan-400">{trainingState?.best_f1 ? (trainingState.best_f1 * 100).toFixed(1) + '%' : '--'}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Best EER</span>
              <span className="font-mono font-bold text-emerald-400">{trainingState?.best_eer !== undefined ? (trainingState.best_eer * 100).toFixed(1) + '%' : '--'}</span>
            </div>
          </div>

          {/* Console Log Terminal */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/90 font-mono text-[11px] text-cyan-300/90 h-56 overflow-y-auto space-y-1">
            {logs.length === 0 ? (
              <div className="text-slate-500">Ready to initiate ML lifecycle. Click 'Start AASIST Training' above.</div>
            ) : (
              logs.map((log, i) => <div key={i} className="leading-tight">{log}</div>)
            )}
          </div>
        </div>

      </div>

    </div>
  );
};
