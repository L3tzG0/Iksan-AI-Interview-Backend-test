import React, { useState, useCallback } from 'react';
import { UploadCloudIcon, FileTextIcon, ClockIcon, SparklesIcon } from './icons';
import Button from './ui/Button';
import type { InterviewReport, InterviewStartPayload, StudentGoal } from '../types';

interface WelcomeScreenProps {
  onStart: (input: InterviewStartPayload) => void;
  history?: InterviewReport[];
  onViewReport?: (report: InterviewReport) => void;
}

const MAX_SIZE_MB = 5;

const stats = [
  { label: '주간 모의면접', value: '+5%', sub: '지난 인터뷰 대비 전체 점수 5% 향상' },
  { label: '평균 준비 시간', value: '10분', sub: '세션당 권장 연습' },
];

const industries = [
  'IT/Software',
  'Manufacturing/Production',
  'Finance/Insurance',
  'Healthcare/Bio',
  'Education',
  'Marketing/Advertising',
  'Public/Non-Profit',
  'Other',
];

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onStart, history, onViewReport }) => {
  const [resumeText, setResumeText] = useState('');
  const [fileName, setFileName] = useState('');
  const [fileData, setFileData] = useState<{ data: string; mimeType: string } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [intent, setIntent] = useState<StudentGoal | null>(null);
  const [universities, setUniversities] = useState<string[]>(['']);
  const [major, setMajor] = useState('');
  const [workIndustry, setWorkIndustry] = useState('');
  const [workField, setWorkField] = useState('');
  const [perQuestionSeconds, setPerQuestionSeconds] = useState(60);
  const hasHistory = Array.isArray(history) && history.length > 0;

  const handleIncomingFile = useCallback((file?: File) => {
    if (!file) return;
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setResumeText(`파일 크기가 ${MAX_SIZE_MB}MB를 초과했습니다. 더 작은 파일을 업로드해주세요.`);
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
        setResumeText(`PDF 파일 "${file.name}"을(를) 불러왔어요. 주요 내용을 분석한 뒤 질문을 생성합니다.`);
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

  const handleIntentSelect = (goal: StudentGoal) => {
    setIntent(goal);
    if (goal === 'university') {
      setWorkField('');
      setWorkIndustry('');
      if (universities.length === 0) setUniversities(['']);
    } else {
      setMajor('');
      setWorkIndustry('');
      setUniversities(['']);
    }
  };

  const handleUniversityChange = (index: number, value: string) => {
    setUniversities((prev) => prev.map((item, i) => (i === index ? value : item)));
  };

  const handleAddUniversity = () => {
    if (universities.length >= 3) return;
    setUniversities((prev) => [...prev, '']);
  };

  const handleRemoveUniversity = (index: number) => {
    setUniversities((prev) => prev.filter((_, i) => i !== index));
  };

  const handleStartClick = () => {
    if (!intent) return;
    const cleanUniversities = universities.map((u) => u.trim()).filter(Boolean).slice(0, 3);
    const payload: InterviewStartPayload = {
      resumeText: fileData ? undefined : resumeText.trim(),
      fileData: fileData ?? undefined,
      intent,
      favoriteUniversities: intent === 'university' ? cleanUniversities : undefined,
      major: intent === 'university' ? major.trim() : undefined,
      workIndustry: intent === 'work' ? workIndustry : undefined,
      workField: intent === 'work' ? workField.trim() : undefined,
      perQuestionSeconds,
    };
    onStart(payload);
  };

  const hasBaseInput = !!fileData || !!resumeText.trim();
  const hasUniversityGoal = intent === 'university' && universities.some((u) => u.trim()) && !!major.trim();
  const hasWorkGoal = intent === 'work' && !!workField.trim() && !!workIndustry;
  const isStartDisabled = !hasBaseInput || !intent || (intent === 'university' ? !hasUniversityGoal : !hasWorkGoal);

  return (
    <div className="space-y-10 animate-fadeIn">
      <section className="relative overflow-hidden rounded-[32px] bg-gradient-to-r from-primary-lightest via-white to-primary-lightest shadow-soft border border-white/70 px-6 py-10 md:px-12 animate-softFadeUp">
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
        <div className="bg-white/95 rounded-[24px] shadow-elice border border-white/70 p-6 sm:p-8 animate-softFadeUp">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-1">자기소개서·이력서·생활기록부 업로드</h2>
              <p className="text-sm text-slate-500">경험·역량을 구체적으로 기재하면 더 정교한 질문이 생성됩니다.​</p>
            </div>
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-lightest text-primary text-xs font-semibold">
              <UploadCloudIcon className="w-4 h-4" />
              PDF/TXT
            </span>
          </div>
          <textarea
            className="w-full h-40 p-4 bg-slate-50/80 border border-slate-200 rounded-[18px] text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-focus focus:border-primary-focus transition-colors disabled:bg-slate-100 disabled:text-slate-500 resize-none"
            placeholder="내용을 입력해주세요."
            value={resumeText}
            onChange={handleTextChange}
            disabled={!!fileData}
          />
          <p className="text-xs text-slate-500 mt-2">
            PDF / TXT ({MAX_SIZE_MB}MB 이하) 파일을 업로드할 수 있습니다. 표/특수문자, 이미지가 많은 경우 텍스트로 변환해 붙여넣으면 정확도가 높습니다.
          </p>

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
                <span className="text-slate-700 font-medium">파일 업로드하기</span>
                <span className="text-slate-400 text-sm mt-2">PDF, TXT 파일을 업로드 할 수 있습니다.</span>
                <span className="text-slate-400 text-sm mt-2">표, 이미지, 특수문자가 많은 자료는 일부 정보가 누락될 수 있습니다.</span>
              </>
            )}
          </label>
          <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".txt,.pdf" />
          <div className="mt-8 space-y-4">
            <div className="grid sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => handleIntentSelect('work')}
                className={`rounded-[16px] border px-4 py-3 text-left transition-all ${
                  intent === 'work'
                    ? 'border-primary bg-primary-lightest text-primary shadow-soft'
                    : 'border-slate-200 bg-white/70 hover:border-primary/60'
                }`}
              >
                <p className="text-sm font-semibold">취업 면접을 준비해요​</p>
                <p className="text-xs text-slate-500 mt-1">희망 분야에 맞는 질문을 준비합니다.</p>
              </button>
              <button
                type="button"
                onClick={() => handleIntentSelect('university')}
                className={`rounded-[16px] border px-4 py-3 text-left transition-all ${
                  intent === 'university'
                    ? 'border-primary bg-primary-lightest text-primary shadow-soft'
                    : 'border-slate-200 bg-white/70 hover:border-primary/60'
                }`}
              >
                <p className="text-sm font-semibold">입시 면접을 준비해요​</p>
                <p className="text-xs text-slate-500 mt-1">선호 대학과 전공을 알려주세요.</p>
              </button>
            </div>

            {intent === 'university' && (
              <div className="rounded-[16px] border border-primary/30 bg-primary-lightest/60 p-4 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-slate-800">선호 대학 (최대 3개)</p>
                    <p className="text-xs text-slate-500">지원하고자 하는 대학을 최대 세 곳까지 추가하세요.</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddUniversity}
                    disabled={universities.length >= 3}
                    className="text-xs font-semibold text-primary disabled:text-slate-400"
                  >
                    + Add
                  </button>
                </div>
                <p className="text-xs text-slate-600 rounded-[12px] border border-primary/20 bg-white/70 px-3 py-2">
                  학생부를 기반으로, 면접에서 공유하려는 주요 경험(활동, 역량, 수상 등)이 담긴 자료를 업로드해주세요.
                </p>
                <div className="space-y-2">
                  {universities.map((uni, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={uni}
                        onChange={(e) => handleUniversityChange(index, e.target.value)}
                        placeholder={`대학교 ${index + 1}`}
                        className={`flex-1 rounded-lg border bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 outline-none ${
                          intent === 'university' && !uni.trim() ? 'border-red-300 focus:border-red-400' : 'border-slate-200 focus:border-primary'
                        }`}
                      />
                      {universities.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveUniversity(index)}
                          className="text-xs text-slate-400 hover:text-slate-600"
                        >
                          제거
                        </button>
                      )}
                    </div>
                  ))}
                  {intent === 'university' && !universities.some((u) => u.trim()) && (
                    <p className="text-xs text-red-600">최소 1개 대학을 입력해주세요.</p>
                  )}
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-slate-800">예정 전공</p>
                  <input
                    type="text"
                    value={major}
                    onChange={(e) => setMajor(e.target.value)}
                    placeholder="예: 컴퓨터 과학, 경영학, 심리학"
                    className={`w-full rounded-lg border bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 outline-none ${
                      intent === 'university' && !major.trim() ? 'border-red-300 focus:border-red-400' : 'border-slate-200 focus:border-primary'
                    }`}
                  />
                  {intent === 'university' && !major.trim() && <p className="text-xs text-red-600">전공을 입력하면 더 정교한 질문을 만들어요.</p>}
                </div>
              </div>
            )}

            {intent === 'work' && (
            <div className="rounded-[16px] border border-primary/30 bg-primary-lightest/60 p-4 space-y-3">
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-800">관심 산업</p>
                <p className="text-xs text-slate-500">희망하는 산업군을 선택하세요.</p>
                <select
                  value={workIndustry}
                  onChange={(e) => setWorkIndustry(e.target.value)}
                  className="w-full rounded-lg border bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 outline-none border-slate-200 focus:border-primary"
                >
                  <option value="">산업을 선택하세요</option>
                  {industries.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                {intent === 'work' && !workIndustry && <p className="text-xs text-red-600">관심 산업을 선택해주세요.</p>}
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-slate-800">희망 직무/역할</p>
                <p className="text-xs text-slate-500">구체적인 역할을 입력하면 맞춤형 질문을 생성해요.</p>
                <input
                  type="text"
                  value={workField}
                  onChange={(e) => setWorkField(e.target.value)}
                  placeholder="예: 프론트엔드 개발자, 생산관리, 데이터 분석"
                  className={`w-full rounded-lg border bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 outline-none ${
                    intent === 'work' && !workField.trim() ? 'border-red-300 focus:border-red-400' : 'border-slate-200 focus:border-primary'
                  }`}
                />
                {intent === 'work' && !workField.trim() && <p className="text-xs text-red-600">희망 직무를 입력해주세요.</p>}
              </div>
            </div>
          )}

            <div className="rounded-[16px] border border-slate-200 bg-white/80 p-4 space-y-2">
              <p className="text-sm font-semibold text-slate-800">답변 시간 선택​</p>
              <p className="text-xs text-slate-500">각 질문에 할당할 시간을 선택하세요.</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[30, 60, 90, 120].map((seconds) => (
                  <button
                    type="button"
                    key={seconds}
                    onClick={() => setPerQuestionSeconds(seconds)}
                    className={`py-2 px-3 rounded-[12px] border text-sm font-semibold transition-colors ${
                      perQuestionSeconds === seconds
                        ? 'bg-primary text-white border-primary'
                        : 'bg-white text-slate-700 border-slate-200 hover:border-primary/70'
                    }`}
                  >
                    {seconds}초
                  </button>
                ))}
              </div>
            </div>

            <Button onClick={handleStartClick} disabled={isStartDisabled} fullWidth className="py-4 text-base">
              모의면접 시작하기​
            </Button>
          </div>
        </div>

        {hasHistory ? (
          <div className="bg-white/90 rounded-[24px] border border-white/80 shadow-soft p-6 flex flex-col animate-softFadeUp-delayed">
            <h2 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
              <ClockIcon className="w-5 h-5 text-primary" />
              최근 연습 기록
            </h2>
            <p className="text-xs text-slate-500 mb-4">지난 AI 면접 결과를 눌러 상세 피드백을 다시 확인해 보세요.</p>
            <div className="flex-1 overflow-auto divide-y divide-slate-100">
              {history!.map((item, index) => (
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
        ) : null}
      </div>
    </div>
  );
};

export default WelcomeScreen;
