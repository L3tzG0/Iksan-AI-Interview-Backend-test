import React, { useMemo, useState } from 'react';
import type { InterviewReport } from '../types';
import InterviewReportView from './InterviewReportView';
import Button from './ui/Button';

const scoreLabels: Record<keyof InterviewReport['scores'], string> = {
  contentRelevance: '내용 적합도',
  structure: '구조/STAR',
  fluency: '유창성',
  confidence: '자신감',
};

interface ResultsScreenProps {
  report: InterviewReport;
  onRetry: () => void;
}

const ResultsScreen: React.FC<ResultsScreenProps> = ({ report, onRetry }) => {
  const [rangeFilter, setRangeFilter] = useState('최근 2회');
  const [categoryFilter, setCategoryFilter] = useState<'all' | keyof InterviewReport['scores']>('all');

  const weakestArea = useMemo(() => {
    if (categoryFilter !== 'all') {
      return { key: categoryFilter, value: report.scores[categoryFilter] };
    }
    const entries = Object.entries(report.scores) as [keyof InterviewReport['scores'], number][];
    const [key, value] = entries.sort((a, b) => a[1] - b[1])[0];
    return { key, value };
  }, [categoryFilter, report.scores]);

  const focusScore = categoryFilter === 'all' ? report.totalScore : report.scores[categoryFilter];

  const nextStep = report.nextSteps?.[0];

  return (
    <div className="animate-fadeIn space-y-8">
      <section className="relative overflow-hidden rounded-[28px] bg-gradient-to-r from-white via-primary-lightest to-white border border-white/70 shadow-soft px-6 py-10 text-center">
        <div className="hero-blob hero-blob--primary right-0 top-0"></div>
        <div className="hero-blob hero-blob--secondary left-0 bottom-0"></div>
        <div className="relative z-10 space-y-3">
          <p className="text-xs font-semibold text-primary-text uppercase tracking-[0.3em]">AI FEEDBACK</p>
          <h1 className="text-3xl font-bold text-slate-900">AI 결과 리포트</h1>
          <p className="text-slate-600 text-sm max-w-2xl mx-auto">
            콘텐츠 적합도, 구조, 유창성, 자신감 네 가지 축으로 학생의 답변을 분석했어요. 강점과 성장 기회를 한눈에 확인해 보세요.
          </p>
        </div>
      </section>

      <section className="bg-white/95 border border-white/70 shadow-soft rounded-[24px] p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-[0.25em]">기간 & 지표</p>
            <h3 className="text-xl font-bold text-slate-800">약한 부분을 빠르게 확인해요</h3>
            <p className="text-sm text-slate-500">최근/전체 결과와 지표를 바꿔 보며 집중할 영역을 살펴보세요.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <label className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 bg-slate-50 text-xs font-semibold">
              <span className="text-slate-500">기간</span>
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
              <span className="text-slate-500">지표</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value as typeof categoryFilter)}
                className="bg-transparent focus:outline-none"
              >
                <option value="all">전체 지표</option>
                <option value="contentRelevance">내용 적합도</option>
                <option value="structure">구조/STAR</option>
                <option value="fluency">유창성</option>
                <option value="confidence">자신감</option>
              </select>
            </label>
          </div>
        </div>
        <div className="grid sm:grid-cols-3 gap-4">
          <div className="rounded-[16px] border border-slate-100 bg-primary-lightest/50 p-4 text-left shadow-inner shadow-white/60">
            <p className="text-xs text-slate-500 uppercase font-semibold">핵심 점수</p>
            <p className="text-3xl font-bold text-primary mt-1">{focusScore.toFixed(1)}<span className="text-base text-slate-500 font-normal">/10</span></p>
            <p className="text-xs text-slate-500">{rangeFilter} 기준 평균 점수입니다.</p>
          </div>
          <div className="rounded-[16px] border border-slate-100 bg-white p-4 shadow-soft">
            <p className="text-xs text-slate-500 uppercase font-semibold">취약 지표</p>
            <p className="text-lg font-bold text-slate-800">{scoreLabels[weakestArea.key]}</p>
            <div className="mt-2 w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full" style={{ width: `${(weakestArea.value / 10) * 100}%` }}></div>
            </div>
            <p className="text-xs text-slate-500 mt-1">집중적으로 개선하면 좋아요.</p>
          </div>
          <div className="rounded-[16px] border border-slate-100 bg-white p-4 shadow-soft">
            <p className="text-xs text-slate-500 uppercase font-semibold">다음 단계</p>
            <p className="text-lg font-bold text-slate-800 truncate">{nextStep?.title || '추천 단계 없음'}</p>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed line-clamp-3">{nextStep?.description || report.summary.areasForGrowth}</p>
          </div>
        </div>
      </section>
      
      <InterviewReportView report={report} />

      <div className="text-center pt-8 pb-12">
        <Button
          onClick={onRetry}
          className="px-10 py-4 text-lg"
        >
          새로운 질문으로 다시 연습
        </Button>
      </div>
    </div>
  );
};

export default ResultsScreen;
