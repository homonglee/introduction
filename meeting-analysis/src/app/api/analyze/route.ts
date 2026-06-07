import { NextRequest, NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { TranscriptResult, Speaker, AnalysisResult, ConversationStat } from '@/lib/types';

export const maxDuration = 120;

function computeStats(transcript: TranscriptResult, speakers: Speaker[]): ConversationStat[] {
  const statMap: Record<string, ConversationStat> = {};

  speakers.forEach((s) => {
    statMap[s.id] = {
      speakerId: s.id,
      wordCount: 0,
      charCount: 0,
      durationMs: 0,
      percentage: 0,
      utteranceCount: 0,
    };
  });

  transcript.utterances.forEach((u) => {
    if (!statMap[u.speaker]) return;
    const words = u.text.split(/\s+/).filter(Boolean);
    statMap[u.speaker].wordCount += words.length;
    statMap[u.speaker].charCount += u.text.replace(/\s/g, '').length;
    statMap[u.speaker].durationMs += u.end - u.start;
    statMap[u.speaker].utteranceCount += 1;
  });

  const totalWords = Object.values(statMap).reduce((sum, s) => sum + s.wordCount, 0);
  Object.values(statMap).forEach((s) => {
    s.percentage = totalWords > 0 ? Math.round((s.wordCount / totalWords) * 100) : 0;
  });

  return Object.values(statMap);
}

function buildTranscriptText(transcript: TranscriptResult, speakers: Speaker[]): string {
  const speakerMap: Record<string, string> = {};
  speakers.forEach((s) => {
    speakerMap[s.id] = s.name || s.displayLabel;
  });

  return transcript.utterances
    .map((u) => `[${speakerMap[u.speaker] || u.speaker}]: ${u.text}`)
    .join('\n');
}

export async function POST(request: NextRequest) {
  try {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Anthropic API 키가 설정되지 않았습니다.' }, { status: 500 });
    }

    const body = await request.json();
    const { transcript, speakers } = body as { transcript: TranscriptResult; speakers: Speaker[] };

    if (!transcript || !speakers?.length) {
      return NextResponse.json({ error: '잘못된 요청입니다.' }, { status: 400 });
    }

    const stats = computeStats(transcript, speakers);
    const transcriptText = buildTranscriptText(transcript, speakers);

    const speakersDesc = speakers
      .map((s) => `- ${s.displayLabel}: ${s.name || '이름 없음'} (${s.gender === 'male' ? '남성' : '여성'})`)
      .join('\n');

    const anthropic = new Anthropic({ apiKey });

    const prompt = `당신은 회의 분석 전문가입니다. 아래 회의 대화를 분석해주세요.

## 화자 정보
${speakersDesc}

## 회의 내용
${transcriptText}

## 분석 요청

다음을 포함하는 JSON 형식으로 응답해주세요:

1. **summary**: 회의 내용 전체 요약 (한국어, 400~600자, 주요 논의 사항과 결론 포함)

2. **habits**: 각 화자의 대화 습관 분석 배열
   - speakerId: 화자 ID (A, B, C...)
   - keywords: 자주 사용하는 단어나 표현 5개 이내
   - style: 말하기 스타일 한 줄 요약
   - patterns: 대화 패턴 특징 3~5개 (한국어 문장으로)

3. **mbti**: 각 화자의 MBTI 추정 분석 배열
   - speakerId: 화자 ID
   - mbti: 추정 MBTI 4자리 (예: INTJ)
   - EI: { type: "E" 또는 "I", score: 0~100, reason: 근거 }
   - SN: { type: "S" 또는 "N", score: 0~100, reason: 근거 }
   - TF: { type: "T" 또는 "F", score: 0~100, reason: 근거 }
   - JP: { type: "J" 또는 "P", score: 0~100, reason: 근거 }
   - description: 종합 성격 설명 (2~3문장)

반드시 아래 JSON 형식만 응답하세요 (다른 텍스트 없이):
{
  "summary": "...",
  "habits": [
    {
      "speakerId": "A",
      "keywords": ["키워드1", "키워드2"],
      "style": "스타일 설명",
      "patterns": ["패턴1", "패턴2", "패턴3"]
    }
  ],
  "mbti": [
    {
      "speakerId": "A",
      "mbti": "INTJ",
      "EI": { "type": "I", "score": 70, "reason": "..." },
      "SN": { "type": "N", "score": 65, "reason": "..." },
      "TF": { "type": "T", "score": 75, "reason": "..." },
      "JP": { "type": "J", "score": 60, "reason": "..." },
      "description": "..."
    }
  ]
}`;

    const message = await anthropic.messages.create({
      model: 'claude-opus-4-8',
      max_tokens: 4096,
      messages: [{ role: 'user', content: prompt }],
    });

    const responseText = message.content[0].type === 'text' ? message.content[0].text : '';

    let aiResult: { summary: string; habits: AnalysisResult['habits']; mbti: AnalysisResult['mbti'] };
    try {
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (!jsonMatch) throw new Error('JSON 파싱 실패');
      aiResult = JSON.parse(jsonMatch[0]);
    } catch {
      throw new Error('AI 응답 파싱에 실패했습니다.');
    }

    const result: AnalysisResult = {
      summary: aiResult.summary,
      stats,
      habits: aiResult.habits,
      mbti: aiResult.mbti,
    };

    return NextResponse.json(result);
  } catch (error: unknown) {
    console.error('Analysis error:', error);
    const message = error instanceof Error ? error.message : '분석 중 오류가 발생했습니다.';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
