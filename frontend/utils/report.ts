import type { InterviewReport } from "../types";

type ScoreShape = {
    contentRelevance: number;
    structure: number;
    fluency: number;
    confidence: number;
};

const defaultScores: ScoreShape = {
    contentRelevance: 0,
    structure: 0,
    fluency: 0,
    confidence: 0,
};

const toNumber = (value: unknown) => {
    const numeric = typeof value === "string" ? Number(value) : value;
    return Number.isFinite(numeric) ? Number(numeric) : 0;
};

export const computeScoresFromFeedback = (feedback?: any[]): ScoreShape => {
    if (!Array.isArray(feedback) || feedback.length === 0) return defaultScores;

    const avg = (key: string) =>
        feedback.reduce((sum, item) => sum + toNumber(item?.[key]), 0) /
            feedback.length || 0;

    return {
        contentRelevance: avg("content_relevance_score"),
        structure: avg("structure_score"),
        fluency: avg("fluency_score"),
        confidence: avg("confidence_score"),
    };
};

export const deriveReportScores = (report: InterviewReport) => {
    const scores = report.scores ?? computeScoresFromFeedback(report.detailedFeedback);
    const totalScore = (() => {
        if (typeof report.overallScore === "number") return report.overallScore;
        if (typeof report.totalScore === "number") return report.totalScore;
        const totals = Object.values(scores);
        return totals.reduce((sum, value) => sum + value, 0) / (totals.length || 1);
    })();

    return { scores, totalScore };
};

export const mapReportFromDetail = (detail: any): InterviewReport => {
    const feedback = Array.isArray(detail?.detailed_feedback)
        ? detail.detailed_feedback
        : [];
    const overallScore =
        detail?.overall_score ?? detail?.overallScore ?? detail?.total_score;
    const scoresFromFeedback = feedback.length
        ? computeScoresFromFeedback(feedback)
        : undefined;

    return {
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
};
