import React, { useState, useEffect, useCallback } from 'react';
import { fetchAllSessions, fetchStudentSessionDetail, StudentSessionResponse } from '../services/studentService';
import type { StudentDetail, StudentSession, StudentSessionDetail, InterviewReport } from '../types';
import Spinner from './Spinner';
import Card from './Card';
import { ArrowLeftIcon } from './icons';
import InterviewReportView from './InterviewReportView';
import Button from './ui/Button';

interface StudentDetailViewProps {
  studentId: string;
  onBack: () => void;
}

const StudentDetailView: React.FC<StudentDetailViewProps> = ({ studentId, onBack }) => {
  const [student, setStudent] = useState<StudentDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessions, setSessions] = useState<StudentSession[]>([]);
  const [isSessionsLoading, setIsSessionsLoading] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [selectedSessionReport, setSelectedSessionReport] = useState<InterviewReport | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [isSessionDetailLoading, setIsSessionDetailLoading] = useState(false);
  const [sessionDetailError, setSessionDetailError] = useState<string | null>(null);

  useEffect(() => {
    setStudent({
      id: studentId,
      name: '학생',
      major: '',
      schoolName: '',
      grade: 0,
      history: [],
    });
    setIsLoading(false);
  }, [studentId]);

  useEffect(() => {
    const loadSessions = async () => {
      setIsSessionsLoading(true);
      setSessionError(null);
      try {
        const data = await fetchAllSessions();
        const normalized = (data as StudentSessionResponse[])
          .filter((s) => String((s as any)?.student_id || (s as any)?.studentId || '') === String(studentId))
          .map((s, idx) => ({
            id: String((s as any).id || (s as any).session_id || idx + 1),
            startedAt: s.startedAt || (s as any).started_at,
            completedAt: s.completedAt || (s as any).completed_at,
            totalScore: s.totalScore ?? (s as any).total_score,
            status: s.status,
            intent: (s.intent as any) || undefined,
          }));
        setSessions(normalized);
      } catch (err: any) {
        console.error('Failed to fetch sessions', err);
        setSessionError(err?.message || 'Failed to load session history. Please try again.');
        setSessions([]);
      } finally {
        setIsSessionsLoading(false);
      }
    };
    loadSessions();
  }, [studentId]);

  const handleViewSessionDetail = useCallback(
    async (sessionId: string) => {
      setIsSessionDetailLoading(true);
      setSessionDetailError(null);
      setSelectedSessionId(sessionId);
      try {
        const data: StudentSessionDetail = await fetchStudentSessionDetail(sessionId);
        const report =
          (data as any)?.report ||
          (data as any)?.feedback ||
          (data as any)?.session?.report ||
          null;
        if (report) {
          setSelectedSessionReport(report as InterviewReport);
        } else {
          setSelectedSessionReport(null);
          setSessionDetailError('이 세션에는 리포트 데이터가 없습니다.');
        }
      } catch (err: any) {
        console.error('Failed to fetch session detail', err);
        setSessionDetailError(err?.message || '세션 상세를 불러오지 못했습니다.');
        setSelectedSessionReport(null);
      } finally {
        setIsSessionDetailLoading(false);
      }
    },
    [studentId]
  );

  const handleDownloadReport = useCallback(() => {}, []);

  if (isLoading || !student) {
    return (
      <div className="container mx-auto animate-pulse space-y-6 pb-12">
        <div className="h-6 w-32 bg-slate-200 rounded-full"></div>
        <div className="h-10 w-40 bg-slate-200 rounded-full"></div>
        <div className="h-56 bg-white border border-slate-100 rounded-[20px] shadow-soft"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto animate-fadeIn pb-12">
        <div className="flex items-center gap-4 mb-6">
            <button onClick={onBack} className="flex items-center gap-2 text-sm text-slate-500 hover:text-primary transition-colors font-medium">
                <ArrowLeftIcon className="w-4 h-4"/>
                대시보드로 돌아가기
            </button>
        </div>
      <div className="flex items-baseline justify-between mb-6">
        <div>
            <h1 className="text-3xl font-bold text-slate-800">{student.name}</h1>
            <p className="text-lg text-primary font-medium">{student.grade}학년 · {student.major}</p>
        </div>
        {student.report && (
          <div className="flex gap-2">
            <Button onClick={handleDownloadReport} variant="secondary" className="px-4 py-2 rounded-[12px] shadow-soft">
              PDF로 다운로드
            </Button>
          </div>
        )}
      </div>

      {student.report ? (
        <InterviewReportView report={student.report} />
      ) : (
        <Card className="text-center py-12">
            <p className="text-slate-500 text-lg">아직 제출된 보고서가 없습니다.</p>
        </Card>
      )}

      <Card className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-xs font-semibold text-primary-text uppercase tracking-[0.2em]">Session History</p>
            <h3 className="text-xl font-bold text-slate-900">학생 세션 내역</h3>
            <p className="text-sm text-slate-500">백엔드 데이터로 최신 면접 기록을 확인합니다.</p>
          </div>
          {isSessionsLoading && <Spinner />}
        </div>
        {sessionError && (
          <div className="mb-4 text-sm text-amber-600 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2">
            {sessionError}
          </div>
        )}
        {!isSessionsLoading && sessions.length === 0 && !sessionError && (
          <p className="text-sm text-slate-500">최근 세션 기록이 없습니다.</p>
        )}
        {sessions.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-left text-slate-700">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 font-semibold">세션 ID</th>
                  <th className="px-4 py-3 font-semibold">시작</th>
                  <th className="px-4 py-3 font-semibold">종료</th>
                  <th className="px-4 py-3 font-semibold text-center">점수</th>
                  <th className="px-4 py-3 font-semibold text-center">상태</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sessions.map((session) => (
                  <tr key={session.id}>
                    <td className="px-4 py-3 font-mono text-xs text-slate-900">{session.id}</td>
                    <td className="px-4 py-3">{session.startedAt || '-'}</td>
                    <td className="px-4 py-3">{session.completedAt || '-'}</td>
                    <td className="px-4 py-3 text-center font-semibold">
                      {typeof session.totalScore === 'number' ? session.totalScore : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
                        {session.status || 'unknown'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Button
                        variant="secondary"
                        className="text-xs px-3 py-1 rounded-lg"
                        onClick={() => handleViewSessionDetail(session.id)}
                        isLoading={isSessionDetailLoading && selectedSessionId === session.id}
                      >
                        보기
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      {selectedSessionReport && (
        <Card className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-xs font-semibold text-primary-text uppercase tracking-[0.2em]">Session Detail</p>
              <h3 className="text-xl font-bold text-slate-900">선택한 세션 리포트</h3>
              <p className="text-sm text-slate-500">세션 ID: {selectedSessionId || '-'}</p>
            </div>
            {isSessionDetailLoading && <Spinner />}
          </div>
          <InterviewReportView report={selectedSessionReport} />
        </Card>
      )}
      {!selectedSessionReport && sessionDetailError && (
        <div className="mt-4 text-sm text-amber-600 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2">
          {sessionDetailError}
        </div>
      )}
    </div>
  );
};

export default StudentDetailView;
