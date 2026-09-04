import React, { useState, useEffect, useRef } from "react";
import {
  Radio,
  Mic,
  MicOff,
  Activity,
  Zap,
  Play,
  RotateCcw,
} from "lucide-react";
import { AudioWaveform } from "../components/common/AudioWaveform";
import { RiskBadge } from "../components/common/RiskBadge";
import { EmergencyAlertModal } from "../components/common/EmergencyAlertModal";
import { getBackendWebSocketUrl } from "../services/api";

interface TimelineEvent {
  time: string;
  message: string;
  type: "INFO" | "WARNING" | "CRITICAL" | "SAFE";
  score?: number;
}

export const LiveProtectionPage: React.FC = () => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  // Live Metrics
  const [aiProbability, setAiProbability] = useState(0.0);
  const [genuineProbability, setGenuineProbability] = useState(1.0);
  const [riskScore, setRiskScore] = useState(0);
  const [riskLevel, setRiskLevel] = useState<
    "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  >("LOW");
  const [classification, setClassification] = useState<string>("GENUINE");
  const [detectedIndicators, setDetectedIndicators] = useState<string[]>([]);
  const [waveformSamples, setWaveformSamples] = useState<number[]>([]);
  const [inferenceLatency, setInferenceLatency] = useState(0.0);

  // Live Timeline
  const [timeline, setTimeline] = useState<TimelineEvent[]>([
    {
      time: new Date().toLocaleTimeString(),
      message:
        "VoiceShield live monitoring initialized. Awaiting audio stream...",
      type: "INFO",
    },
  ]);

  // Critical Alert Modal State
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [alertReasons, setAlertReasons] = useState<string[]>([]);

  // Refs for Audio & WebSocket
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const simulationTimerRef = useRef<any>(null);

  // Helper to add timeline events
  const addEvent = (
    msg: string,
    type: "INFO" | "WARNING" | "CRITICAL" | "SAFE" = "INFO",
    score?: number,
  ) => {
    setTimeline((prev) => [
      { time: new Date().toLocaleTimeString(), message: msg, type, score },
      ...prev.slice(0, 40),
    ]);
  };

  // Start Real Microphone Monitoring
  const startMonitoring = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      });
      mediaStreamRef.current = stream;

      const AudioContextClass =
        window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioContextClass({ sampleRate: 16000 });
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      // Connect WebSocket
      const wsUrl = getBackendWebSocketUrl("/ws/live-analysis");
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsMonitoring(true);
        addEvent(
          "Microphone connected. Live WebSocket stream established with AASIST model.",
          "SAFE",
        );
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "STREAM_UPDATE") {
            const pred = data.prediction;
            const risk = data.risk;
            const scam = data.scam_context;

            setAiProbability(pred.ai_probability);
            setGenuineProbability(pred.genuine_probability);
            setClassification(pred.classification);
            setRiskScore(risk.score);
            setRiskLevel(risk.level);
            setDetectedIndicators(scam.detected_patterns || []);
            setInferenceLatency(data.performance?.inference_latency_ms || 0);

            if (data.audio_metrics?.waveform_samples) {
              setWaveformSamples(data.audio_metrics.waveform_samples);
            }

            // Timeline escalation checks
            if (risk.level === "CRITICAL") {
              addEvent(
                `CRITICAL THREAT: Multi-factor risk escalated to ${risk.score}/100!`,
                "CRITICAL",
                risk.score,
              );
              setAlertReasons(
                data.explanation || [
                  "High synthetic speech probability detected",
                ],
              );
              setShowAlertModal(true);
            } else if (risk.level === "HIGH") {
              addEvent(
                `HIGH RISK: Synthetic probability ${(pred.ai_probability * 100).toFixed(0)}% with suspicious context.`,
                "WARNING",
                risk.score,
              );
            } else if (pred.ai_probability > 0.6) {
              addEvent(
                `Acoustic anomaly detected: AI probability ${(pred.ai_probability * 100).toFixed(0)}%`,
                "WARNING",
              );
            }
          }
        } catch (e) {
          console.error("Error parsing WS frame", e);
        }
      };

      ws.onerror = (e) => {
        console.error("WS error", e);
        addEvent("WebSocket connection encountered an error.", "WARNING");
      };

      let buffer: Float32Array[] = [];
      let totalSamples = 0;

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        buffer.push(new Float32Array(inputData));
        totalSamples += inputData.length;

        // Send ~2.0 second chunks (32,000 samples at 16kHz)
        if (totalSamples >= 32000) {
          const merged = new Float32Array(totalSamples);
          let offset = 0;
          for (const b of buffer) {
            merged.set(b, offset);
            offset += b.length;
          }

          // Convert to 16-bit PCM binary
          const pcm16 = new Int16Array(merged.length);
          for (let i = 0; i < merged.length; i++) {
            const s = Math.max(-1, Math.min(1, merged[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
          }

          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(pcm16.buffer);
          }

          buffer = [];
          totalSamples = 0;
        }
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);
    } catch (err) {
      console.error("Microphone access denied", err);
      addEvent(
        "Microphone permission denied or device unavailable.",
        "CRITICAL",
      );
    }
  };

  // Stop Monitoring
  const stopMonitoring = () => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (simulationTimerRef.current) {
      clearInterval(simulationTimerRef.current);
      simulationTimerRef.current = null;
    }

    setIsMonitoring(false);
    setIsSimulating(false);
    addEvent("Live monitoring paused.", "INFO");
  };

  // Run Realistic Simulation (Simulated Voice-Cloning Scam Call Flow)
  const runSimulatedScamCall = () => {
    stopMonitoring();
    setIsSimulating(true);
    setIsMonitoring(true);

    addEvent(
      '19:42:01 Simulated incoming call session initiated ("Grandson Emergency Claim")',
      "INFO",
    );

    let step = 0;
    simulationTimerRef.current = setInterval(() => {
      step++;

      if (step === 1) {
        // Step 1: Normal voice onset
        setWaveformSamples(
          Array.from({ length: 64 }, () => (Math.random() - 0.5) * 0.4),
        );
        setAiProbability(0.24);
        setGenuineProbability(0.76);
        setClassification("GENUINE");
        setRiskScore(18);
        setRiskLevel("LOW");
        setInferenceLatency(42.5);
        addEvent(
          "19:42:03 Voice analysis started. Initial acoustic features extracted.",
          "SAFE",
        );
      } else if (step === 2) {
        // Step 2: Synthetic clone onset
        setWaveformSamples(
          Array.from({ length: 64 }, () => (Math.random() - 0.5) * 0.7),
        );
        setAiProbability(0.74);
        setGenuineProbability(0.26);
        setClassification("SYNTHETIC");
        setRiskScore(58);
        setRiskLevel("MEDIUM");
        setInferenceLatency(48.2);
        addEvent(
          "19:42:07 Synthetic probability increased to 74% (Neural vocoder pitch anomaly).",
          "WARNING",
          58,
        );
      } else if (step === 3) {
        // Step 3: Scam context trigger (Financial Demand)
        setWaveformSamples(
          Array.from({ length: 64 }, () => (Math.random() - 0.5) * 0.85),
        );
        setAiProbability(0.89);
        setGenuineProbability(0.11);
        setClassification("SYNTHETIC");
        setDetectedIndicators([
          "financial_request",
          "emergency_distress",
          "urgency_pressure",
        ]);
        setRiskScore(84);
        setRiskLevel("CRITICAL");
        setInferenceLatency(51.0);
        addEvent(
          '19:42:10 Financial request detected: "Send ₹50,000 immediately, in trouble with police"',
          "CRITICAL",
          84,
        );
      } else if (step === 4) {
        // Step 4: Critical Escalation & Trigger Alert Modal
        setRiskScore(94);
        setRiskLevel("CRITICAL");
        addEvent(
          "19:42:12 Multi-factor risk escalated to 94/100 (CRITICAL THREAT)",
          "CRITICAL",
          94,
        );
        addEvent(
          "19:42:15 Identity verification recommended. Directives dispatched to caller.",
          "CRITICAL",
        );
        setAlertReasons([
          "High synthetic speech probability (89% likelihood of AI voice cloning)",
          "Financial demand detected (Urgent transfer request)",
          'Emergency coercion detected ("In trouble, don\'t tell anyone")',
          "Caller identity unverified through out-of-band challenge",
        ]);
        setShowAlertModal(true);
        clearInterval(simulationTimerRef.current);
      }
    }, 2400);
  };

  useEffect(() => {
    return () => {
      stopMonitoring();
    };
  }, []);

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header Card */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-[#0d1626] to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-widest mb-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            Active Real-Time Stream Processor
          </div>
          <h1 className="text-2xl font-bold font-display text-white">
            Live Voice Clone Protection & Call Interception
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Live microphone streaming, sliding-window AASIST inference, NLP scam
            phrase detection, and instant critical fraud mitigation.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {!isMonitoring ? (
            <>
              <button
                onClick={startMonitoring}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-lg shadow-cyan-600/30 transition-all"
              >
                <Mic className="w-4 h-4" />
                Start Live Mic Monitoring
              </button>

              <button
                onClick={runSimulatedScamCall}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600/80 hover:bg-purple-600 text-white font-semibold text-xs border border-purple-500/40 shadow-lg shadow-purple-600/20 transition-all"
              >
                <Play className="w-4 h-4" />
                Simulate Scam Call Test
              </button>
            </>
          ) : (
            <button
              onClick={stopMonitoring}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-lg shadow-rose-600/30 animate-pulse transition-all"
            >
              <MicOff className="w-4 h-4" />
              Stop Active Monitoring
            </button>
          )}
        </div>
      </div>

      {/* Main Real-Time HUD */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Waveform & Radar Stream (Span 2) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Waveform Card */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold font-display text-white">
                  Real-Time Acoustic Oscilloscope
                </h3>
              </div>

              <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
                <span>
                  Latency:{" "}
                  <strong className="text-cyan-300">
                    {inferenceLatency > 0 ? `${inferenceLatency}ms` : "< 50ms"}
                  </strong>
                </span>
                <span>
                  Mode:{" "}
                  <strong
                    className={
                      isSimulating
                        ? "text-purple-300 font-bold"
                        : isMonitoring
                          ? "text-emerald-400 font-bold"
                          : "text-slate-300"
                    }
                  >
                    {isSimulating
                      ? "DEMO MODE — NOT REAL MODEL INFERENCE"
                      : isMonitoring
                        ? "REAL MODEL INFERENCE (LIVE WEBSOCKET)"
                        : "STANDBY"}
                  </strong>
                </span>
              </div>
            </div>

            <AudioWaveform
              waveformSamples={waveformSamples}
              isActive={isMonitoring}
              riskLevel={riskLevel}
              height={110}
            />

            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
              <span>Sampling: 16 kHz Mono Float32</span>
              <span>Window: 2.0s Sliding Chunk with Hop</span>
              <span>Neural Backbone: AASIST Graph Attention</span>
            </div>
          </div>

          {/* Live Metric Gauges */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* AI Probability */}
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
              <span className="text-xs font-semibold text-slate-400">
                AI Voice Probability
              </span>
              <div className="my-3 flex items-baseline gap-2">
                <span
                  className={`text-4xl font-black font-mono-numbers ${aiProbability > 0.7 ? "text-rose-400" : aiProbability > 0.4 ? "text-amber-400" : "text-emerald-400"}`}
                >
                  {(aiProbability * 100).toFixed(1)}%
                </span>
                <span className="text-xs font-mono text-slate-400">
                  synthetic
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${aiProbability > 0.7 ? "bg-rose-500" : aiProbability > 0.4 ? "bg-amber-500" : "bg-emerald-500"}`}
                  style={{ width: `${aiProbability * 100}%` }}
                />
              </div>
            </div>

            {/* Composite Risk Score */}
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">
                  Threat Risk Score
                </span>
                <RiskBadge level={riskLevel} showScore={false} size="sm" />
              </div>
              <div className="my-3 flex items-baseline gap-2">
                <span
                  className={`text-4xl font-black font-mono-numbers ${riskScore > 80 ? "text-rose-400 animate-pulse" : riskScore > 60 ? "text-orange-400" : riskScore > 30 ? "text-amber-400" : "text-emerald-400"}`}
                >
                  {riskScore}
                </span>
                <span className="text-xs font-mono text-slate-400">/ 100</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${riskScore > 80 ? "bg-rose-500" : riskScore > 60 ? "bg-orange-500" : riskScore > 30 ? "bg-amber-500" : "bg-emerald-500"}`}
                  style={{ width: `${riskScore}%` }}
                />
              </div>
            </div>

            {/* Classification & Confidence */}
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
              <span className="text-xs font-semibold text-slate-400">
                Decision State
              </span>
              <div className="my-3">
                <RiskBadge classification={classification as any} />
              </div>
              <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between pt-1">
                <span>Genuine Confidence:</span>
                <span className="text-emerald-400 font-bold">
                  {(genuineProbability * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Scam Indicators Card */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Scam & Social Engineering Indicators
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
              <div
                className={`p-2.5 rounded-xl border flex items-center gap-2 ${detectedIndicators.includes("financial_request") ? "bg-rose-500/20 border-rose-500/40 text-rose-300" : "bg-slate-950/40 border-slate-800 text-slate-500"}`}
              >
                <span className="w-2 h-2 rounded-full bg-current" />
                <span>Financial Demand</span>
              </div>

              <div
                className={`p-2.5 rounded-xl border flex items-center gap-2 ${detectedIndicators.includes("urgency_pressure") ? "bg-orange-500/20 border-orange-500/40 text-orange-300" : "bg-slate-950/40 border-slate-800 text-slate-500"}`}
              >
                <span className="w-2 h-2 rounded-full bg-current" />
                <span>Urgency Pressure</span>
              </div>

              <div
                className={`p-2.5 rounded-xl border flex items-center gap-2 ${detectedIndicators.includes("emergency_distress") ? "bg-amber-500/20 border-amber-500/40 text-amber-300" : "bg-slate-950/40 border-slate-800 text-slate-500"}`}
              >
                <span className="w-2 h-2 rounded-full bg-current" />
                <span>Emergency Distress</span>
              </div>

              <div
                className={`p-2.5 rounded-xl border flex items-center gap-2 ${detectedIndicators.includes("credential_theft") ? "bg-rose-500/20 border-rose-500/40 text-rose-300" : "bg-slate-950/40 border-slate-800 text-slate-500"}`}
              >
                <span className="w-2 h-2 rounded-full bg-current" />
                <span>OTP / PIN Harvesting</span>
              </div>

              <div
                className={`p-2.5 rounded-xl border flex items-center gap-2 ${detectedIndicators.includes("secrecy_coercion") ? "bg-purple-500/20 border-purple-500/40 text-purple-300" : "bg-slate-950/40 border-slate-800 text-slate-500"}`}
              >
                <span className="w-2 h-2 rounded-full bg-current" />
                <span>Secrecy Coercion</span>
              </div>

              <div
                className={`p-2.5 rounded-xl border flex items-center gap-2 ${detectedIndicators.includes("impersonation_authority") ? "bg-cyan-500/20 border-cyan-500/40 text-cyan-300" : "bg-slate-950/40 border-slate-800 text-slate-500"}`}
              >
                <span className="w-2 h-2 rounded-full bg-current" />
                <span>Impersonation</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Live Event Timeline (Span 1) */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between h-[620px]">
          <div>
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold font-display text-white flex items-center gap-2">
                <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
                Live Incident Feed
              </h3>
              <button
                onClick={() => setTimeline([])}
                className="text-[10px] text-slate-400 hover:text-slate-200 flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" />
                Clear
              </button>
            </div>

            <div className="overflow-y-auto max-h-[490px] space-y-2.5 pr-1">
              {timeline.map((evt, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-xl border text-xs leading-relaxed transition-all ${
                    evt.type === "CRITICAL"
                      ? "bg-rose-500/15 border-rose-500/35 text-rose-200"
                      : evt.type === "WARNING"
                        ? "bg-amber-500/15 border-amber-500/30 text-amber-200"
                        : evt.type === "SAFE"
                          ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                          : "bg-slate-950/50 border-slate-800/80 text-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1">
                    <span>{evt.time}</span>
                    {evt.score !== undefined && (
                      <span className="font-bold text-rose-400 font-mono">
                        Risk: {evt.score}
                      </span>
                    )}
                  </div>
                  <p>{evt.message}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              Listening to Stream
            </span>
            <span className="font-mono">{timeline.length} Events</span>
          </div>
        </div>
      </div>

      {/* Critical Emergency Alert Popup Modal */}
      <EmergencyAlertModal
        isOpen={showAlertModal}
        onClose={() => setShowAlertModal(false)}
        aiProbability={aiProbability}
        riskScore={riskScore}
        reasons={alertReasons}
        callerLabel="Simulated Grandson / Unknown Caller"
        onTriggerVerification={() => {
          setShowAlertModal(false);
          addEvent(
            "Secret Question challenge dispatched to caller.",
            "WARNING",
          );
        }}
        onMarkSafe={() => {
          setShowAlertModal(false);
          setRiskScore(10);
          setRiskLevel("LOW");
          addEvent("Call manually marked as safe by analyst.", "SAFE");
        }}
        onBlockCall={() => {
          setShowAlertModal(false);
          stopMonitoring();
          addEvent(
            "Call intercepted and terminated due to confirmed voice spoofing threat.",
            "CRITICAL",
          );
        }}
      />
    </div>
  );
};
