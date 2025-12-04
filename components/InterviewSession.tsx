// Fix: Added type definitions for the Web Speech API to resolve TypeScript errors about SpeechRecognition.
// Manually define types for the Web Speech API as they are not standard in all TS lib files.
interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  [index: number]: SpeechRecognitionAlternative;
  length: number;
}

interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
}

// Extend the Window interface
declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognition;
    webkitSpeechRecognition?: new () => SpeechRecognition;
  }
}

import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { Question, Answer } from '../types';
import Card from './Card';
import Button from './ui/Button';
import { LightbulbIcon, ClockIcon } from './icons';
import VoiceAnswerArea from './interview/VoiceAnswerArea';

interface InterviewSessionProps {
  questions: Question[];
  onFinish: (answers: Answer[]) => void;
  perQuestionSeconds?: number;
  onExit?: () => void;
}

const InterviewSession: React.FC<InterviewSessionProps> = ({ questions, onFinish, perQuestionSeconds = 60, onExit }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeechSupported, setIsSpeechSupported] = useState(true);
  const [timeLeft, setTimeLeft] = useState(perQuestionSeconds);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(null);
  const [isTimerPaused, setIsTimerPaused] = useState(false);
  const [isTimerVisible, setIsTimerVisible] = useState(true);
  const [isTimerInView, setIsTimerInView] = useState(true);
  const [micPermission, setMicPermission] = useState<'unknown' | 'granted' | 'denied'>('unknown');
  const [drafts, setDrafts] = useState<Record<number, { text: string; audioUrl?: string }>>(() => {
    if (typeof window === 'undefined') return {};
    try {
      const cached = sessionStorage.getItem('ai-interview-draft');
      return cached ? JSON.parse(cached) : {};
    } catch {
      return {};
    }
  });

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const finalTranscriptRef = useRef('');
  const isRecordingRef = useRef(isRecording);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const inlineTimerRef = useRef<HTMLDivElement | null>(null);

  const requestMicPermission = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setMicPermission('denied');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setMicPermission('granted');
      stream.getTracks().forEach((track) => track.stop());
    } catch (err) {
      setMicPermission('denied');
      throw err;
    }
  }, []);

  useEffect(() => {
    isRecordingRef.current = isRecording;
  }, [isRecording]);

  useEffect(() => {
    if (!inlineTimerRef.current) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        setIsTimerInView(entry.isIntersecting);
      },
      { threshold: 0.4 }
    );
    observer.observe(inlineTimerRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!navigator.permissions?.query) return;
    navigator.permissions
      .query({ name: 'microphone' as PermissionName })
      .then((result) => {
        if (result.state === 'granted') setMicPermission('granted');
        if (result.state === 'denied') setMicPermission('denied');
        result.onchange = () => {
          if (result.state === 'granted') setMicPermission('granted');
          else if (result.state === 'denied') setMicPermission('denied');
          else setMicPermission('unknown');
        };
      })
      .catch(() => {
        setMicPermission('unknown');
      });
  }, []);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = '연습 세션을 종료하면 진행 중인 답변이 사라집니다. 나가시겠습니까?';
    };
    const handlePopState = () => {
      const leave = window.confirm('연습 세션을 종료하면 진행 중인 답변이 사라집니다. 나가시겠습니까?');
      if (!leave) {
        window.history.pushState(null, '', window.location.href);
      } else if (onExit) {
        window.history.replaceState(null, '', '/');
        onExit();
      } else {
        window.location.href = '/';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.history.pushState(null, '', window.location.href);
    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [onExit]);
  const updateDraft = useCallback((questionId: number, data: Partial<{ text: string; audioUrl?: string }>) => {
    setDrafts((prev) => {
      const next = { ...prev, [questionId]: { ...(prev[questionId] || {}), ...data } };
      try {
        sessionStorage.setItem('ai-interview-draft', JSON.stringify(next));
      } catch {
        // ignore storage errors
      }
      return next;
    });
  }, []);

  const stopAudioRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const stopCurrentRecording = useCallback(() => {
    if (isRecordingRef.current) {
      setIsRecording(false);
      recognitionRef.current?.stop();
      stopAudioRecording();
    }
  }, [stopAudioRecording]);

  const isLowTime = timeLeft <= 15;
  useEffect(() => {
    if (!isLowTime || isTimerPaused) return;
    try {
      const context = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = context.createOscillator();
      const gainNode = context.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, context.currentTime);
      gainNode.gain.setValueAtTime(0.05, context.currentTime);
      oscillator.connect(gainNode).connect(context.destination);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.1);
    } catch {
      // Audio may be blocked; fail silently.
    }
  }, [isLowTime, isTimerPaused]);

  const startAudioRecording = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setMicPermission('granted');
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setRecordedAudioUrl(url);
        const question = questions[currentQuestionIndex];
        if (question) {
          updateDraft(question.id, { audioUrl: url, text: currentAnswer });
        }
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
    } catch (err) {
      setMicPermission('denied');
      console.error('Microphone access denied or failed', err);
    }
  }, [currentAnswer, currentQuestionIndex, questions, updateDraft]);

  const handleNext = useCallback((options?: { allowEmpty?: boolean; skipReason?: string }) => {
    const question = questions[currentQuestionIndex];
    if (!question) return;

    stopCurrentRecording();
    const trimmed = currentAnswer.trim();
    if (!options?.allowEmpty && !trimmed) {
      setInlineError('답변이 비어 있어요. 최소 한 문장을 작성해 주세요.');
      return;
    }

    const answerText = trimmed || options?.skipReason || '이 질문을 건너뛰겠습니다.';
    setInlineError(null);

    const newAnswer: Answer = {
      questionId: question.id,
      text: answerText,
      audioUrl: recordedAudioUrl || drafts[question.id]?.audioUrl,
    };
    const updatedAnswers = [...answers, newAnswer];
    setAnswers(updatedAnswers);

    if (currentQuestionIndex === questions.length - 1) {
      onFinish(updatedAnswers);
    } else {
      setCurrentQuestionIndex((prev) => prev + 1);
      setTimeLeft(perQuestionSeconds);
      setIsTimerPaused(false);
    }
  }, [answers, currentAnswer, currentQuestionIndex, drafts, onFinish, questions, recordedAudioUrl, stopCurrentRecording]);

  useEffect(() => {
    setTimeLeft(perQuestionSeconds);
    setInlineError(null);
  }, [currentQuestionIndex, perQuestionSeconds]);

  useEffect(() => {
    if (isTimerPaused) return;
    const timerId = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timerId);
  }, [currentQuestionIndex, isTimerPaused]);

  useEffect(() => {
    if (timeLeft === 0 && !isTimerPaused) {
      if (!currentAnswer.trim()) {
        setInlineError('시간이 다 되었습니다. 답변을 작성하거나 타이머를 일시정지해 주세요.');
        setIsTimerPaused(true);
        return;
      }
      handleNext();
    }
  }, [timeLeft, isTimerPaused, currentAnswer, handleNext]);

  useEffect(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      setIsSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognitionAPI();
    recognitionRef.current = recognition;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'ko-KR';

    recognition.onresult = (event) => {
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscriptRef.current += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }
      const fullTranscript = (finalTranscriptRef.current + ' ' + interimTranscript).trim();
      setCurrentAnswer(fullTranscript);
      updateDraft(currentQuestion.id, { text: fullTranscript });
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error === 'no-speech') return;
      console.error('Speech recognition error:', event.error);
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        setIsSpeechSupported(false);
        setIsRecording(false);
      }
    };

    recognition.onend = () => {
      if (isRecordingRef.current) {
        try {
          recognition.start();
        } catch (e) {
          console.error('Recognition restart failed', e);
        }
      }
    };

    return () => {
      isRecordingRef.current = false;
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.stop();
      }
      stopAudioRecording();
    };
  }, [stopAudioRecording]);

  const toggleRecording = () => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      setIsSpeechSupported(false);
      return;
    }
    if (micPermission === 'denied') {
      setInlineError('마이크 권한이 필요합니다. 브라우저 설정에서 허용해 주세요.');
      return;
    }
    if (micPermission === 'unknown') {
      requestMicPermission().catch(() => setInlineError('마이크 권한 요청에 실패했습니다.'));
      return;
    }

    const newIsRecording = !isRecording;
    setIsRecording(newIsRecording);
    setInlineError(null);

    if (newIsRecording) {
      finalTranscriptRef.current = '';
      recognitionRef.current?.start();
      startAudioRecording().catch((err) => console.error('Audio recording failed', err));
    } else {
      recognitionRef.current?.stop();
      stopAudioRecording();
    }
  };

  useEffect(() => {
    const question = questions[currentQuestionIndex];
    if (!question) return;
    const draft = drafts[question.id];
    const text = draft?.text || '';
    setCurrentAnswer(text);
    finalTranscriptRef.current = text;
    setRecordedAudioUrl(draft?.audioUrl || null);
    setInlineError(null);
    setIsTimerPaused(false);
    stopCurrentRecording();
  }, [currentQuestionIndex, drafts, questions, stopCurrentRecording]);

  useEffect(() => {
    const question = questions[currentQuestionIndex];
    if (!question) return;
    updateDraft(question.id, { text: currentAnswer });
  }, [currentAnswer, currentQuestionIndex, questions, updateDraft]);

  useEffect(() => {
    const question = questions[currentQuestionIndex];
    if (!question || !recordedAudioUrl) return;
    updateDraft(question.id, { audioUrl: recordedAudioUrl });
  }, [recordedAudioUrl, currentQuestionIndex, questions, updateDraft]);

  const handleSkipQuestion = () => {
    const question = questions[currentQuestionIndex];
    if (!question) return;
    const hasAnyAnswer = answers.some((answer) => answer.text.trim().length > 0 || answer.audioUrl);
    if (!hasAnyAnswer && !currentAnswer.trim()) {
      setInlineError('첫 질문은 비워둘 수 없어요. 최소 한 문장을 작성해 주세요.');
      return;
    }
    handleNext({ allowEmpty: true, skipReason: '이 질문을 건너뛰겠습니다. 다음 질문으로 넘어갈게요.' });
  };

  const handleRetryAnswer = () => {
    setCurrentAnswer('');
    finalTranscriptRef.current = '';
    setRecordedAudioUrl(null);
    setInlineError(null);
    stopCurrentRecording();
  };

  const currentQuestion = questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === questions.length - 1;
  const isResumeBased = currentQuestion.type === 'resume-based';
  const progressPercentage = ((currentQuestionIndex + 1) / questions.length) * 100;
  const currentStepLabel = isResumeBased ? '3/3 이력서 기반' : '2/3 즉흥 질문';
  const progressLabel = `${currentQuestionIndex + 1} / ${questions.length} · ${isResumeBased ? '이력서 기반' : '즉흥 질문'}`;
  const quickTips = [
    { title: 'STAR 구조', description: '상황-과제-행동-결과 순서로 핵심만 또렷하게 설명해요.' },
    { title: '30초 생각 시간', description: '질문을 들은 뒤 30초는 정리하고 10초 안에 말문을 여세요.' },
    { title: '감정 + 숫자', description: '느낀 점과 수치를 함께 말하면 설득력 있는 답변이 됩니다.' },
  ];

  return (
    <div className="flex flex-col items-center justify-start min-h-[calc(100vh-10rem)] animate-fadeIn pt-6">
      {isTimerVisible && !isTimerInView && (
        <div className="fixed bottom-4 right-2 sm:top-20 sm:bottom-auto sm:right-4 z-50 pb-[env(safe-area-inset-bottom)]">
          <div
            className={`backdrop-blur bg-white/90 border shadow-[0_12px_30px_rgba(103,0,230,0.15)] rounded-2xl px-3 py-2 sm:px-4 sm:py-3 flex items-center gap-3 sm:gap-4 transition-opacity duration-200 ${
              isLowTime ? 'border-red-300 animate-pulse' : 'border-primary/30'
            }`}
          >
            <ClockIcon className={`w-5 h-5 sm:w-6 sm:h-6 ${isLowTime ? 'text-red-600' : 'text-primary'}`} />
            <div>
              <p className="text-[11px] sm:text-xs font-semibold text-slate-500 uppercase tracking-widest">남은 시간</p>
              <p className={`text-lg sm:text-xl font-bold ${timeLeft <= 10 ? 'text-red-600' : isLowTime ? 'text-amber-600' : 'text-slate-800'}`}>
                {formatTime(timeLeft)}
              </p>
            </div>
          </div>
        </div>
      )}
      <div className="w-full max-w-5xl space-y-8">
        <section className="relative overflow-hidden rounded-[28px] bg-gradient-to-r from-primary-lightest via-white to-primary-lightest border border-white/70 shadow-soft p-6 sm:p-8">
          <div className="hero-blob hero-blob--primary -right-10 -top-10"></div>
          <div className="hero-blob hero-blob--secondary -left-14 bottom-0"></div>
          <div className="relative z-10 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold text-primary-text uppercase tracking-[0.25em] mb-1">AI 면접 진행</p>
                <div className="flex items-center gap-4 flex-wrap">
                  <span className="text-sm text-slate-500 font-semibold">
                    질문 {currentQuestionIndex + 1} / {questions.length}
                  </span>
                  <span className="text-xs font-semibold text-primary bg-primary-lightest px-3 py-1 rounded-full">{currentStepLabel}</span>
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                      isResumeBased ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                    }`}
                  >
                    {isResumeBased ? '이력서 기반' : '즉흥 질문'}
                  </span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-2 text-primary font-bold text-2xl">
                {isTimerVisible ? (
                  <div className="flex items-center gap-2" ref={inlineTimerRef}>
                    <ClockIcon className={`w-6 h-6 ${isLowTime ? 'text-red-600' : ''}`} />
                    <span className={isLowTime ? 'text-red-600' : ''}>{formatTime(timeLeft)}</span>
                  </div>
                ) : (
                  <span className="text-xs text-slate-500 font-semibold">타이머가 숨겨져 있어요</span>
                )}
                <div className="flex items-center gap-2 text-xs font-semibold">
                  <button
                    type="button"
                    onClick={() => setIsTimerPaused((prev) => !prev)}
                    className="px-3 py-1 rounded-full bg-white border border-slate-200 text-slate-600 hover:border-primary"
                  >
                    {isTimerPaused ? '재개' : '일시정지'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsTimerVisible((prev) => !prev)}
                    className="px-3 py-1 rounded-full bg-white border border-slate-200 text-slate-600 hover:border-primary"
                  >
                    {isTimerVisible ? '타이머 숨기기' : '타이머 보이기'}
                  </button>
                </div>
              </div>
            </div>
            <div className="w-full h-3 bg-white/70 rounded-full overflow-hidden shadow-inner shadow-white/60">
              <div
                className="h-full bg-gradient-to-r from-primary via-primary-medium to-primary-dark rounded-full transition-all duration-500 animate-progressGlow"
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
            <p className="text-xs text-slate-500 font-semibold">{progressLabel}</p>
          </div>
        </section>

        <Card>
          <p className="text-sm text-slate-500 mb-4 font-semibold tracking-wider uppercase flex items-center gap-2">
            <LightbulbIcon className="w-4 h-4 text-primary" />
            AI 질문
          </p>
          <h2 className="text-2xl font-bold text-slate-800 leading-tight">{currentQuestion.text}</h2>
          <p className="text-xs text-slate-500 mt-2">각 답변은 1~2분 안에 핵심만 정리해 주세요. 긴장되면 잠시 멈추고 다시 이어도 괜찮아요.</p>
        </Card>

        <Card>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
            <p className="text-slate-600 font-medium">A. 답변</p>
            <div className="text-xs bg-yellow-100 text-yellow-800 px-3 py-1.5 rounded-full flex items-center">
              <LightbulbIcon className="w-4 h-4 mr-1.5" />
              <span>TIP: 핵심 경험을 2~3문장으로 요약한 다음 세부 내용을 덧붙여요.</span>
            </div>
          </div>

          <VoiceAnswerArea
            currentAnswer={currentAnswer}
            onChangeAnswer={setCurrentAnswer}
            isRecording={isRecording}
            onToggleRecording={toggleRecording}
            isSpeechSupported={isSpeechSupported}
            isReadOnly={isResumeBased}
            recordingUrl={recordedAudioUrl}
            onClearRecording={handleRetryAnswer}
            inlineError={inlineError}
            micPermission={micPermission}
            onRequestMicPermission={requestMicPermission}
          />

          <div className="mt-8 space-y-4">
            <div className="flex flex-wrap justify-end gap-3 items-center">
              <span className="text-xs text-slate-500">모든 질문에 답변하지 않아도 필요하면 건너뛸 수 있습니다.</span>
              <Button onClick={handleSkipQuestion} variant="secondary" className="px-6 bg-white text-slate-700 border border-slate-200 hover:border-primary">
                건너뛰기
              </Button>
              <Button onClick={() => handleNext()} className="px-8">
                {isLastQuestion ? '연습 마치고 결과 보기' : '다음 질문'}
              </Button>
            </div>
            {inlineError && <p className="text-sm text-red-600 font-semibold text-right">{inlineError}</p>}
          </div>
        </Card>

        <Card>
          <p className="text-sm text-slate-500 mb-3 font-semibold tracking-wider uppercase flex items-center gap-2">
            <LightbulbIcon className="w-4 h-4 text-primary" />
            답변 팁
          </p>
          <div className="grid md:grid-cols-3 gap-4 w-full">
            {quickTips.map((tip, index) => (
              <div key={tip.title} className="rounded-[16px] border border-primary-lightest/80 bg-white/90 p-4 shadow-soft">
                <p className="text-xs uppercase text-slate-400 font-semibold mb-1">TIP {index + 1}</p>
                <p className="font-semibold text-slate-800">{tip.title}</p>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">{tip.description}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

  export default InterviewSession;
