import React, { useState, useEffect, useCallback } from 'react';
import { getStudentDetails } from '../services/geminiService';
import type { StudentDetail } from '../types';
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

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const data = await getStudentDetails(studentId);
        setStudent(data);
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [studentId]);

  const handleDownloadReport = useCallback(() => {
    if (!student?.report) return;

    const report = student.report;
    const today = new Date().toLocaleDateString('ko-KR');
    const detailed = report.detailedFeedback
      .map(
        (item, idx) =>
          `<div style="margin-bottom:12px;"><strong>Q${idx + 1}. ${item.question}</strong><br/>A${idx + 1}: ${
            item.answer || ''
          }<br/><em>AI 평가:</em> ${item.evaluation}</div>`
      )
      .join('');

    const nextSteps = report.nextSteps
      .map((step, idx) => `<li><strong>Step ${idx + 1}:</strong> ${step.title} - ${step.description}</li>`)
      .join('');

    const html = `
      <html>
        <head>
          <meta charset="UTF-8" />
          <title>${student.name} - Interview Report</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 24px; color: #0f172a; }
            h1, h2, h3 { margin: 0 0 8px 0; }
            .section { margin-bottom: 18px; }
            .badge { display: inline-block; padding: 4px 10px; border-radius: 12px; background: #ede9fe; color: #6d28d9; font-size: 12px; }
            ul { padding-left: 18px; }
          </style>
        </head>
        <body>
          <h1>${student.name} (${student.grade}학년 · ${student.major})</h1>
          <p style="color:#475569;font-size:12px;margin:4px 0 12px;">학교: ${student.schoolName || '-'} | 시험일: ${today}</p>
          <div class="badge">총점 ${report.totalScore.toFixed(1)}/10</div>
          <div class="section">
            <h2>요약</h2>
            <p><strong>강점:</strong> ${report.summary.strengths}</p>
            <p><strong>개선 영역:</strong> ${report.summary.areasForGrowth}</p>
          </div>
          <div class="section">
            <h2>상세 피드백</h2>
            ${detailed}
          </div>
          <div class="section">
            <h2>다음 단계</h2>
            <ul>${nextSteps}</ul>
          </div>
        </body>
      </html>
    `;

    const printWindow = window.open('', '_blank', 'width=900,height=1200');
    if (printWindow) {
      printWindow.document.write(html);
      printWindow.document.close();
      printWindow.focus();
      printWindow.print();
    }
  }, [student]);

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
    </div>
  );
};

export default StudentDetailView;
