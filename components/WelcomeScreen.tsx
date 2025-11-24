import React, { useState, useCallback } from 'react';
import { UploadCloudIcon, FileTextIcon, ClockIcon, SparklesIcon } from './icons';
import Button from './ui/Button';
import type { InterviewReport } from '../types';

interface WelcomeScreenProps {
  onStart: (input: string | { data: string; mimeType: string }) => void;
  history?: InterviewReport[];
  onViewReport?: (report: InterviewReport) => void;
}

const MAX_SIZE_MB = 5;

const stats = [
  { label: '주간 모의면접', value: '15회', sub: 'AI 맞춤 질문 제공' },
  { label: '평균 준비 시간', value: '10분', sub: '세션당 권장 연습' },
];

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onStart, history, onViewReport }) => {
  const [resumeText, setResumeText] = useState('');
  const [fileName, setFileName] = useState('');
  const [fileData, setFileData] = useState<{ data: string; mimeType: string } | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleIncomingFile = useCallback((file?: File) => {
    if (!file) return;
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setResumeText(`파일 용량이 ${MAX_SIZE_MB}MB를 초과했습니다. 더 작은 파일을 업로드해 주세요.`);
      return;
    }

    setFileName(file.name);
    setResumeText('');
    setFileData(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      if (file.type === 'application/pdf') {
        const base64Data = result.split(',')[1];
        setFileData({ data: base64Data, mimeType: file.type });
        setResumeText(`PDF 파일 "${file.name}"을(를) 불러왔어요. 주요 내용을 분석해 맞춤 질문을 생성합니다.`);
      } else {
        setResumeText(result);
      }
    };
    reader.onerror = () => {
      setResumeText(`오류: 파일 "${file.name}"을(를) 읽어오지 못했어요. 다시 시도해 주세요.`);
    };

    if (file.type === 'application/pdf') {
      reader.readAsDataURL(file);
    } else {
      reader.readAsText(file);
    }
  }, []);

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    handleIncomingFile(event.target.files?.[0]);
  }, [handleIncomingFile]);

  const handleDrop = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files?.[0];
    handleIncomingFile(file);
  };

  const handleDragOver = (event: React.DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFileName('');
    setFileData(null);
    setResumeText(e.target.value);
  };

  const handleStartClick = () => {
    if (fileData) {
      onStart(fileData);
    } else {
      onStart(resumeText);
    }
  };

  const isStartDisabled = !resumeText.trim() && !fileData;

  return (
    <div className="space-y-10 animate-fadeIn">
      <section className="relative overflow-hidden rounded-[32px] bg-gradient-to-r from-primary-lightest via-white to-primary-lightest shadow-soft border border-white/70 px-6 py-10 md:px-12">
        <div className="hero-blob hero-blob--primary -right-10 -top-10"></div>
        <div className="hero-blob hero-blob--secondary -left-10 bottom-0"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center gap-8">
          <div>
            <p className="text-sm font-semibold text-primary-text uppercase tracking-[0.2em] mb-3 flex items-center gap-2">
              <SparklesIcon className="w-4 h-4" />
              AI 모의면접 코치
            </p>
            <h1 className="text-3xl md:text-4xl font-bold text-slate-900 leading-tight mb-4">
              나만의 스토리로 준비하는<br /> 친구 같은 AI 면접 코치
            </h1>
            <p className="text-slate-600 leading-relaxed">
              간단히 자기소개서나 이력서를 붙여넣으면, 목표 학과와 직무에 맞춘 질문을 추천해 드려요.
              <br className="hidden md:block" />
              PDF 파일도 바로 업로드하여 빠르게 분석하고 연습을 시작할 수 있습니다.
            </p>
          </div>
          <div className="flex flex-1 flex-wrap gap-4">
            {stats.map((item) => (
              <div key={item.label} className="flex-1 min-w-[140px] rounded-2xl bg-white/90 border border-white/70 p-4 text-center shadow-soft">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">{item.label}</p>
                <p className="text-3xl font-bold text-primary mt-2">{item.value}</p>
                <p className="text-xs text-slate-500 mt-1">{item.sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="w-full mx-auto max-w-5xl grid lg:grid-cols-[3fr_2fr] gap-8">
        <div className="bg-white/95 rounded-[24px] shadow-elice border border-white/70 p-6 sm:p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-1">이력서 붙여넣기 / 업로드</h2>
              <p className="text-sm text-slate-500">작성 중인 자기소개서나 활동 기록을 입력하면 맞춤 질문을 추천해 드려요.</p>
            </div>
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-lightest text-primary text-xs font-semibold">
              <UploadCloudIcon className="w-4 h-4" />
              PDF / TXT / MD
            </span>
          </div>
          <textarea
            className="w-full h-40 p-4 bg-slate-50/80 border border-slate-200 rounded-[18px] text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-focus focus:border-primary-focus transition-colors disabled:bg-slate-100 disabled:text-slate-500 resize-none"
            placeholder="이력서나 자기소개서를 붙여넣어 주세요. 핵심 경험과 강점을 적어둘수록 더 정교한 질문이 생성됩니다."
            value={resumeText}
            onChange={handleTextChange}
            disabled={!!fileData}
          />

          <div className="flex items-center justify-center w-full my-6">
            <div className="flex-grow border-t border-slate-200"></div>
            <span className="text-slate-400 mx-4 flex-shrink-0 text-sm font-medium uppercase tracking-widest">or</span>
            <div className="flex-grow border-t border-slate-200"></div>
          </div>

          <label
            htmlFor="file-upload"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`w-full cursor-pointer border-2 border-dashed rounded-[20px] p-8 flex flex-col items-center justify-center transition-all duration-300 group text-center ${
              isDragging ? 'border-primary bg-primary-lightest/80' : 'border-slate-200 bg-slate-50/90 hover:border-primary hover:bg-primary-lightest'
            }`}
          >
            {fileName ? (
              <>
                <FileTextIcon className="w-12 h-12 text-primary mb-3" />
                <span className="text-slate-700 font-semibold text-lg">{fileName}</span>
                <span className="text-slate-500 text-sm mt-2">새 파일이 업로드되었습니다</span>
              </>
            ) : (
              <>
                <UploadCloudIcon className="w-12 h-12 text-slate-400 group-hover:text-primary mb-3 transition-colors" />
                <span className="text-slate-700 font-medium">파일을 드래그하거나 선택해 업로드하세요</span>
                <span className="text-slate-400 text-sm mt-2">PDF, TXT, MD · 최대 {MAX_SIZE_MB}MB</span>
              </>
            )}
          </label>
          <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".txt,.md,.pdf" />

          <Button onClick={handleStartClick} disabled={isStartDisabled} fullWidth className="mt-8 py-4 text-base">
            면접 연습 시작하기
          </Button>
        </div>

        {history && history.length > 0 ? (
          <div className="bg-white/90 rounded-[24px] border border-white/80 shadow-soft p-6 flex flex-col">
            <h2 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
              <ClockIcon className="w-5 h-5 text-primary" />
              최근 연습 기록
            </h2>
            <p className="text-xs text-slate-500 mb-4">지난 AI 면접 결과를 눌러 상세 피드백을 다시 확인해 보세요.</p>
            <div className="flex-1 overflow-auto divide-y divide-slate-100">
              {history.map((item, index) => (
                <button
                  key={index}
                  onClick={() => onViewReport && onViewReport(item)}
                  className="w-full text-left py-4 px-2 hover:bg-primary-lightest/50 rounded-[12px] transition-all flex items-center justify-between group"
                >
                  <div>
                    <p className="font-semibold text-slate-700 group-hover:text-primary transition-colors">
                      {item.date || '날짜 정보 없음'}
                    </p>
                    <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 text-green-600 font-semibold">
                        총점 <strong className="text-slate-900 ml-2">{item.totalScore.toFixed(1)}</strong>/10
                      </span>
                    </div>
                  </div>
                  <div className="text-sm text-primary font-semibold">
                    결과 열기 →
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-white/80 rounded-[24px] border border-dashed border-primary-light p-6 flex flex-col items-center justify-center text-center text-slate-500">
            <ClockIcon className="w-10 h-10 text-primary/70 mb-3" />
            <p className="font-semibold text-slate-700 mb-2">아직 기록이 없어요</p>
            <p className="text-xs text-slate-400">AI 코치와 첫 면접을 진행하면 이곳에 리포트가 쌓입니다.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default WelcomeScreen;
