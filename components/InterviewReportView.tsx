import React, { useMemo, useState, useEffect } from 'react';
import type { InterviewReport } from '../types';
import Card from './Card';
import { CheckCircleIcon, AlertTriangleIcon, BrainIcon, FileTextIcon, MicIcon, ShieldIcon } from './icons';
import Button from './ui/Button';

interface InterviewReportViewProps {
  report: InterviewReport;
}

const createChips = (paragraph?: string | null) => {
  if (!paragraph) return [];
  return paragraph
    .split(/[\n\u0007\-]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 4);
};

const RadarChart: React.FC<{ scores: { contentRelevance: number; structure: number; fluency: number; confidence: number } }> = ({ scores }) => {
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const [size, setSize] = useState(320);
  const center = size / 2;
  const radius = Math.min(Math.max(size * 0.35, 90), 160);
  const maxScore = 10;
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => setIsReady(true));
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    const updateSize = () => {
      const width = containerRef.current?.offsetWidth || 320;
      // Keep chart responsive but within sensible bounds for text
      setSize(Math.min(Math.max(width - 32, 260), 420));
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  const axes = [
    { label: '내용 연관성', key: 'contentRelevance', angle: 0, anchor: 'middle', baseline: 'auto' },
    { label: '구조 (STAR)', key: 'structure', angle: Math.PI / 2, anchor: 'start', baseline: 'middle' },
    { label: '유창성', key: 'fluency', angle: Math.PI, anchor: 'middle', baseline: 'hanging' },
    { label: '자신감', key: 'confidence', angle: (3 * Math.PI) / 2, anchor: 'end', baseline: 'middle' },
  ];

  const getCoordinates = (score: number, angle: number) => {
    const r = (score / maxScore) * radius;
    const x = center + r * Math.cos(angle - Math.PI / 2);
    const y = center + r * Math.sin(angle - Math.PI / 2);
    return { x, y };
  };

  const levels = [2, 4, 6, 8, 10];
  const gridPolygons = levels.map((level) => {
    const points = axes
      .map((axis) => {
        const { x, y } = getCoordinates(level, axis.angle);
        return `${x},${y}`;
      })
      .join(' ');
    return <polygon key={level} points={points} fill="none" stroke="#e2e8f0" strokeWidth="1" />;
  });

  const axisLines = axes.map((axis, index) => {
    const { x, y } = getCoordinates(maxScore, axis.angle);
    return <line key={index} x1={center} y1={center} x2={x} y2={y} stroke="#cbd5e1" strokeWidth="1" />;
  });

  const dataPoints = axes
    .map((axis) => {
      const score = scores[axis.key as keyof typeof scores];
      const { x, y } = getCoordinates(score, axis.angle);
      return `${x},${y}`;
    })
    .join(' ');

  const labels = axes.map((axis, index) => {
    const { x, y } = getCoordinates(maxScore + 1.5, axis.angle);
    const finalY = index === 0 ? y - 5 : y;

    return (
      <text key={index} x={x} y={finalY} textAnchor={axis.anchor} dominantBaseline={axis.baseline} className="fill-slate-600 font-bold text-xs">
        {axis.label}
      </text>
    );
  });

  return (
    <div ref={containerRef} className="flex justify-center py-4">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
        <g>
          {gridPolygons}
          {axisLines}
          <polygon
            points={dataPoints}
            fill="rgba(103, 0, 230, 0.2)"
            stroke="#6700e6"
            strokeWidth="2"
            style={{
              opacity: isReady ? 1 : 0,
              transform: isReady ? 'scale(1)' : 'scale(0.9)',
              transformOrigin: '50% 50%',
              transition: 'opacity 0.6s ease, transform 0.6s ease',
            }}
          />
          {axes.map((axis, i) => {
            const score = scores[axis.key as keyof typeof scores];
            const { x, y } = getCoordinates(score, axis.angle);
            return <circle key={i} cx={x} cy={y} r="4" fill="#6700e6" />;
          })}
          {labels}
        </g>
      </svg>
    </div>
  );
};

