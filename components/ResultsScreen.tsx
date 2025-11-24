import React from 'react';
import type { InterviewReport } from '../types';
import InterviewReportView from './InterviewReportView';
import Button from './ui/Button';

interface ResultsScreenProps {
  report: InterviewReport;
  onRetry: () => void;
}

const ResultsScreen: React.FC<ResultsScreenProps> = ({ report, onRetry }) => {
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
