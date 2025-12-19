import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { GeneratedStudentAccount, StudentSummary, User } from '../types';
import type {
  AccountManagementSectionProps,
  FilterControlsProps,
  GoalFilter,
  GradeFilter,
  NewStudentInput,
  SortOption,
  TeacherDashboardProps,
} from '../types/teacherDashboard';
import Card from './Card';
import { useToast } from './ui/Toast';
import {
  bulkCreateStudents,
  createStudent,
  fetchUsers,
  fetchAllSessionsForTeacherAndAdminRole,
  type BulkRowError,
  type CreateStudentPayload,
  type NormalizedSessionSummary,
} from '../services/studentService';
import AccountManagementSection from './teacher-dashboard/AccountManagementSection';
import CompletedSessionsSection from './teacher-dashboard/CompletedSessionsSection';
import DashboardHero from './teacher-dashboard/DashboardHero';
import TabSwitcher from './teacher-dashboard/TabSwitcher';

const TeacherDashboard: React.FC<TeacherDashboardProps> = ({ currentUser }) => {
  const navigate = useNavigate();
  const { tab } = useParams<{ tab?: string }>();
  const tabFromRoute: 'completed' | 'manage' = tab === '2' ? 'manage' : 'completed';
  const showSchoolField = currentUser.role === 'admin';

  const templateCsvContent =
    '\ufeff이름,학교,학년,전공,반\n김학생,스프링필드고등학교,2,컴퓨터공학,A1\n박학생,리버데일고등학교,3,경영학,B2';
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [activeTab, setActiveTab] = useState<'completed' | 'manage'>(tabFromRoute);
  const [sortOption, setSortOption] = useState<SortOption>('recent');
  const [gradeFilter, setGradeFilter] = useState<GradeFilter>('all');
  const [goalFilter, setGoalFilter] = useState<GoalFilter>('all');
  const [newStudent, setNewStudent] = useState<NewStudentInput>({
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
  const [bulkStudentsPayload, setBulkStudentsPayload] = useState<CreateStudentPayload[]>([]);
  const [isLoadingStudents, setIsLoadingStudents] = useState(false);
  const [isCreatingStudent, setIsCreatingStudent] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const { addToast } = useToast();

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
          status: 'in_progress',
          intent: 'university',
          tempPassword: u.tempPassword,
        }));

        // Merge the freshly hydrated user list with any session-derived student state
        // to avoid clobbering completed/score info when the requests resolve out of order.
        setStudents((prev) => {
          const byId = new Map(prev.map((s) => [s.id, s]));

          hydrated.forEach((student) => {
            const existing = byId.get(student.id);
            const merged: StudentSummary = {
              ...student,
              ...existing,
              latestScore: existing?.latestScore ?? student.latestScore,
              improvement: existing?.improvement ?? student.improvement,
              completed: existing?.completed ?? student.completed,
              status: existing?.status ?? student.status,
              tempPassword: student.tempPassword || existing?.tempPassword,
              sessionId: existing?.sessionId ?? existing?.session_id ?? student.sessionId,
              session_id: existing?.session_id ?? existing?.sessionId ?? student.session_id,
            };
            byId.set(student.id, merged);
          });

          return Array.from(byId.values());
        });
      } catch (err: any) {
        if (isMounted) {
          const message = err?.message || '학생 목록을 불러오지 못했습니다.';
          // addToast(message, 'error');
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

  const mergeSessionsIntoStudents = (sessionItems: NormalizedSessionSummary[]) => {
    setStudents((prev) => {
      const byId = new Map(prev.map((s) => [s.id, s]));

      sessionItems.forEach((session) => {
        const studentId = session.studentIdentifier || session.studentName || session.id;
        if (!studentId) return;

        const existing = byId.get(String(studentId));
        const completed = (session.status || '').toLowerCase() === 'completed' || Boolean(session.completedAt);
        const latestScore = typeof session.totalScore === 'number' ? Math.round(session.totalScore) : existing?.latestScore ?? 0;
        const gradeLevel = typeof session.gradeLevel === 'number' ? session.gradeLevel : existing?.grade ?? 0;
        const sessionIdValue = session.id ? String(session.id) : existing?.sessionId || existing?.session_id;

        const merged: StudentSummary = {
          id: String(studentId),
          name: session.studentName || existing?.name || '이름 없음',
          major: session.majorName || existing?.major || '',
          schoolName: session.schoolName || existing?.schoolName || '',
          grade: gradeLevel,
          latestScore,
          improvement: existing?.improvement ?? 0,
          completed: completed || existing?.completed || false,
          status: session.status || existing?.status || null,
          intent: session.interviewType || existing?.interviewType || null,
          tempPassword: existing?.tempPassword,
          sessionId: sessionIdValue,
          session_id: sessionIdValue,
        };

        byId.set(merged.id, merged);
      });

      return Array.from(byId.values());
    });
  };

  useEffect(() => {
    let isMounted = true;
    const loadSessions = async () => {
      try {
        const res = await fetchAllSessionsForTeacherAndAdminRole();
        if (!isMounted) return;
        // console.log('Fetched sessions for teacher/admin:', res);
        mergeSessionsIntoStudents(res.sessions);
      } catch (err: any) {
        if (isMounted) {
          const message = err?.message || '세션 데이터를 불러오지 못했습니다.';
          addToast(message, 'error');
        }
      }
    };

    loadSessions();
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
      ...(showSchoolField ? { school_name: trimmedSchool || undefined } : {}),
      major_name: trimmedMajor,
      class_name: trimmedClassLabel || undefined,
      grade_level: newStudent.gradeYear,
    };

    setIsCreatingStudent(true);
    try {
      const created = await createStudent(payload);
      const accountSchool = showSchoolField ? trimmedSchool : currentUser.schoolName || '';
      const account: GeneratedStudentAccount = {
        name: created.fullName || trimmedName,
        school: accountSchool,
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
        schoolName: accountSchool,
        grade: account.gradeYear,
        latestScore: 0,
        improvement: 0,
        completed: false,
        status: 'in_progress',
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
    setBulkStudentsPayload([]);

    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);

      // Skip the first row (header)
      if (lines.length <= 1) {
        setBulkErrors(['CSV 파일에 데이터 행이 없습니다.']);
        setBulkPreview([]);
        return;
      }
      const dataLines = lines.slice(1);

      const errors: string[] = [];
      const preview: GeneratedStudentAccount[] = [];
      const payloads: CreateStudentPayload[] = [];

      dataLines.forEach((line, idx) => {
        // idx is 0-based for data lines; add 2 to get the original CSV row number (header = 1)
        const rowNumber = idx + 2;
        const cols = line.split(',').map((c) => c.trim());
        if (cols.length < 4) {
          errors.push(`${rowNumber}행: 필수 컬럼 누락 (이름, 학교, 학년, 전공)`);
          return;
        }
        const [name, school, gradeStr, major, classLabel = ''] = cols;
        const gradeYear = Number(gradeStr) as 1 | 2 | 3;
        if (!name || !school || !major || ![1, 2, 3].includes(gradeYear)) {
          errors.push(`${rowNumber}행: 데이터가 올바르지 않습니다.`);
          return;
        }
        preview.push({ name, school, gradeYear, major, classLabel });
        payloads.push({
          full_name: name,
          school_name: school || currentUser.schoolName,
          major_name: major,
          class_name: classLabel || undefined,
          grade_level: gradeYear,
        });
      });

      setBulkErrors(errors);
      setBulkPreview(preview);
      setBulkStudentsPayload(errors.length ? [] : payloads);
    };
    reader.onerror = () => {
      setBulkErrors(['CSV 파일을 불러오지 못했습니다.']);
    };
    reader.readAsText(file);
  };

  const submitBulkUpload = async () => {
    if (!bulkStudentsPayload.length) {
      addToast('업로드할 CSV를 선택하거나 내용이 올바른지 확인해주세요.', 'error');
      return;
    }
    setIsUploadingCsv(true);
    setBackendErrors([]);
    setBulkUploadSummary(null);
    try {
      const res = await bulkCreateStudents(bulkStudentsPayload);
      setBulkUploadSummary({ total: res.total, created: res.created, failed: res.failed });
      if (res.errors?.length) {
        setBackendErrors(res.errors);
      }
      if (res.students?.length) {
        const createdSummaries: StudentSummary[] = res.students.map((s, idx) => {
          const payload = bulkStudentsPayload[idx] || {};
          const schoolName = payload.school_name || currentUser.schoolName || '';
          return {
            id: s.studentId,
            name: payload.full_name || s.fullName || '이름 없음',
            major: payload.major_name || '',
            schoolName,
            grade: payload.grade_level || 0,
            latestScore: 0,
            improvement: 0,
            completed: false,
            status: 'in_progress',
            intent: 'university',
            tempPassword: s.password,
          };
        });
        setStudents((prev) => [...createdSummaries, ...prev]);
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

  const handleTabChange = (nextTab: 'completed' | 'manage') => {
    setActiveTab(nextTab);
    const tabSegment = nextTab === 'manage' ? '2' : '1';
    navigate(`/teacher/dashboard/${tabSegment}`, { replace: true });
  };

  const handleNewStudentChange: AccountManagementSectionProps['onUpdateNewStudent'] = (field, value) => {
    setNewStudent((prev) => ({ ...prev, [field]: value }));
  };

  const filterControlsProps: FilterControlsProps = {
    gradeFilter,
    gradeOptions,
    sortOption,
    goalFilter,
    onGradeChange: setGradeFilter,
    onSortChange: setSortOption,
    onGoalChange: (goal) => setGoalFilter(goal),
  };

  return (
    <div className="space-y-8 mx-auto animate-fadeIn container">
      <DashboardHero
        test={students}
        currentUser={currentUser}
        studentCount={students.length}
        completedCount={stats.completed}
        averageScore={stats.avgScore}
      />

      <Card className="space-y-6">
        <TabSwitcher activeTab={activeTab} onChange={handleTabChange} />

        {activeTab === 'completed' && (
          <CompletedSessionsSection
            filterControlsProps={filterControlsProps}
          />
        )}

        {activeTab === 'manage' && (
          <AccountManagementSection
            newStudent={newStudent}
            onUpdateNewStudent={handleNewStudentChange}
            onCreateStudent={handleCreateStudent}
            isCreatingStudent={isCreatingStudent}
            generatedAccount={generatedAccount}
            showSchoolField={showSchoolField}
            bulkFileName={bulkFileName}
            bulkErrors={bulkErrors}
            bulkPreview={bulkPreview}
            backendErrors={backendErrors}
            bulkUploadSummary={bulkUploadSummary}
            isUploadingCsv={isUploadingCsv}
            onBulkFileChange={handleBulkUpload}
            onBulkSubmit={submitBulkUpload}
            onTemplateDownload={downloadTemplate}
            onCsvPicker={triggerCsvPicker}
            onBackendErrorDownload={downloadBackendErrors}
            filterControlsProps={filterControlsProps} 
            fileInputRef={fileInputRef}
            canSubmitBulkUpload={Boolean(bulkStudentsPayload.length) && !isUploadingCsv && bulkErrors.length === 0}
          />
        )}
      </Card>
    </div>
  );
};

export default TeacherDashboard;
