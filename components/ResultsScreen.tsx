import React, { useMemo, useState } from 'react';
import type { InterviewReport } from '../types';
import InterviewReportView from './InterviewReportView';
import { downloadInterviewReportPdf } from '../utils/reportPdf';
import { deriveReportScores } from '../utils/report';

interface ResultsScreenProps {
  report: InterviewReport;
  onRetry: () => void;
  studentMeta?: { name?: string; schoolName?: string; grade?: number; major?: string };
}

const ResultsScreen: React.FC<ResultsScreenProps> = ({ report, onRetry, studentMeta }) => {
  const [isExporting, setIsExporting] = useState(false);

  const { scores, totalScore } = useMemo(() => deriveReportScores(report), [report]);

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
    <div className="animate-fadeIn">
      <div className="print-area">
        <InterviewReportView report={{ ...report, scores, totalScore }} onDownload={handleDownloadPdf} canDownload={Boolean(report)} />
      </div>
    </div>
  );
};

export default ResultsScreen;

