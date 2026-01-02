import React, { useMemo, useState } from 'react';
import type { InterviewReport } from '../types';
import InterviewReportView from './InterviewReportView';
import Button from './ui/Button';
import { downloadInterviewReportPdf } from '../utils/reportPdf';

interface ResultsScreenProps {
  report: InterviewReport;
  onRetry: () => void;
  studentMeta?: { name?: string; schoolName?: string; grade?: number; major?: string };
}

const ResultsScreen: React.FC<ResultsScreenProps> = ({ report, onRetry, studentMeta }) => {
  const [isExporting, setIsExporting] = useState(false);

  const scores = useMemo(() => {
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
  }, [report.detailedFeedback, report.scores]);

  const totalScore = useMemo(() => {
    if (typeof report.overallScore === 'number') return report.overallScore;
    if (typeof report.totalScore === 'number') return report.totalScore;
    const vals = Object.values(scores);
    return vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
  }, [report.overallScore, report.totalScore, scores]);

  const handleDownloadPdf = async () => {
    if (isExporting) return;
    setIsExporting(true);
    try {
      await downloadInterviewReportPdf({
        report: { ...report, scores, totalScore },
        student: studentMeta,
      });
    } catch (err) {
      console.error('Failed to export PDF', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="space-y-8 print-area">

        <InterviewReportView report={{ ...report, scores, totalScore }} />
      </div>

      <div className="pt-8 pb-12 text-center no-print">
        <Button onClick={handleDownloadPdf} variant="secondary" className="mr-4 mb-4 px-6 py-3" disabled={isExporting}>
          PDF 저장
        </Button>
        <Button onClick={onRetry} className="px-10 py-4 text-lg" disabled={isExporting}>
          다시 연습하기
        </Button>
      </div>
    </div>
  );
};

export default ResultsScreen;

