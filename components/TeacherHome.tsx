import React from 'react';
import { ClockIcon, SparklesIcon, GraduationCapIcon, BrainIcon } from './icons';
import Button from './ui/Button';
import type { User } from '../types';

interface TeacherHomeProps {
  user: User;
  onGoDashboard: () => void;
  onPreviewStudent: () => void;
}

const TeacherHome: React.FC<TeacherHomeProps> = ({ user, onGoDashboard, onPreviewStudent }) => {
  return (
    <div className="space-y-8 animate-fadeIn">
      <section className="relative overflow-hidden rounded-[28px] bg-gradient-to-r from-primary-lightest via-white to-white border border-white/70 shadow-soft px-6 py-10">
        <div className="hero-blob hero-blob--primary right-0 top-0"></div>
        <div className="hero-blob hero-blob--secondary left-0 bottom-0"></div>
        <div className="relative z-10 space-y-4">
          <p className="text-xs font-semibold text-primary-text uppercase tracking-[0.3em] flex items-center gap-2">
            <SparklesIcon className="w-4 h-4" />
            TEACHER HOME
          </p>
          <h1 className="text-3xl font-bold text-slate-900 leading-snug">
            {user.schoolName} {user.grade ? `${user.grade}학년` : ''} 담임 선생님을 위한
            <br />
            AI 면접 코치 홈
          </h1>
          <p className="text-slate-600 text-sm max-w-2xl">
            학생 진행 현황을 한눈에 보고, 대시보드로 바로 이동하거나 학생 화면을 체험해 보세요.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button onClick={onGoDashboard} className="px-6 py-3 text-sm">
              학생 대시보드로 이동
            </Button>
            <Button onClick={onPreviewStudent} variant="secondary" className="px-6 py-3 text-sm bg-white text-primary border border-primary-light">
              학생 화면 체험하기
            </Button>
          </div>
        </div>
      </section>

      <section className="grid md:grid-cols-3 gap-4">
        <div className="rounded-[18px] bg-white/90 border border-white/70 p-5 shadow-soft flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-primary-lightest text-primary shadow-inner shadow-white/60">
            <GraduationCapIcon className="w-7 h-7" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide">학급 정보</p>
            <p className="text-sm font-bold text-slate-800">
              {user.schoolName} {user.grade ? `${user.grade}학년` : ''} · {user.major || '담당 과목'}
            </p>
          </div>
        </div>
        <div className="rounded-[18px] bg-white/90 border border-white/70 p-5 shadow-soft flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-primary-lightest text-primary shadow-inner shadow-white/60">
            <ClockIcon className="w-7 h-7" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide">최근 활동</p>
            <p className="text-sm font-bold text-slate-800">학생 연습 기록 확인</p>
            <p className="text-xs text-slate-500">대시보드에서 바로 이어서 확인하세요.</p>
          </div>
        </div>
        <div className="rounded-[18px] bg-white/90 border border-white/70 p-5 shadow-soft flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-primary-lightest text-primary shadow-inner shadow-white/60">
            <BrainIcon className="w-7 h-7" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide">학생 체험</p>
            <p className="text-sm font-bold text-slate-800">학생 화면 미리보기</p>
            <p className="text-xs text-slate-500">버튼 한 번으로 학생 흐름을 확인합니다.</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default TeacherHome;
