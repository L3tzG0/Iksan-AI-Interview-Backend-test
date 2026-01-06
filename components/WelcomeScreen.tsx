import React, { useState, useCallback, useMemo } from 'react';
import { UploadCloudIcon, FileTextIcon, SparklesIcon } from './icons';
import Button from './ui/Button';
import type { InterviewReport, InterviewStartPayload, StudentGoal } from '../types';

interface WelcomeScreenProps {
  onStart: (input: InterviewStartPayload) => void;
  history?: InterviewReport[];
  remainingAttempts?: number | null;
}

const MAX_SIZE_MB = 5;

const industries = [
'상업',
'기계',
'전기·전자',
'컴퓨터',
'디자인·예술',
'건설업',
'화학·환경',
'조리·식품가공',
'관광·서비스',
'자동차',
];

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onStart, history, remainingAttempts }) => {
  const [resumeText, setResumeText] = useState('');
  const [fileName, setFileName] = useState('');
  const [fileData, setFileData] = useState<{ data: string; mimeType: string } | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [intent, setIntent] = useState<StudentGoal | null>(null);
  const [universities, setUniversities] = useState<string[]>(['']);
  const [major, setMajor] = useState('');
  const [workIndustry, setWorkIndustry] = useState('');
  const [workField, setWorkField] = useState('');
  const [perQuestionSeconds, setPerQuestionSeconds] = useState(60);
  const stats = useMemo(() => {
    const getScore = (r?: InterviewReport) => {
      if (!r) return 0;
      if (typeof r.overallScore === 'number') return r.overallScore;
      if (typeof r.totalScore === 'number') return r.totalScore;
      const vals = Object.values(r.scores || {});
      return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
    };

    const latestReport = history?.[0];
    const previousReport = history?.[1];
    const improvementRaw = getScore(latestReport) - getScore(previousReport);
    const improvement = `${improvementRaw >= 0 ? '+' : ''}${Math.round(improvementRaw)}%`;

    const now = Date.now();
    const weekAgo = now - 7 * 24 * 60 * 60 * 1000;
    const weeklyCount =
      (history || []).filter((r) => {
        if (!r?.date) return false;
        const ts = Date.parse(r.date);
        return !Number.isNaN(ts) && ts >= weekAgo;
      }).length || (history ? history.length : 0);

    const latestFeedback = latestReport?.detailedFeedback || [];
    const avgPauseSeconds =
      latestFeedback.length > 0
        ? latestFeedback.reduce((sum, item) => sum + (item.total_pause_duration_seconds || 0), 0) /
          latestFeedback.length
        : 0;
    const prepSeconds =
      avgPauseSeconds > 0
        ? Math.round(avgPauseSeconds)
        : Math.round(
            latestFeedback.reduce((sum, item) => sum + (item.audio_duration_seconds || 0), 0) /
              (latestFeedback.length || 1)
          );
    const prepLabel =
      prepSeconds > 0
        ? `${Math.floor(prepSeconds / 60)}분 ${prepSeconds % 60}초`
        : `${perQuestionSeconds}초`;

    /*
    const tiles = [
      { label: '주간 모의면접', value: improvement, sub: `최근 7일 인터뷰 ${weeklyCount}회` },
      { label: '평균 준비 시간', value: prepLabel, sub: '세션당 평균 준비' },
      {
        label: '남은 시도',
        value: typeof remainingAttempts === 'number' ? remainingAttempts : '--',
        sub: '학생 계정 기준',
      },
    ];
    return tiles;
    */
    // Tiles removed — return empty array so the header area is rendered with a custom layout instead
    return [];
  }, [history, perQuestionSeconds, remainingAttempts]);

  const handleIncomingFile = useCallback((file?: File) => {
    if (!file) return;
    const lowerName = file.name.toLowerCase();
    const isPdf = file.type === 'application/pdf' || lowerName.endsWith('.pdf');
    const isDocx =
      file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
      lowerName.endsWith('.docx');
    const isAllowed = isPdf || isDocx;
    if (!isAllowed) {
      setFileName('');
      setFileData(null);
      setFileError('PDF 또는 DOCX 파일만 업로드할 수 있습니다.');
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setFileName('');
      setFileData(null);
      setFileError(`파일 크기가 ${MAX_SIZE_MB}MB를 초과했습니다. 더 작은 파일을 업로드해주세요.`);
      return;
    }

    setFileName(file.name);
    setResumeText('');
    setFileData(null);
    setFileError(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      const mimeType = isDocx
        ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        : 'application/pdf';
      const base64Data = result.split(',')[1];
      setFileData({ data: base64Data, mimeType });
      setResumeText(`파일 "${file.name}"을(를) 불러왔어요. 주요 내용을 분석한 뒤 질문을 생성합니다.`);
    };
    reader.onerror = () => {
      setResumeText(`오류: 파일 "${file.name}"을(를) 읽어오지 못했어요. 다시 시도해 주세요.`);
    };

    reader.readAsDataURL(file);
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
    setFileError(null);
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

  const hasBaseInput = (!!fileData || !!resumeText.trim()) && !fileError;
  // For university intent we only require the upload (student record) and the per-question time.
  // The previous UI asked for preferred universities and major; that form is commented out below.
  const hasUniversityGoal = intent === 'university';
  const hasWorkGoal = intent === 'work' && !!workField.trim() && !!workIndustry;
  const isStartDisabled = !hasBaseInput || !intent || (intent === 'university' ? !hasUniversityGoal : !hasWorkGoal);

  return (
    <div className="space-y-0 animate-fadeIn">
      <div className="relative px-6 md:px-3 py-3 overflow-hidden animate-softFadeUp">
        {/* <div className="-top-10 -right-10 hero-blob hero-blob--primary"></div> */}
        {/* <div className="bottom-0 -left-10 hero-blob hero-blob--secondary"></div> */}
        <div className="z-10 relative flex md:flex-row flex-col md:items-center gap-8">
          {/* <div>
            <p className="flex items-center gap-2 mb-3 font-semibold text-primary-text text-sm uppercase tracking-[0.2em]">
              AI 모의면접 코치
            </p>
            <h1 className="mb-4 font-bold text-slate-900 text-3xl md:text-4xl leading-tight">
              나만의 스토리로 준비하는<br /> 친구 같은 AI 면접 코치
            </h1>
            <p className="text-slate-600 leading-relaxed">
              간단히 자기소개서나 이력서를 붙여넣으면, 목표 학과와 직무에 맞춘 질문을 추천해 드려요.
              <br className="hidden md:block" />
              PDF 파일도 바로 업로드하여 빠르게 분석하고 연습을 시작할 수 있습니다.
            </p>
          </div> */}
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-slate-900 text-3xl">면접 준비하기​</div>
              <div className="text-sm font-semibold text-slate-700 bg-white/90 px-4 py-2 rounded-lg border border-slate-200">
                (남은 횟수: {typeof remainingAttempts === 'number' ? remainingAttempts : "--"}회)
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full mx-auto grid gap-3 lg:grid-cols-1">
        <div className="bg-white/95 shadow-soft p-6 sm:p-8 border border-white/70 rounded-[24px] animate-softFadeUp">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="mb-1 font-bold text-slate-900 text-lg">자기소개서·이력서·생활기록부 업로드</h2>
              <p className="text-slate-500 text-sm">경험·역량을 구체적으로 기재하면 더 정교한 질문이 생성됩니다.​</p>
            </div>
            <span className="inline-flex items-center gap-2 bg-primary-lightest px-3 py-1 rounded-full font-semibold text-primary text-xs">
              <UploadCloudIcon className="w-4 h-4" />
              PDF/DOCX
            </span>
          </div>
          <div className="grid gap-y-8 lg:grid-cols-2">
            <div className="space-y-1 lg:pr-6 lg:border-r lg:border-dashed lg:border-slate-200">
              <textarea
                className="bg-slate-50/80 disabled:bg-slate-100 p-4 border border-slate-200 focus:border-primary-focus rounded-[18px] focus:outline-none focus:ring-2 focus:ring-primary-focus w-full h-35 text-slate-800 disabled:text-slate-500 transition-colors resize-none placeholder-slate-400"
                placeholder="내용을 입력해주세요."
                value={resumeText}
                onChange={handleTextChange}
                disabled={!!fileData}
              />
              {/* <p className="text-slate-500 text-xs">
                PDF / DOCX ({MAX_SIZE_MB}MB 이하) 파일을 업로드할 수 있습니다. 표/특수문자, 이미지가 많은 경우 텍스트로 변환해 붙여넣으면 정확도가 높습니다.
              </p> */}
              {fileError && <p className="text-xs text-rose-600 font-semibold">{fileError}</p>}

              <div className="flex justify-center items-center w-full">
                <div className="flex-grow border-slate-200 border-t"></div>
                <span className="flex-shrink-0 mx-4 font-medium text-slate-400 text-base uppercase tracking-widest">or</span>
                <div className="flex-grow border-slate-200 border-t"></div>
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
                    <FileTextIcon className="mb-3 w-12 h-12 text-primary" />
                    <span className="font-semibold text-slate-700 text-lg">{fileName}</span>
                    <span className="mt-2 text-slate-500 text-sm">새 파일이 업로드되었습니다</span>
                  </>
                ) : (
                  <>
                    <UploadCloudIcon className="mb-3 w-12 h-12 text-slate-400 group-hover:text-primary transition-colors" />
                    <span className="font-medium text-slate-700">파일 업로드하기</span>
                    <span className="mt-2 text-slate-400 text-sm">PDF, DOCX 파일(5MB 이하)을 업로드 할 수 있습니다.​</span>
                    <span className="text-slate-400 text-sm">{intent === "work" ? `표, 이미지, 특수문자가 많은 자료는 일부 정보가 누락될 수 있습니다.` : '표, 이미지, 특수문자가 많은 자료는 일부 정보가 누락될 수 있습니다.'}</span>
                  </>
                )}
              </label>
              <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".pdf,.docx" />
            </div>

            <div className="space-y-4 lg:pl-6">
              <div className="gap-3 grid sm:grid-cols-2">
                <button
                type="button"
                onClick={() => handleIntentSelect('work')}
                className={`rounded-[16px] border px-4 py-3 text-left transition-all duration-200 ease-out transform ${
                  intent === 'work'
                    ? 'border-primary bg-primary-lightest text-primary shadow-md -translate-y-0.5 scale-[1.01] ring-1 ring-primary/20'
                    : 'border-slate-200 bg-white/70 hover:border-primary/60 hover:-translate-y-0.5 hover:shadow-md'
                }`}
              >
                  <p className="font-semibold text-sm">취업 면접을 준비해요​</p>
                  {/* <p className="mt-1 text-slate-500 text-xs">희망 분야에 맞는 질문을 준비합니다.</p> */}
                </button>
                <button
                type="button"
                onClick={() => handleIntentSelect('university')}
                className={`rounded-[16px] border px-4 py-3 text-left transition-all duration-200 ease-out transform ${
                  intent === 'university'
                    ? 'border-primary bg-primary-lightest text-primary shadow-md -translate-y-0.5 scale-[1.01] ring-1 ring-primary/20'
                    : 'border-slate-200 bg-white/70 hover:border-primary/60 hover:-translate-y-0.5 hover:shadow-md'
                }`}
              >
                  <p className="font-semibold text-sm">입시 면접을 준비해요​</p>
                  {/* <p className="mt-1 text-slate-500 text-xs">선호 대학과 전공을 알려주세요.</p> */}
                </button>
              </div>

              {/* University preference form commented out.
              We no longer ask for preferred universities or major here.
              For university intent we only request the student record upload and per-question time selection.

            {intent === 'university' && (
              <div className="space-y-3 bg-primary-lightest/60 p-4 border border-primary/30 rounded-[16px]">
                <div className="flex justify-between items-start gap-3">
                  <div className="flex-1">
                    <p className="font-semibold text-slate-800 text-sm">선호 대학 (최대 3개)</p>
                    <p className="text-slate-500 text-xs">지원하고자 하는 대학을 최대 세 곳까지 추가하세요.</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddUniversity}
                    disabled={universities.length >= 3}
                    className="font-semibold text-primary disabled:text-slate-400 text-xs"
                  >
                    + Add
                  </button>
                </div>
                <div className="space-y-2">
                  {universities.map((uni, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={uni}
                        onChange={(e) => handleUniversityChange(index, e.target.value)}
                        placeholder={`대학 ${index + 1}`}
                        className={`flex-1 rounded-lg border bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 outline-none ${
                          intent === 'university' && !uni.trim() ? 'border-red-300 focus:border-red-400' : 'border-slate-200 focus:border-primary'
                        }`}
                      />
                      {universities.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveUniversity(index)}
                          className="text-slate-400 hover:text-slate-600 text-xs"
                        >
                          삭제
                        </button>
                      )}
                    </div>
                  ))}
                  {intent === 'university' && !universities.some((u) => u.trim()) && (
                    <p className="text-red-600 text-xs">최소 1개 대학을 입력해주세요.</p>
                  )}
                </div>
                <div className="space-y-1">
                  <p className="font-semibold text-slate-800 text-sm">전공 분야</p>
                  <input
                    type="text"
                    value={major}
                    onChange={(e) => setMajor(e.target.value)}
                    placeholder="예: 컴퓨터 공학, 경영, 디자인"
                    className={`w-full rounded-lg border bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 outline-none ${
                      intent === 'university' && !major.trim() ? 'border-red-300 focus:border-red-400' : 'border-slate-200 focus:border-primary'
                    }`}
                  />
                  {intent === 'university' && !major.trim() && <p className="text-red-600 text-xs">전공 분야를 입력해주세요.</p>}
                </div>
              </div>
            )}
            */}

              {intent === 'university' && (
                <div className="space-y-3 bg-primary-lightest/60 p-4 border border-primary/30 rounded-[16px]">
                  <p className="text-slate-600 text-sm">학생부를 기반으로, 면접에서 공유하려는 주요 경험(활동, 역량, 수상 등)이 담긴 자료를 업로드해주세요.</p>
                </div>
              )}

              {intent === 'work' && (
              <div className="space-y-3 bg-primary-lightest/60 p-4 border border-primary/30 rounded-[16px]">
                <div className="space-y-1">
                  <p className="font-semibold text-slate-800 text-sm">지원 분야</p>
                  <p className="text-slate-500 text-xs">어떤 분야에 지원할 계획인가요.</p>
                  <select
                    value={workIndustry}
                    onChange={(e) => setWorkIndustry(e.target.value)}
                    className="bg-white px-3 py-2 border border-slate-200 focus:border-primary rounded-lg outline-none focus:ring-2 focus:ring-primary/30 w-full text-sm"
                  >
                    <option value="">분야를 선택하세요</option>
                    {industries.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                  {intent === 'work' && !workIndustry && <p className="text-red-600 text-xs">지원 분야를 선택해주세요.</p>}
                </div>
                <div className="space-y-1">
                  <p className="font-semibold text-slate-800 text-sm">직무/포지션</p>
                  <p className="text-slate-500 text-xs">어떤 직무를 준비하고 계신가요.</p>
                  <input
                    type="text"
                    value={workField}
                    onChange={(e) => setWorkField(e.target.value)}
                    placeholder="예: 프론트엔드 개발자, 마케팅, 데이터 분석"
                    className={`w-full rounded-lg border bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-primary/30 outline-none ${
                      intent === 'work' && !workField.trim() ? 'border-red-300 focus:border-red-400' : 'border-slate-200 focus:border-primary'
                    }`}
                  />
                  {intent === 'work' && !workField.trim() && <p className="text-red-600 text-xs">직무를 입력해주세요.</p>}
                </div>
              </div>
            )}

              <div className="space-y-2 bg-white/80 p-4 border border-slate-200 rounded-[16px]">
                <p className="font-semibold text-slate-800 text-sm">답변 시간 선택​</p>
                {/* <p className="text-slate-500 text-xs">각 질문별 답변 준비 시간을 선택하세요.</p> */}
                <div className="gap-2 grid grid-cols-2 sm:grid-cols-4">
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
        </div>

      </div>
    </div>
  );
};

export default WelcomeScreen;
