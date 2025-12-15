import React, { useMemo, useState, useRef } from 'react';
import Button from './ui/Button';
import ProgressBar from './ui/ProgressBar';
import { createStudent, bulkCreateStudents, type BulkRowError } from '../services/studentService';
import { useToast } from './ui/Toast';

interface AddStudentModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultSchool?: string;
}

const normalizeCode = (value: string, fallback: string) =>
  value
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .slice(0, 3) || fallback;

const AddStudentModal: React.FC<AddStudentModalProps> = ({ isOpen, onClose, defaultSchool }) => {
  const [name, setName] = useState('');
  const [school, setSchool] = useState(defaultSchool || '');
  const [gradeYear, setGradeYear] = useState<1 | 2 | 3>(1);
  const [major, setMajor] = useState('');
  const [classLabel, setClassLabel] = useState('');
  const [generatedId, setGeneratedId] = useState<string | null>(null);
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const [csvFileName, setCsvFileName] = useState('');
  const [csvSummary, setCsvSummary] = useState<{ total: number; valid: number } | null>(null);
  const [csvError, setCsvError] = useState<string | null>(null);
  const [selectedCsv, setSelectedCsv] = useState<File | null>(null);
  const [isBulkSaving, setIsBulkSaving] = useState(false);
  const [bulkMessage, setBulkMessage] = useState<string | null>(null);
  const [bulkErrors, setBulkErrors] = useState<BulkRowError[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const { addToast } = useToast();

  const canSave = useMemo(() => name.trim() && school.trim() && major.trim(), [name, school, major]);

  if (!isOpen) return null;

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!canSave) {
      setError('이름, 학교, 전공을 입력해주세요.');
      return;
    }
    setIsSaving(true);
    try {
      const res = await createStudent({
        full_name: name.trim(),
        school_name: school.trim(),
        major_name: major.trim(),
        class_name: classLabel.trim() || undefined,
        grade_level: gradeYear,
      });
      const studentId = res.studentId || res.student_id || res.id || `${normalizeCode(school, 'SCH')}${normalizeCode(major, 'GEN')}${Math.floor(Math.random() * 9000 + 1000)}`;
      const pw = res.tempPassword || res.password || `PW${Math.floor(Math.random() * 9000 + 1000)}`;
      setGeneratedId(studentId);
      setTempPassword(pw);
      addToast('ID/PW가 생성되었습니다.', 'success');
    } catch (err: any) {
      const message = err?.message || '학생을 생성할 수 없어요.';
      setError(message);
      addToast(message, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const resetForm = () => {
    setName('');
    setMajor('');
    setClassLabel('');
    setGeneratedId(null);
    setTempPassword(null);
    setError(null);
    setCsvFileName('');
    setCsvSummary(null);
    setCsvError(null);
    setSelectedCsv(null);
    setBulkMessage(null);
    setBulkErrors([]);
  };

  const handleCsvFile = (file?: File) => {
    if (!file) return;
    setSelectedCsv(file);
    setCsvFileName(file.name);
    setCsvError(null);
    setCsvSummary(null);
    setBulkMessage(null);
    setBulkErrors([]);
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      const lines = text
        .split(/\r?\n/)
        .map((l) => l.trim())
        .filter(Boolean);
      if (!lines.length) {
        setCsvError('비어 있는 CSV 입니다.');
        return;
      }
      let valid = 0;
      lines.forEach((line) => {
        const cols = line.split(',').map((c) => c.trim());
        if (cols.length >= 4 && ['1', '2', '3'].includes(cols[2])) valid += 1;
      });
      setCsvSummary({ total: lines.length, valid });
      if (valid === 0) setCsvError('형식: 이름, 학교, 학년(1/2/3), 전공, 반(선택)');
    };
    reader.onerror = () => setCsvError('CSV를 읽지 못했습니다.');
    reader.readAsText(file);
  };

  const triggerCsv = () => fileInputRef.current?.click();

  const handleBulkUpload = async () => {
    if (!selectedCsv) return;
    setIsBulkSaving(true);
    setBulkMessage(null);
    setCsvError(null);
    setBulkErrors([]);
    try {
      const res = await bulkCreateStudents(selectedCsv);
      const total = res?.total || csvSummary?.total || 0;
      const created = res?.created || csvSummary?.valid || 0;
      const failed = res?.failed ?? Math.max(total - created, 0);
      setBulkMessage(`업로드 결과: ${created}/${total} 추가, 실패 ${failed}`);
      if (res?.errors?.length) {
        setBulkErrors(res.errors);
      }
      addToast('CSV 업로드가 완료됐어요.', failed ? 'info' : 'success');
    } catch (err: any) {
      const message = err?.message || 'CSV 업로드에 실패했어요.';
      setCsvError(message);
      addToast(message, 'error');
    } finally {
      setIsBulkSaving(false);
    }
  };

  const handleDownloadErrors = () => {
    if (!bulkErrors.length) return;
    const header = 'row,message,raw';
    const rows = bulkErrors.map((e) => {
      const raw = Array.isArray(e.raw) ? e.raw.join(' ') : e.raw || '';
      const safeRaw = `${raw}`.replace(/\"/g, '""');
      const safeMessage = e.message.replace(/\"/g, '""');
      return `${e.row},"${safeMessage}","${safeRaw}"`;
    });
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'csv-errors.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm px-4">
      <div className="relative w-full max-w-xl rounded-2xl bg-white shadow-2xl border border-white/70 p-6 space-y-4 animate-softFadeUp">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold text-primary uppercase tracking-[0.2em]">학생 추가</p>
            <h3 className="text-xl font-bold text-slate-900 mt-1">ID/PW 생성</h3>
            <p className="text-sm text-slate-500">학교 코드 + 전공 코드 + 숫자로 ID를 만들어요.</p>
          </div>
          <button
            onClick={() => {
              resetForm();
              onClose();
            }}
            className="text-slate-400 hover:text-slate-700 text-lg font-bold"
            aria-label="close"
          >
            x
          </button>
        </div>

        <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-4 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-slate-800">CSV로 한번에 추가</p>
              <p className="text-xs text-slate-500">형식: 이름, 학교, 학년(1/2/3), 전공, 반(선택)</p>
            </div>
            <Button type="button" variant="secondary" onClick={triggerCsv} className="bg-white text-primary border border-primary/50">
              CSV 선택
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              aria-label="CSV 파일 선택"
              onChange={(e) => handleCsvFile(e.target.files?.[0] || undefined)}
            />
          </div>
          {csvFileName && (
            <p className="text-xs text-slate-600">
              선택한 파일: <span className="font-semibold">{csvFileName}</span>
              {csvSummary && `  · ${csvSummary.valid}/${csvSummary.total}행 유효`}
            </p>
          )}
          {csvError && <p className="text-xs text-red-600 font-semibold">{csvError}</p>}
          {!csvError && csvSummary && (
            <p className="text-xs text-green-700 font-semibold">미리보기에서 {csvSummary.valid}행을 추가할 수 있습니다.</p>
          )}
          {isBulkSaving && (
            <ProgressBar indeterminate tone="primary" label="CSV 업로드 중..." />
          )}
          <div className="flex gap-2 items-center flex-wrap">
            <Button
              type="button"
              variant="secondary"
              onClick={handleBulkUpload}
              disabled={!selectedCsv || !!csvError || isBulkSaving}
              className="bg-white text-primary border border-primary/50"
              isLoading={isBulkSaving}
            >
              CSV 업로드
            </Button>
            {bulkMessage && <span className="text-xs text-green-700 font-semibold">{bulkMessage}</span>}
            {bulkErrors.length > 0 && (
              <>
                <span className="text-xs text-red-600 font-semibold">{bulkErrors.length}건 실패</span>
                <Button type="button" variant="ghost" onClick={handleDownloadErrors} className="text-xs px-2 py-1">
                  오류 CSV 다운로드
                </Button>
              </>
            )}
          </div>
          {bulkErrors.length > 0 && (
            <div className="max-h-32 overflow-auto rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 space-y-1">
              {bulkErrors.map((err) => (
                <div key={`${err.row}-${err.message}`} className="flex gap-2">
                  <span className="font-bold">#{err.row}</span>
                  <span>{err.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <form className="space-y-3" onSubmit={handleGenerate}>
          <div className="grid sm:grid-cols-2 gap-3">
            <label className="space-y-1 text-sm font-semibold text-slate-700">
              이름
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="예: 홍길동"
                required
              />
            </label>
            <label className="space-y-1 text-sm font-semibold text-slate-700">
              학교
              <input
                value={school}
                onChange={(e) => setSchool(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="예: 이산고등학교"
                required
              />
            </label>
          </div>
          <div className="grid sm:grid-cols-3 gap-3">
            <label className="space-y-1 text-sm font-semibold text-slate-700">
              학년
              <select
                value={gradeYear}
                onChange={(e) => setGradeYear(Number(e.target.value) as 1 | 2 | 3)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                {[1, 2, 3].map((year) => (
                  <option key={year} value={year}>
                    {year}학년
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm font-semibold text-slate-700 sm:col-span-2">
              전공 / 학과
              <input
                value={major}
                onChange={(e) => setMajor(e.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="예: 소프트웨어"
                required
              />
            </label>
          </div>
          <label className="space-y-1 text-sm font-semibold text-slate-700">
            반/학급 (선택)
            <input
              value={classLabel}
              onChange={(e) => setClassLabel(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/30"
              placeholder="예: 3반"
            />
          </label>

          {error && <p className="text-sm text-red-600 font-semibold">{error}</p>}

          <div className="flex flex-wrap justify-end gap-2">
            <Button type="button" variant="secondary" onClick={resetForm} className="bg-white text-slate-600 border border-slate-200">
              초기화
            </Button>
            <Button type="submit" className="px-5" isLoading={isSaving} disabled={!canSave}>
              ID/PW 생성
            </Button>
          </div>
        </form>

        {generatedId && tempPassword && (
          <div className="rounded-xl border border-primary/30 bg-primary-lightest/60 p-4 space-y-2">
            <p className="text-sm font-semibold text-primary">생성된 계정</p>
            <p className="text-xs text-slate-500">학생에게 전달해 주세요.</p>
            <div className="flex flex-col sm:flex-row gap-3 text-sm font-mono">
              <span className="px-3 py-2 rounded-lg bg-white border border-slate-200 flex-1">ID: {generatedId}</span>
              <span className="px-3 py-2 rounded-lg bg-white border border-slate-200 flex-1">PW: {tempPassword}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AddStudentModal;
