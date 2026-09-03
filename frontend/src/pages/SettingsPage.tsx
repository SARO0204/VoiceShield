import React, { useState } from 'react';
import { Settings, Shield, Sliders, Check, Save } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [classificationThresh, setClassificationThresh] = useState(0.50);
  const [uncertaintyMin, setUncertaintyMin] = useState(0.45);
  const [uncertaintyMax, setUncertaintyMax] = useState(0.55);
  const [purgeRawAudio, setPurgeRawAudio] = useState(true);
  const [enableDesktopNotifications, setEnableDesktopNotifications] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <Settings className="w-4 h-4" />
            Security Policies & Calibration
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Privacy, Policies & Calibration Settings
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Configure zero-retention ephemeral audio handling, AI decision thresholds, and threat escalation weights.
          </p>
        </div>

        <button
          onClick={handleSave}
          className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-lg shadow-cyan-600/30 flex items-center gap-2 transition-all"
        >
          {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          <span>{saved ? 'Settings Saved!' : 'Save Changes'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Privacy & Zero-Retention Policy */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold font-display text-white flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-400" />
            Zero-Retention Privacy Controls
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex items-start justify-between gap-4">
              <div>
                <span className="font-bold text-slate-200 block mb-1">Ephemeral Audio Ingestion</span>
                <p className="text-slate-400 leading-relaxed">
                  Automatically purge raw voice recordings and PCM buffers immediately after AASIST feature extraction. Only cryptographic metadata and risk scores are persisted.
                </p>
              </div>
              <input
                type="checkbox"
                checked={purgeRawAudio}
                onChange={(e) => setPurgeRawAudio(e.target.checked)}
                className="mt-1 w-4 h-4 rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
              />
            </div>

            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex items-start justify-between gap-4">
              <div>
                <span className="font-bold text-slate-200 block mb-1">Desktop Threat Alerts</span>
                <p className="text-slate-400 leading-relaxed">
                  Trigger immediate browser push notifications when a CRITICAL voice cloning scam event is intercepted.
                </p>
              </div>
              <input
                type="checkbox"
                checked={enableDesktopNotifications}
                onChange={(e) => setEnableDesktopNotifications(e.target.checked)}
                className="mt-1 w-4 h-4 rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Confidence & Uncertainty Calibration */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-base font-bold font-display text-white flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            Decision Boundary & Uncertainty Calibration
          </h3>

          <div className="space-y-4 text-xs">
            <div>
              <div className="flex justify-between text-slate-300 font-semibold mb-1">
                <span>Classification Threshold:</span>
                <span className="font-mono text-cyan-400">{(classificationThresh * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.30"
                max="0.80"
                step="0.05"
                value={classificationThresh}
                onChange={(e) => setClassificationThresh(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
              <span className="text-[10px] text-slate-500">Audio with AI probability above this threshold is labeled SYNTHETIC.</span>
            </div>

            <div>
              <div className="flex justify-between text-slate-300 font-semibold mb-1">
                <span>Uncertainty Lower Bound:</span>
                <span className="font-mono text-amber-400">{(uncertaintyMin * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.35"
                max="0.49"
                step="0.01"
                value={uncertaintyMin}
                onChange={(e) => setUncertaintyMin(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 font-semibold mb-1">
                <span>Uncertainty Upper Bound:</span>
                <span className="font-mono text-amber-400">{(uncertaintyMax * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.51"
                max="0.65"
                step="0.01"
                value={uncertaintyMax}
                onChange={(e) => setUncertaintyMax(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
