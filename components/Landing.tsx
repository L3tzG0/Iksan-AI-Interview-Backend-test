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
  onGoTeacherTab1?: () => void;
  onGoTeacherTab2?: () => void;
  onGoTeacherPreview?: () => void;
}

const Landing: React.FC<LandingProps> = ({
  user,
  hasResults,
  latestReport,
  onStartInterview,
  onGoDashboard,
  onViewResults,
  onGoTeacherTab1,
  onGoTeacherTab2,
  onGoTeacherPreview,
}) => {
  const isTeacher = user.role === 'teacher' || user.role === 'admin';
  const remainingAttempts = user.interviewSessionQuota;
  const heroTitle = isTeacher
    ? `${user.name}님, 반가워요! 학생들을 위한 연습 세션을 준비해볼까요?`
    : `${user.name}님, AI 인터뷰 연습을 시작해보세요.`;
  const heroBody = isTeacher
    ? '대시보드에서 진행 상황을 확인하고, 학생 인터뷰를 관리할 수 있어요.'
    : 'AI 면접관과 함께 실전처럼 연습하고, 즉시 피드백을 받아보세요.';

  const cards = isTeacher
    ? [
      {
        icon: <ChartIcon className="w-5 h-5" />,
        title: '학생 면접 결과',
        body: '학생들의 면접 결과와 AI 평가(점수, 피드백)를 한눈에 확인합니다.',
        extra: <span className="text-slate-500 text-xs">추천 기능: 전체 현황</span>,
        button: (
          <Button onClick={isTeacher ? onGoTeacherTab1 || onGoDashboard : onStartInterview} className="px-6 py-3">
            {isTeacher ? '대시보드' : 'AI 면접 시작'}
          </Button>
        )
      },
      {
        icon: <UsersIcon className="w-5 h-5" />,
        title: '학생 등록 관리',
        body: '학생 목록을 CSV로 업로드하고 계정을 쉽게 관리할 수 있어요.',
        extra: <span className="text-slate-500 text-xs">추천 기능: 학생/반 관리</span>,
        button: (
          <Button onClick={onGoTeacherTab2 || onGoDashboard} className="w-full">
            학생 관리
          </Button>
        ),
      },
      {
        icon: <SparklesIcon className="w-5 h-5" />,
        title: '면접 미리보기',
        body: '학생용 질문 흐름을 미리 보고 안내/운영에 활용하세요.',
        extra: <span className="text-slate-500 text-xs">추천 기능: 질문 리스트 확인</span>,
        button: (
          isTeacher ? (
            <Button
              onClick={onGoTeacherPreview || onGoTeacherTab2 || onGoDashboard}
              className="px-6 py-3"
            >
              면접 미리보기
            </Button>
          ) : (
            <Button
              onClick={onViewResults}
              variant="secondary"
              className="px-6 py-3"
              disabled={!hasResults}
            >
              결과 보기
            </Button>
          )
        )
      },

    ]
    : [
      {
        icon: <SparklesIcon className="w-5 h-5" />,
        title: '취업 면접 대비',
        body: '희망 직무(Job Title)를 입력하고, 맞춤 질문을 받아보세요.',
        extra: <span className="text-slate-500 text-xs">추천 기능: 직무 맞춤 질문</span>,
      },
      {
        icon: <HomeIcon className="w-5 h-5" />,
        title: '대학 면접 대비',
        body: '희망 전공과 관심 분야를 입력하면 AI가 질문을 추천합니다.',
        extra: <span className="text-slate-500 text-xs">추천 기능: 전공 맞춤 질문</span>,
      },
      {
        icon: <ChartIcon className="w-5 h-5" />,
        title: 'AI 면접 분석 & 리포트',
        body: '내용 구성, 구조, 표현력, 자신감 등 4개 항목을 분석합니다.',
        extra: <span className="text-slate-500 text-xs">추천 기능: 피드백 요약</span>,
      },
    ];


  const cardGridClass =
    cards.length === 1
      ? 'grid grid-cols-1 gap-4'
      : cards.length === 2
        ? 'grid grid-cols-1 md:grid-cols-2 gap-4'
        : 'grid grid-cols-1 md:grid-cols-3 gap-4';

  return (
    <div className="space-y-8 animate-fadeIn">
      <section className="relative pl-3 md:pl-6 py-10 overflow-hidden">
        {/* <div className="-top-10 -right-10 hero-blob hero-blob--primary"></div> */}
        {/* <div className="bottom-0 -left-10 hero-blob hero-blob--secondary"></div> */}
        <div className="z-10 relative flex md:flex-row flex-col md:items-center gap-8">
          <div className="space-y-4">
            <p className="flex items-center gap-2 font-semibold text-primary-text text-sm uppercase tracking-[0.2em]">
              환영합니다
            </p>
            <h1 className="font-bold text-slate-900 text-3xl md:text-4xl leading-tight">{heroTitle}</h1>
            <p className="max-w-3xl text-slate-600 leading-relaxed">{heroBody}</p>
            <div className="flex flex-wrap gap-3">
              {!isTeacher && (
              <Button onClick={isTeacher ? onGoTeacherTab1 || onGoDashboard : onStartInterview} className="px-6 py-3">
                {isTeacher ? '대시보드' : 'AI 인터뷰 시작'}
              </Button>
              )}
            </div>
          </div>
                    {latestReport && !isTeacher && (
            <div className="flex-1 grid gap-4 sm:grid-cols-2 min-w-[260px] animate-softFadeUp">
              <div className="space-y-3 bg-white/90 shadow-soft p-6 border border-white/70 rounded-[24px]">
                <p className="font-semibold text-slate-500 text-xs uppercase">최근 점수</p>
                <div className="flex justify-center items-baseline gap-2">
                  <span className="font-bold text-primary text-5xl">{latestReport.totalScore?.toFixed(1) ?? '--'}</span>
                  <span className="text-slate-500 text-sm">/ 10</span>
                </div>
                <p className="text-slate-600 text-sm">{latestReport.summary?.strengths?.slice(0, 60) ?? ''}</p>
                <Button onClick={onViewResults} variant="secondary" fullWidth disabled={!hasResults}>결과 보기</Button>
              </div>
              <div className="space-y-3 bg-white/90 shadow-soft p-6 border border-white/70 rounded-[24px]">
                <p className="font-semibold text-slate-500 text-xs uppercase">남은 응시 횟수</p>
                <div className="flex justify-center items-baseline gap-2">
                  <span className="font-bold text-slate-700 text-4xl">
                    {typeof remainingAttempts === 'number' ? remainingAttempts : '--'}
                  </span>
                  <span className="text-slate-500 text-sm">회</span>
                </div>
                <p className="text-slate-500 text-sm">계정 기준 잔여 횟수</p>
                <Button variant="secondary" fullWidth disabled>확인</Button>
              </div>
            </div>
          )}
        </div>
      </section>

      <div className={cardGridClass}>
        {cards.map((card, index) => (
          <div
            key={card.title}
            className={`bg-white rounded-[20px] border border-slate-100 shadow-soft p-5 flex flex-col gap-3 justify-between ${index === 0 ? 'animate-softFadeUp' : 'animate-softFadeUp-delayed'
              }`}
          >
            <div className="flex items-center gap-3 font-bold text-primary text-lg">
              {card.icon}
              {card.title}
            </div>
            <p className="text-slate-600 text-sm">{card.body}</p>
            {card.extra}
            {card.button}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Landing;
