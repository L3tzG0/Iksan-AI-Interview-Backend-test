import React from 'react';
import { ChartIcon, SparklesIcon, UsersIcon } from './icons';
import Button from './ui/Button';
import type { User } from '../types';

interface TeacherHomeProps {
  user: User;
  onGoDashboard: () => void;
  onPreviewStudent: () => void;
}

const TeacherHome: React.FC<TeacherHomeProps> = ({ user, onGoDashboard, onPreviewStudent }) => {
  const cards = [
    {
      icon: <ChartIcon className="w-7 h-7" />,
      title: '학생 대시보드',
      body: '학급 면접 진행 상황과 인사이트를 확인하세요.',
      sub: `${user.schoolName} 학생들을 한 곳에서 관리합니다.`,
    },
    {
      icon: <UsersIcon className="w-7 h-7" />,
      title: '학생 추가',
      body: '새 학생을 등록해 AI 면접 연습을 시작하세요.',
      sub: '초대를 보내고 바로 준비할 수 있습니다.',
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
      <section className="relative overflow-hidden rounded-[28px] bg-gradient-to-r from-primary-lightest via-white to-white border border-white/70 shadow-soft px-6 py-10">
        <div className="hero-blob hero-blob--primary right-0 top-0"></div>
        <div className="hero-blob hero-blob--secondary left-0 bottom-0"></div>
        <div className="relative z-10 space-y-4">
          <p className="text-xs font-semibold text-primary-text uppercase tracking-[0.3em] flex items-center gap-2">
            <SparklesIcon className="w-4 h-4" />
            교사 홈
          </p>
          <h1 className="text-3xl font-bold text-slate-900 leading-snug">
            {user.schoolName} {user.grade ? `${user.grade}학년 ` : ''}교사님, 반갑습니다!
            <br />
            AI 면접 준비를 함께 시작해 보세요.
          </h1>
          <p className="text-slate-600 text-sm max-w-2xl">
            학생 진행 상황을 확인하고 필요할 때 바로 대시보드나 학생 뷰 미리보기로 이동하세요.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button onClick={onGoDashboard} className="px-6 py-3 text-sm">
              대시보드 이동
            </Button>
            <Button onClick={onPreviewStudent} variant="secondary" className="px-6 py-3 text-sm bg-white text-primary border border-primary-light">
              학생 뷰 미리보기
            </Button>
          </div>
        </div>
      </section>

      <section className={cardGridClass}>
        {cards.map((card) => (
          <div key={card.title} className="rounded-[18px] bg-white/90 border border-white/70 p-5 shadow-soft flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-primary-lightest text-primary shadow-inner shadow-white/60">
              {card.icon}
            </div>
            <div>
              <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide">{card.title}</p>
              <p className="text-sm font-bold text-slate-800">{card.body}</p>
              <p className="text-xs text-slate-500">{card.sub}</p>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
};

export default TeacherHome;
