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
import jsPDF from 'jspdf';
import { ensurePdfFont } from '../utils/pdfFont';

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
  const [isExporting, setIsExporting] = useState(false);

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

  const handleDownloadReport = useCallback(async () => {
    if (isExporting) return;
    const report = selectedSessionReport || student?.report;
    if (!report) return;
    setIsExporting(true);
    try {
      const scores = (() => {
        if (report.scores) return report.scores;
        const defaults = { contentRelevance: 0, structure: 0, fluency: 0, confidence: 0 };
        const feedback = report.detailedFeedback || [];
        if (!feedback.length) return defaults;
        const avg = (key: string) => feedback.reduce((sum, item: any) => sum + (item?.[key] || 0), 0) / feedback.length || 0;
        return {
          contentRelevance: avg('content_relevance_score'),
          structure: avg('structure_score'),
          fluency: avg('fluency_score'),
          confidence: avg('confidence_score'),
        };
      })();

      const totalScore = (() => {
        if (typeof report.overallScore === 'number') return report.overallScore;
        if (typeof report.totalScore === 'number') return report.totalScore;
        const vals = Object.values(scores);
        return vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
      })();

      const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4' });
      await ensurePdfFont(pdf);
      const pageWidth =
        pdf.internal?.pageSize?.getWidth?.() ??
        (pdf.internal?.pageSize as any)?.width ??
        210;
      const pageHeight =
        pdf.internal?.pageSize?.getHeight?.() ??
        (pdf.internal?.pageSize as any)?.height ??
        297;
      const margin = 16;
      const contentWidth = pageWidth - margin * 2;
      let cursorY = margin;

      const ensureSpace = (space: number) => {
        if (cursorY + space > pageHeight - margin) {
          pdf.addPage();
          cursorY = margin;
        }
      };

      const addTextBlock = (
        text: string | string[] | undefined,
        {
          size = 11,
          weight = 'normal',
          gap = 4,
          bullet = false,
        }: { size?: number; weight?: 'normal' | 'bold'; gap?: number; bullet?: boolean } = {}
      ) => {
        if (!text) return;
        const lines = Array.isArray(text) ? text : [text];
        pdf.setFont('NotoSansKR', weight);
        pdf.setFontSize(size);
        const lineHeight = size * 0.5 + 3;

        lines.forEach((line) => {
          const wrapped = pdf.splitTextToSize(bullet ? `- ${line}` : line, contentWidth);
          const totalHeight = wrapped.length * lineHeight + gap;
          ensureSpace(totalHeight);
          wrapped.forEach((wrappedLine, idx) => {
            const lineText = bullet && idx > 0 ? `  ${wrappedLine}` : wrappedLine;
            pdf.text(lineText, margin, cursorY);
            cursorY += lineHeight;
          });
          cursorY += gap;
        });
      };

      const addSectionTitle = (title: string) => {
        ensureSpace(10);
        pdf.setFont('NotoSansKR', 'bold');
        pdf.setFontSize(14);
        pdf.text(title, margin, cursorY);
        cursorY += 8;
        pdf.setDrawColor(220);
        pdf.setLineWidth(0.4);
        pdf.line(margin, cursorY, pageWidth - margin, cursorY);
        cursorY += 6;
      };

      const addKeyValue = (
        label: string,
        value?: string | number,
        options: { lineHeight?: number; gapAfter?: number } = {}
      ) => {
        if (!value && value !== 0) return;
        const combined = `${label}: ${value}`;
        const lineHeight = options.lineHeight ?? 8;
        const gapAfter = options.gapAfter ?? 8;
        pdf.setFont('NotoSansKR', 'bold');
        pdf.setFontSize(11);
        const wrapped = pdf.splitTextToSize(combined, contentWidth);
        const totalHeight = wrapped.length * lineHeight;
        ensureSpace(totalHeight + gapAfter);
        wrapped.forEach((line, idx) => {
          pdf.text(line, margin, cursorY + idx * lineHeight);
        });
        cursorY += totalHeight + gapAfter;
      };

      pdf.setFont('NotoSansKR', 'bold');
      pdf.setFontSize(18);
      pdf.text('AI 면접 리포트', margin, cursorY);
      cursorY += 10;

      if (student) {
        addSectionTitle('학생 정보');
        addKeyValue('이름', student.name || 'N/A', { gapAfter: 4 });
        addKeyValue('학교', student.schoolName || 'N/A', { gapAfter: 4 });
        addKeyValue('학년', student.grade ? `${student.grade}` : 'N/A', { gapAfter: 4 });
        addKeyValue('전공', student.major || 'N/A', { gapAfter: 6 });
      }

      addSectionTitle('점수');
      addKeyValue('총점', Math.round(totalScore), { gapAfter: 4 });
      addKeyValue('내용 적합성', Math.round(scores.contentRelevance), { gapAfter: 4 });
      cursorY += 2;
      addKeyValue('구성', Math.round(scores.structure), { gapAfter: 4 });
      addKeyValue('유창성', Math.round(scores.fluency), { gapAfter: 4 });
      addKeyValue('자신감', Math.round(scores.confidence), { gapAfter: 6 });

      const strengths = report.summary?.strengths || report.strengthSummary;
      const growth = report.summary?.areasForGrowth || report.areasForGrowth;
      const steps = report.nextStepsDetailed?.map((s) => `${s.title}: ${s.description}`) || report.nextSteps;

      if (strengths) {
        addSectionTitle('강점');
        addTextBlock(strengths, { size: 11 });
      }

      if (growth) {
        addSectionTitle('개선 영역');
        addTextBlock(growth, { size: 11 });
      }

      if (steps && steps.length) {
        addSectionTitle('다음 단계');
        addTextBlock(steps, { size: 11, bullet: true });
      }

      const feedback = report.detailedFeedback || [];
      if (feedback.length) {
        addSectionTitle('문항별 피드백');
        feedback.forEach((item, idx) => {
          const questionLabel = item.question_order || idx + 1;
          addTextBlock(`Q${questionLabel}: ${item.question}`, { size: 12, weight: 'bold', gap: 3 });
          if (item.answer) addTextBlock(`학생 답변: ${item.answer}`, { size: 11, gap: 3 });
          if (item.evaluation) addTextBlock(`AI 피드백: ${item.evaluation}`, { size: 11, gap: 3 });
          const sectionLine = [
            `내용 적합성 ${item.content_relevance_score ?? '-'} |`,
            `구성 ${item.structure_score ?? '-'} |`,
            `유창성 ${item.fluency_score ?? '-'} |`,
            `자신감 ${item.confidence_score ?? '-'}`,
          ].join(' ');
          addTextBlock(`점수: ${sectionLine}`, { size: 10, gap: 8 });
        });
      }

      pdf.save('ai-interview-result.pdf');
    } catch (err) {
      console.error('Failed to export PDF', err);
    } finally {
      setIsExporting(false);
    }
  }, [isExporting, selectedSessionReport, student]);

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
        {(student.report || selectedSessionReport) && (
          <div className="flex gap-2">
            <Button
              onClick={handleDownloadReport}
              variant="secondary"
              className="shadow-soft px-4 py-2 rounded-[12px]"
              disabled={isExporting}
            >
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

