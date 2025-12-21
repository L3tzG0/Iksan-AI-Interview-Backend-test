import { useCallback, useEffect, useRef, useState, type DragEvent, type FC } from 'react';
import type { AccountManagementSectionProps } from '../../types/teacherDashboard';
import type { User } from '../../types';
import Button from '../ui/Button';
import FilterControls from './FilterControls';
import SearchBar from './SearchBar';
import Spinner from '../Spinner';
import { fetchUsers } from '../../services/studentService';

const AccountManagementSection: FC<AccountManagementSectionProps> = ({
  newStudent,
  onUpdateNewStudent,
  onCreateStudent,
  isCreatingStudent,
  generatedAccount,
  showSchoolField,
  bulkFileName,
  bulkErrors,
  bulkPreview,
  backendErrors,
  bulkUploadSummary,
  isUploadingCsv,
  onBulkFileChange,
  onBulkSubmit,
  onTemplateDownload,
  onCsvPicker,
  onBackendErrorDownload,
  searchTerm,
  onSearch,
  isLoadingStudents,
  fileInputRef,
  canSubmitBulkUpload,
}) => {
  const [isDraggingFile, setIsDraggingFile] = useState(false);
  const [userList, setUserList] = useState<User[]>([]);
  const [page, setPage] = useState<number>(1);
  const PAGE_SIZE = 20;
  const [totalUsers, setTotalUsers] = useState<number | undefined>(undefined);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const dragCounter = useRef(0);

  const handleDragEnter = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current += 1;
    if (e.dataTransfer?.types.includes('Files')) {
      setIsDraggingFile(true);
    }
  }, []);

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = 'copy';
    }
    setIsDraggingFile(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current -= 1;
    if (dragCounter.current <= 0) {
      setIsDraggingFile(false);
      dragCounter.current = 0;
    }
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter.current = 0;
      setIsDraggingFile(false);
      const file = e.dataTransfer?.files?.[0];
      if (!file) return;
      if (file.type === 'text/csv' || file.name.toLowerCase().endsWith('.csv')) {
        onBulkFileChange(file);
      }
    },
    [onBulkFileChange]
  );

  useEffect(() => {
    let isActive = true;

    const loadUsers = async () => {
      setIsLoadingUsers(true);
      try {
        const result = await fetchUsers({
          role: 'student',
          page,
          pageSize: PAGE_SIZE,
          search: searchTerm,
        });
        if (!isActive) return;
        setUserList(result.data ?? []);
        setTotalUsers(typeof result.total === 'number' ? result.total : undefined);
      } catch (error) {
        console.error('학생 계정 목록을 불러오는 중 오류가 발생했습니다.', error);
        setUserList([]);
        setTotalUsers(undefined);
      } finally {
        if (isActive) {
          setIsLoadingUsers(false);
        }
      }
    };

    loadUsers();

    return () => {
      isActive = false;
    };
  }, [searchTerm, page]);

  // when search term changes, reset to first page
  useEffect(() => {
    if (page !== 1) setPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm]);

  const isStudentTableLoading = isLoadingUsers || isLoadingStudents;

  return (
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
      <form className="gap-3 grid sm:grid-cols-2" onSubmit={onCreateStudent}>
        <label className="space-y-1 font-semibold text-slate-700 text-sm">
          이름
          <input
            value={newStudent.name}
            onChange={(e) => onUpdateNewStudent('name', e.target.value)}
            className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
            placeholder="예: 홍길동"
            required
          />
        </label>
        {showSchoolField && (
          <label className="space-y-1 font-semibold text-slate-700 text-sm">
            학교
            <input
              value={newStudent.school}
              onChange={(e) => onUpdateNewStudent('school', e.target.value)}
              className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
              placeholder="예: 부산자동차고등학교"
            />
          </label>
        )}
        <label className="space-y-1 font-semibold text-slate-700 text-sm">
          학년
          <select
            value={newStudent.gradeYear}
            onChange={(e) => onUpdateNewStudent('gradeYear', Number(e.target.value) as 1 | 2 | 3)}
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
            onChange={(e) => onUpdateNewStudent('major', e.target.value)}
            className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
            placeholder="예: 전자과, 자동차과"
            required
          />
        </label>
        <label className="space-y-1 font-semibold text-slate-700 text-sm">
          Class Label (선택)
          <input
            value={newStudent.classLabel}
            onChange={(e) => onUpdateNewStudent('classLabel', e.target.value)}
            className="px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full"
            placeholder="예: A1, B3"
          />
        </label>
        <div className={`flex items-end ${!showSchoolField ? 'sm:col-span-2' : ''}`}>
          <Button type="submit" className="w-full" disabled={isCreatingStudent}>
            {isCreatingStudent ? '추가 중...' : '학생 추가'}
          </Button>
        </div>
      </form>

      <div className="space-y-3">
        <div
          className={`bg-slate-50/70 p-4 rounded-2xl border transition-all duration-200 ${
            isDraggingFile
              ? 'border-primary/60 bg-primary-lightest/70 shadow-[0_8px_30px_rgba(59,130,246,0.15)] scale-[1.01] border-dashed'
              : 'border-slate-200'
          }`}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <p className="mb-1 font-semibold text-slate-800 text-sm">CSV 업로드</p>
          <p className="mb-3 text-slate-500 text-xs">
            여러 학생을 한 번에 등록합니다. 파일을 드래그해 바로 놓거나 버튼으로 선택하세요.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="secondary" onClick={onTemplateDownload} className="text-sm">
              CSV 템플릿 다운로드
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".csv"
              onChange={(e) => onBulkFileChange(e.target.files?.[0])}
            />
            <Button variant="secondary" onClick={onCsvPicker} className="text-sm">
              CSV 선택하기
            </Button>
            <span className="text-slate-500 text-xs">{bulkFileName || '선택된 파일 없음'}</span>
          </div>
          {isDraggingFile && (
            <div className="flex items-center gap-2 bg-white/60 mt-3 px-3 py-2 border border-primary/30 rounded-xl font-semibold text-primary text-xs">
              <span className="inline-block bg-primary rounded-full w-2 h-2 animate-ping"></span>
              <span>CSV 파일을 여기에 놓으면 업로드가 시작됩니다.</span>
            </div>
          )}
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
                      <th className="px-2 py-1 text-left">학년</th>
                      <th className="px-2 py-1 text-left">전공</th>
                      <th className="px-2 py-1 text-left">반</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {bulkPreview.slice(0, 5).map((row, idx) => (
                      <tr key={`${row.name}-${idx}`}>
                        <td className="px-2 py-1">{row.name}</td>
                        <td className="px-2 py-1">{row.school}</td>
                        <td className="px-2 py-1">{row.gradeYear}</td>
                        <td className="px-2 py-1">{row.major}</td>
                        <td className="px-2 py-1">{row.classLabel}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {bulkPreview.length > 5 && (
                  <p className="px-2 py-1 text-[10px] text-slate-400">+ {bulkPreview.length - 5}개 더</p>
                )}
              </div>
              <Button onClick={onBulkSubmit} disabled={!canSubmitBulkUpload} className="w-full text-sm">
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
                  <Button variant="secondary" onClick={onBackendErrorDownload} className="mt-2 text-xs">
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
        <SearchBar value={searchTerm} onChange={onSearch} placeholder="학생 이름 검색" />
        {/* <FilterControls {...filterControlsProps} compact showGrade={false} showGoal={false} /> */}
      </div>

      <div className="bg-white shadow-soft border border-slate-100 rounded-[20px] overflow-hidden">
        {/* <div className="flex flex-wrap items-center gap-3 bg-slate-50/80 px-6 py-3 border-slate-100 border-b text-slate-500 text-xs">
          <span className="inline-flex items-center gap-2"><span className="bg-green-400 border border-green-600 rounded-full w-3 h-3"></span>완료</span>
          <span className="inline-flex items-center gap-2"><span className="bg-slate-200 border border-slate-400 rounded-full w-3 h-3"></span>진행 중</span>
          <span className="ml-auto text-slate-400">총 {userList.length}명</span>
        </div> */}
        <div className="overflow-x-auto">
          <table className="min-w-full text-slate-600 text-sm text-left">
            <thead className="bg-slate-50 border-slate-200 border-b text-slate-500 text-xs uppercase">
              <tr>
                <th className="px-6 py-4 font-bold">이름</th>
                <th className="px-6 py-4 font-bold">전공</th>
                <th className="px-6 py-4 font-bold">로그인 ID</th>
                <th className="px-6 py-4 font-bold">비밀번호</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isStudentTableLoading && userList.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-6 text-slate-400 text-center"><Spinner label="불러오는 중..." /></td>
                </tr>
              )}
              {userList.map((student) => (
                <tr
                  key={student.id}
                  className={`group cursor-pointer transition-all border-primary text-primary hover:bg-primary-lightest/80`}
                  onClick={() => { }}
                >
                  <td className="px-6 py-4 font-semibold text-slate-800 group-hover:text-primary">{student.name}</td>
                  <td className="px-6 py-4 font-medium text-slate-700">{student.major}</td>
                  <td className="px-6 py-4 font-mono font-semibold text-primary">{student.id}</td>
                  <td className="px-6 py-4 font-mono text-slate-700">{student.tempPassword || '—'}</td>
                </tr>
              ))}
              {!isStudentTableLoading && userList.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-6 text-slate-400 text-center">표시할 학생이 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {/* Pagination Controls */}
        <div className="px-4 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
          <div className="text-slate-500 text-xs">
            {typeof totalUsers === 'number' ? (
              (() => {
                const start = totalUsers === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
                const end = Math.min(page * PAGE_SIZE, totalUsers);
                return `표시 ${start} - ${end} / ${totalUsers}명`;
              })()
            ) : (
              `페이지 ${page}`
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || isStudentTableLoading}
            >
              이전
            </Button>
            <Button
              variant="secondary"
              onClick={() => setPage((p) => p + 1)}
              disabled={
                isStudentTableLoading || (typeof totalUsers === 'number' && page >= Math.ceil(totalUsers / PAGE_SIZE))
              }
            >
              다음
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
  );
};

export default AccountManagementSection;