const InterviewReportView: React.FC<InterviewReportViewProps> = ({ report }) => {
  const detailedFeedback = report.detailedFeedback || [];
  const scores = useMemo(() => {
    if (report.scores) return report.scores;
    if (!detailedFeedback.length) {
      return { contentRelevance: 0, structure: 0, fluency: 0, confidence: 0 };
    }
    const avg = (key: string) =>
      detailedFeedback.reduce((sum, item: any) => sum + (item?.[key] || 0), 0) / detailedFeedback.length || 0;
    return {
      contentRelevance: avg('content_relevance_score'),
      structure: avg('structure_score'),
      fluency: avg('fluency_score'),
      confidence: avg('confidence_score'),
    };
  }, [report.scores, detailedFeedback]);

  const totalScore = useMemo(() => {
    if (typeof report.overallScore === 'number') return report.overallScore;
    if (typeof report.totalScore === 'number') return report.totalScore;
    const vals = [scores.contentRelevance, scores.structure, scores.fluency, scores.confidence];
    return vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
  }, [report.overallScore, report.totalScore, scores]);

  const strengthText = report.strengthSummary || report.summary?.strengths || '';
  const weaknessText = report.areasForGrowth || report.summary?.areasForGrowth || '';
  const strengthChips = useMemo(() => createChips(strengthText), [strengthText]);
  const weaknessChips = useMemo(() => createChips(weaknessText), [weaknessText]);
  const jumpTargets = useMemo(
    () => detailedFeedback.map((_, idx) => ({ label: `Q${idx + 1}`, id: `question-${idx + 1}` })),
    [detailedFeedback]
  );

  const nextSteps = useMemo(() => {
    if (Array.isArray(report.nextStepsDetailed) && report.nextStepsDetailed.length) return report.nextStepsDetailed;
    if (Array.isArray(report.nextSteps) && report.nextSteps.length) {
      return report.nextSteps.map((step) =>
        typeof step === 'string' ? { title: step, description: step } : { title: step.title, description: step.description }
      );
    }
    return [] as { title: string; description: string }[];
  }, [report.nextSteps, report.nextStepsDetailed]);

  const categoryMeta = [
    { key: 'contentRelevance', label: '내용 연관성', icon: FileTextIcon, accent: 'text-indigo-600', bg: 'bg-indigo-50' },
    { key: 'structure', label: '구조/STAR', icon: BrainIcon, accent: 'text-purple-600', bg: 'bg-purple-50' },
    { key: 'fluency', label: '유창성', icon: MicIcon, accent: 'text-pink-600', bg: 'bg-pink-50' },
    { key: 'confidence', label: '자신감', icon: ShieldIcon, accent: 'text-emerald-600', bg: 'bg-emerald-50' },
  ] as const;

  return (
    <div className="space-y-8">
      <div className="gap-6 grid lg:grid-cols-3">
        <Card className="flex flex-col gap-6 lg:col-span-1 text-center">
          <div>
            <p className="font-semibold text-slate-400 text-xs uppercase tracking-[0.25em]">TOTAL</p>
            <div className="mt-2 font-bold text-primary text-6xl">{totalScore.toFixed(1)}<span className="font-normal text-slate-400 text-2xl">/10</span></div>
            <p className="mt-2 text-slate-500 text-xs">AI 평가(40 / 30 / 20 / 10%) 기반</p>
          </div>
          <div className="gap-3 grid">
            {categoryMeta.map((category) => {
              const Icon = category.icon;
              const score = scores[category.key];
              return (
                <div key={category.key} className="flex justify-between items-center bg-white/90 shadow-inner shadow-white/60 px-4 py-3 border border-slate-100 rounded-[14px]">
                  <div className="flex items-center gap-3">
                    <span className={`w-10 h-10 rounded-full ${category.bg} flex items-center justify-center`}>
                      <Icon className={`w-5 h-5 ${category.accent}`} />
                    </span>
                    <span className="font-semibold text-slate-700">{category.label}</span>
                  </div>
                  <span className="font-bold text-slate-900">{score.toFixed(1)}</span>
                </div>
              );
            })}
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="mb-4 font-semibold text-slate-500 text-sm text-center uppercase tracking-widest">점수 레이더</h3>
          <RadarChart scores={scores} />
        </Card>
      </div>

      <div className="gap-6 grid md:grid-cols-2">
        <Card className="bg-green-50/60 border border-green-200/60">
          <h3 className="flex items-center gap-2 mb-3 font-bold text-green-700 text-xl">
            <CheckCircleIcon className="w-5 h-5" /> 강점 요약
          </h3>
          {/* <div className="flex flex-wrap gap-2 mb-3">
            {strengthChips.map((chip, index) => (
              <span key={`${chip}-${index}`} className="bg-green-100 px-3 py-1 rounded-full font-semibold text-green-600 text-xs">
                {chip}
              </span>
            ))}
          </div> */}
          <p className="text-slate-600 leading-relaxed">{strengthText || '강점 요약이 없습니다.'}</p>
        </Card>



        <Card className="bg-primary-lightest/70 border border-primary-light">
          <h3 className="flex items-center gap-2 mb-3 font-bold text-primary text-xl">
            <AlertTriangleIcon className="w-5 h-5" /> 개선 영역
          </h3>
{/* 

          <div className="flex flex-wrap gap-2 mb-3">
            {weaknessChips.map((chip, index) => (
              <span key={`${chip}-${index}`} className="bg-rose-100 px-3 py-1 rounded-full font-semibold text-rose-600 text-xs">
                {chip}
              </span>
            ))}
          </div> */}
          <p className="text-slate-600 leading-relaxed">{weaknessText || '개선 영역 요약이 없습니다.'}</p>
        </Card>



      </div>

      <Card>
        <div className="flex flex-wrap justify-between items-center gap-3 mb-4">
          <h2 className="font-bold text-slate-800 text-2xl">문항별 피드백</h2>
          <div className="flex flex-wrap gap-2">
            {jumpTargets.map((target) => (
              <button
                key={target.id}
                onClick={() => {
                  const el = document.getElementById(target.id);
                  el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }}
                className="px-3 py-1 border border-slate-200 hover:border-primary rounded-full font-semibold text-slate-600 hover:text-primary text-xs transition-colors"
              >
                {target.label}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-4">
          {detailedFeedback.map((item: any, index) => {
            const questionText = item.question || item.question_text || `Q${index + 1}`;
            const answerText = item.answer || item.answer_text || '';
            const evaluation = item.evaluation || item.feedback || '';
            const isCorrect = item.is_correct ?? item.isCorrect ?? null;
            const score = item.overall_score ?? item.score ?? item.content_relevance_score ?? null;
            return (
              <details
                key={index}
                id={`question-${index + 1}`}
                className={`group rounded-[18px] border transition-all ${
                  isCorrect ? 'bg-green-50 border-green-200' : 'bg-white border-slate-200 shadow-sm'
                }`}
              >
                <summary className="flex items-center gap-3 px-6 py-4 cursor-pointer list-none">
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                    isCorrect ? 'bg-green-200 text-green-800' : 'bg-primary-light text-primary'
                  }`}>
                    Q{index + 1}
                  </div>
                  <div className="flex flex-col gap-1">
                    <p className="font-semibold text-slate-800 text-base">{questionText}</p>
                    <p className="text-slate-500 text-xs">문항별 평가</p>
                  </div>
                </summary>
                <div className="space-y-3 px-6 pb-6">
                  <div className="bg-white/60 p-4 border border-slate-200 rounded-[14px]">
                    <p className="mb-1 font-bold text-slate-500 text-xs uppercase">내 답변</p>
                    <p className="text-slate-700 italic">"{answerText || '답변이 제공되지 않았습니다.'}"</p>
                  </div>
                  <div className={`p-4 rounded-[14px] ${isCorrect ? 'bg-green-100/50' : 'bg-primary-lightest'}`}>
                    <div className="flex justify-between items-center mb-2">
                      <h4 className={`font-bold text-sm flex items-center gap-2 ${isCorrect ? 'text-green-800' : 'text-primary'}`}>
                        <BrainIcon className="w-4 h-4" />
                        AI 피드백
                      </h4>
                      {score !== null && <span className="bg-white shadow-sm px-2 py-1 rounded font-bold text-sm">점수: {score}</span>}
                    </div>
                    <p className="text-slate-700 text-sm leading-relaxed">{evaluation || '피드백이 제공되지 않았습니다.'}</p>
                  </div>
                </div>
              </details>
            );
          })}
          {detailedFeedback.length === 0 && <p className="text-slate-500 text-sm">문항별 피드백이 아직 없습니다.</p>}
        </div>
      </Card>

      <Card>
        <h2 className="mb-4 font-bold text-slate-800 text-2xl">다음 단계</h2>
        <div className="space-y-4">
          {nextSteps.map((step, index) => (
            <div key={index} className="flex items-start gap-4 bg-white/80 p-4 border border-slate-100 rounded-[16px]">
              <div className="flex flex-shrink-0 justify-center items-center bg-primary-light mt-1 rounded-full w-8 h-8 font-bold text-primary">
                {index + 1}
              </div>
              <div>
                <span className="block mb-1 font-bold text-slate-800">{step.title}</span>
                <span className="text-slate-600 text-sm leading-relaxed">{step.description}</span>
              </div>
            </div>
          ))}
          {nextSteps.length === 0 && <p className="text-slate-500 text-sm">다음 단계 제안이 없습니다.</p>}
        </div>
      </Card>
    </div>
  );
};

export default InterviewReportView;
