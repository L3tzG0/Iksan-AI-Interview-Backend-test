import React from 'react';
import Button from './ui/Button';
import { SparklesIcon, ChartIcon, HomeIcon, UsersIcon } from './icons';
import type { InterviewReport, User } from '../types';

interface LandingProps {
  user: User;
  hasResults: boolean;
  latestReport?: InterviewReport | null;
  onStartInterview: () => void;
  onGoDashboard: () => void;
  onViewResults: () => void;
}

const Landing: React.FC<LandingProps> = ({ user, hasResults, latestReport, onStartInterview, onGoDashboard, onViewResults }) => {
  const isTeacher = user.role === 'teacher' || user.role === 'admin';
  return (
    <div className="space-y-8 animate-fadeIn">
      <section className="relative overflow-hidden rounded-[32px] bg-gradient-to-r from-primary-lightest via-white to-primary-lightest shadow-soft border border-white/70 px-6 py-10 md:px-12">
        <div className="hero-blob hero-blob--primary -right-10 -top-10"></div>
        <div className="hero-blob hero-blob--secondary -left-10 bottom-0"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center gap-8">
          <div className="space-y-4">
            <p className="text-sm font-semibold text-primary-text uppercase tracking-[0.2em] flex items-center gap-2">
              <SparklesIcon className="w-4 h-4" />
              환영합니다
            </p>
            <h1 className="text-3xl md:text-4xl font-bold text-slate-900 leading-tight">{user.name}님, {isTeacher ? '교사 대시보드로 이동하거나 학생 모의면접을 확인해 보세요.' : 'AI 면접 연습을 시작해 보세요.'}</h1>
            <p className="text-slate-600 leading-relaxed max-w-3xl">
              {isTeacher
                ? '학생들의 진행 상황과 보고서를 확인하고, 필요하면 즉시 대시보드로 이동하세요.'
                : '이력서 또는 자기소개를 기반으로 AI가 맞춤 질문을 생성합니다. 원하는 시간과 목표를 선택해 연습을 시작하세요.'}
            </p>
            <div className="flex flex-wrap gap-3">
              <Button onClick={onStartInterview} className="px-6 py-3">
                {isTeacher ? '학생 뷰 미리보기' : 'AI 면접 시작하기'}
              </Button>
              <Button onClick={isTeacher ? onGoDashboard : onViewResults} variant="secondary" className="px-6 py-3" disabled={!isTeacher && !hasResults}>
                {isTeacher ? '대시보드 이동' : '최근 결과 보기'}
              </Button>
            </div>
          </div>
          {latestReport && !isTeacher && (
            <div className="flex-1 min-w-[260px] bg-white/90 border border-white/70 rounded-[24px] shadow-soft p-6 space-y-3 animate-softFadeUp">
              <p className="text-xs font-semibold text-slate-500 uppercase">최근 연습 결과</p>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-primary">{latestReport.totalScore?.toFixed(1) ?? '--'}</span>
                <span className="text-sm text-slate-500">/ 10</span>
              </div>
              <p className="text-sm text-slate-600">{latestReport.summary?.strengths?.slice(0, 60) ?? ''}</p>
              <Button onClick={onViewResults} variant="secondary" fullWidth disabled={!hasResults}>결과 상세 보기</Button>
            </div>
          )}
        </div>
      </section>

      <div className="grid md:grid-cols-3 gap-4">
        {isTeacher ? (
          <>
            <div className="bg-white rounded-[20px] border border-slate-100 shadow-soft p-5 flex flex-col gap-3 animate-softFadeUp">
              <div className="flex items-center gap-3 text-primary font-bold text-lg">
                <ChartIcon className="w-5 h-5" />
                학생 대시보드
              </div>
              <p className="text-sm text-slate-600">학급/학생 진행 상황을 한눈에 확인하고 상세 보고서를 열람하세요.</p>
              <Button variant="secondary" onClick={onGoDashboard} className="w-full">대시보드로 이동</Button>
            </div>
            <div className="bg-white rounded-[20px] border border-slate-100 shadow-soft p-5 flex flex-col gap-3 animate-softFadeUp-delayed">
              <div className="flex items-center gap-3 text-primary font-bold text-lg">
                <SparklesIcon className="w-5 h-5" />
                학생 뷰 미리보기
              </div>
              <p className="text-sm text-slate-600">학생이 보게 될 인터뷰 시작 화면을 빠르게 확인해 보세요.</p>
              <Button onClick={onStartInterview} className="w-full">미리보기</Button>
            </div>
            <div className="bg-white rounded-[20px] border border-slate-100 shadow-soft p-5 flex flex-col gap-3 animate-softFadeUp-delayed">
              <div className="flex items-center gap-3 text-primary font-bold text-lg">
                <UsersIcon className="w-5 h-5" />
                최근 보고서
              </div>
              <p className="text-sm text-slate-600">최근 생성된 보고서를 확인하고 PDF로 내려받으세요.</p>
              <Button variant="secondary" onClick={onGoDashboard} className="w-full">보고서 보기</Button>
            </div>
          </>
        ) : (
          <>
            <div className="bg-white rounded-[20px] border border-slate-100 shadow-soft p-5 flex flex-col gap-3 animate-softFadeUp">
              <div className="flex items-center gap-3 text-primary font-bold text-lg">
                <SparklesIcon className="w-5 h-5" />
                새 인터뷰 시작
              </div>
              <p className="text-sm text-slate-600">이력서/소개를 업로드하고 맞춤 질문으로 연습을 시작하세요.</p>
              <Button onClick={onStartInterview} className="w-full">AI 면접 시작</Button>
            </div>
            <div className="bg-white rounded-[20px] border border-slate-100 shadow-soft p-5 flex flex-col gap-3 animate-softFadeUp-delayed">
              <div className="flex items-center gap-3 text-primary font-bold text-lg">
                <HomeIcon className="w-5 h-5" />
                최근 결과 보기
              </div>
              <p className="text-sm text-slate-600">마지막 연습 결과와 피드백을 다시 확인합니다.</p>
              <Button variant="secondary" onClick={onViewResults} className="w-full" disabled={!hasResults}>결과 열람</Button>
            </div>
            <div className="bg-white rounded-[20px] border border-slate-100 shadow-soft p-5 flex flex-col gap-3 animate-softFadeUp-delayed">
              <div className="flex items-center gap-3 text-primary font-bold text-lg">
                <ChartIcon className="w-5 h-5" />
                학습 조언
              </div>
              <p className="text-sm text-slate-600">STAR 구조로 답변하고 수치/결과를 넣어 완성도를 높여보세요.</p>
              <span className="text-xs text-slate-500">연습을 시작하면 AI가 자동으로 분석합니다.</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Landing;
