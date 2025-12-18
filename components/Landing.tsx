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
          title: '진행 현황',
          body: '학생들의 인터뷰 결과와 진행 상태를 확인하세요.',
          button: (
            <Button variant="secondary" onClick={onGoTeacherTab1 || onGoDashboard} className="w-full">
              대시보드 보기
            </Button>
          ),
        },
        {
          icon: <UsersIcon className="w-5 h-5" />,
          title: '학생 관리',
          body: '학생 계정을 추가하고 인터뷰를 배정할 수 있어요.',
          button: (
            <Button onClick={onGoTeacherTab2 || onGoDashboard} className="w-full">
              학생 관리하기
            </Button>
          ),
        },
      ]
    : [
        {
          icon: <SparklesIcon className="w-5 h-5" />,
          title: 'AI 인터뷰',
          body: '지금 바로 AI 면접 연습을 시작해보세요.',
          button: (
            <Button onClick={onStartInterview} className="w-full">
              AI 연습 시작
            </Button>
          ),
        },
        // {
        //   icon: <HomeIcon className="w-5 h-5" />,
        //   title: '최근 결과',
        //   body: '이전에 받은 피드백을 다시 확인해보세요.',
        //   button: (
        //     <Button variant="secondary" onClick={onViewResults} className="w-full" disabled={!hasResults}>
        //       결과 보기
        //     </Button>
        //   ),
        // },
        {
          icon: <ChartIcon className="w-5 h-5" />,
          title: '면접 TIP',
          body: 'STAR 기법과 답변 구조화 팁을 확인해보세요.',
          extra: <span className="text-slate-500 text-xs">실전 준비를 위한 빠른 가이드.</span>,
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
      <section className="relative bg-gradient-to-r from-primary-lightest via-white to-primary-lightest shadow-soft px-6 md:px-12 py-10 border border-white/70 rounded-[32px] overflow-hidden">
        <div className="-top-10 -right-10 hero-blob hero-blob--primary"></div>
        <div className="bottom-0 -left-10 hero-blob hero-blob--secondary"></div>
        <div className="z-10 relative flex md:flex-row flex-col md:items-center gap-8">
          <div className="space-y-4">
            <p className="flex items-center gap-2 font-semibold text-primary-text text-sm uppercase tracking-[0.2em]">
              <SparklesIcon className="w-4 h-4" />
              환영합니다
            </p>
            <h1 className="font-bold text-slate-900 text-3xl md:text-4xl leading-tight">{heroTitle}</h1>
            <p className="max-w-3xl text-slate-600 leading-relaxed">{heroBody}</p>
            <div className="flex flex-wrap gap-3">
              <Button onClick={isTeacher ? onGoTeacherTab1 || onGoDashboard : onStartInterview} className="px-6 py-3">
                {isTeacher ? '대시보드' : 'AI 인터뷰 시작'}
              </Button>
              {isTeacher && <Button
                onClick={isTeacher ? onGoTeacherPreview || onGoTeacherTab2 || onGoDashboard : onViewResults}
                variant="secondary"
                className="px-6 py-3"
                disabled={!isTeacher && !hasResults}
              >
                {isTeacher ? '학생 인터뷰 미리보기' : '결과 보기'}
              </Button>}
            </div>
          </div>
          {latestReport && !isTeacher && (
            <div className="flex-1 space-y-3 bg-white/90 shadow-soft p-6 border border-white/70 rounded-[24px] min-w-[260px] animate-softFadeUp">
              <p className="font-semibold text-slate-500 text-xs uppercase">최근 점수</p>
              <div className="flex items-baseline gap-2">
                <span className="font-bold text-primary text-5xl">{latestReport.totalScore?.toFixed(1) ?? '--'}</span>
                <span className="text-slate-500 text-sm">/ 10</span>
              </div>
              <p className="text-slate-600 text-sm">{latestReport.summary?.strengths?.slice(0, 60) ?? ''}</p>
              <Button onClick={onViewResults} variant="secondary" fullWidth disabled={!hasResults}>자세히 보기</Button>
            </div>
          )}
        </div>
      </section>

      <div className={cardGridClass}>
        {cards.map((card, index) => (
          <div
            key={card.title}
            className={`bg-white rounded-[20px] border border-slate-100 shadow-soft p-5 flex flex-col gap-3 ${
              index === 0 ? 'animate-softFadeUp' : 'animate-softFadeUp-delayed'
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
