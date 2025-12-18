import React, { useMemo } from 'react';
import type { InterviewReport } from '../types';
import InterviewReportView from './InterviewReportView';
import Button from './ui/Button';

interface ResultsScreenProps {
  report: InterviewReport;
  onRetry: () => void;
  studentMeta?: { name?: string; schoolName?: string; grade?: number; major?: string };
}

const ResultsScreen: React.FC<ResultsScreenProps> = ({ report, onRetry, studentMeta }) => {
  const scores = useMemo(() => {
    if (report.scores) return report.scores;
    const defaults = { contentRelevance: 0, structure: 0, fluency: 0, confidence: 0 };
    const feedback = report.detailedFeedback || [];
    if (!feedback.length) return defaults;
    const avg = (key: string) => feedback.reduce((sum, item: any) => sum + (item?.[key] || 0), 0) / feedback.length || 0;
    return {
      contentRelevance: avg('content_relevance_score'),
      structure: avg('structure_score'),
      fluency: avg('fluency_score'),
      confidence: avg('confidence_score'),
    };
  }, [report.detailedFeedback, report.scores]);

  const totalScore = useMemo(() => {
    if (typeof report.overallScore === 'number') return report.overallScore;
    if (typeof report.totalScore === 'number') return report.totalScore;
    const vals = Object.values(scores);
    return vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
  }, [report.overallScore, report.totalScore, scores]);

  const handleDownloadPdf = () => {
    window.print();
  };

  return (
    <div className="animate-fadeIn space-y-8">
      <section className="relative overflow-hidden rounded-[28px] bg-gradient-to-r from-white via-primary-lightest to-white border border-white/70 shadow-soft px-6 py-10 text-center">
        <div className="hero-blob hero-blob--primary right-0 top-0"></div>
        <div className="hero-blob hero-blob--secondary left-0 bottom-0"></div>
        <div className="relative z-10 space-y-3">
          <p className="text-xs font-semibold text-primary-text uppercase tracking-[0.3em]">AI FEEDBACK</p>
          <h1 className="text-3xl font-bold text-slate-900">AI 모의 면접 결과</h1>
          <p className="text-slate-600 text-sm max-w-2xl mx-auto">
            면접 응답을 분석하고, AI가 제공하는 피드백을 확인하세요.
          </p>
        </div>
      </section>

      {studentMeta && (
        <section className="bg-white/95 border border-white/70 shadow-soft rounded-[20px] p-5 flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1 text-sm text-slate-700">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-[0.2em]">학생 정보</p>
            <p className="text-lg font-bold text-slate-900">{studentMeta.name || '이름 없음'}</p>
            <p className="text-sm text-slate-600">{studentMeta.schoolName || '학교 없음'} {studentMeta.grade ? `${studentMeta.grade}학년` : ''}</p>
            <p className="text-sm text-slate-600">전공/희망: {studentMeta.major || '미입력'}</p>
          </div>
          <Button onClick={handleDownloadPdf} variant="secondary" className="px-6 py-3">PDF 저장</Button>
        </section>
      )}

      <InterviewReportView report={{ ...report, scores, totalScore }} />

      <div className="text-center pt-8 pb-12">
        <Button onClick={onRetry} className="px-10 py-4 text-lg">
          다시 연습하기
        </Button>
      </div>
    </div>
  );
};

export default ResultsScreen;
