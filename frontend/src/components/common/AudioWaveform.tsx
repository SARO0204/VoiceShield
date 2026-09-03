import React, { useRef, useEffect } from 'react';

interface AudioWaveformProps {
  waveformSamples?: number[];
  isActive?: boolean;
  riskLevel?: string;
  height?: number;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({
  waveformSamples = [],
  isActive = false,
  riskLevel = 'LOW',
  height = 80,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;

    const render = () => {
      const width = canvas.width;
      const h = canvas.height;
      const centerY = h / 2;

      ctx.clearRect(0, 0, width, h);

      // Background grid lines
      ctx.strokeStyle = 'rgba(51, 65, 85, 0.2)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, centerY);
      ctx.lineTo(width, centerY);
      ctx.stroke();

      // Dynamic color gradient based on risk
      const gradient = ctx.createLinearGradient(0, 0, width, 0);
      if (riskLevel === 'CRITICAL') {
        gradient.addColorStop(0, '#ef4444');
        gradient.addColorStop(0.5, '#f43f5e');
        gradient.addColorStop(1, '#dc2626');
      } else if (riskLevel === 'HIGH') {
        gradient.addColorStop(0, '#f97316');
        gradient.addColorStop(0.5, '#fb923c');
        gradient.addColorStop(1, '#ea580c');
      } else if (riskLevel === 'MEDIUM') {
        gradient.addColorStop(0, '#f59e0b');
        gradient.addColorStop(0.5, '#fbbf24');
        gradient.addColorStop(1, '#d97706');
      } else {
        gradient.addColorStop(0, '#06b6d4');
        gradient.addColorStop(0.5, '#3b82f6');
        gradient.addColorStop(1, '#10b981');
      }

      ctx.strokeStyle = gradient;
      ctx.lineWidth = 2.5;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      ctx.beginPath();

      if (waveformSamples.length > 0) {
        const sliceWidth = width / waveformSamples.length;
        let x = 0;

        for (let i = 0; i < waveformSamples.length; i++) {
          const v = waveformSamples[i];
          const y = centerY + v * (h / 2) * 0.85;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
          x += sliceWidth;
        }
      } else if (isActive) {
        // Idle live ambient wave
        const now = Date.now() / 300;
        const count = 48;
        const sliceWidth = width / count;

        for (let i = 0; i < count; i++) {
          const amp = Math.sin(now + i * 0.3) * Math.cos(now * 0.8 + i * 0.2) * (h * 0.25);
          const x = i * sliceWidth;
          const y = centerY + amp;

          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
      } else {
        // Flat inactive line
        ctx.moveTo(0, centerY);
        ctx.lineTo(width, centerY);
      }

      ctx.stroke();

      // Glowing shadow
      ctx.shadowBlur = isActive ? 12 : 0;
      ctx.shadowColor = riskLevel === 'CRITICAL' ? '#ef4444' : '#06b6d4';

      if (isActive && waveformSamples.length === 0) {
        animationId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      if (animationId) cancelAnimationFrame(animationId);
    };
  }, [waveformSamples, isActive, riskLevel]);

  return (
    <div className="relative w-full rounded-xl overflow-hidden bg-slate-950/80 border border-slate-800/80 p-2 shadow-inner">
      <div className="absolute top-2 left-3 flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest text-slate-400">
        <span className={`w-1.5 h-1.5 rounded-full ${isActive ? (riskLevel === 'CRITICAL' ? 'bg-rose-500 animate-ping' : 'bg-cyan-400 animate-pulse') : 'bg-slate-600'}`} />
        {isActive ? 'Live Oscilloscope / 16 kHz Mono' : 'Audio Inactive'}
      </div>
      <canvas
        ref={canvasRef}
        width={600}
        height={height}
        className="w-full block"
      />
    </div>
  );
};
