import { NextRequest, NextResponse } from 'next/server';
import { AssemblyAI } from 'assemblyai';
import { TranscriptResult } from '@/lib/types';

export const maxDuration = 300;

export async function POST(request: NextRequest) {
  try {
    const apiKey = process.env.ASSEMBLYAI_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'AssemblyAI API 키가 설정되지 않았습니다.' }, { status: 500 });
    }

    const formData = await request.formData();
    const audioFile = formData.get('audio') as File;

    if (!audioFile) {
      return NextResponse.json({ error: '오디오 파일이 없습니다.' }, { status: 400 });
    }

    const client = new AssemblyAI({ apiKey });

    const audioBuffer = Buffer.from(await audioFile.arrayBuffer());
    const uploadedUrl = await client.files.upload(audioBuffer);

    const transcript = await client.transcripts.transcribe({
      audio_url: uploadedUrl,
      speaker_labels: true,
      language_code: 'ko',
    });

    if (transcript.status === 'error') {
      throw new Error(transcript.error || '음성 분석에 실패했습니다.');
    }

    const utterances = (transcript.utterances || []).map((u) => ({
      speaker: u.speaker,
      text: u.text,
      start: u.start,
      end: u.end,
      words: (u.words || []).map((w) => ({
        text: w.text,
        start: w.start,
        end: w.end,
        speaker: w.speaker || u.speaker,
      })),
    }));

    const speakerSet = new Set<string>();
    utterances.forEach((u) => speakerSet.add(u.speaker));

    const result: TranscriptResult = {
      text: transcript.text || '',
      utterances,
      speakerIds: Array.from(speakerSet).sort(),
    };

    return NextResponse.json(result);
  } catch (error: unknown) {
    console.error('Transcription error:', error);
    const message = error instanceof Error ? error.message : '음성 분석 중 오류가 발생했습니다.';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
