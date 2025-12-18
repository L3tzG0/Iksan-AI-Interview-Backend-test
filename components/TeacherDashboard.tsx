import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { StudentSummary, StudentGoal, User, GeneratedStudentAccount } from '../types';
import Card from './Card';
import Button from './ui/Button';
import { FilterIcon, SortIcon, SearchIcon, ChartIcon } from './icons';
import { useToast } from './ui/Toast';
import { bulkCreateStudents, createStudent, fetchUsers, type BulkRowError, type CreateStudentPayload } from '../services/studentService';

interface TeacherDashboardProps {
  currentUser: User;
  onSelectStudent: (studentId: string) => void;
}

const TeacherDashboard: React.FC<TeacherDashboardProps> = ({ currentUser, onSelectStudent }) => {
  const navigate = useNavigate();
  const { tab } = useParams<{ tab?: string }>();
  const tabFromRoute: 'completed' | 'manage' = tab === '2' ? 'manage' : 'completed';

  const templateCsvContent =
    '\ufeff이름,학교,학년,전공,반\n김학생,스프링필드고등학교,2,컴퓨터공학,A1\n박학생,리버데일고등학교,3,경영학,B2';
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [activeTab, setActiveTab] = useState<'completed' | 'manage'>(tabFromRoute);
  const [sortOption, setSortOption] = useState<'recent' | 'score' | 'growth'>('recent');
  const [gradeFilter, setGradeFilter] = useState<number | 'all'>('all');
  const [goalFilter, setGoalFilter] = useState<'all' | StudentGoal>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeStudentId, setActiveStudentId] = useState<string | null>(null);
  const [newStudent, setNewStudent] = useState<{ name: string; school: string; gradeYear: 1 | 2 | 3; major: string; classLabel: string }>(
    {
      name: '',
      school: currentUser.schoolName || '',
      gradeYear: 1,
      major: '',
      classLabel: '',
    }
  );
  const [generatedAccount, setGeneratedAccount] = useState<GeneratedStudentAccount | null>(null);
  const [bulkFileName, setBulkFileName] = useState('');
  const [bulkPreview, setBulkPreview] = useState<GeneratedStudentAccount[]>([]);
  const [bulkErrors, setBulkErrors] = useState<string[]>([]);
  const [backendErrors, setBackendErrors] = useState<BulkRowError[]>([]);
  const [bulkUploadSummary, setBulkUploadSummary] = useState<{ total: number; created: number; failed: number } | null>(null);
  const [isUploadingCsv, setIsUploadingCsv] = useState(false);
  const [bulkSelectedFile, setBulkSelectedFile] = useState<File | null>(null);
  const [isLoadingStudents, setIsLoadingStudents] = useState(false);
  const [isCreatingStudent, setIsCreatingStudent] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const { addToast } = useToast();

  const normalizeCode = (value: string, fallback: string) => {
    const letters = value.trim().toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 3);
    return letters || fallback;
  };

  useEffect(() => {
    setActiveTab(tabFromRoute);
  }, [tabFromRoute]);

  useEffect(() => {
    let isMounted = true;
    const loadStudents = async () => {
      setIsLoadingStudents(true);
      try {
        const res = await fetchUsers({ role: 'student', page: 1, pageSize: 200 });
        if (!isMounted) return;
        const hydrated: StudentSummary[] = res.data.map((u) => ({
          id: u.studentId || u.id,
          name: u.name,
          major: u.major || '',
          schoolName: u.schoolName || '',
          grade: u.grade ?? 0,
          latestScore: 0,
          improvement: 0,
          completed: false,
          intent: 'university',
          tempPassword: u.tempPassword,
        }));
        setStudents(hydrated);
      } catch (err: any) {
        if (isMounted) {
          const message = err?.message || '학생 목록을 불러오지 못했습니다.';
          addToast(message, 'error');
        }
      } finally {
        if (isMounted) setIsLoadingStudents(false);
      }
    };

    loadStudents();
    return () => {
      isMounted = false;
    };
  }, [addToast]);

  const triggerCsvPicker = () => fileInputRef.current?.click();
  const downloadTemplate = () => {
    const blob = new Blob([templateCsvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'student_bulk_template.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const generateStudentId = (school: string, major: string) => {
    const schoolCode = normalizeCode(school, 'SCH');
    const majorCode = normalizeCode(major, 'GEN');
    const existingCount = students.filter(
      (s) => normalizeCode(s.schoolName, 'SCH') === schoolCode && normalizeCode(s.major, 'GEN') === majorCode
    ).length;
    const nextNumber = (existingCount + 1).toString().padStart(4, '0');
    return `${schoolCode}${majorCode}${nextNumber}`;
  };

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = newStudent.name.trim();
    const trimmedMajor = newStudent.major.trim();
    const trimmedSchool = (newStudent.school || currentUser.schoolName || '').trim();
    const trimmedClassLabel = newStudent.classLabel.trim();

    if (!trimmedName || !trimmedMajor) {
      addToast('학생 이름과 전공을 입력해주세요.', 'error');
      return;
    }

    const payload: CreateStudentPayload = {
      full_name: trimmedName,
      school_name: trimmedSchool || undefined,
      major_name: trimmedMajor,
      class_name: trimmedClassLabel || undefined,
      grade_level: newStudent.gradeYear,
    };

    setIsCreatingStudent(true);
    try {
      const created = await createStudent(payload);
      const account: GeneratedStudentAccount = {
        name: created.fullName || trimmedName,
        school: trimmedSchool || currentUser.schoolName || '',
        gradeYear: newStudent.gradeYear,
        major: trimmedMajor,
        classLabel: trimmedClassLabel,
        studentId: created.studentId,
        tempPassword: created.password || '',
      };
      setGeneratedAccount(account);

      const summary: StudentSummary = {
        id: created.studentId,
        name: account.name,
        major: account.major,
        schoolName: account.school,
        grade: account.gradeYear,
        latestScore: 0,
        improvement: 0,
        completed: false,
        intent: 'university',
        tempPassword: account.tempPassword,
      };
      setStudents((prev) => [summary, ...prev]);
      setNewStudent((prev) => ({ ...prev, name: '', major: '', classLabel: '' }));
      addToast('학생이 추가되었습니다.', 'success');
    } catch (err: any) {
      const message = err?.message || '학생을 추가할 수 없어요.';
      addToast(message, 'error');
    } finally {
      setIsCreatingStudent(false);
    }
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
      const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);

      const errors: string[] = [];
      const preview: GeneratedStudentAccount[] = [];
      const counters: Record<string, number> = {};

      const ensureCounter = (school: string, major: string) => {
        const key = `${normalizeCode(school, 'SCH')}-${normalizeCode(major, 'GEN')}`;
        if (!(key in counters)) {
          const existing = students.filter(
            (s) => normalizeCode(s.schoolName, 'SCH') === normalizeCode(school, 'SCH') && normalizeCode(s.major, 'GEN') === normalizeCode(major, 'GEN')
          ).length;
          counters[key] = existing;
        }
        counters[key] += 1;
        return counters[key];
      };

      lines.forEach((line, idx) => {
        const cols = line.split(',').map((c) => c.trim());
        if (cols.length < 4) {
          errors.push(`${idx + 1}행: 필수 컬럼 누락 (이름, 학교, 학년, 전공)`);
          return;
        }
        const [name, school, gradeStr, major, classLabel = ''] = cols;
        const gradeYear = Number(gradeStr) as 1 | 2 | 3;
        if (!name || !school || !major || ![1, 2, 3].includes(gradeYear)) {
          errors.push(`${idx + 1}행: 데이터가 올바르지 않습니다.`);
          return;
        }
        const number = ensureCounter(school, major);
        const studentId = `${normalizeCode(school, 'SCH')}${normalizeCode(major, 'GEN')}${number.toString().padStart(4, '0')}`;
        const tempPassword = `PW${Math.floor(Math.random() * 9999).toString().padStart(4, '0')}`;
        preview.push({ name, school, gradeYear, major, classLabel, studentId, tempPassword });
      });

      setBulkErrors(errors);
      setBulkPreview(preview);
    };
    reader.onerror = () => {
      setBulkErrors(['CSV 파일을 불러오지 못했습니다.']);
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

  const stats = useMemo(() => {
    if (students.length === 0) return { avgScore: 0, completed: 0 };
    const completed = students.filter((s) => s.completed).length;
    const avgScore = students.reduce((sum, s) => sum + s.latestScore, 0) / students.length;
    return { avgScore: Math.round(avgScore), completed };
  }, [students]);

  const gradeOptions = useMemo(() => Array.from(new Set(students.map((s) => s.grade))).sort((a, b) => a - b), [students]);

  const processedAll = useMemo(() => {
    let filtered = [...students];
    if (searchTerm.trim()) filtered = filtered.filter((s) => s.name.toLowerCase().includes(searchTerm.toLowerCase()));

    const sorted = [...filtered];
    if (sortOption === 'score') sorted.sort((a, b) => b.latestScore - a.latestScore);
    else if (sortOption === 'growth') sorted.sort((a, b) => b.improvement - a.improvement);
    else sorted.sort((a, b) => a.name.localeCompare(b.name));
    return sorted;
  }, [students, searchTerm, sortOption]);

  const processedCompleted = useMemo(() => {
    const filtered = gradeFilter === 'all' ? students : students.filter((s) => s.grade === gradeFilter);
    return filtered.filter((s) => s.completed);
  }, [students, gradeFilter]);

  const FilterControls = ({
    compact,
    showGrade = true,
    showGoal = true,
  }: {
    compact?: boolean;
    showGrade?: boolean;
    showGoal?: boolean;
  }) => (
    <div className={`flex flex-wrap gap-3 items-center ${compact ? 'justify-end' : ''}`}>
      {showGrade && (
        <label className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-full font-semibold text-xs">
          <ChartIcon className="w-4 h-4 text-primary" />
          <select
            value={gradeFilter === 'all' ? 'all' : gradeFilter}
            onChange={(e) => setGradeFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))}
            className="bg-transparent focus:outline-none"
          >
            <option value="all">전체 학년</option>
            {gradeOptions.map((grade) => (
              <option key={grade} value={grade}>
                {grade}학년
              </option>
            ))}
          </select>
        </label>
      )}
      {showGoal && (
        <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-full font-semibold text-xs">
          <FilterIcon className="w-4 h-4 text-primary" />
          <div className="flex gap-1">
            {[
              { value: 'all', label: '전체' },
              { value: 'work', label: 'Job Prep' },
              { value: 'university', label: 'Uni Prep' },
            ].map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setGoalFilter(opt.value as typeof goalFilter)}
                className={`px-2 py-1 rounded-full border ${
                  goalFilter === opt.value
                    ? 'bg-primary text-white border-primary'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-primary/60'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}
      <label className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 border border-slate-200 rounded-full font-semibold text-xs">
        <SortIcon className="w-4 h-4 text-primary" />
        <select
          value={sortOption}
          onChange={(e) => setSortOption(e.target.value as typeof sortOption)}
          className="bg-transparent focus:outline-none"
        >
          <option value="recent">이름순</option>
          <option value="score">점수순</option>
          <option value="growth">개선율</option>
        </select>
      </label>
    </div>
  );

  return (
    <div className="space-y-8 mx-auto animate-fadeIn container">
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
              <p className="mt-2 font-bold text-primary text-3xl">{students.length}</p>
              <p className="text-slate-500 text-xs">등록된 전체 학생</p>
            </div>
            <div className="bg-white/90 shadow-soft p-4 border border-white/70 rounded-[18px]">
              <p className="text-slate-400 text-xs uppercase">완료</p>
              <p className="mt-2 font-bold text-primary text-3xl">{stats.completed}</p>
              <p className="text-slate-500 text-xs">면접 완료 학생</p>
            </div>
            <div className="bg-white/90 shadow-soft p-4 border border-white/70 rounded-[18px]">
              <p className="text-slate-400 text-xs uppercase">평균 점수</p>
              <p className="mt-2 font-bold text-primary text-3xl">{stats.avgScore}</p>
              <p className="text-slate-500 text-xs">최근 평균 점수</p>
            </div>
          </div>
        </div>
      </section>

      <Card className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-slate-100 border-b">
          {[{ key: 'completed', label: '완료 학생' }, { key: 'manage', label: '학생 관리' }].map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => {
                const nextTab = tab.key as typeof activeTab;
                const tabSegment = nextTab === 'manage' ? '2' : '1';
                navigate(`/teacher/dashboard/${tabSegment}`, { replace: true });
              }}
              className={`px-3 py-2 text-sm font-semibold rounded-full transition-colors ${
                activeTab === tab.key ? 'bg-primary text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'completed' && (
          <div className="space-y-4">
            <div className="flex lg:flex-row flex-col lg:items-center gap-4">
              <div className="flex flex-1 items-center gap-3 bg-white/90 shadow-inner shadow-white/60 px-4 py-2 border border-slate-200 rounded-full">
                <SearchIcon className="w-5 h-5 text-primary" />
                <input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="학생 이름 검색"
                  className="flex-1 bg-transparent focus:outline-none text-sm"
                />
              </div>
              <FilterControls />
            </div>

            {processedCompleted.length === 0 ? (
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
                        setActiveStudentId(student.id);
                        onSelectStudent(student.id);
                      }}
                    >
                      <td className="px-6 py-4 font-semibold text-slate-800 group-hover:text-primary">{student.name}</td>
                      <td className="px-6 py-4">{student.grade}학년</td>
                      <td className="px-6 py-4 font-medium text-slate-700">{student.major}</td>
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
        )}

        {activeTab === 'manage' && (
          <div className="space-y-6">
            <div className="flex lg:flex-row flex-col lg:justify-between lg:items-center gap-3">
              <div>
                <p className="font-semibold text-primary-text text-xs uppercase tracking-[0.25em]">Student Accounts</p>
                <h2 className="font-bold text-slate-900 text-xl">학생 계정 생성</h2>
                <p className="text-slate-500 text-sm">학교 코드 + 전공 코드 + 4자리 번호로 학생 ID를 만듭니다. (예: 001000100001)</p>
              </div>
              {generatedAccount && (
                <div className="bg-primary-lightest/70 px-4 py-3 border border-primary/30 rounded-2xl text-slate-800 text-sm">
                  <p className="font-semibold text-primary">새로 생성됨</p>
                  <p className="font-mono text-slate-900">ID: {generatedAccount.studentId}</p>
                  <p className="font-mono text-slate-900">PW: {generatedAccount.tempPassword}</p>
                  <p className="mt-1 text-slate-500 text-xs">첫 로그인 후 비밀번호를 변경하도록 안내하세요.</p>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <form className="gap-3 grid sm:grid-cols-2" onSubmit={handleCreateStudent}>
                <label className="space-y-1 font-semibold text-slate-700 text-sm">
                  이름
                  <input
                    value={newStudent.name}
                    onChange={(e) => setNewStudent((prev) => ({ ...prev, name: e.target.value }))}
                    className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
                    placeholder="예: 홍길동"
                    required
                  />
                </label>
                <label className="space-y-1 font-semibold text-slate-700 text-sm">
                  학교
                  <input
                    value={newStudent.school}
                    onChange={(e) => setNewStudent((prev) => ({ ...prev, school: e.target.value }))}
                    className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
                    placeholder="예: 부산자동차고등학교"
                  />
                </label>
                <label className="space-y-1 font-semibold text-slate-700 text-sm">
                  학년
                  <select
                    value={newStudent.gradeYear}
                    onChange={(e) => setNewStudent((prev) => ({ ...prev, gradeYear: Number(e.target.value) as 1 | 2 | 3 }))}
                    className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
                  >
                    {[1, 2, 3].map((year) => (
                      <option key={year} value={year}>{year}학년</option>
                    ))}
                  </select>
                </label>
                <label className="space-y-1 font-semibold text-slate-700 text-sm">
                  전공 / 반
                  <input
                    value={newStudent.major}
                    onChange={(e) => setNewStudent((prev) => ({ ...prev, major: e.target.value }))}
                    className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
                    placeholder="예: 전자과, 자동차과"
                    required
                  />
                </label>
                <label className="space-y-1 font-semibold text-slate-700 text-sm">
                  Class Label (선택)
                  <input
                    value={newStudent.classLabel}
                    onChange={(e) => setNewStudent((prev) => ({ ...prev, classLabel: e.target.value }))}
                    className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
                    placeholder="예: A1, B3"
                  />
                </label>
                <div className="flex items-end">
                  <Button type="submit" className="w-full" disabled={isCreatingStudent}>
                    {isCreatingStudent ? '추가 중...' : '학생 추가'}
                  </Button>
                </div>
              </form>

              <div className="space-y-3">
                <div className="bg-slate-50/70 p-4 border border-slate-200 rounded-2xl">
                  <p className="mb-1 font-semibold text-slate-800 text-sm">CSV 업로드</p>
                  <p className="mb-3 text-slate-500 text-xs">여러 학생을 한 번에 등록합니다.</p>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button variant="secondary" onClick={downloadTemplate} className="text-sm">
                      CSV 템플릿 다운로드
                    </Button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="hidden"
                      accept=".csv"
                      onChange={(e) => handleBulkUpload(e.target.files?.[0])}
                    />
                    <Button variant="secondary" onClick={triggerCsvPicker} className="text-sm">
                      CSV 선택하기
                    </Button>
                    <span className="text-slate-500 text-xs">{bulkFileName || '선택된 파일 없음'}</span>
                  </div>
                  {bulkErrors.length > 0 && (
                    <div className="space-y-1 mt-3 text-red-600 text-xs">
                      {bulkErrors.map((err, idx) => (
                        <p key={idx}>- {err}</p>
                      ))}
                    </div>
                  )}
                  {bulkPreview.length > 0 && (
                    <div className="space-y-2 mt-3">
                      <p className="font-semibold text-slate-700 text-xs">Preview ({bulkPreview.length})</p>
                      <div className="bg-white border border-slate-200 rounded-lg max-h-56 overflow-auto">
                        <table className="w-full text-xs">
                          <thead className="bg-slate-50 text-slate-500">
                            <tr>
                              <th className="px-2 py-1 text-left">이름</th>
                              <th className="px-2 py-1 text-left">학교</th>
                              <th className="px-2 py-1 text-left">전공</th>
                              <th className="px-2 py-1 text-left">ID</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {bulkPreview.slice(0, 5).map((row) => (
                              <tr key={row.studentId}>
                                <td className="px-2 py-1">{row.name}</td>
                                <td className="px-2 py-1">{row.school}</td>
                                <td className="px-2 py-1">{row.major}</td>
                                <td className="px-2 py-1 font-mono text-primary">{row.studentId}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {bulkPreview.length > 5 && (
                          <p className="px-2 py-1 text-[10px] text-slate-400">+ {bulkPreview.length - 5}개 더</p>
                        )}
                      </div>
                      <Button onClick={submitBulkUpload} disabled={!bulkSelectedFile || isUploadingCsv} className="w-full text-sm">
                        {isUploadingCsv ? '업로드 중...' : 'CSV 업로드'}
                      </Button>
                      {backendErrors.length > 0 && (
                        <div className="text-red-600 text-xs">
                          <p className="font-semibold">Backend Errors</p>
                          <ul className="list-disc list-inside">
                            {backendErrors.map((err, idx) => (
                              <li key={idx}>{err.message}</li>
                            ))}
                          </ul>
                          <Button variant="secondary" onClick={downloadBackendErrors} className="mt-2 text-xs">
                            오류 다운로드
                          </Button>
                        </div>
                      )}
                      {bulkUploadSummary && (
                        <div className="text-slate-600 text-xs">
                          <p className="font-semibold text-primary">업로드 결과</p>
                          <p>{bulkUploadSummary.created}/{bulkUploadSummary.total} 개 등록</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <p className="font-semibold text-slate-800 text-sm">전체 학생 목록</p>
              <div className="flex lg:flex-row flex-col lg:items-center gap-4">
                <div className="flex flex-1 items-center gap-3 bg-white/90 shadow-inner shadow-white/60 px-4 py-2 border border-slate-200 rounded-full">
                  <SearchIcon className="w-5 h-5 text-primary" />
                  <input
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="학생 이름 검색"
                    className="flex-1 bg-transparent focus:outline-none text-sm"
                  />
                </div>
                <FilterControls compact showGrade={false} showGoal={false} />
              </div>

              <div className="bg-white shadow-soft border border-slate-100 rounded-[20px] overflow-hidden">
                <div className="flex flex-wrap items-center gap-3 bg-slate-50/80 px-6 py-3 border-slate-100 border-b text-slate-500 text-xs">
                  <span className="inline-flex items-center gap-2"><span className="bg-green-400 border border-green-600 rounded-full w-3 h-3"></span>완료</span>
                  <span className="inline-flex items-center gap-2"><span className="bg-slate-200 border border-slate-400 rounded-full w-3 h-3"></span>진행 중</span>
                  <span className="ml-auto text-slate-400">총 {processedAll.length}명</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-slate-600 text-sm text-left">
                    <thead className="bg-slate-50 border-slate-200 border-b text-slate-500 text-xs uppercase">
                      <tr>
                        <th className="px-6 py-4 font-bold">이름</th>
                        <th className="px-6 py-4 font-bold">전공</th>
                        <th className="px-6 py-4 font-bold">로그인 ID</th>
                        <th className="px-6 py-4 font-bold">임시 비밀번호</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {isLoadingStudents && processedAll.length === 0 && (
                        <tr>
                          <td colSpan={4} className="px-6 py-6 text-slate-400 text-center">불러오는 중...</td>
                        </tr>
                      )}
                      {processedAll.map((student) => (
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
                          <td className="px-6 py-4 font-medium text-slate-700">{student.major}</td>
                          <td className="px-6 py-4 font-mono font-semibold text-primary">{student.id}</td>
                          <td className="px-6 py-4 font-mono text-slate-700">{student.tempPassword || '—'}</td>
                        </tr>
                      ))}
                      {!isLoadingStudents && processedAll.length === 0 && (
                        <tr>
                          <td colSpan={4} className="px-6 py-6 text-slate-400 text-center">표시할 학생이 없습니다.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default TeacherDashboard;

