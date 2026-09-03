import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileAudio,
  Play,
  Pause,
  ShieldCheck,
  ShieldAlert,
  Activity,
  FileText,
  FileDown,
  Lock,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { api } from '../services/api';
import type { AnalysisRecord } from '../types';
import { RiskBadge } from '../components/common/RiskBadge';
import { AudioWaveform } from '../components/common/AudioWaveform';

export const AnalyzeAudioPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [callerLabel, setCallerLabel] = useState('Unknown Caller');
  const [transcript, setTranscript] = useState('');
  const [financialHint, setFinancialHint] = useState(false);
  const [urgencyHint, setUrgencyHint] = useState(false);
  const [otpHint, setOtpHint] = useState(false);

  // Analysis State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [analysisStep, setAnalysisStep] = useState<string>('');
  const [result, setResult] = useState<AnalysisRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    setAudioUrl(URL.createObjectURL(file));
    setResult(null);
    setError(null);
  };

  const togglePlayAudio = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleRunAnalysis = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      setAnalysisStep('Preprocessing Audio (16 kHz Mono & Silence Trimming)...');
      await new Promise((r) => setTimeout(r, 600));

      setAnalysisStep('Executing AASIST Neural Graph Attention Model...');
      await new Promise((r) => setTimeout(r, 800));

      setAnalysisStep('Extracting Scam Context & Social Engineering Patterns...');
      await new Promise((r) => setTimeout(r, 600));

      setAnalysisStep('Computing Composite Multi-Factor Risk Score...');

      const data = await api.analyzeAudio(
        selectedFile,
        selectedFile.name,
        transcript || undefined,
        callerLabel,
        { financial: financialHint, urgency: urgencyHint, otp: otpHint }
      );

      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Audio analysis failed.');
    } finally {
      setIsAnalyzing(false);
      setAnalysisStep('');
    }
  };

  const handleDownloadPdf = async () => {
    if (!result?.id) return;
    try {
      setIsDownloadingPdf(true);
      await api.downloadReportPdf(result.id);
    } catch (err: any) {
      setError(err.message || 'Failed to download forensic report');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  // Quick Preset Sample Loader for demonstration
  const loadDemoSample = async (type: 'genuine' | 'synthetic_scam') => {
    const sampleRate = 16000;
    const duration = 3.5;
    const numSamples = sampleRate * duration;
    const buffer = new ArrayBuffer(44 + numSamples * 2);
    const view = new DataView(buffer);

    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + numSamples * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, numSamples * 2, true);

    const freq = type === 'synthetic_scam' ? 220 : 440;
    for (let i = 0; i < numSamples; i++) {
      const sample = Math.sin((i / sampleRate) * 2 * Math.PI * freq) * 0.5;
      const int16 = Math.max(-32768, Math.min(32767, Math.floor(sample * 32767)));
      view.setInt16(44 + i * 2, int16, true);
    }

    const blob = new Blob([buffer], { type: 'audio/wav' });
    const filename = type === 'synthetic_scam' ? 'voice_clone_scam_sample.wav' : 'genuine_human_sample.wav';
    const file = new File([blob], filename, { type: 'audio/wav' });

    setSelectedFile(file);
    setAudioUrl(URL.createObjectURL(file));
    setCallerLabel(type === 'synthetic_scam' ? 'Grandson Claim (Urgent Call)' : 'Colleague Verification');
    setTranscript(
      type === 'synthetic_scam'
        ? 'Hey, I am in big trouble at the police station. Please send 50000 rupees immediately to this UPI number. Do not tell mom or dad.'
        : 'Hi team, confirming our project deployment meeting scheduled for tomorrow afternoon at 2 PM.'
    );
    setFinancialHint(type === 'synthetic_scam');
    setUrgencyHint(type === 'synthetic_scam');
    setResult(null);
  };

  return (
    <div className="space-y-6 pb-12">
      
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            Forensic Audio File Analysis
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Inspect & Verify Voice Authenticity
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Upload voice recordings, voicemails, or call captures to perform deep spectro-temporal AASIST graph analysis and scam intent extraction.
          </p>
        </div>

        {/* Preset sample buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => loadDemoSample('synthetic_scam')}
            className="px-3 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Load Voice Clone Sample
          </button>
          <button
            onClick={() => loadDemoSample('genuine')}
            className="px-3 py-2 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            Load Genuine Sample
          </button>
        </div>
      </div>

      {/* Main Form & Upload Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left: File Ingestion & Audio Controls */}
        <div className="space-y-4">
          
          {/* Drag and Drop Zone */}
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files?.[0]) handleFileChange(e.dataTransfer.files[0]);
            }}
            className="p-8 rounded-2xl border-2 border-dashed border-slate-700 hover:border-cyan-500/60 bg-slate-900/40 hover:bg-slate-900/70 transition-all cursor-pointer text-center flex flex-col items-center justify-center min-h-[220px]"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".wav,.mp3,.flac,.ogg,.m4a,.webm"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.[0]) handleFileChange(e.target.files[0]);
              }}
            />

            <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mb-3">
              <UploadCloud className="w-7 h-7 text-cyan-400" />
            </div>

            {selectedFile ? (
              <div className="space-y-1">
                <span className="text-sm font-bold text-slate-100 block">{selectedFile.name}</span>
                <span className="text-xs font-mono text-cyan-400 block">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB | Ready for AASIST Inspection
                </span>
              </div>
            ) : (
              <div className="space-y-1">
                <span className="text-sm font-bold text-slate-200 block">
                  Drop audio file here or click to browse
                </span>
                <span className="text-xs text-slate-400 block">
                  Supports WAV, MP3, FLAC, OGG, M4A (16 kHz Resampled Automatically)
                </span>
              </div>
            )}
          </div>

          {/* Audio Player Card (If file selected) */}
          {audioUrl && (
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileAudio className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-bold text-slate-200">{selectedFile?.name}</span>
                </div>
                <button
                  onClick={togglePlayAudio}
                  className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold flex items-center gap-1.5 transition-colors"
                >
                  {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  {isPlaying ? 'Pause' : 'Play Audio'}
                </button>
              </div>

              <audio
                ref={audioRef}
                src={audioUrl}
                onEnded={() => setIsPlaying(false)}
                className="hidden"
              />

              <AudioWaveform isActive={isPlaying} riskLevel={result?.risk.level || 'LOW'} height={65} />
            </div>
          )}

          {/* Context & Transcript Inputs */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3.5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              Caller & Context Metadata (Optional)
            </h3>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                Caller Label / Target Identity:
              </label>
              <input
                type="text"
                value={callerLabel}
                onChange={(e) => setCallerLabel(e.target.value)}
                placeholder="e.g. Unknown Caller, Grandson, Bank Representative"
                className="w-full px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                Transcript / Spoken Content:
              </label>
              <textarea
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                rows={3}
                placeholder="Enter what the caller said to run NLP scam and fraud detection..."
                className="w-full px-3 py-2 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 resize-none"
              />
            </div>

            {/* Quick Trigger Checkboxes */}
            <div className="flex flex-wrap gap-4 pt-1 text-xs">
              <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={financialHint}
                  onChange={(e) => setFinancialHint(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-700 text-cyan-500 focus:ring-0"
                />
                <span>Money / Transfer Demand</span>
              </label>

              <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={urgencyHint}
                  onChange={(e) => setUrgencyHint(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-700 text-cyan-500 focus:ring-0"
                />
                <span>Urgency / Panic Pressure</span>
              </label>

              <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={otpHint}
                  onChange={(e) => setOtpHint(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-700 text-cyan-500 focus:ring-0"
                />
                <span>OTP / Password Request</span>
              </label>
            </div>
          </div>

          {/* Run Analysis Button */}
          <button
            onClick={handleRunAnalysis}
            disabled={!selectedFile || isAnalyzing}
            className={`w-full py-3.5 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all shadow-xl ${
              !selectedFile || isAnalyzing
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-cyan-600/25'
            }`}
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin text-cyan-300" />
                <span>{analysisStep || 'Processing Neural Pipeline...'}</span>
              </>
            ) : (
              <>
                <Activity className="w-5 h-5" />
                <span>Run Voice Deepfake Analysis</span>
              </>
            )}
          </button>

          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          )}

        </div>

        {/* Right: Forensic Results Card */}
        <div>
          {!result && !isAnalyzing ? (
            <div className="p-12 rounded-2xl bg-slate-900/40 border border-slate-800 flex flex-col items-center justify-center text-center h-full min-h-[480px]">
              <div className="w-16 h-16 rounded-full bg-slate-800/60 flex items-center justify-center mb-4 text-slate-500">
                <ShieldCheck className="w-8 h-8" />
              </div>
              <h3 className="text-base font-bold text-slate-300 mb-1">Awaiting Audio Submission</h3>
              <p className="text-xs text-slate-500 max-w-sm">
                Select an audio sample on the left to run AASIST neural inference, spectro-temporal graph attention, and fraud scoring.
              </p>
            </div>
          ) : isAnalyzing ? (
            <div className="p-12 rounded-2xl bg-slate-900/60 border border-cyan-500/30 flex flex-col items-center justify-center text-center h-full min-h-[480px] space-y-4">
              <div className="w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin" />
              <h3 className="text-base font-bold text-cyan-300">{analysisStep}</h3>
              <p className="text-xs font-mono text-slate-400">Model: AASIST v1.0 | SincNet Frontend</p>
            </div>
          ) : (
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6 animate-fadeIn">
              
              {/* Result Header */}
              <div className="flex items-start justify-between pb-4 border-b border-slate-800">
                <div>
                  <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest block">
                    Forensic Verdict
                  </span>
                  <h2 className="text-xl font-bold font-display text-white mt-0.5">
                    {result?.prediction.classification === 'SYNTHETIC'
                      ? 'AI Synthetic / Cloned Speech Detected'
                      : result?.prediction.classification === 'UNCERTAIN'
                      ? 'Uncertain Voice Authenticity'
                      : 'Authentic Human Speech'}
                  </h2>
                  <span className="text-xs text-slate-400">Duration: {result?.audio_duration_sec.toFixed(2)}s | Chunks: {result?.chunks?.length || 1}</span>
                </div>

                <RiskBadge level={result?.risk.level} score={result?.risk.score} size="lg" />
              </div>

              {/* Gauges */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-[11px] font-medium text-slate-400 block">AI Synthetic Likelihood</span>
                  <span className={`text-2xl font-black font-mono-numbers ${result?.prediction.ai_probability && result.prediction.ai_probability > 0.7 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {((result?.prediction.ai_probability || 0) * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                  <span className="text-[11px] font-medium text-slate-400 block">Scam Context Score</span>
                  <span className="text-2xl font-black font-mono-numbers text-amber-400">
                    {((result?.scam_context.score || 0) * 100).toFixed(0)} / 100
                  </span>
                </div>
              </div>

              {/* Explainability Reasons */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-cyan-400" />
                  Why is this flagged? (Explainability)
                </h4>
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5 text-xs text-slate-200">
                  {result?.explanation.map((reason, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <span className="text-cyan-400 font-bold">✓</span>
                      <span>{reason}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommended Action Directives */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-amber-500/30 space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-300">
                  <Lock className="w-4 h-4 text-amber-400" />
                  <span>Recommended Action:</span>
                </div>
                <p className="text-xs text-slate-300 font-medium">
                  {result?.risk.recommended_action}
                </p>
              </div>

              {/* Download PDF Forensic Report Action */}
              <button
                onClick={handleDownloadPdf}
                disabled={isDownloadingPdf}
                className="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-750 text-cyan-300 hover:text-cyan-200 border border-cyan-500/30 hover:border-cyan-500/60 font-semibold text-xs flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-cyan-500/10"
              >
                {isDownloadingPdf ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
                    <span>Generating Cryptographic PDF...</span>
                  </>
                ) : (
                  <>
                    <FileDown className="w-4 h-4 text-cyan-400" />
                    <span>Download Official PDF Forensic Report</span>
                  </>
                )}
              </button>

              {/* Legal / Model Disclaimer */}
              <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 text-[10px] text-slate-500 leading-relaxed font-mono">
                <strong>Disclaimer:</strong> {result?.disclaimer}
              </div>

            </div>
          )}
        </div>

      </div>

    </div>
  );
};
