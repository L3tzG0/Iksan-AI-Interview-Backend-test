import React from 'react';
import { HistoryIcon } from './icons';
import type { InterviewReport } from '../types';

interface StudentHistoryProps {
  history: InterviewReport[];
  onViewReport: (report: InterviewReport) => void;
}

const StudentHistory: React.FC<StudentHistoryProps> = ({ history, onViewReport }) => {
  const hasHistory = Array.isArray(history) && history.length > 0;

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 font-bold text-slate-900 text-2xl">
            <HistoryIcon className="w-6 h-6 text-primary" />
            면접 기록
          </h1>
          <p className="mt-1 text-slate-500 text-sm">이전 AI 면접 결과를 확인하고 다시 열어볼 수 있어요.</p>
        </div>
        <div className="inline-flex items-center gap-2 bg-primary-lightest px-3 py-1.5 rounded-full font-semibold text-primary text-xs">
          총 {history.length}건
        </div>
      </div>

      <div className="bg-white/90 shadow-soft p-6 border border-white/80 rounded-[24px]">
        {!hasHistory && (
          <div className="py-10 text-center text-slate-500 text-sm">아직 기록이 없어요.</div>
        )}
        {hasHistory && (
          <div className="divide-y divide-slate-100">
            {history.map((item, index) => (
              <button
                key={index}
                onClick={() => onViewReport(item)}
                className="group flex justify-between items-center hover:bg-primary-lightest/50 px-2 py-4 rounded-[12px] w-full text-left transition-all"
              >
                <div>
                  <p className="font-semibold text-slate-700 group-hover:text-primary transition-colors">
                    {item.date || '면접 날짜 없음'}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-slate-500 text-xs">
                    <span className="inline-flex items-center gap-1 bg-green-50 px-2 py-0.5 rounded-full font-semibold text-green-600">
                      점수{' '}
                      <strong className="ml-2 text-slate-900">
                        {typeof item.totalScore === 'number' ? item.totalScore.toFixed(1) : '--'}
                      </strong>
                      /10
                    </span>
                  </div>
                </div>
                <div className="font-semibold text-primary text-sm">상세 보기</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentHistory;
