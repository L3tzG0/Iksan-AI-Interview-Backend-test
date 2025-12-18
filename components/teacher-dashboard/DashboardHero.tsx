import type { FC } from 'react';
import type { DashboardHeroProps } from '../../types/teacherDashboard';

const DashboardHero: FC<DashboardHeroProps> = ({ currentUser, studentCount, completedCount, averageScore }) => (
  <section className="relative bg-gradient-to-r from-primary-lightest via-white to-white shadow-soft p-6 sm:p-8 border border-white/70 rounded-[28px] overflow-hidden">
    <div className="-top-8 -right-8 hero-blob hero-blob--primary"></div>
    <div className="bottom-0 -left-8 hero-blob hero-blob--secondary"></div>
    <div className="z-10 relative flex flex-col gap-4">
      <div>
        <p className="font-semibold text-primary-text text-xs uppercase tracking-[0.25em]">Teacher Dashboard</p>
        <h1 className="font-bold text-slate-900 text-3xl">{currentUser.schoolName}{currentUser.grade ? ` ${currentUser.grade}학년` : ''} 교사</h1>
        <p className="mt-1 font-medium text-slate-500">학생 진행 현황을 확인하고 계정을 관리하세요.</p>
      </div>
      <div className="gap-4 grid sm:grid-cols-3">
        <div className="bg-white/90 shadow-soft p-4 border border-white/70 rounded-[18px]">
          <p className="text-slate-400 text-xs uppercase">학생 수</p>
          <p className="mt-2 font-bold text-primary text-3xl">{studentCount}</p>
          <p className="text-slate-500 text-xs">등록된 전체 학생</p>
        </div>
        <div className="bg-white/90 shadow-soft p-4 border border-white/70 rounded-[18px]">
          <p className="text-slate-400 text-xs uppercase">완료</p>
          <p className="mt-2 font-bold text-primary text-3xl">{completedCount}</p>
          <p className="text-slate-500 text-xs">면접 완료 학생</p>
        </div>
        <div className="bg-white/90 shadow-soft p-4 border border-white/70 rounded-[18px]">
          <p className="text-slate-400 text-xs uppercase">평균 점수</p>
          <p className="mt-2 font-bold text-primary text-3xl">{averageScore}</p>
          <p className="text-slate-500 text-xs">최근 평균 점수</p>
        </div>
      </div>
    </div>
  </section>
);

export default DashboardHero;
