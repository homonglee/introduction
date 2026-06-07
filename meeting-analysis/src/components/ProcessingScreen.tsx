'use client';

interface ProcessingScreenProps {
  status: string;
  step: number;
  totalSteps: number;
}

const STEPS = [
  { label: '음성 분석 & 화자 분리', icon: '🎙️' },
  { label: 'AI 회의 분석', icon: '🧠' },
];

export default function ProcessingScreen({ status, step, totalSteps }: ProcessingScreenProps) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      {/* Animated Logo */}
      <div className="relative flex items-center justify-center w-24 h-24 mb-10">
        <div className="absolute inset-0 rounded-full border-2 border-violet-500/20 animate-spin" style={{ animationDuration: '3s' }} />
        <div className="absolute inset-2 rounded-full border-2 border-violet-400/40 animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }} />
        <div className="w-12 h-12 rounded-full bg-violet-600/30 border border-violet-500/50 flex items-center justify-center">
          <span className="text-2xl">{STEPS[step - 1]?.icon || '⚙️'}</span>
        </div>
      </div>

      <h2 className="text-2xl font-bold text-white mb-3">처리 중...</h2>

      <div className="text-center mb-10 max-w-sm">
        {status.split('\n').map((line, i) => (
          <p key={i} className="text-slate-400 text-sm leading-relaxed">
            {line}
          </p>
        ))}
      </div>

      {/* Steps */}
      <div className="flex flex-col gap-3 w-full max-w-xs">
        {STEPS.map((s, idx) => {
          const stepNum = idx + 1;
          const isDone = stepNum < step;
          const isActive = stepNum === step;

          return (
            <div
              key={s.label}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all ${
                isActive
                  ? 'border-violet-500/50 bg-violet-500/10'
                  : isDone
                  ? 'border-green-500/30 bg-green-500/5'
                  : 'border-slate-700 bg-slate-800/50 opacity-40'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                  isDone ? 'bg-green-500 text-white' : isActive ? 'bg-violet-600 text-white' : 'bg-slate-700 text-slate-400'
                }`}
              >
                {isDone ? '✓' : stepNum}
              </div>
              <span
                className={`text-sm font-medium ${
                  isActive ? 'text-violet-300' : isDone ? 'text-green-400' : 'text-slate-500'
                }`}
              >
                {s.label}
              </span>
              {isActive && (
                <div className="ml-auto flex gap-1">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
