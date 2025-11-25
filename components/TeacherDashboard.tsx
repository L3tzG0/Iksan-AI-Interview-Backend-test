import React, { useState, useEffect, useMemo } from 'react';
import { getTeacherDashboardData } from '../services/geminiService';
import type { StudentSummary, User } from '../types';
import Spinner from './Spinner';
import Card from './Card';
import { FilterIcon, SortIcon, SearchIcon, ChartIcon } from './icons';

interface TeacherDashboardProps {
  currentUser: User;
  onSelectStudent: (studentId: string) => void;
}

const TeacherDashboard: React.FC<TeacherDashboardProps> = ({ currentUser, onSelectStudent }) => {
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortOption, setSortOption] = useState<'recent' | 'score' | 'growth'>('recent');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'pending'>('all');
  const [gradeFilter, setGradeFilter] = useState<number | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeStudentId, setActiveStudentId] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      const allStudents = await getTeacherDashboardData();

      const myStudents = allStudents.filter((s) => {
        if (s.schoolName !== currentUser.schoolName) return false;
        if (currentUser.grade && s.grade !== currentUser.grade) return false;
        return true;
      });

      setStudents(myStudents);
      setIsLoading(false);
    };
    if (currentUser.schoolName) {
      fetchData();
    }
  }, [currentUser]);

  const stats = useMemo(() => {
    if (students.length === 0) {
      return { avgScore: 0, completed: 0 };
    }
    const completed = students.filter((s) => s.completed).length;
    const avgScore = students.reduce((sum, s) => sum + s.latestScore, 0) / students.length;
    return { avgScore: Math.round(avgScore), completed };
  }, [students]);

  const gradeOptions = useMemo(() => Array.from(new Set(students.map((s) => s.grade))).sort((a, b) => a - b), [students]);

  const processedStudents = useMemo(() => {
    let filtered = [...students];
    if (statusFilter !== 'all') {
      filtered = filtered.filter((s) => (statusFilter === 'completed' ? s.completed : !s.completed));
    }
    if (gradeFilter !== 'all') {
      filtered = filtered.filter((s) => s.grade === gradeFilter);
    }
    if (searchTerm.trim()) {
      filtered = filtered.filter((s) => s.name.toLowerCase().includes(searchTerm.toLowerCase()));
    }

    const sorted = [...filtered];
    if (sortOption === 'score') {
      sorted.sort((a, b) => b.latestScore - a.latestScore);
    } else if (sortOption === 'growth') {
      sorted.sort((a, b) => b.improvement - a.improvement);
    } else {
      sorted.sort((a, b) => a.name.localeCompare(b.name));
    }
    return sorted;
  }, [students, statusFilter, gradeFilter, searchTerm, sortOption]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="container mx-auto animate-fadeIn space-y-8">
      <section className="relative overflow-hidden rounded-[28px] bg-gradient-to-r from-primary-lightest via-white to-white border border-white/70 shadow-soft p-6 sm:p-8">
        <div className="hero-blob hero-blob--primary -right-8 -top-8"></div>
        <div className="hero-blob hero-blob--secondary -left-8 bottom-0"></div>
        <div className="relative z-10 flex flex-col gap-4">
          <div>
            <p className="text-xs font-semibold text-primary-text uppercase tracking-[0.25em]">Teacher Dashboard</p>
            <h1 className="text-3xl font-bold text-slate-900">{currentUser.schoolName}{currentUser.grade ? ` ${currentUser.grade}학년` : ''} 학생 관리</h1>
            <p className="text-slate-500 mt-1 font-medium">담당 학생들의 AI 모의면접 현황을 한눈에 확인해 보세요.</p>
          </div>
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="rounded-[18px] bg-white/90 border border-white/70 p-4 shadow-soft">
              <p className="text-xs text-slate-400 uppercase">학생 수</p>
              <p className="text-3xl font-bold text-primary mt-2">{students.length}</p>
              <p className="text-xs text-slate-500">등록된 전체 학생</p>
            </div>
            <div className="rounded-[18px] bg-white/90 border border-white/70 p-4 shadow-soft">
              <p className="text-xs text-slate-400 uppercase">완료 세션</p>
              <p className="text-3xl font-bold text-primary mt-2">{stats.completed}</p>
              <p className="text-xs text-slate-500">최근 일주일 기준</p>
            </div>
            <div className="rounded-[18px] bg-white/90 border border-white/70 p-4 shadow-soft">
              <p className="text-xs text-slate-400 uppercase">평균 점수</p>
              <p className="text-3xl font-bold text-primary mt-2">{stats.avgScore}</p>
              <p className="text-xs text-slate-500">최근 모의면접 평균</p>
            </div>
          </div>
        </div>
      </section>

      <Card className="space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          <div className="flex-1 flex items-center gap-3 rounded-full border border-slate-200 px-4 py-2 bg-white/90 shadow-inner shadow-white/60">
            <SearchIcon className="w-5 h-5 text-primary" />
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="학생 이름을 입력해 검색하세요"
              className="flex-1 bg-transparent text-sm focus:outline-none"
            />
          </div>
          <div className="flex flex-wrap gap-3">
            <label className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 bg-slate-50 text-xs font-semibold">
              <FilterIcon className="w-4 h-4 text-primary" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
                className="bg-transparent focus:outline-none"
              >
                <option value="all">상태 전체</option>
                <option value="completed">완료</option>
                <option value="pending">대기</option>
              </select>
            </label>
            <label className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 bg-slate-50 text-xs font-semibold">
              <ChartIcon className="w-4 h-4 text-primary" />
              <select
                value={gradeFilter === 'all' ? 'all' : gradeFilter}
                onChange={(e) => setGradeFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))}
                className="bg-transparent focus:outline-none"
              >
                <option value="all">학년 전체</option>
                {gradeOptions.map((grade) => (
                  <option key={grade} value={grade}>
                    {grade}학년
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 bg-slate-50 text-xs font-semibold">
              <SortIcon className="w-4 h-4 text-primary" />
              <select
                value={sortOption}
                onChange={(e) => setSortOption(e.target.value as typeof sortOption)}
                className="bg-transparent focus:outline-none"
              >
                <option value="recent">이름순</option>
                <option value="score">평균 점수순</option>
                <option value="growth">향상도순</option>
              </select>
            </label>
          </div>
        </div>

        {processedStudents.length === 0 ? (
          <div className="text-center py-16 text-slate-500">
            <p className="text-lg font-semibold">표시할 학생 데이터를 찾을 수 없습니다.</p>
            <p className="text-sm text-slate-400 mt-2">다른 필터를 선택하거나 검색어를 지워 다시 시도하세요.</p>
          </div>
        ) : (
          <div className="bg-white border border-slate-100 rounded-[20px] shadow-soft overflow-hidden">
            <div className="flex flex-wrap items-center gap-3 px-6 py-3 text-xs text-slate-500 bg-slate-50/80 border-b border-slate-100">
              <span className="inline-flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-green-400 border border-green-600"></span>완료</span>
              <span className="inline-flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-slate-200 border border-slate-400"></span>진행 전</span>
              <span className="font-semibold text-slate-400">필터를 사용해 원하는 학생을 빠르게 찾아보세요.</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm text-left text-slate-600">
                <caption className="sr-only">학생/점수 현황을 보여주는 표입니다.</caption>
                <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th scope="col" className="px-6 py-4 font-bold">학생 이름</th>
                    <th scope="col" className="px-6 py-4 font-bold">학년</th>
                    <th scope="col" className="px-6 py-4 font-bold">전공</th>
                    <th scope="col" className="px-6 py-4 font-bold">진행 상태</th>
                    <th scope="col" className="px-6 py-4 font-bold text-center">최신 점수</th>
                    <th scope="col" className="px-6 py-4 font-bold text-center">최근 향상도</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {processedStudents.map((student) => (
                    <tr
                      key={student.id}
                      className={`group cursor-pointer transition-all ${
                        activeStudentId === student.id
                          ? 'bg-primary-lightest/80 border-l-4 border-primary text-primary'
                          : 'hover:bg-primary-lightest/50'
                      }`}
                      onClick={() => {
                        setActiveStudentId(student.id);
                        onSelectStudent(student.id);
                      }}
                    >
                      <td className="px-6 py-4 font-semibold text-slate-800 group-hover:text-primary">{student.name}</td>
                      <td className="px-6 py-4">{student.grade}학년</td>
                      <td className="px-6 py-4 font-medium text-slate-700">{student.major}</td>
                      <td className="px-6 py-4">
                        {student.completed ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold text-green-800 bg-green-100">완료</span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold text-slate-600 bg-slate-100">진행 전</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-center font-mono text-slate-800 font-bold">{student.latestScore}/100</td>
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
      </Card>
    </div>
  );
};

export default TeacherDashboard;
