'use client';

import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { RotateCcw, FileText, BarChart2, MessageCircle, Brain } from 'lucide-react';
import { AnalysisResult, Speaker, TranscriptResult } from '@/lib/types';

interface AnalysisResultsProps {
  analysis: AnalysisResult;
  speakers: Speaker[];
  transcript: TranscriptResult;
  onReset: () => void;
}

type TabId = 'summary' | 'stats' | 'habits' | 'mbti';

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'summary', label: '회의록', icon: <FileText size={16} /> },
  { id: 'stats', label: '대화량', icon: <BarChart2 size={16} /> },
  { id: 'habits', label: '대화습관', icon: <MessageCircle size={16} /> },
  { id: 'mbti', label: 'MBTI', icon: <Brain size={16} /> },
];

const BAR_COLORS = ['#7c3aed', '#2563eb', '#059669', '#d97706', '#dc2626'];

const MBTI_COLORS: Record<string, string> = {
  INTJ: '#7c3aed', INTP: '#6d28d9', ENTJ: '#4f46e5', ENTP: '#4338ca',
  INFJ: '#0891b2', INFP: '#0284c7', ENFJ: '#059669', ENFP: '#10b981',
  ISTJ: '#92400e', ISFJ: '#b45309', ESTJ: '#d97706', ESFJ: '#f59e0b',
  ISTP: '#dc2626', ISFP: '#ef4444', ESTP: '#7f1d1d', ESFP: '#b91c1c',
};

function getSpeakerName(speakers: Speaker[], id: string): string {
  const s = speakers.find((sp) => sp.id === id);
  if (!s) return id;
  return s.name ? `${s.displayLabel} (${s.name})` : s.displayLabel;
}

