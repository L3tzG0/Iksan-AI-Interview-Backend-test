import jsPDF from 'jspdf';
import type { InterviewReport } from '../types';
import { ensurePdfFont } from './pdfFont';

export interface PdfStudentMeta {
  name?: string;
  schoolName?: string;
  grade?: number | string;
  major?: string;
}

const computeScores = (report: InterviewReport) => {
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
};

const computeTotalScore = (report: InterviewReport, scores: ReturnType<typeof computeScores>) => {
  if (typeof report.overallScore === 'number') return report.overallScore;
  if (typeof report.totalScore === 'number') return report.totalScore;
  const vals = Object.values(scores);
  return vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
};

export const downloadInterviewReportPdf = async ({
  report,
  student,
  fileName = 'ai-interview-result.pdf',
}: {
  report: InterviewReport;
  student?: PdfStudentMeta;
  fileName?: string;
}) => {
  const scores = computeScores(report);
  const totalScore = computeTotalScore(report, scores);

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
      const wrapped = pdf.splitTextToSize(bullet ? `• ${line}` : line, contentWidth);
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

  pdf.save(fileName);
};
