export type Gender = 'male' | 'female';

export interface Speaker {
  id: string;
  name: string;
  gender: Gender;
  displayLabel: string;
}

export interface TranscriptUtterance {
  speaker: string;
  text: string;
  start: number;
  end: number;
  words: Array<{ text: string; start: number; end: number; speaker: string }>;
}

export interface TranscriptResult {
  text: string;
  utterances: TranscriptUtterance[];
  speakerIds: string[];
}

export interface ConversationStat {
  speakerId: string;
  wordCount: number;
  charCount: number;
  durationMs: number;
  percentage: number;
  utteranceCount: number;
}

export interface HabitDimension {
  label: string;
  score: number;
  description: string;
}

export interface ConversationHabit {
  speakerId: string;
  keywords: string[];
  style: string;
  patterns: string[];
  dimensions: HabitDimension[];
}

export interface MbtiDimension {
  type: string;
  score: number;
  reason: string;
}

export interface MbtiAnalysis {
  speakerId: string;
  mbti: string;
  EI: MbtiDimension;
  SN: MbtiDimension;
  TF: MbtiDimension;
  JP: MbtiDimension;
  description: string;
}

export interface AnalysisResult {
  summary: string;
  stats: ConversationStat[];
  habits: ConversationHabit[];
  mbti: MbtiAnalysis[];
}
