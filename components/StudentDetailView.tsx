import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchAllSessionsForTeacherAndAdminRole, type NormalizedSessionSummary } from '../services/studentService';
import { fetchSessionDetail } from '../services/sessionService';
import type { StudentDetail, StudentSession, InterviewReport } from '../types';
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
  const [searchParams] = useSearchParams();

  const mapReportFromDetail = useCallback((detail: any): InterviewReport => {
    const feedback = Array.isArray(detail?.detailed_feedback) ? detail.detailed_feedback : [];
    const overallScore = detail?.overall_score ?? detail?.overallScore;
    return {
      sessionId: detail?.session_id || detail?.sessionId,
      status: detail?.status,
      overallScore,
      strengthSummary: detail?.strength_summary,
      areasForGrowth: detail?.areas_for_growth,
      detailedFeedback: feedback,
      nextSteps: detail?.next_steps,
      scores: feedback.length
        ? {
            contentRelevance: feedback.reduce((sum: number, item: any) => sum + (item.content_relevance_score || 0), 0) / feedback.length || 0,
            structure: feedback.reduce((sum: number, item: any) => sum + (item.structure_score || 0), 0) / feedback.length || 0,
            fluency: feedback.reduce((sum: number, item: any) => sum + (item.fluency_score || 0), 0) / feedback.length || 0,
            confidence: feedback.reduce((sum: number, item: any) => sum + (item.confidence_score || 0), 0) / feedback.length || 0,
          }
        : undefined,
      totalScore: overallScore,
      summary:
        detail?.strength_summary || detail?.areas_for_growth
          ? { strengths: detail.strength_summary || '', areasForGrowth: detail.areas_for_growth || '' }
          : undefined,
      nextStepsDetailed: Array.isArray(detail?.next_steps)
        ? detail.next_steps.map((step: string) => ({ title: step, description: step }))
        : undefined,
    };
  }, []);

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
        const data = await fetchAllSessionsForTeacherAndAdminRole();
        const normalized = data.sessions
          .filter((s: NormalizedSessionSummary) => {
            const studentIdentifier = s.studentIdentifier ?? '';
            return String(studentIdentifier) === String(studentId);
          })
          .map((s) => ({
            id: s.id,
            startedAt: s.createdAt,
            completedAt: s.completedAt,
            totalScore: s.totalScore,
            status: s.status,
            intent: undefined,
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
        const detail = await fetchSessionDetail(sessionId);
        const mappedReport = mapReportFromDetail(detail);
        setSelectedSessionReport(mappedReport);
        if (!mappedReport.detailedFeedback?.length && mappedReport.totalScore === undefined && mappedReport.overallScore === undefined) {
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
    [mapReportFromDetail]
  );

  useEffect(() => {
    const sessionIdFromQuery = searchParams.get('session_id');
    if (sessionIdFromQuery && sessionIdFromQuery !== selectedSessionId) {
      handleViewSessionDetail(sessionIdFromQuery);
    }
  }, [searchParams, selectedSessionId, handleViewSessionDetail]);

  const handleDownloadReport = useCallback(() => {}, []);

  if (isLoading || !student) {
    return (
      <div className="space-y-6 mx-auto pb-12 animate-pulse container">
        <div className="bg-slate-200 rounded-full w-32 h-6"></div>
        <div className="bg-slate-200 rounded-full w-40 h-10"></div>
        <div className="bg-white shadow-soft border border-slate-100 rounded-[20px] h-56"></div>
      </div>
    );
  }

  return (
    <div className="mx-auto pb-12 animate-fadeIn container">
        <div className="flex items-center gap-4 mb-6">
            <button onClick={onBack} className="flex items-center gap-2 font-medium text-slate-500 hover:text-primary text-sm transition-colors">
                <ArrowLeftIcon className="w-4 h-4"/>
                대시보드로 돌아가기
            </button>
        </div>
      <div className="flex justify-between items-baseline mb-6">
        <div>
            <h1 className="font-bold text-slate-800 text-3xl">{student.name}</h1>
            <p className="font-medium text-primary text-lg">{student.grade}학년 · {student.major}</p>
        </div>
        {student.report && (
          <div className="flex gap-2">
            <Button onClick={handleDownloadReport} variant="secondary" className="shadow-soft px-4 py-2 rounded-[12px]">
              PDF로 다운로드
            </Button>
          </div>
        )}
      </div>

      {/* {student.report ? (
        <InterviewReportView report={student.report} />
      ) : (
        <Card className="py-12 text-center">
            <p className="text-slate-500 text-lg">아직 제출된 보고서가 없습니다.</p>
        </Card>
      )} */}

      {/* <Card className="mt-8">
        <div className="flex justify-between items-center mb-4">
          <div>
            <p className="font-semibold text-primary-text text-xs uppercase tracking-[0.2em]">Session History</p>
            <h3 className="font-bold text-slate-900 text-xl">학생 세션 내역</h3>
            <p className="text-slate-500 text-sm">백엔드 데이터로 최신 면접 기록을 확인합니다.</p>
          </div>
          {isSessionsLoading && <Spinner />}
        </div>
        {sessionError && (
          <div className="bg-amber-50 mb-4 px-3 py-2 border border-amber-100 rounded-xl text-amber-600 text-sm">
            {sessionError}
          </div>
        )}
        {!isSessionsLoading && sessions.length === 0 && !sessionError && (
          <p className="text-slate-500 text-sm">최근 세션 기록이 없습니다.</p>
        )}
        {sessions.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-slate-700 text-sm text-left">
              <thead className="bg-slate-50 border-slate-200 border-b text-slate-500 text-xs uppercase">
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
                    <td className="px-4 py-3 font-mono text-slate-900 text-xs">{session.id}</td>
                    <td className="px-4 py-3">{session.startedAt || '-'}</td>
                    <td className="px-4 py-3">{session.completedAt || '-'}</td>
                    <td className="px-4 py-3 font-semibold text-center">
                      {typeof session.totalScore === 'number' ? session.totalScore : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center bg-slate-100 px-3 py-1 rounded-full font-semibold text-slate-700 text-xs">
                        {session.status || 'unknown'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Button
                        variant="secondary"
                        className="px-3 py-1 rounded-lg text-xs"
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
       */}
      {selectedSessionReport && (
        <>
          <div className="flex justify-between items-center mb-4">
            <div>
              <p className="font-semibold text-primary-text text-xs uppercase tracking-[0.2em]">Session Detail</p>
              <h3 className="font-bold text-slate-900 text-xl">선택한 세션 리포트</h3>
              <p className="text-slate-500 text-sm">세션 ID: {selectedSessionId || '-'}</p>
            </div>
            {isSessionDetailLoading && <Spinner />}
          </div>
          <InterviewReportView report={selectedSessionReport} />
          </>
      )}
      {!selectedSessionReport && sessionDetailError && (
        <div className="bg-amber-50 mt-4 px-3 py-2 border border-amber-100 rounded-xl text-amber-600 text-sm">
          {sessionDetailError}
        </div>
      )}
    </div>
  );
};

export default StudentDetailView;
