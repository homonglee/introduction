'use client';

import { useState } from 'react';
import RecordingScreen from '@/components/RecordingScreen';
import ProcessingScreen from '@/components/ProcessingScreen';
import SpeakerSetup from '@/components/SpeakerSetup';
import AnalysisResults from '@/components/AnalysisResults';
import { TranscriptResult, Speaker, AnalysisResult } from '@/lib/types';

type AppState = 'idle' | 'processing' | 'speaker-setup' | 'analyzing' | 'results';

export default function Home() {
  const [appState, setAppState] = useState<AppState>('idle');
  const [transcriptResult, setTranscriptResult] = useState<TranscriptResult | null>(null);
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [processingStatus, setProcessingStatus] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleRecordingComplete = async (blob: Blob) => {
    setError(null);
    setAppState('processing');
    setProcessingStatus('음성을 업로드하는 중...');

    try {
      const formData = new FormData();
      formData.append('audio', blob, 'recording.webm');

      setProcessingStatus('음성을 분석하고 화자를 분리하는 중...\n(최대 2~3분 소요될 수 있습니다)');

      const response = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || '음성 분석 실패');
      }

      const result: TranscriptResult = await response.json();
      setTranscriptResult(result);

      const maleCount: Record<string, number> = {};
      const femaleCount: Record<string, number> = {};

      const initialSpeakers: Speaker[] = result.speakerIds.map((id) => ({
        id,
        name: '',
        gender: 'male' as const,
        displayLabel: `화자 ${id}`,
      }));

      setSpeakers(initialSpeakers);
      setAppState('speaker-setup');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.';
      setError(msg);
      setAppState('idle');
    }
  };

  const handleAnalyze = async (updatedSpeakers: Speaker[]) => {
    setError(null);
    setSpeakers(updatedSpeakers);
    setAppState('analyzing');

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: transcriptResult,
          speakers: updatedSpeakers,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || '분석 실패');
      }

      const result: AnalysisResult = await response.json();
      setAnalysisResult(result);
      setAppState('results');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '분석 중 오류가 발생했습니다.';
      setError(msg);
      setAppState('speaker-setup');
    }
  };

  const handleReset = () => {
    setAppState('idle');
    setTranscriptResult(null);
    setSpeakers([]);
    setAnalysisResult(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-slate-900">
      {appState === 'idle' && (
        <RecordingScreen onRecordingComplete={handleRecordingComplete} error={error} />
      )}

      {appState === 'processing' && (
        <ProcessingScreen status={processingStatus} step={1} totalSteps={2} />
      )}

      {appState === 'speaker-setup' && transcriptResult && (
        <SpeakerSetup
          transcript={transcriptResult}
          speakers={speakers}
          onAnalyze={handleAnalyze}
          onBack={handleReset}
          error={error}
        />
      )}

      {appState === 'analyzing' && (
        <ProcessingScreen status="AI가 회의 내용을 분석하는 중..." step={2} totalSteps={2} />
      )}

      {appState === 'results' && analysisResult && (
        <AnalysisResults
          analysis={analysisResult}
          speakers={speakers}
          transcript={transcriptResult!}
          onReset={handleReset}
        />
      )}
    </main>
  );
}
