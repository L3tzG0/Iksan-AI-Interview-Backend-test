import type { FC } from 'react';
import { useNavigate } from 'react-router-dom';
import type { CompletedSessionsSectionProps } from '../../types/teacherDashboard';
import FilterControls from './FilterControls';
import SearchBar from './SearchBar';
import Spinner from '../Spinner';

const CompletedSessionsSection: FC<CompletedSessionsSectionProps> = ({
  searchTerm,
  onSearch,
  filterControlsProps,
  processedCompleted,
  isLoadingStudents,
  activeStudentId,
  onHighlightStudent,
}) => {
  const navigate = useNavigate();

    return (
        <div className="space-y-4">
    <div className="flex lg:flex-row flex-col lg:items-center gap-4">
      <SearchBar value={searchTerm} onChange={onSearch} placeholder="학생 이름 검색" />
      <FilterControls {...filterControlsProps} />
    </div>

    {isLoadingStudents ? (
      <div className="bg-white shadow-soft border border-slate-100 rounded-[20px] overflow-hidden">
        <div className="flex justify-center py-16">
          <Spinner label="학생 목록을 불러오는 중..." />
        </div>
      </div>
    ) : processedCompleted.length === 0 ? (
      <div className="py-16 text-slate-500 text-center">
        <p className="font-semibold text-lg">완료된 학생이 없습니다.</p>
        <p className="mt-2 text-slate-400 text-sm">필터를 변경하거나 학생을 추가해 주세요.</p>
      </div>
    ) : (
      <div className="bg-white shadow-soft border border-slate-100 rounded-[20px] overflow-hidden">
        <div className="flex flex-wrap items-center gap-3 bg-slate-50/80 px-6 py-3 border-slate-100 border-b text-slate-500 text-xs">
          <span className="inline-flex items-center gap-2"><span className="bg-green-400 border border-green-600 rounded-full w-3 h-3"></span>완료</span>
          <span className="font-semibold text-slate-400">학생을 클릭하면 상세로 이동합니다.</span>
          <span className="ml-auto text-slate-400">총 {processedCompleted.length}명</span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-slate-600 text-sm text-left">
            <thead className="bg-slate-50 border-slate-200 border-b text-slate-500 text-xs uppercase">
              <tr>
                <th className="px-6 py-4 font-bold">이름</th>
                <th className="px-6 py-4 font-bold">학년</th>
                <th className="px-6 py-4 font-bold">전공</th>
                <th className="px-6 py-4 font-bold text-center">상태</th>
                <th className="px-6 py-4 font-bold text-center">점수</th>
                <th className="px-6 py-4 font-bold text-center">개선률</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {processedCompleted.map((student) => (
                <tr
                  key={student.id}
                  className={`group cursor-pointer transition-all ${
                    activeStudentId === student.id
                      ? 'bg-primary-lightest/80 border-l-4 border-primary text-primary'
                      : 'hover:bg-primary-lightest/50'
                  }`}
                  onClick={() => {
                    onHighlightStudent(student.id);
                    const sessionId = student.session_id || student.sessionId;
                    const path = sessionId
                      ? `/teacher/students/${student.id}?session_id=${encodeURIComponent(sessionId)}`
                      : `/teacher/students/${student.id}`;
                    navigate(path);
                  }}
                >
                  <td className="px-6 py-4 font-semibold text-slate-800 group-hover:text-primary">{student.name}</td>
                  <td className="px-6 py-4">{student.grade}학년</td>
                  <td className="px-6 py-4 font-medium text-slate-700">{student.major}</td>
                  <td className="px-6 py-4 text-center">
                    <span
                      className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-semibold ${
                        student.status === 'completed'
                          ? 'bg-green-100 text-green-700 border border-green-200'
                          : 'bg-amber-100 text-amber-700 border border-amber-200'
                      }`}
                    >
                      {student.status === 'completed' ? '완료' : '진행중'}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono font-bold text-slate-800 text-center">{student.latestScore}/100</td>
                  <td className={`px-6 py-4 text-center font-mono font-bold ${student.improvement >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {student.improvement >= 0 ? `+${student.improvement}%` : `-${Math.abs(student.improvement)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )}
        </div>
)
}

export default CompletedSessionsSection;