function DimensionBar({ label, left, right, type, score }: {
  label: string; left: string; right: string; type: string; score: number;
}) {
  const isLeft = type === left[0];
  const pct = isLeft ? score : 100 - score;

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between text-xs text-slate-400 font-medium">
        <span className={isLeft ? 'text-violet-300 font-bold' : ''}>{left}</span>
        <span className="text-slate-500">{label}</span>
        <span className={!isLeft ? 'text-violet-300 font-bold' : ''}>{right}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
        <div
          className={`h-full rounded-full bg-violet-500 transition-all duration-700 ${isLeft ? '' : 'ml-auto'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-slate-500 text-center">{type} {score}%</p>
    </div>
  );
}

export default function AnalysisResults({ analysis, speakers, transcript, onReset }: AnalysisResultsProps) {
  const [activeTab, setActiveTab] = useState<TabId>('summary');

  const chartData = analysis.stats.map((stat, i) => ({
    name: getSpeakerName(speakers, stat.speakerId),
    단어수: stat.wordCount,
    비율: stat.percentage,
    color: BAR_COLORS[i % BAR_COLORS.length],
  }));

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur border-b border-slate-800">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white">분석 완료</h1>
            <p className="text-xs text-slate-500">{speakers.length}명 · {transcript.utterances.length}개 발화</p>
          </div>
          <button
            onClick={onReset}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-700 hover:border-slate-500 text-slate-400 hover:text-white transition-all text-sm"
          >
            <RotateCcw size={14} />
            새 회의
          </button>
        </div>

        {/* Tabs */}
        <div className="max-w-3xl mx-auto px-6 flex gap-1 pb-0">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium transition-all border-b-2 ${
                activeTab === tab.id
                  ? 'border-violet-500 text-violet-300'
                  : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 max-w-3xl mx-auto w-full px-6 py-8">
        {/* Summary Tab */}
        {activeTab === 'summary' && (
          <div className="flex flex-col gap-6">
            <div className="rounded-2xl border border-slate-700 bg-slate-800/50 p-6">
              <h2 className="text-sm font-semibold text-slate-400 mb-4 flex items-center gap-2">
                <FileText size={16} className="text-violet-400" />
                회의 내용 요약
              </h2>
              <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">{analysis.summary}</p>
            </div>

            {/* Transcript */}
            <div className="rounded-2xl border border-slate-700 bg-slate-800/50 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-700">
                <h2 className="text-sm font-semibold text-slate-400">전체 대화 내용</h2>
              </div>
              <div className="p-4 max-h-96 overflow-y-auto flex flex-col gap-3">
                {transcript.utterances.map((u, i) => {
                  const speaker = speakers.find((s) => s.id === u.speaker);
                  const name = speaker?.name ? `${speaker.displayLabel} (${speaker.name})` : speaker?.displayLabel || u.speaker;
                  const isMale = speaker?.gender === 'male';

                  return (
                    <div key={i} className="flex gap-3">
                      <div
                        className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold border ${
                          isMale
                            ? 'bg-blue-500/20 border-blue-500/40 text-blue-300'
                            : 'bg-pink-500/20 border-pink-500/40 text-pink-300'
                        }`}
                      >
                        {u.speaker}
                      </div>
                      <div>
                        <p className={`text-xs font-medium mb-1 ${isMale ? 'text-blue-400' : 'text-pink-400'}`}>{name}</p>
                        <p className="text-sm text-slate-300 leading-relaxed">{u.text}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Stats Tab */}
        {activeTab === 'stats' && (
          <div className="flex flex-col gap-6">
            {/* Bar Chart */}
            <div className="rounded-2xl border border-slate-700 bg-slate-800/50 p-6">
              <h2 className="text-sm font-semibold text-slate-400 mb-6">화자별 단어 수</h2>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }}
                    cursor={{ fill: 'rgba(124,58,237,0.1)' }}
                  />
                  <Bar dataKey="단어수" radius={[6, 6, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {analysis.stats.map((stat, i) => {
                const name = getSpeakerName(speakers, stat.speakerId);
                const durationSec = Math.round(stat.durationMs / 1000);
                const mins = Math.floor(durationSec / 60);
                const secs = durationSec % 60;

                return (
                  <div
                    key={stat.speakerId}
                    className="rounded-2xl border border-slate-700 bg-slate-800/50 p-5"
                    style={{ borderLeftColor: BAR_COLORS[i % BAR_COLORS.length], borderLeftWidth: 3 }}
                  >
                    <p className="text-sm font-semibold text-white mb-3">{name}</p>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-slate-500 mb-1">단어 수</p>
                        <p className="text-xl font-bold text-white">{stat.wordCount.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 mb-1">대화 비율</p>
                        <p className="text-xl font-bold text-white">{stat.percentage}%</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 mb-1">발언 횟수</p>
                        <p className="text-xl font-bold text-white">{stat.utteranceCount}회</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500 mb-1">총 발언 시간</p>
                        <p className="text-xl font-bold text-white">{mins}분 {secs}초</p>
                      </div>
                    </div>
                    {/* Progress bar */}
                    <div className="mt-3 h-1.5 rounded-full bg-slate-700 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${stat.percentage}%`, background: BAR_COLORS[i % BAR_COLORS.length] }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Habits Tab */}
        {activeTab === 'habits' && (
          <div className="flex flex-col gap-6">
            {analysis.habits.map((habit, i) => {
              const name = getSpeakerName(speakers, habit.speakerId);
              const color = BAR_COLORS[i % BAR_COLORS.length];

              return (
                <div key={habit.speakerId} className="rounded-2xl border border-slate-700 bg-slate-800/50 overflow-hidden">
                  <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-700"
                    style={{ borderLeftColor: color, borderLeftWidth: 3 }}>
                    <div
                      className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold"
                      style={{ background: `${color}20`, border: `1px solid ${color}60`, color }}
                    >
                      {habit.speakerId}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{name}</p>
                      <p className="text-xs text-slate-500">{habit.style}</p>
                    </div>
                  </div>

                  <div className="px-5 py-4 flex flex-col gap-4">
                    {/* Keywords */}
                    <div>
                      <p className="text-xs text-slate-500 font-medium mb-2">자주 사용하는 표현</p>
                      <div className="flex flex-wrap gap-2">
                        {habit.keywords.map((kw, ki) => (
                          <span
                            key={ki}
                            className="px-2.5 py-1 rounded-lg text-xs font-medium"
                            style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}
                          >
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Patterns */}
                    <div>
                      <p className="text-xs text-slate-500 font-medium mb-2">대화 패턴</p>
                      <div className="flex flex-col gap-2">
                        {habit.patterns.map((p, pi) => (
                          <div key={pi} className="flex items-start gap-2 text-sm text-slate-300">
                            <span className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: color }} />
                            {p}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* MBTI Tab */}
        {activeTab === 'mbti' && (
          <div className="flex flex-col gap-6">
            {analysis.mbti.map((m, i) => {
              const name = getSpeakerName(speakers, m.speakerId);
              const mbtiColor = MBTI_COLORS[m.mbti] || BAR_COLORS[i % BAR_COLORS.length];

              return (
                <div key={m.speakerId} className="rounded-2xl border border-slate-700 bg-slate-800/50 overflow-hidden">
                  {/* MBTI Header */}
                  <div className="px-5 py-5 flex items-center gap-4 border-b border-slate-700">
                    <div
                      className="w-16 h-16 rounded-2xl flex items-center justify-center text-xl font-black"
                      style={{ background: `${mbtiColor}20`, border: `2px solid ${mbtiColor}50`, color: mbtiColor }}
                    >
                      {m.mbti}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-slate-400 mb-0.5">{name}</p>
                      <p className="text-2xl font-bold text-white">{m.mbti}</p>
                    </div>
                  </div>

                  <div className="px-5 py-4 flex flex-col gap-4">
                    {/* Description */}
                    <p className="text-sm text-slate-300 leading-relaxed">{m.description}</p>

                    {/* Dimensions */}
                    <div className="flex flex-col gap-4 pt-2">
                      <DimensionBar label="에너지" left="E (외향)" right="I (내향)" type={m.EI.type} score={m.EI.score} />
                      <p className="text-xs text-slate-500 -mt-2 px-1">{m.EI.reason}</p>

                      <DimensionBar label="인식" left="S (감각)" right="N (직관)" type={m.SN.type} score={m.SN.score} />
                      <p className="text-xs text-slate-500 -mt-2 px-1">{m.SN.reason}</p>

                      <DimensionBar label="판단" left="T (사고)" right="F (감정)" type={m.TF.type} score={m.TF.score} />
                      <p className="text-xs text-slate-500 -mt-2 px-1">{m.TF.reason}</p>

                      <DimensionBar label="생활양식" left="J (판단)" right="P (인식)" type={m.JP.type} score={m.JP.score} />
                      <p className="text-xs text-slate-500 -mt-2 px-1">{m.JP.reason}</p>
                    </div>
                  </div>
                </div>
              );
            })}

            <p className="text-xs text-slate-600 text-center px-4">
              * MBTI 분석은 회의 대화 내용을 기반으로 한 AI 추정값으로, 공인된 MBTI 검사 결과와 다를 수 있습니다.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
