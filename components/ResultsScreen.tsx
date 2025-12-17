import React, { useMemo, useState } from 'react';
import type { InterviewReport } from '../types';
import InterviewReportView from './InterviewReportView';
import Button from './ui/Button';

const scoreLabels: Record<'contentRelevance' | 'structure' | 'fluency' | 'confidence', string> = {
  contentRelevance: '내용 연관성',
  structure: '구조/STAR',
  fluency: '유창성',
  confidence: '자신감',
};

interface ResultsScreenProps {
  report: InterviewReport;
  onRetry: () => void;
  studentMeta?: { name?: string; schoolName?: string; grade?: number; major?: string };
}

const ResultsScreen: React.FC<ResultsScreenProps> = ({ report, onRetry, studentMeta }) => {
  const [rangeFilter, setRangeFilter] = useState('최근 2회');
  const [categoryFilter, setCategoryFilter] = useState<'all' | 'contentRelevance' | 'structure' | 'fluency' | 'confidence'>('all');

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

  const weakestArea = useMemo(() => {
    const entries = Object.entries(scores) as [keyof typeof scores, number][];
    if (categoryFilter !== 'all') {
      return { key: categoryFilter, value: scores[categoryFilter] };
    }
    const [key, value] = entries.sort((a, b) => a[1] - b[1])[0] || ['contentRelevance', 0];
    return { key, value };
  }, [categoryFilter, scores]);

  const focusScore = categoryFilter === 'all' ? totalScore : scores[categoryFilter];

  const nextStep = useMemo(() => {
    if (Array.isArray(report.nextStepsDetailed) && report.nextStepsDetailed.length) {
      return report.nextStepsDetailed[0];
    }
    if (Array.isArray(report.nextSteps) && report.nextSteps.length) {
      const first = report.nextSteps[0];
      return typeof first === 'string' ? { title: first, description: first } : first;
    }
    return undefined;
  }, [report.nextSteps, report.nextStepsDetailed]);

  const summaryStrength = report.strengthSummary || report.summary?.strengths || '';
  const summaryWeakness = report.areasForGrowth || report.summary?.areasForGrowth || '';

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
          <h1 className="text-3xl font-bold text-slate-900">AI 인터뷰 결과</h1>
          <p className="text-slate-600 text-sm max-w-2xl mx-auto">
            총점과 카테고리별 점수, 그리고 AI가 제안하는 다음 단계를 확인하세요.
          </p>
        </div>
      </section>

      {studentMeta && (
        <section className="bg-white/95 border border-white/70 shadow-soft rounded-[20px] p-5 flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1 text-sm text-slate-700">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-[0.2em]">학생 정보</p>
            <p className="text-lg font-bold text-slate-900">{studentMeta.name || '학생'}</p>
            <p className="text-sm text-slate-600">{studentMeta.schoolName || '학교 미입력'} {studentMeta.grade ? `${studentMeta.grade}학년` : ''}</p>
            <p className="text-sm text-slate-600">전공/희망: {studentMeta.major || '미입력'}</p>
          </div>
          <Button onClick={handleDownloadPdf} variant="secondary" className="px-6 py-3">PDF 저장</Button>
        </section>
      )}

      <section className="bg-white/95 border border-white/70 shadow-soft rounded-[24px] p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-[0.25em]">점수 & 포커스</p>
            <h3 className="text-xl font-bold text-slate-800">나의 인터뷰 성과</h3>
            <p className="text-sm text-slate-500">카테고리별 점수와 향후 집중 영역을 확인하세요.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <label className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 bg-slate-50 text-xs font-semibold">
              <span className="text-slate-500">범위</span>
              <select
                value={rangeFilter}
                onChange={(e) => setRangeFilter(e.target.value)}
                className="bg-transparent focus:outline-none"
              >
                <option value="최근 2회">최근 2회</option>
                <option value="최근 1회">최근 1회</option>
                <option value="전체">전체</option>
              </select>
            </label>
            <label className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 bg-slate-50 text-xs font-semibold">
              <span className="text-slate-500">카테고리</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value as typeof categoryFilter)}
                className="bg-transparent focus:outline-none"
              >
                <option value="all">전체</option>
                <option value="contentRelevance">내용 연관성</option>
                <option value="structure">구조/STAR</option>
                <option value="fluency">유창성</option>
                <option value="confidence">자신감</option>
              </select>
            </label>
            <Button variant="secondary" onClick={handleDownloadPdf}>PDF 저장</Button>
          </div>
        </div>
        <div className="grid sm:grid-cols-3 gap-4">
          <div className="rounded-[16px] border border-slate-100 bg-primary-lightest/50 p-4 text-left shadow-inner shadow-white/60">
            <p className="text-xs text-slate-500 uppercase font-semibold">현재 점수</p>
            <p className="text-3xl font-bold text-primary mt-1">{focusScore.toFixed(1)}<span className="text-base text-slate-500 font-normal">/10</span></p>
            <p className="text-xs text-slate-500">{rangeFilter} 기준입니다.</p>
          </div>
          <div className="rounded-[16px] border border-slate-100 bg-white p-4 shadow-soft">
            <p className="text-xs text-slate-500 uppercase font-semibold">가장 약한 영역</p>
            <p className="text-lg font-bold text-slate-800">{scoreLabels[weakestArea.key]}</p>
            <div className="mt-2 w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full" style={{ width: `${(weakestArea.value / 10) * 100}%` }}></div>
            </div>
            <p className="text-xs text-slate-500 mt-1">집중 보완이 필요합니다.</p>
          </div>
          <div className="rounded-[16px] border border-slate-100 bg-white p-4 shadow-soft">
            <p className="text-xs text-slate-500 uppercase font-semibold">다음 한 걸음</p>
            <p className="text-lg font-bold text-slate-800 truncate">{nextStep?.title || '제안 대기 중'}</p>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed line-clamp-3">{nextStep?.description || summaryWeakness || '곧 결과가 제공됩니다.'}</p>
          </div>
        </div>
      </section>
      
      <InterviewReportView report={{ ...report, scores, totalScore }} />

      <div className="text-center pt-8 pb-12">
        <Button
          onClick={onRetry}
          className="px-10 py-4 text-lg"
        >
          새 인터뷰 시작하기
        </Button>
      </div>
    </div>
  );
};

export default ResultsScreen;
