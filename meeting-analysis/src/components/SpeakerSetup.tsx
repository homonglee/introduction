'use client';

import { useState } from 'react';
import { User, Users, ChevronRight, ArrowLeft, AlertCircle } from 'lucide-react';
import { TranscriptResult, Speaker, Gender } from '@/lib/types';

interface SpeakerSetupProps {
  transcript: TranscriptResult;
  speakers: Speaker[];
  onAnalyze: (speakers: Speaker[]) => void;
  onBack: () => void;
  error?: string | null;
}

function getSampleQuotes(speakerId: string, transcript: TranscriptResult, maxCount = 2): string[] {
  return transcript.utterances
    .filter((u) => u.speaker === speakerId)
    .slice(0, maxCount)
    .map((u) => u.text.slice(0, 60) + (u.text.length > 60 ? '...' : ''));
}

export default function SpeakerSetup({ transcript, speakers: initialSpeakers, onAnalyze, onBack, error }: SpeakerSetupProps) {
  const [speakers, setSpeakers] = useState<Speaker[]>(initialSpeakers);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getDisplayLabel = (speakerList: Speaker[], id: string): string => {
    const speaker = speakerList.find((s) => s.id === id)!;
    const sameGender = speakerList.filter((s) => s.gender === speaker.gender);
    const idx = sameGender.findIndex((s) => s.id === id);
    const genderLabel = speaker.gender === 'male' ? '남성' : '여성';
    return `${genderLabel} ${idx + 1}`;
  };

  const updateSpeaker = (id: string, updates: Partial<Speaker>) => {
    setSpeakers((prev) => {
      const updated = prev.map((s) => (s.id === id ? { ...s, ...updates } : s));
      return updated.map((s) => ({ ...s, displayLabel: getDisplayLabel(updated, s.id) }));
    });
  };

  const handleSubmit = () => {
    setIsSubmitting(true);
    onAnalyze(speakers);
  };

  const totalUtterances = transcript.utterances.length;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={onBack} className="p-2 rounded-lg hover:bg-slate-800 transition-colors">
              <ArrowLeft size={18} className="text-slate-400" />
            </button>
            <div>
              <h1 className="text-lg font-bold text-white">화자 설정</h1>
              <p className="text-xs text-slate-500">{speakers.length}명 감지됨 · {totalUtterances}개 발화</p>
            </div>
          </div>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-semibold text-white shadow-lg shadow-violet-900/40"
          >
            분석 시작
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div className="flex-1 max-w-2xl mx-auto w-full px-6 py-8">
        <p className="text-slate-400 text-sm mb-6">
          음성 분석으로 총 <strong className="text-white">{speakers.length}명</strong>의 화자가 감지되었습니다.
          각 화자의 성별을 선택하고 이름을 입력해주세요.
        </p>

        <div className="flex flex-col gap-4">
          {speakers.map((speaker) => {
            const quotes = getSampleQuotes(speaker.id, transcript);
            const utteranceCount = transcript.utterances.filter((u) => u.speaker === speaker.id).length;

            return (
              <div
                key={speaker.id}
                className="rounded-2xl border border-slate-700 bg-slate-800/50 overflow-hidden"
              >
                {/* Speaker Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700/50">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border ${
                        speaker.gender === 'male'
                          ? 'bg-blue-500/20 border-blue-500/40 text-blue-300'
                          : 'bg-pink-500/20 border-pink-500/40 text-pink-300'
                      }`}
                    >
                      {speaker.id}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">화자 {speaker.id}</p>
                      <p className="text-xs text-slate-500">{utteranceCount}회 발언</p>
                    </div>
                  </div>
                  <span
                    className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                      speaker.gender === 'male'
                        ? 'bg-blue-500/20 text-blue-300'
                        : 'bg-pink-500/20 text-pink-300'
                    }`}
                  >
                    {speaker.displayLabel}
                  </span>
                </div>

                {/* Settings */}
                <div className="px-5 py-4 flex flex-col gap-4">
                  {/* Gender */}
                  <div>
                    <label className="text-xs text-slate-500 font-medium mb-2 block">성별</label>
                    <div className="flex gap-2">
                      {([
                        { value: 'male', label: '남성', icon: '👨' },
                        { value: 'female', label: '여성', icon: '👩' },
                      ] as { value: Gender; label: string; icon: string }[]).map((opt) => (
                        <button
                          key={opt.value}
                          onClick={() => updateSpeaker(speaker.id, { gender: opt.value })}
                          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                            speaker.gender === opt.value
                              ? opt.value === 'male'
                                ? 'bg-blue-500/20 border-blue-500 text-blue-300'
                                : 'bg-pink-500/20 border-pink-500 text-pink-300'
                              : 'border-slate-700 text-slate-500 hover:border-slate-500'
                          }`}
                        >
                          <span>{opt.icon}</span>
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Name Input */}
                  <div>
                    <label className="text-xs text-slate-500 font-medium mb-2 block">이름 (선택)</label>
                    <input
                      type="text"
                      value={speaker.name}
                      onChange={(e) => updateSpeaker(speaker.id, { name: e.target.value })}
                      placeholder={`예: 김철수, 이영희`}
                      className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 focus:border-violet-500 focus:outline-none text-sm text-white placeholder:text-slate-600 transition-colors"
                    />
                  </div>

                  {/* Sample quotes */}
                  {quotes.length > 0 && (
                    <div>
                      <label className="text-xs text-slate-500 font-medium mb-2 block">발언 샘플</label>
                      <div className="flex flex-col gap-1.5">
                        {quotes.map((q, i) => (
                          <div key={i} className="px-3 py-2 rounded-lg bg-slate-900 border border-slate-700/50 text-xs text-slate-400 leading-relaxed">
                            "{q}"
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Summary preview */}
        <div className="mt-6 px-5 py-4 rounded-2xl bg-violet-500/5 border border-violet-500/20">
          <p className="text-xs text-violet-400 font-medium mb-3 flex items-center gap-2">
            <Users size={14} />
            분석에 사용될 화자 레이블
          </p>
          <div className="flex flex-wrap gap-2">
            {speakers.map((s) => (
              <div key={s.id} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700">
                <User size={12} className="text-slate-500" />
                <span className="text-xs text-slate-300 font-medium">
                  {s.displayLabel}
                  {s.name && ` (${s.name})`}
                </span>
              </div>
            ))}
          </div>
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-3 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-400">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  );
}
