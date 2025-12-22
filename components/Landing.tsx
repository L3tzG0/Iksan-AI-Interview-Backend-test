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
        title: '학생 결과 대시보드',
        body: '학생들의 인터뷰 진행률과 AI 분석 결과(점수, 피드백)를 실시간으로 모니터링하세요.',
        extra: <span className="text-slate-500 text-xs">지원 기능: 리포트 조회</span>,
        button: (
          <Button onClick={isTeacher ? onGoTeacherTab1 || onGoDashboard : onStartInterview} className="px-6 py-3">
            {isTeacher ? '대시보드' : 'AI 인터뷰 시작'}
          </Button>
        )
      },
      {
        icon: <UsersIcon className="w-5 h-5" />,
        title: '학생 계정 관리',
        body: '새로운 학생 계정을 생성하거나 CSV로 일괄 등록하여 빠르고 간편하게 관리할 수 있습니다.',
        extra: <span className="text-slate-500 text-xs">지원 기능: 개별/일괄 계정 생성</span>,
        button: (
          <Button onClick={onGoTeacherTab2 || onGoDashboard} className="w-full">
            학생 관리하기
          </Button>
        ),
      },
      {
        icon: <SparklesIcon className="w-5 h-5" />,
        title: '학생 화면 미리보기',
        body: '학생들이 경험할 이력서 제출 및 생활기록부 입력 화면을 교사 시점에서 미리 확인해보세요.',
        extra: <span className="text-slate-500 text-xs">지원 기능: 학생 프로세스 미리보기</span>,
        button: (
          isTeacher ? (
            <Button
              onClick={onGoTeacherPreview || onGoTeacherTab2 || onGoDashboard}
              className="px-6 py-3"
            >
              학생 인터뷰 미리보기
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
        title: '직무 중심 취업 면접',
        body: '이력서를 기반으로 희망 분야와 직무(Job Title)를 설정하여, 실전과 같은 맞춤형 면접을 연습하세요.',
        extra: <span className="text-slate-500 text-xs">지원 기능: 이력서 업로드 및 직무 설정</span>,
      },
      {
        icon: <HomeIcon className="w-5 h-5" />,
        title: '대학 입시 모의 면접',
        body: '생활기록부를 분석해 목표 대학과 희망 학과(Major)에 최적화된 예상 질문으로 시뮬레이션합니다.',
        extra: <span className="text-slate-500 text-xs">지원 기능: 생활기록부 기반 질문 생성</span>,
      },
      {
        icon: <ChartIcon className="w-5 h-5" />,
        title: 'AI 정밀 분석 & 피드백',
        body: '내용 적합성, 논리 구조, 유창성, 자신감 등 4가지 핵심 지표를 분석해 개인별 맞춤 피드백을 제공합니다.',
        extra: <span className="text-slate-500 text-xs">면접 직후 상세 리포트 제공</span>,
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
            <div className="flex-1 space-y-3 bg-white/90 shadow-soft p-6 border border-white/70 rounded-[24px] min-w-[260px] animate-softFadeUp">
              <p className="font-semibold text-slate-500 text-xs uppercase">최근 점수</p>
              <div className="flex justify-center items-baseline gap-2">
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
