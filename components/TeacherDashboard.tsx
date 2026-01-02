import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import type { GeneratedStudentAccount, StudentSummary, User } from '../types';
import type {
  AccountManagementSectionProps,
  DashboardTab,
  NewStudentInput,
  TeacherDashboardProps,
} from '../types/teacherDashboard';
import Card from './Card';
import { useToast } from './ui/Toast';
import {
  bulkCreateStudents,
  createStudent,
  type BulkRowError,
  type CreateStudentPayload,
  type NormalizedSessionSummary,
} from '../services/studentService';
import AccountManagementSection from './teacher-dashboard/AccountManagementSection';
import CompletedSessionsSection from './teacher-dashboard/CompletedSessionsSection';
import DashboardHero from './teacher-dashboard/DashboardHero';

const TeacherDashboard: React.FC<TeacherDashboardProps> = ({ currentUser }) => {
  const navigate = useNavigate();
  const { tab } = useParams<{ tab?: string }>();
  const activeTab: DashboardTab = tab === '2' ? 'manage' : 'completed';
  const showSchoolField = currentUser.role === 'admin';

  // Template CSV is served from public/teacher_bulk_template.csv
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
  const [isCreatingStudent, setIsCreatingStudent] = useState(false);
  const [studentRefreshKey, setStudentRefreshKey] = useState(0);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const { addToast } = useToast();

  const triggerCsvPicker = () => fileInputRef.current?.click();
  const downloadTemplate = () => {
    const link = document.createElement('a');
    const isAdmin = currentUser.role === 'admin';
    link.href = isAdmin ? '/admin_bulk_template.csv' : '/teacher_bulk_template.csv';
    link.download = isAdmin ? '관리자_학생_템플릿.csv' : '교사_학생_템플릿.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
      setStudentRefreshKey((prev) => prev + 1);

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
        const minCols = showSchoolField ? 4 : 3;

        if (cols.length < minCols) {
          const missing = showSchoolField ? '이름, 학교, 학년, 전공' : '이름, 학년, 전공';
          errors.push(`${rowNumber}행: 필수 컬럼 누락 (${missing})`);
          return;
        }

        if (showSchoolField) {
          const [name, school, gradeStr, major, classLabel = ''] = cols;
          const gradeYear = Number(gradeStr) as 1 | 2 | 3;
          if (!name || !school || !major || ![1, 2, 3].includes(gradeYear)) {
            errors.push(`${rowNumber}행: 데이터가 올바르지 않습니다.`);
            return;
          }
          const previewSchool = school || currentUser.schoolName || '';
          preview.push({ name, school: previewSchool, gradeYear, major, classLabel });
          payloads.push({
            full_name: name,
            school_name: previewSchool,
            major_name: major,
            class_name: classLabel || undefined,
            grade_level: gradeYear,
          });
        } else {
          const [name, gradeStr, major, classLabel = ''] = cols;
          const gradeYear = Number(gradeStr) as 1 | 2 | 3;
          if (!name || !major || ![1, 2, 3].includes(gradeYear)) {
            errors.push(`${rowNumber}행: 데이터가 올바르지 않습니다.`);
            return;
          }
          const previewSchool = currentUser.schoolName || '';
          preview.push({ name, school: previewSchool, gradeYear, major, classLabel });
          payloads.push({
            full_name: name,
            major_name: major,
            class_name: classLabel || undefined,
            grade_level: gradeYear,
          });
        }
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
      setStudentRefreshKey((prev) => prev + 1);
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

  const handleNewStudentChange: AccountManagementSectionProps['onUpdateNewStudent'] = (field, value) => {
    setNewStudent((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-8 mx-auto animate-fadeIn">
      {/* <DashboardHero
        test={students}
        currentUser={currentUser}
        studentCount={students.length}
        completedCount={stats.completed}
        averageScore={stats.avgScore}
      /> */}

      <div className="flex flex-col">
        {activeTab === 'completed' && (
          <CompletedSessionsSection />
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
            fileInputRef={fileInputRef}
            canSubmitBulkUpload={Boolean(bulkStudentsPayload.length) && !isUploadingCsv && bulkErrors.length === 0}
            refreshKey={studentRefreshKey}
          />
        )}
      </div>
    </div>
  );
};

export default TeacherDashboard;
