import React, { useMemo, useState, useEffect } from 'react';
import type { InterviewReport } from '../types';
import Card from './Card';
import { CheckCircleIcon, AlertTriangleIcon, BrainIcon, FileTextIcon, MicIcon, ShieldIcon } from './icons';
import Button from './ui/Button';

interface InterviewReportViewProps {
  report: InterviewReport;
}

const createChips = (paragraph: string) => {
  return paragraph
    .split(/[\n•\-]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 4);
};

const RadarChart: React.FC<{ scores: { contentRelevance: number; structure: number; fluency: number; confidence: number } }> = ({ scores }) => {
  const size = 320;
  const center = size / 2;
  const radius = 110;
  const maxScore = 10;
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const id = requestAnimationFrame(() => setIsReady(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const axes = [
    { label: '내용 적합도', key: 'contentRelevance', angle: 0, anchor: 'middle', baseline: 'auto' },
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
      <text key={index} x={x} y={finalY} textAnchor={axis.anchor} dominantBaseline={axis.baseline} className="text-xs font-bold fill-slate-600">
        {axis.label}
      </text>
    );
  });

  return (
    <div className="flex justify-center py-4">
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
  const strengthChips = useMemo(() => createChips(report.summary.strengths), [report.summary.strengths]);
  const weaknessChips = useMemo(() => createChips(report.summary.areasForGrowth), [report.summary.areasForGrowth]);
  const jumpTargets = useMemo(
    () => report.detailedFeedback.map((_, idx) => ({ label: `Q${idx + 1}`, id: `question-${idx + 1}` })),
    [report.detailedFeedback]
  );

  const categoryMeta = [
    { key: 'contentRelevance', label: '내용 적합도', icon: FileTextIcon, accent: 'text-indigo-600', bg: 'bg-indigo-50' },
    { key: 'structure', label: '구조/STAR', icon: BrainIcon, accent: 'text-purple-600', bg: 'bg-purple-50' },
    { key: 'fluency', label: '유창성', icon: MicIcon, accent: 'text-pink-600', bg: 'bg-pink-50' },
    { key: 'confidence', label: '자신감', icon: ShieldIcon, accent: 'text-emerald-600', bg: 'bg-emerald-50' },
  ] as const;

  return (
    <div className="space-y-8">
      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1 text-center flex flex-col gap-6">
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-[0.25em]">TOTAL</p>
            <div className="text-6xl font-bold text-primary mt-2">{report.totalScore.toFixed(1)}<span className="text-2xl text-slate-400 font-normal">/10</span></div>
            <p className="text-xs text-slate-500 mt-2">AI 평가 지표(40 / 30 / 20 / 10%) 반영</p>
          </div>
          <div className="grid gap-3">
            {categoryMeta.map((category) => {
              const Icon = category.icon;
              const score = report.scores[category.key];
              return (
                <div key={category.key} className="flex items-center justify-between rounded-[14px] border border-slate-100 px-4 py-3 bg-white/90 shadow-inner shadow-white/60">
                  <div className="flex items-center gap-3">
                    <span className={`w-10 h-10 rounded-full ${category.bg} flex items-center justify-center`}>
                      <Icon className={`w-5 h-5 ${category.accent}`} />
                    </span>
                    <span className="font-semibold text-slate-700">{category.label}</span>
                  </div>
                  <span className="font-bold text-slate-900">{score}</span>
                </div>
              );
            })}
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="text-sm text-slate-500 font-semibold uppercase tracking-widest text-center mb-4">세부 지표</h3>
          <RadarChart scores={report.scores} />
        </Card>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="bg-green-50/60 border border-green-200/60">
          <h3 className="font-bold text-xl mb-3 text-green-700 flex items-center gap-2">
            <CheckCircleIcon className="w-5 h-5" /> 강점 포인트
          </h3>
          <div className="flex flex-wrap gap-2 mb-3">
            {strengthChips.map((chip, index) => (
              <span key={`${chip}-${index}`} className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-600">
                {chip}
              </span>
            ))}
          </div>
          <p className="text-slate-600 leading-relaxed">{report.summary.strengths}</p>
        </Card>
        <Card className="bg-primary-lightest/70 border border-primary-light">
          <h3 className="font-bold text-xl mb-3 text-primary flex items-center gap-2">
            <AlertTriangleIcon className="w-5 h-5" />
            보완이 필요한 점
          </h3>
          <div className="flex flex-wrap gap-2 mb-3">
            {weaknessChips.map((chip, index) => (
              <span key={`${chip}-${index}`} className="px-3 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-600">
                {chip}
              </span>
            ))}
          </div>
          <p className="text-slate-600 leading-relaxed">{report.summary.areasForGrowth}</p>
        </Card>
      </div>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="text-2xl font-bold text-slate-800">질문별 상세 피드백</h2>
          <div className="flex flex-wrap gap-2">
            {jumpTargets.map((target) => (
              <button
                key={target.id}
                onClick={() => {
                  const el = document.getElementById(target.id);
                  el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }}
                className="px-3 py-1 rounded-full border border-slate-200 text-xs font-semibold text-slate-600 hover:border-primary hover:text-primary transition-colors"
              >
                {target.label}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-4">
          {report.detailedFeedback.map((item, index) => (
            <details
              key={index}
              id={`question-${index + 1}`}
              className={`group rounded-[18px] border transition-all ${
                item.isCorrect ? 'bg-green-50 border-green-200' : 'bg-white border-slate-200 shadow-sm'
              }`}
            >
              <summary className="cursor-pointer list-none px-6 py-4 flex items-center gap-3">
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${item.isCorrect ? 'bg-green-200 text-green-800' : 'bg-primary-light text-primary'}`}>
                  Q{index + 1}
                </div>
                <div className="flex flex-col gap-1">
                  <p className="font-semibold text-slate-800 text-base">{item.question}</p>
                  <p className="text-xs text-slate-500">학생 답변 요약 보기</p>
                </div>
              </summary>
              <div className="px-6 pb-6 space-y-3">
                <div className="bg-white/60 p-4 rounded-[14px] border border-slate-200">
                  <p className="text-xs font-bold uppercase text-slate-500 mb-1">학생 답변</p>
                  <p className="text-slate-700 italic">"{item.answer}"</p>
                </div>
                <div className={`p-4 rounded-[14px] ${item.isCorrect ? 'bg-green-100/50' : 'bg-primary-lightest'}`}>
                  <div className="flex justify-between items-center mb-2">
                    <h4 className={`font-bold text-sm flex items-center gap-2 ${item.isCorrect ? 'text-green-800' : 'text-primary'}`}>
                      <BrainIcon className="w-4 h-4" />
                      AI 코칭 요약
                    </h4>
                    <span className="font-bold text-sm bg-white px-2 py-1 rounded shadow-sm">점수: {item.score}/10</span>
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed">{item.evaluation}</p>
                </div>
              </div>
            </details>
          ))}
        </div>
      </Card>

      <Card>
        <h2 className="text-2xl font-bold mb-4 text-slate-800">학습 추천 단계</h2>
        <div className="space-y-4">
          {report.nextSteps.map((step, index) => (
            <div key={index} className="flex gap-4 items-start bg-white/80 border border-slate-100 rounded-[16px] p-4">
              <div className="bg-primary-light text-primary font-bold rounded-full w-8 h-8 flex items-center justify-center flex-shrink-0 mt-1">
                {index + 1}
              </div>
              <div>
                <span className="font-bold text-slate-800 block mb-1">{step.title}</span>
                <span className="text-slate-600 text-sm leading-relaxed">{step.description}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default InterviewReportView;
