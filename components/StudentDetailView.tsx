import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
    fetchAllSessionsForTeacherAndAdminRole,
    type NormalizedSessionSummary,
} from "../services/studentService";
import { fetchSessionDetail } from "../services/sessionService";
import type { StudentDetail, StudentSession, InterviewReport } from "../types";
import Spinner from "./Spinner";
import InterviewReportView from "./InterviewReportView";
import { downloadInterviewReportPdf } from "../utils/reportPdf";

interface StudentDetailViewProps {
    studentId: string;
    onBack: () => void;
}

const StudentDetailView: React.FC<StudentDetailViewProps> = ({
    studentId,
}) => {
    const [student, setStudent] = useState<StudentDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [sessions, setSessions] = useState<StudentSession[]>([]);
    const [isSessionsLoading, setIsSessionsLoading] = useState(false);
    const [sessionError, setSessionError] = useState<string | null>(null);
    const [selectedSessionReport, setSelectedSessionReport] =
        useState<InterviewReport | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
        null
    );
    const [isSessionDetailLoading, setIsSessionDetailLoading] = useState(false);
    const [sessionDetailError, setSessionDetailError] = useState<string | null>(
        null
    );
    const [searchParams] = useSearchParams();
    const [isExporting, setIsExporting] = useState(false);

    const mapReportFromDetail = useCallback((detail: any): InterviewReport => {
        const feedback = Array.isArray(detail?.detailed_feedback)
            ? detail.detailed_feedback
            : [];
        const overallScore = detail?.overall_score ?? detail?.overallScore ?? detail?.total_score;
        const scoresFromFeedback = feedback.length
            ? {
                  contentRelevance:
                      feedback.reduce(
                          (sum: number, item: any) =>
                              sum + (item.content_relevance_score || 0),
                          0
                      ) / feedback.length || 0,
                  structure:
                      feedback.reduce(
                          (sum: number, item: any) =>
                              sum + (item.structure_score || 0),
                          0
                      ) / feedback.length || 0,
                  fluency:
                      feedback.reduce(
                          (sum: number, item: any) =>
                              sum + (item.fluency_score || 0),
                          0
                      ) / feedback.length || 0,
                  confidence:
                      feedback.reduce(
                          (sum: number, item: any) =>
                              sum + (item.confidence_score || 0),
                          0
                      ) / feedback.length || 0,
              }
            : undefined;

        const mapped: InterviewReport = {
            ...detail,
            sessionId: detail?.session_id || detail?.sessionId,
            status: detail?.status,
            overallScore,
            totalScore: detail?.total_score ?? overallScore,
            strengthSummary: detail?.strength_summary ?? detail?.strengthSummary,
            areasForGrowth: detail?.areas_for_growth ?? detail?.areasForGrowth,
            detailedFeedback: feedback,
            nextSteps: detail?.next_steps ?? detail?.nextSteps,
            scores: scoresFromFeedback,
            summary:
                detail?.strength_summary || detail?.areas_for_growth
                    ? {
                          strengths: detail.strength_summary || "",
                          areasForGrowth: detail.areas_for_growth || "",
                      }
                    : undefined,
            nextStepsDetailed: Array.isArray(detail?.next_steps)
                ? detail.next_steps.map((step: any) =>
                      typeof step === "string"
                          ? { title: step, description: step }
                          : {
                                title:
                                    step?.title ||
                                    step?.title_text ||
                                    step?.label ||
                                    "",
                                description:
                                    step?.description ||
                                    step?.description_text ||
                                    step?.body ||
                                    "",
                            }
                  )
                : undefined,
        };

        return mapped;
    }, []);

    useEffect(() => {
        setStudent({
            id: studentId,
            name: "학생",
            major: "",
            schoolName: "",
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
                        const studentIdentifier = s.studentIdentifier ?? "";
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
                console.error("Failed to fetch sessions", err);
                setSessionError(
                    err?.message ||
                        "Failed to load session history. Please try again."
                );
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
                if (
                    !mappedReport.detailedFeedback?.length &&
                    mappedReport.totalScore === undefined &&
                    mappedReport.overallScore === undefined
                ) {
                    setSessionDetailError(
                        "이 세션에는 리포트 데이터가 없습니다."
                    );
                }
            } catch (err: any) {
                console.error("Failed to fetch session detail", err);
                setSessionDetailError(
                    err?.message || "세션 상세를 불러오지 못했습니다."
                );
                setSelectedSessionReport(null);
            } finally {
                setIsSessionDetailLoading(false);
            }
        },
        [mapReportFromDetail]
    );

    useEffect(() => {
        const sessionIdFromQuery = searchParams.get("session_id");
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
            await downloadInterviewReportPdf({
                report,
                student: student
                    ? {
                          name: student.name,
                          schoolName: student.schoolName,
                          grade: student.grade,
                          major: student.major,
                      }
                    : undefined,
            });
        } catch (err) {
            console.error("Failed to export PDF", err);
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
        <div>
            {selectedSessionReport && (
                <>
                    <div className="flex justify-between items-center mb-4">
                        {isSessionDetailLoading && <Spinner />}
                    </div>
                    <InterviewReportView
                        report={selectedSessionReport}
                        onDownload={handleDownloadReport}
                        canDownload={Boolean(student?.report || selectedSessionReport)}
                        isExporting={isExporting}
                    />
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
