'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, Square, Upload, AlertCircle } from 'lucide-react';

interface RecordingScreenProps {
  onRecordingComplete: (blob: Blob) => void;
  error?: string | null;
}

export default function RecordingScreen({ onRecordingComplete, error }: RecordingScreenProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [levels, setLevels] = useState<number[]>(new Array(40).fill(2));

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const stopVisualization = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (timerRef.current) clearInterval(timerRef.current);
  }, []);

  useEffect(() => () => stopVisualization(), [stopVisualization]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      streamRef.current = stream;

      const ctx = new AudioContext();
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 128;
      source.connect(analyser);
      analyserRef.current = analyser;

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        stream.getTracks().forEach((t) => t.stop());
        onRecordingComplete(blob);
      };

      recorder.start(200);
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => setRecordingTime((t) => t + 1), 1000);

      const data = new Uint8Array(analyser.frequencyBinCount);
      const draw = () => {
        animFrameRef.current = requestAnimationFrame(draw);
        analyser.getByteFrequencyData(data);
        const bars = Array.from(data.slice(0, 40)).map((v) => Math.max(4, (v / 255) * 60));
        setLevels(bars);
      };
      draw();
    } catch {
      alert('마이크 접근 권한이 필요합니다. 브라우저 설정에서 마이크 권한을 허용해주세요.');
    }
  };

  const stopRecording = () => {
    stopVisualization();
    setIsRecording(false);
    setLevels(new Array(40).fill(2));
    mediaRecorderRef.current?.stop();
  };

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onRecordingComplete(file);
  };

  const formatTime = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-violet-600/20 border border-violet-500/30 mb-4">
          <Mic size={28} className="text-violet-400" />
        </div>
        <h1 className="text-4xl font-bold text-white tracking-tight mb-2">회의 분석 AI</h1>
        <p className="text-slate-400 text-lg">회의를 녹음하면 AI가 자동으로 분석해드립니다</p>
      </div>

      {/* Feature badges */}
      <div className="flex flex-wrap gap-2 justify-center mb-10">
        {['회의록 요약', '대화량 분석', '대화 습관', 'MBTI 분류'].map((label) => (
          <span
            key={label}
            className="px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700"
          >
            {label}
          </span>
        ))}
      </div>

      {/* Waveform */}
      <div className="flex items-end gap-1 h-16 mb-6">
        {levels.map((h, i) => (
          <div
            key={i}
            className={`w-1.5 rounded-full transition-all duration-75 ${
              isRecording ? 'bg-red-400' : 'bg-slate-700'
            }`}
            style={{ height: `${h}px` }}
          />
        ))}
      </div>

      {/* Timer */}
      <div className="h-10 mb-6 flex items-center">
        {isRecording && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span className="text-2xl font-mono font-bold text-red-400">{formatTime(recordingTime)}</span>
            <span className="text-slate-500 text-sm ml-2">녹음 중...</span>
          </div>
        )}
      </div>

      {/* Record Button */}
      <div className="relative flex items-center justify-center mb-8">
        {isRecording && (
          <>
            <div className="pulse-ring absolute w-28 h-28 rounded-full border-2 border-red-500/50" />
            <div className="pulse-ring absolute w-28 h-28 rounded-full border-2 border-red-500/30" style={{ animationDelay: '0.5s' }} />
          </>
        )}
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 shadow-2xl ${
            isRecording
              ? 'bg-slate-700 hover:bg-slate-600 shadow-slate-900'
              : 'bg-red-600 hover:bg-red-500 shadow-red-900/50 hover:shadow-red-800/50 hover:scale-105'
          }`}
        >
          {isRecording ? (
            <Square size={28} className="text-red-400" fill="currentColor" />
          ) : (
            <Mic size={32} className="text-white" />
          )}
        </button>
      </div>

      <p className="text-slate-500 text-sm mb-10">
        {isRecording ? '버튼을 눌러 녹음을 중지하세요' : '버튼을 눌러 녹음을 시작하세요'}
      </p>

      {/* Upload option */}
      {!isRecording && (
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-4">
            <div className="w-24 h-px bg-slate-700" />
            <span className="text-slate-600 text-xs">또는</span>
            <div className="w-24 h-px bg-slate-700" />
          </div>
          <label className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 hover:border-slate-500 cursor-pointer transition-colors text-sm text-slate-400 hover:text-slate-300">
            <Upload size={16} />
            오디오 파일 업로드 (mp3, wav, m4a)
            <input type="file" accept="audio/*" className="hidden" onChange={handleUpload} />
          </label>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-6 flex items-start gap-3 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 max-w-md text-sm text-red-400">
          <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
