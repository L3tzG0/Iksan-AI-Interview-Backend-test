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
  }

  const InterviewSession: React.FC<InterviewSessionProps> = ({ questions, onFinish }) => {
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [currentAnswer, setCurrentAnswer] = useState('');
    const [answers, setAnswers] = useState<Answer[]>([]);
    const [isRecording, setIsRecording] = useState(false);
    const [isSpeechSupported, setIsSpeechSupported] = useState(true);
    const [timeLeft, setTimeLeft] = useState(60);

    const recognitionRef = useRef<SpeechRecognition | null>(null);
    const finalTranscriptRef = useRef('');
    const isRecordingRef = useRef(isRecording);

    useEffect(() => {
      isRecordingRef.current = isRecording;
    }, [isRecording]);

    const stopCurrentRecording = useCallback(() => {
      if (isRecordingRef.current) {
        setIsRecording(false);
        recognitionRef.current?.stop();
      }
    }, []);

    const handleNext = useCallback(() => {
      stopCurrentRecording();
      const newAnswer: Answer = {
        questionId: questions[currentQuestionIndex].id,
        text: currentAnswer,
      };
      const updatedAnswers = [...answers, newAnswer];
      setAnswers(updatedAnswers);

      if (currentQuestionIndex === questions.length - 1) {
        onFinish(updatedAnswers);
      } else {
        setCurrentQuestionIndex((prev) => prev + 1);
      }
    }, [answers, currentAnswer, currentQuestionIndex, onFinish, questions, stopCurrentRecording]);

    useEffect(() => {
      setTimeLeft(60);
      const timerId = setInterval(() => {
        setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
      return () => clearInterval(timerId);
    }, [currentQuestionIndex]);

    useEffect(() => {
      if (timeLeft === 0) {
        handleNext();
      }
    }, [timeLeft, handleNext]);

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
        const fullTranscript = finalTranscriptRef.current + interimTranscript;
        setCurrentAnswer(fullTranscript);
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
      };
    }, []);

    const toggleRecording = () => {
      if (!recognitionRef.current) return;

      const newIsRecording = !isRecording;
      setIsRecording(newIsRecording);

      if (newIsRecording) {
        recognitionRef.current.start();
      } else {
        recognitionRef.current.stop();
      }
    };

    useEffect(() => {
      setCurrentAnswer('');
      finalTranscriptRef.current = '';
      stopCurrentRecording();
    }, [currentQuestionIndex, stopCurrentRecording]);

    const currentQuestion = questions[currentQuestionIndex];
    const isLastQuestion = currentQuestionIndex === questions.length - 1;
    const isResumeBased = currentQuestion.type === 'resume-based';
    const progressPercentage = ((currentQuestionIndex + 1) / questions.length) * 100;
    const currentStepLabel = isResumeBased ? '3/3 이력서 기반 질문' : '2/3 일반 질문';
    const quickTips = [
      { title: 'STAR 구조', description: '상황-과제-행동-결과 순서로 핵심만 또렷하게 설명해요.' },
      { title: '30초 생각 후 시작', description: '질문을 들은 뒤 30초 정리하고 10초 안에 말문을 여세요.' },
      { title: '감정 + 숫자', description: '느낀 점과 수치를 함께 말하면 설득력 있는 답변이 됩니다.' },
    ];

    return (
      <div className="flex flex-col items-center justify-start min-h-[calc(100vh-10rem)] animate-fadeIn pt-6">
        <div className="w-full max-w-4xl space-y-8">
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
                <div className="flex items-center gap-2 text-primary font-bold text-2xl">
                  <ClockIcon className="w-6 h-6" />
                  <span>{timeLeft}초</span>
                </div>
              </div>
              <div className="w-full h-3 bg-white/70 rounded-full overflow-hidden shadow-inner shadow-white/60">
                <div
                  className="h-full bg-gradient-to-r from-primary via-primary-medium to-primary-dark rounded-full transition-all duration-500 animate-progressGlow"
                  style={{ width: `${progressPercentage}%` }}
                ></div>
              </div>
            </div>
          </section>

          <Card>
            <p className="text-sm text-slate-500 mb-4 font-semibold tracking-wider uppercase flex items-center gap-2">
              <LightbulbIcon className="w-4 h-4 text-primary" />
              AI 질문
            </p>
            <h2 className="text-2xl font-bold text-slate-800 leading-tight">{currentQuestion.text}</h2>
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
            />

            <div className="mt-6 flex flex-col gap-4">
              <div className="grid md:grid-cols-3 gap-4">
                {quickTips.map((tip, index) => (
                  <div key={tip.title} className="rounded-[16px] border border-primary-lightest/80 bg-white/90 p-4 shadow-soft">
                    <p className="text-xs uppercase text-slate-400 font-semibold mb-1">TIP {index + 1}</p>
                    <p className="font-semibold text-slate-800">{tip.title}</p>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">{tip.description}</p>
                  </div>
                ))}
              </div>
              <div className="flex justify-end">
                <Button onClick={handleNext} className="px-8">
                  {isLastQuestion ? '연습 마치고 결과 보기' : '다음 질문'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    );
  };

  export default InterviewSession