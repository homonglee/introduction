import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "회의 분석 AI",
  description: "AI 기반 회의 녹음 분석 - 요약, 대화량, 습관, MBTI 분류",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="bg-slate-900 text-white antialiased">
        {children}
      </body>
    </html>
  );
}
