import React, { useState, useEffect, useMemo, useRef } from 'react';
import { getTeacherDashboardData } from '../services/geminiService';
import type { StudentSummary, User, GeneratedStudentAccount } from '../types';
import Spinner from './Spinner';
import Card from './Card';
import { FilterIcon, SortIcon, SearchIcon, ChartIcon } from './icons';
import { bulkCreateStudents, type BulkRowError } from '../services/studentService';
import { useToast } from './ui/Toast';
import ProgressBar from './ui/ProgressBar';

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
  const [newStudent, setNewStudent] = useState<{ name: string; school: string; gradeYear: 1 | 2 | 3; major: string; classLabel: string }>({
    name: '',
    school: currentUser.schoolName || '',
    gradeYear: 1,
    major: '',
    classLabel: '',
  });
  const [generatedAccount, setGeneratedAccount] = useState<GeneratedStudentAccount | null>(null);
  const [bulkFileName, setBulkFileName] = useState('');
  const [bulkPreview, setBulkPreview] = useState<GeneratedStudentAccount[]>([]);
  const [bulkErrors, setBulkErrors] = useState<string[]>([]);
  const [backendErrors, setBackendErrors] = useState<BulkRowError[]>([]);
  const [bulkUploadSummary, setBulkUploadSummary] = useState<{ total: number; created: number; failed: number } | null>(null);
  const [isUploadingCsv, setIsUploadingCsv] = useState(false);
  const [bulkSelectedFile, setBulkSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const { addToast } = useToast();

  const normalizeCode = (value: string, fallback: string) => {
    const letters = value
      .trim()
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, '')
      .slice(0, 3);
    return letters || fallback;
  };

  const triggerCsvPicker = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const generateStudentId = (school: string, major: string) => {
    const schoolCode = normalizeCode(school, 'SCH');
    const majorCode = normalizeCode(major, 'GEN');
    const existingCount = students.filter(
      (s) =>
        normalizeCode(s.schoolName, 'SCH') === schoolCode &&
        normalizeCode(s.major, 'GEN') === majorCode
    ).length;
    const nextNumber = (existingCount + 1).toString().padStart(4, '0');
    return `${schoolCode}${majorCode}${nextNumber}`;
  };

  const handleCreateStudent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newStudent.name.trim() || !newStudent.major.trim()) {
      alert('학생 이름과 전공을 입력해주세요.');
      return;
    }
    const studentId = generateStudentId(newStudent.school || currentUser.schoolName, newStudent.major);
    const tempPassword = `PW${Math.floor(Math.random() * 9999).toString().padStart(4, '0')}`;
    const account: GeneratedStudentAccount = {
      name: newStudent.name.trim(),
      school: newStudent.school || currentUser.schoolName,
      gradeYear: newStudent.gradeYear,
      major: newStudent.major.trim(),
      classLabel: newStudent.classLabel.trim(),
      studentId,
      tempPassword,
    };
    setGeneratedAccount(account);
    const summary: StudentSummary = {
      id: studentId,
      name: account.name,
      major: account.major,
      schoolName: account.school,
      grade: account.gradeYear,
      latestScore: 0,
      improvement: 0,
      completed: false,
    };
    setStudents((prev) => [summary, ...prev]);
    setNewStudent((prev) => ({ ...prev, name: '', major: '', classLabel: '' }));
  };

  const handleBulkUpload = (file?: File) => {
    if (!file) return;
    setBulkFileName(file.name);
    setBulkErrors([]);
    setBulkPreview([]);
    setBackendErrors([]);
    setBulkUploadSummary(null);
    setBulkSelectedFile(file);

    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      const lines = text
        .split(/\r?\n/)
        .map((l) => l.trim())
        .filter(Boolean);

      const errors: string[] = [];
      const preview: GeneratedStudentAccount[] = [];
      const counters: Record<string, number> = {};

      const ensureCounter = (school: string, major: string) => {
        const key = `${normalizeCode(school, 'SCH')}-${normalizeCode(major, 'GEN')}`;
        if (!(key in counters)) {
          const existing = students.filter(
            (s) =>
              normalizeCode(s.schoolName, 'SCH') === normalizeCode(school, 'SCH') &&
              normalizeCode(s.major, 'GEN') === normalizeCode(major, 'GEN')
          ).length;
          counters[key] = existing;
        }
        counters[key] += 1;
        return counters[key];
      };

      lines.forEach((line, idx) => {
        const cols = line.split(',').map((c) => c.trim());
        if (cols.length < 4) {
          errors.push(`${idx + 1}행: 필수 컬럼 부족 (이름, 학교, 학년, 전공 필요)`);
          return;
        }
        const [name, school, gradeStr, major, classLabel = ''] = cols;
        const gradeYear = Number(gradeStr) as 1 | 2 | 3;
        if (!name || !school || !major || ![1, 2, 3].includes(gradeYear)) {
          errors.push(`${idx + 1}행: 값이 올바르지 않습니다.`);
          return;
        }
        const number = ensureCounter(school, major);
        const studentId = `${normalizeCode(school, 'SCH')}${normalizeCode(major, 'GEN')}${number.toString().padStart(4, '0')}`;
        const tempPassword = `PW${Math.floor(Math.random() * 9999).toString().padStart(4, '0')}`;
        preview.push({
          name,
          school,
          gradeYear,
          major,
          classLabel,
          studentId,
          tempPassword,
        });
      });

      setBulkErrors(errors);
      setBulkPreview(preview);
    };
    reader.onerror = () => {
      setBulkErrors(['CSV 파일을 읽는 중 오류가 발생했습니다.']);
    };
    reader.readAsText(file);
  };

  const submitBulkUpload = async () => {
    if (!bulkSelectedFile) return;
    setIsUploadingCsv(true);
    setBackendErrors([]);
    setBulkUploadSummary(null);
    try {
      const res = await bulkCreateStudents(bulkSelectedFile);
      setBulkUploadSummary({ total: res.total, created: res.created, failed: res.failed });
      if (res.errors?.length) {
        setBackendErrors(res.errors);
      }
      addToast(`CSV 업로드 완료: ${res.created}/${res.total}`, res.failed ? 'info' : 'success');
    } catch (err: any) {
      const message = err?.message || 'CSV 업로드에 실패했습니다.';
      addToast(message, 'error');
    } finally {
      setIsUploadingCsv(false);
    }
  };

  const downloadBackendErrors = () => {
    if (!backendErrors.length) return;
    const header = 'row,message,raw';
    const lines = backendErrors.map((err) => {
      const raw = Array.isArray(err.raw) ? err.raw.join(' ') : err.raw || '';
      const safeRaw = `${raw}`.replace(/"/g, '""');
      const safeMsg = err.message.replace(/"/g, '""');
      return `${err.row},"${safeMsg}","${safeRaw}"`;
    });
    const csv = [header, ...lines].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'csv-errors.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      const allStudents = await getTeacherDashboardData();

      const scopedStudents = currentUser.role === 'admin'
        ? allStudents
        : allStudents.filter((s) => {
            if (s.schoolName !== currentUser.schoolName) return false;
            if (currentUser.grade && s.grade !== currentUser.grade) return false;
            return true;
          });

      setStudents(scopedStudents);
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
      <div className="container mx-auto animate-pulse space-y-6">
        <div className="rounded-[28px] bg-gradient-to-r from-slate-50 via-white to-slate-50 border border-white/70 shadow-soft p-6 sm:p-8">
          <div className="h-4 w-32 bg-slate-200/80 rounded-full mb-3"></div>
          <div className="h-8 w-64 bg-slate-200/80 rounded-full mb-4"></div>
          <div className="grid sm:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-[18px] bg-white/90 border border-white/70 p-4 shadow-soft h-20">
                <div className="h-3 w-20 bg-slate-200/70 rounded-full mb-3"></div>
                <div className="h-6 w-16 bg-slate-200/80 rounded-full"></div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white/90 border border-slate-100 rounded-[20px] shadow-soft overflow-hidden">
          <div className="h-10 bg-slate-50/80 border-b border-slate-100"></div>
          <div className="divide-y divide-slate-100">
            {[...Array(4)].map((_, idx) => (
              <div key={idx} className="flex items-center justify-between px-6 py-4">
                <div className="h-4 w-32 bg-slate-200/80 rounded-full"></div>
                <div className="h-4 w-20 bg-slate-200/80 rounded-full"></div>
              </div>
            ))}
          </div>
        </div>
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

      <Card className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
          <div>
            <p className="text-xs font-semibold text-primary-text uppercase tracking-[0.25em]">Student Accounts</p>
            <h2 className="text-xl font-bold text-slate-900">학생 계정 발급</h2>
            <p className="text-sm text-slate-500">학생 ID는 학교 코드 + 전공 코드 + 4자리 번호로 생성됩니다. (예: ABCEGR0001)</p>
          </div>
          {generatedAccount && (
            <div className="bg-primary-lightest/70 border border-primary/30 rounded-2xl px-4 py-3 text-sm text-slate-800">
              <p className="font-semibold text-primary">최근 발급</p>
              <p className="font-mono text-slate-900">ID: {generatedAccount.studentId}</p>
              <p className="font-mono text-slate-900">PW: {generatedAccount.tempPassword}</p>
              <p className="text-xs text-slate-500 mt-1">첫 로그인 시 비밀번호 변경 안내를 표시해주세요.</p>
            </div>
          )}
        </div>

        <div className="grid lg:grid-cols-3 gap-4">
          <form className="lg:col-span-2 grid sm:grid-cols-2 gap-3" onSubmit={handleCreateStudent}>
            <label className="space-y-1 text-sm font-semibold text-slate-700">
              이름
              <input
                value={newStudent.name}
                onChange={(e) => setNewStudent((prev) => ({ ...prev, name: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="홍길동"
                required
              />
            </label>
            <label className="space-y-1 text-sm font-semibold text-slate-700">
              학교
              <input
                value={newStudent.school}
                onChange={(e) => setNewStudent((prev) => ({ ...prev, school: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="예: 익산고등학교"
              />
            </label>
            <label className="space-y-1 text-sm font-semibold text-slate-700">
              학년
              <select
                value={newStudent.gradeYear}
                onChange={(e) => setNewStudent((prev) => ({ ...prev, gradeYear: Number(e.target.value) as 1 | 2 | 3 }))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                {[1, 2, 3].map((year) => (
                  <option key={year} value={year}>{year}학년</option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm font-semibold text-slate-700">
              전공 / 계열
              <input
                value={newStudent.major}
                onChange={(e) => setNewStudent((prev) => ({ ...prev, major: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="예: 공학, 정보통신"
                required
              />
            </label>
            <label className="space-y-1 text-sm font-semibold text-slate-700">
              반/학급 (선택)
              <input
                value={newStudent.classLabel}
                onChange={(e) => setNewStudent((prev) => ({ ...prev, classLabel: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="예: 3반"
              />
            </label>
            <div className="flex items-end">
              <button
                type="submit"
                className="w-full sm:w-auto px-4 py-3 rounded-lg bg-primary text-white font-semibold shadow-soft hover:bg-primary-dark transition-colors"
              >
                학생 계정 생성
              </button>
            </div>
          </form>

          <div className="rounded-2xl border border-dashed border-slate-200 bg-white/90 p-4 space-y-3">
            <p className="text-sm font-semibold text-slate-800">CSV 일괄 업로드</p>
            <p className="text-xs text-slate-500">열 순서: 이름, 학교, 학년(1/2/3), 전공, 반(선택)</p>
            <label className="block">
              <input
                type="file"
                accept=".csv"
                ref={fileInputRef}
                onChange={(e) => handleBulkUpload(e.target.files?.[0] || undefined)}
                className="block w-full text-sm text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded file:border-0 file:bg-primary-lightest file:text-primary file:font-semibold"
              />
            </label>
            {bulkFileName && <p className="text-xs text-slate-500">선택한 파일: {bulkFileName}</p>}
            <p className="text-xs text-slate-500">업로드 후 생성된 ID/PW를 CSV로 내려받게 안내하세요.</p>
            {bulkErrors.length > 0 && (
              <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-3 space-y-1">
                {bulkErrors.map((err) => (
                  <p key={err}>{err}</p>
                ))}
              </div>
            )}
            {bulkPreview.length > 0 && (
              <div className="max-h-48 overflow-auto rounded-lg border border-slate-200">
                <table className="min-w-full text-xs text-slate-700">
                  <thead className="bg-slate-50 text-slate-500 uppercase">
                    <tr>
                      <th className="px-3 py-2 text-left">이름</th>
                      <th className="px-3 py-2 text-left">학교</th>
                      <th className="px-3 py-2 text-left">학년</th>
                      <th className="px-3 py-2 text-left">전공</th>
                      <th className="px-3 py-2 text-left">ID</th>
                      <th className="px-3 py-2 text-left">PW</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {bulkPreview.map((row, idx) => (
                      <tr key={`${row.studentId}-${idx}`}>
                        <td className="px-3 py-2">{row.name}</td>
                        <td className="px-3 py-2">{row.school}</td>
                        <td className="px-3 py-2">{row.gradeYear}학년</td>
                        <td className="px-3 py-2">{row.major}</td>
                        <td className="px-3 py-2 font-mono text-xs">{row.studentId}</td>
                        <td className="px-3 py-2 font-mono text-xs">{row.tempPassword}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {bulkUploadSummary && (
              <div className="text-xs text-slate-700 flex flex-wrap items-center gap-2">
                <span className="font-semibold">업로드 결과</span>
                <span className="px-2 py-1 rounded bg-green-50 text-green-700 font-semibold">{bulkUploadSummary.created}/{bulkUploadSummary.total} 추가</span>
                <span className={`px-2 py-1 rounded ${bulkUploadSummary.failed ? 'bg-rose-50 text-rose-700' : 'bg-slate-100 text-slate-600'}`}>
                  실패 {bulkUploadSummary.failed}
                </span>
              </div>
            )}
            {backendErrors.length > 0 && (
              <div className="max-h-40 overflow-auto rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 space-y-1">
                {backendErrors.map((err) => (
                  <div key={`${err.row}-${err.message}`} className="flex gap-2 items-start">
                    <span className="font-bold">#{err.row}</span>
                    <span className="flex-1">{err.message}</span>
                  </div>
                ))}
                <div className="flex gap-2 pt-2">
                  <button type="button" onClick={downloadBackendErrors} className="text-[11px] underline text-rose-700">
                    오류 CSV 다운로드
                  </button>
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setBulkPreview([]);
                  setBulkErrors([]);
                  setBackendErrors([]);
                  setBulkFileName('');
                  setBulkUploadSummary(null);
                  setBulkSelectedFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = '';
                }}
                className="text-xs px-3 py-2 rounded-lg border border-slate-200 text-slate-600 hover:border-primary"
              >
                초기화
              </button>
              <button
                type="button"
                className="text-xs px-3 py-2 rounded-lg bg-primary text-white font-semibold shadow-soft disabled:opacity-50 flex items-center gap-2"
                disabled={bulkPreview.length === 0 || isUploadingCsv}
                onClick={submitBulkUpload}
              >
                {isUploadingCsv ? "업로드 중..." : "CSV 업로드"}
              </button>
            </div>
          </div>
        </div>
      </Card>

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





