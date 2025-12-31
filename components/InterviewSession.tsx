import React, { useState, useEffect, useRef, useCallback } from "react";
import type { Question, Answer } from "../types";
import Card from "./Card";
import Button from "./ui/Button";
import { LightbulbIcon, ClockIcon } from "./icons";
import VoiceAnswerArea from "./interview/VoiceAnswerArea";
import { useNavigate, useLocation } from "react-router-dom";
import { createLiveSttSocket } from "../services/sttService";

const TARGET_SAMPLE_RATE = 16000;
const AUDIO_BUFFER_SIZE = 4096;
const FINAL_SUMMARY_TIMEOUT_MS = 5000;

interface InterviewSessionProps {
    questions: Question[];
    onFinish: (answers: Answer[]) => void;
    perQuestionSeconds?: number;
    onExit?: () => void;
}

const InterviewSession: React.FC<InterviewSessionProps> = ({
    questions,
    onFinish,
    perQuestionSeconds = 60,
    onExit,
}) => {
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [currentAnswer, setCurrentAnswer] = useState("");
    const [answers, setAnswers] = useState<Answer[]>([]);
    const [isRecording, setIsRecording] = useState(false);
    const [isSpeechSupported, setIsSpeechSupported] = useState(true);
    const [timeLeft, setTimeLeft] = useState(perQuestionSeconds);
    const [inlineError, setInlineError] = useState<string | null>(null);
    const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(
        null
    );
    const [isTimerPaused, setIsTimerPaused] = useState(false);
    const [isTimerVisible, setIsTimerVisible] = useState(true);
    const [isTimerInView, setIsTimerInView] = useState(true);
    const [timeExceeded, setTimeExceeded] = useState(false);
    const [micPermission, setMicPermission] = useState<
        "unknown" | "granted" | "denied"
    >("unknown");
    const [isRequestingMic, setIsRequestingMic] = useState(false);
    const [showExitModal, setShowExitModal] = useState(false);
    const [micDevices, setMicDevices] = useState<
        { deviceId: string; label: string }[]
    >([]);
    const [selectedMicId, setSelectedMicId] = useState<string | undefined>(
        undefined
    );
    const [isSoundDetected, setIsSoundDetected] = useState(false);
    const [sttSummary, setSttSummary] = useState<{
        finalTranscript?: string;
        audioDurationSeconds?: number;
        wordCount?: number;
        totalPauseDurationSeconds?: number;
        totalPauseCount?: number;
    } | null>(null);
    const [sttMetricsByQuestion, setSttMetricsByQuestion] = useState<
        Record<
            number,
            {
                audioDurationSeconds?: number;
                wordCount?: number;
                totalPauseDurationSeconds?: number;
                totalPauseCount?: number;
            }
        >
    >({});
    const [pauseEvents, setPauseEvents] = useState<
        {
            type?: string;
            gapSeconds?: number;
            afterWord?: string;
            beforeWord?: string;
        }[]
    >([]);
    const navigate = useNavigate();
    const location = useLocation();
    const [drafts, setDrafts] = useState<
        Record<number, { text: string; audioUrl?: string }>
    >(() => {
        if (typeof window === "undefined") return {};
        try {
            const cached = sessionStorage.getItem("ai-interview-draft");
            return cached ? JSON.parse(cached) : {};
        } catch {
            return {};
        }
    });

    const sttSocketRef = useRef<WebSocket | null>(null);
    const sttFinalTranscriptRef = useRef("");
    const sttInterimRef = useRef("");
    const hiddenTranscriptionRef = useRef(""); // For even questions: store transcription without displaying
    const isRecordingRef = useRef(isRecording);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const audioContextRef = useRef<AudioContext | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const micSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const micStreamRef = useRef<MediaStream | null>(null);
    const soundDetectedRef = useRef(false);
    const lastSoundTimestampRef = useRef(0);
    const finalSummaryTimeoutRef = useRef<number | null>(null);
    const inlineTimerRef = useRef<HTMLDivElement | null>(null);
    const devicesLoadedRef = useRef(false);

    const loadMicDevices = useCallback(async () => {
        if (!navigator.mediaDevices?.enumerateDevices) return;
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const micList = devices
                .filter((d) => d.kind === "audioinput")
                .map((d, idx) => ({
                    deviceId: d.deviceId || `mic-${idx}`,
                    label: d.label || `마이크 ${idx + 1}`,
                }));
            setMicDevices(micList);
            if (micList.length && !selectedMicId) {
                setSelectedMicId(micList[0].deviceId);
            } else if (
                selectedMicId &&
                !micList.find((m) => m.deviceId === selectedMicId) &&
                micList[0]
            ) {
                setSelectedMicId(micList[0].deviceId);
            }
            devicesLoadedRef.current = true;
        } catch {
            // ignore enumeration errors
        }
    }, [selectedMicId]);

    const requestMicPermission = useCallback(async () => {
        if (!navigator.mediaDevices?.getUserMedia) {
            setMicPermission("denied");
            setInlineError("이 기기에서는 마이크를 사용할 수 없어요.");
            return false;
        }
        setIsRequestingMic(true);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
            });
            setMicPermission("granted");
            setInlineError(null);
            stream.getTracks().forEach((track) => track.stop());
            return true;
        } catch (err) {
            setMicPermission("denied");
            setInlineError(
                "마이크 권한이 거부되었어요. 브라우저 주소창의 마이크 아이콘을 눌러 허용 후 다시 시도해주세요."
            );
            return false;
        } finally {
            setIsRequestingMic(false);
        }
    }, []);

    const resampleToTarget = useCallback(
        (inputBuffer: Float32Array, originalSampleRate: number) => {
            if (originalSampleRate === TARGET_SAMPLE_RATE) return inputBuffer;
            const ratio = originalSampleRate / TARGET_SAMPLE_RATE;
            const newLength = Math.round(inputBuffer.length / ratio);
            const output = new Float32Array(newLength);
            for (let i = 0; i < newLength; i++) {
                const index = Math.floor(i * ratio);
                output[i] = inputBuffer[index];
            }
            return output;
        },
        []
    );

    const convertFloat32ToInt16 = useCallback((buffer: Float32Array) => {
        const output = new Int16Array(buffer.length);
        for (let i = 0; i < buffer.length; i++) {
            const s = Math.max(-1, Math.min(1, buffer[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }
        return output.buffer;
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
            .query({ name: "microphone" as PermissionName })
            .then((result) => {
                if (result.state === "granted") setMicPermission("granted");
                if (result.state === "denied") setMicPermission("denied");
                result.onchange = () => {
                    if (result.state === "granted") setMicPermission("granted");
                    else if (result.state === "denied")
                        setMicPermission("denied");
                    else setMicPermission("unknown");
                };
            })
            .catch(() => {
                setMicPermission("unknown");
            });
    }, []);

    // Proactively request mic permission on first render if unknown
    useEffect(() => {
        if (micPermission === "unknown") {
            requestMicPermission();
        }
    }, [micPermission, requestMicPermission]);

    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            e.preventDefault();
            e.returnValue =
                "연습 세션을 종료하면 진행 중인 답변이 사라집니다. 나가시겠습니까?";
        };
        const handlePopState = () => {
            const leave = window.confirm(
                "연습 세션을 종료하면 진행 중인 답변이 사라집니다. 나가시겠습니까?"
            );
            if (!leave) {
                window.history.pushState(null, "", window.location.href);
            } else if (onExit) {
                window.history.replaceState(null, "", "/");
                onExit();
            } else {
                window.location.href = "/";
            }
        };
        window.addEventListener("beforeunload", handleBeforeUnload);
        window.history.pushState(null, "", window.location.href);
        window.addEventListener("popstate", handlePopState);
        return () => {
            window.removeEventListener("beforeunload", handleBeforeUnload);
            window.removeEventListener("popstate", handlePopState);
        };
    }, [onExit]);
    const updateDraft = useCallback(
        (
            questionId: number,
            data: Partial<{ text: string; audioUrl?: string }>
        ) => {
            setDrafts((prev) => {
                const next = {
                    ...prev,
                    [questionId]: { ...(prev[questionId] || {}), ...data },
                };
                try {
                    sessionStorage.setItem(
                        "ai-interview-draft",
                        JSON.stringify(next)
                    );
                } catch {
                    // ignore storage errors
                }
                return next;
            });
        },
        []
    );

    const stopAudioRecording = useCallback(() => {
        if (mediaRecorderRef.current) {
            if (mediaRecorderRef.current.state !== "inactive") {
                mediaRecorderRef.current.stop();
            }
            mediaRecorderRef.current = null;
        }

        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current.onaudioprocess = null;
            processorRef.current = null;
        }

        if (micSourceRef.current) {
            micSourceRef.current.disconnect();
            micSourceRef.current = null;
        }

        if (micStreamRef.current) {
            micStreamRef.current.getTracks().forEach((track) => track.stop());
            micStreamRef.current = null;
        }

        if (audioContextRef.current) {
            const ctx = audioContextRef.current;
            audioContextRef.current = null;
            ctx.close().catch(() => {});
        }

        soundDetectedRef.current = false;
        lastSoundTimestampRef.current = 0;
        setIsSoundDetected(false);
    }, []);

    const closeSttSocket = useCallback(() => {
        if (finalSummaryTimeoutRef.current) {
            clearTimeout(finalSummaryTimeoutRef.current);
            finalSummaryTimeoutRef.current = null;
        }
        if (sttSocketRef.current) {
            try {
                sttSocketRef.current.close();
            } catch {
                // ignore close errors
            }
            sttSocketRef.current = null;
        }
    }, []);

    const scheduleFinalSummaryClose = useCallback(() => {
        if (finalSummaryTimeoutRef.current) {
            clearTimeout(finalSummaryTimeoutRef.current);
        }
        finalSummaryTimeoutRef.current = window.setTimeout(() => {
            closeSttSocket();
        }, FINAL_SUMMARY_TIMEOUT_MS);
    }, [closeSttSocket]);

    const sendCloseSignal = useCallback(() => {
        if (
            sttSocketRef.current &&
            sttSocketRef.current.readyState === WebSocket.OPEN
        ) {
            sttSocketRef.current.send(JSON.stringify({ type: "CLOSE_SIGNAL" }));
            scheduleFinalSummaryClose();
        } else {
            closeSttSocket();
        }
    }, [closeSttSocket, scheduleFinalSummaryClose]);

    const connectSttSocket = useCallback(async () => {
        return new Promise<void>((resolve, reject) => {
            try {
                const socket = createLiveSttSocket();
                socket.binaryType = "arraybuffer";
                sttSocketRef.current = socket;
                socket.onopen = () => resolve();
                socket.onerror = (e) => {
                    console.error("STT socket error", e);
                    reject(new Error("STT 연결에 실패했습니다."));
                };
                socket.onclose = () => {
                    sttSocketRef.current = null;
                };
                socket.onmessage = (event) => {
                    if (typeof event.data !== "string") return;
                    try {
                        const payload = JSON.parse(event.data);

                        if (payload.pauses && Array.isArray(payload.pauses)) {
                            setPauseEvents((prev) => [
                                ...prev,
                                ...payload.pauses.map((p: any) => ({
                                    type: p.type,
                                    gapSeconds: p.gap_seconds ?? p.gapSeconds,
                                    afterWord: p.after_word ?? p.afterWord,
                                    beforeWord: p.before_word ?? p.beforeWord,
                                })),
                            ]);
                        }

                        if (payload.type === "FINAL_SUMMARY") {
                            const question = questions[currentQuestionIndex];
                            const summaryMetrics = {
                                audioDurationSeconds:
                                    payload.audio_duration_seconds,
                                wordCount: payload.word_count,
                                totalPauseDurationSeconds:
                                    payload.total_pause_duration_seconds,
                                totalPauseCount: payload.total_pause_count,
                            };
                            setSttSummary({
                                finalTranscript: payload.final_transcript,
                                ...summaryMetrics,
                            });
                            if (question) {
                                setSttMetricsByQuestion((prev) => ({
                                    ...prev,
                                    [question.id]: summaryMetrics,
                                }));
                                setAnswers((prev) =>
                                    prev.map((a) =>
                                        a.questionId === question.id
                                            ? {
                                                  ...a,
                                                  audioDurationSeconds:
                                                      summaryMetrics.audioDurationSeconds,
                                                  wordCount:
                                                      summaryMetrics.wordCount,
                                                  totalPauseDurationSeconds:
                                                      summaryMetrics.totalPauseDurationSeconds,
                                                  totalPauseCount:
                                                      summaryMetrics.totalPauseCount,
                                              }
                                            : a
                                    )
                                );
                            }
                            sttFinalTranscriptRef.current =
                                payload.final_transcript ||
                                sttFinalTranscriptRef.current;
                            setCurrentAnswer(
                                payload.final_transcript ||
                                    sttFinalTranscriptRef.current
                            );
                            stopAudioRecording();
                            setIsRecording(false);
                            if (finalSummaryTimeoutRef.current) {
                                clearTimeout(finalSummaryTimeoutRef.current);
                                finalSummaryTimeoutRef.current = null;
                            }
                            closeSttSocket();
                            return;
                        }

                        if (payload.transcript) {
                            if (payload.is_final) {
                                sttFinalTranscriptRef.current =
                                    `${sttFinalTranscriptRef.current} ${payload.transcript}`.trim();
                                sttInterimRef.current = "";
                            } else {
                                sttInterimRef.current = payload.transcript;
                            }
                            const combined =
                                `${sttFinalTranscriptRef.current} ${sttInterimRef.current}`.trim();

                            // For even questions, store transcription without displaying it
                            const question = questions[currentQuestionIndex];
                            const isOddQuestion =
                                question?.questionOrder % 2 === 1;

                            if (isOddQuestion) {
                                // Odd questions: display transcription normally
                                setCurrentAnswer(combined);
                                if (question) {
                                    updateDraft(question.id, {
                                        text: combined,
                                    });
                                }
                            } else {
                                // Even questions: hide transcription, only store it
                                hiddenTranscriptionRef.current = combined;
                            }
                        }
                    } catch {
                        // ignore parse errors
                    }
                };
            } catch (err) {
                reject(err);
            }
        });
    }, [currentQuestionIndex, questions, stopAudioRecording, updateDraft]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, "0")}`;
    };

    const stopCurrentRecording = useCallback(() => {
        if (isRecordingRef.current) {
            setIsRecording(false);
            stopAudioRecording();
            sendCloseSignal();
        }
    }, [sendCloseSignal, stopAudioRecording]);

    // Stop any active recording when unmounting or leaving the page
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.visibilityState === "hidden") {
                stopCurrentRecording();
            }
        };
        document.addEventListener("visibilitychange", handleVisibilityChange);
        return () => {
            document.removeEventListener(
                "visibilitychange",
                handleVisibilityChange
            );
            stopCurrentRecording();
        };
    }, [stopCurrentRecording]);

    // Stop any active recording when unmounting or navigating away
    useEffect(() => {
        return () => {
            stopCurrentRecording();
        };
    }, [stopCurrentRecording]);

    const isLowTime = timeLeft <= 15;
    useEffect(() => {
        if (!isLowTime || isTimerPaused) return;
        try {
            const context = new (window.AudioContext ||
                (window as any).webkitAudioContext)();
            const oscillator = context.createOscillator();
            const gainNode = context.createGain();
            oscillator.type = "sine";
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
            const constraints: MediaStreamConstraints = {
                audio: selectedMicId
                    ? { deviceId: { exact: selectedMicId } }
                    : true,
            };

            const stream = await navigator.mediaDevices.getUserMedia(
                constraints
            );
            micStreamRef.current = stream;
            setMicPermission("granted");

            const audioContext = new (window.AudioContext ||
                (window as any).webkitAudioContext)();
            audioContextRef.current = audioContext;
            const source = audioContext.createMediaStreamSource(stream);
            micSourceRef.current = source;

            const processor = audioContext.createScriptProcessor(
                AUDIO_BUFFER_SIZE,
                1,
                1
            );
            processorRef.current = processor;
            processor.onaudioprocess = (e) => {
                const inputData = e.inputBuffer.getChannelData(0);
                let sumSquares = 0;
                for (let i = 0; i < inputData.length; i++) {
                    const sample = inputData[i];
                    sumSquares += sample * sample;
                }
                const rms = Math.sqrt(sumSquares / inputData.length);
                const now = performance.now();
                if (rms > 0.015) {
                    lastSoundTimestampRef.current = now;
                }
                const isActive = now - lastSoundTimestampRef.current < 450;
                if (soundDetectedRef.current !== isActive) {
                    soundDetectedRef.current = isActive;
                    setIsSoundDetected(isActive);
                }

                if (
                    sttSocketRef.current &&
                    sttSocketRef.current.readyState === WebSocket.OPEN
                ) {
                    const resampled = resampleToTarget(
                        inputData,
                        audioContext.sampleRate
                    );
                    const pcm16 = convertFloat32ToInt16(resampled);
                    sttSocketRef.current.send(pcm16);
                }
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            const recorder = new MediaRecorder(stream);
            audioChunksRef.current = [];
            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };
            recorder.onstop = () => {
                const blob = new Blob(audioChunksRef.current, {
                    type: "audio/webm",
                });
                const url = URL.createObjectURL(blob);
                setRecordedAudioUrl(url);
                const question = questions[currentQuestionIndex];
                if (question) {
                    updateDraft(question.id, {
                        audioUrl: url,
                        text: currentAnswer,
                    });
                }
            };
            recorder.start(1000);
            mediaRecorderRef.current = recorder;
        } catch (err) {
            setMicPermission("denied");
            setInlineError(
                "마이크에 접근할 수 없습니다. 브라우저 설정을 확인해주세요."
            );
            setIsRecording(false);
            console.error("Microphone access denied or failed", err);
        }
    }, [
        convertFloat32ToInt16,
        currentAnswer,
        currentQuestionIndex,
        questions,
        resampleToTarget,
        selectedMicId,
        updateDraft,
    ]);

    const handleNext = useCallback(
        (options?: { allowEmpty?: boolean; skipReason?: string }) => {
            console.log("Handling next question");
            const question = questions[currentQuestionIndex];
            if (!question) return;

            stopCurrentRecording();
            const isOddQuestion = question.questionOrder % 2 === 1;
            // For even questions, merge hidden transcription with typed answer
            const finalText = isOddQuestion
                ? (sttSummary?.finalTranscript || currentAnswer).trim()
                : `${hiddenTranscriptionRef.current} ${currentAnswer}`.trim() ||
                  (sttSummary?.finalTranscript || "").trim();
            if (!options?.allowEmpty && !finalText) {
                setInlineError("답변이 비어 있어요. 답변을 주세요.");
                return;
            }

            const isSkipped = Boolean(options?.skipReason);
            const answerText =
                finalText || options?.skipReason || "이 질문은 건너뛸게요.";
            const metrics =
                sttMetricsByQuestion[question.id] || sttSummary || {};
            const pauseCountFallback = pauseEvents.length
                ? pauseEvents.length
                : undefined;
            const pauseDurationFallback = pauseEvents.length
                ? pauseEvents.reduce((acc, p) => acc + (p.gapSeconds || 0), 0)
                : undefined;
            setInlineError(null);
            setTimeExceeded(false);

            const newAnswer: Answer = {
                questionId: question.id,
                text: answerText,
                audioUrl: recordedAudioUrl || drafts[question.id]?.audioUrl,
                questionOrder: currentQuestionIndex + 1,
                questionText: question.text,
                isSkipped,
                audioDurationSeconds: metrics.audioDurationSeconds,
                wordCount: metrics.wordCount,
                totalPauseDurationSeconds:
                    metrics.totalPauseDurationSeconds ?? pauseDurationFallback,
                totalPauseCount: metrics.totalPauseCount ?? pauseCountFallback,
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
        },
        [
            answers,
            currentAnswer,
            currentQuestionIndex,
            drafts,
            onFinish,
            pauseEvents,
            perQuestionSeconds,
            questions,
            recordedAudioUrl,
            sttMetricsByQuestion,
            sttSummary,
            stopCurrentRecording,
        ]
    );

    useEffect(() => {
        setTimeLeft(perQuestionSeconds);
        setInlineError(null);
        setTimeExceeded(false);
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
                setInlineError("시간이 다 되었습니다. 답변을 주세요.");
                setIsTimerPaused(true);
                return;
            }
            handleNext();
        }
    }, [timeLeft, isTimerPaused, currentAnswer, handleNext]);

    useEffect(() => {
        return () => {
            isRecordingRef.current = false;
            closeSttSocket();
            stopAudioRecording();
        };
    }, [closeSttSocket, stopAudioRecording]);

    const toggleRecording = async () => {
        if (micPermission === "denied") {
            setInlineError(
                "마이크 권한이 거부되었습니다. 브라우저 설정을 확인해 주세요."
            );
            return;
        }
        if (micPermission === "unknown") {
            try {
                const ok = await requestMicPermission();
                if (!ok) return;
            } catch {
                setInlineError("마이크 권한 요청에 실패했습니다.");
                return;
            }
        }

        const newIsRecording = !isRecording;
        setIsRecording(newIsRecording);
        setInlineError(null);

        if (newIsRecording) {
            sttFinalTranscriptRef.current = "";
            sttInterimRef.current = "";
            setSttSummary(null);
            setPauseEvents([]);
            try {
                await connectSttSocket();
                await startAudioRecording();
            } catch (err) {
                console.error("Audio/STT start failed", err);
                setInlineError("음성 녹음 시작에 실패했습니다.");
                setIsRecording(false);
                closeSttSocket();
            }
        } else {
            stopAudioRecording();
            sendCloseSignal();
        }
    };

    useEffect(() => {
        const question = questions[currentQuestionIndex];
        if (!question) return;
        const draft = drafts[question.id];
        const text = draft?.text || "";
        setCurrentAnswer(text);
        sttFinalTranscriptRef.current = text;
        hiddenTranscriptionRef.current = ""; // Reset hidden transcription for new question
        setRecordedAudioUrl(draft?.audioUrl || null);
        setSttSummary(null);
        setSttMetricsByQuestion((prev) => {
            const next = { ...prev };
            delete next[question.id];
            return next;
        });
        setPauseEvents([]);
        setInlineError(null);
        setIsTimerPaused(false);
        stopCurrentRecording();
        closeSttSocket();
    }, [closeSttSocket, currentQuestionIndex, questions, stopCurrentRecording]);

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
        console.log("Attempting to skip question");
        const question = questions[currentQuestionIndex];
        if (!question) return;
        const hasAnyAnswer = answers.some(
            (answer) => answer.text.trim().length > 0 || answer.audioUrl
        );
        if (!hasAnyAnswer && !currentAnswer.trim()) {
            setInlineError(
                "첫 질문은 비워둘 수 없어요. 최소 한 문장을 작성해 주세요."
            );
            return;
        }
        handleNext({
            allowEmpty: true,
            skipReason: "이 질문을 건너뛰겠습니다. 다음 질문으로 넘어갈게요.",
        });
    };

    const handleRetryAnswer = () => {
        setCurrentAnswer("");
        sttFinalTranscriptRef.current = "";
        setRecordedAudioUrl(null);
        setSttSummary(null);
        setSttMetricsByQuestion((prev) => {
            const next = { ...prev };
            const question = questions[currentQuestionIndex];
            if (question) delete next[question.id];
            return next;
        });
        setPauseEvents([]);
        setInlineError(null);
        stopCurrentRecording();
    };

    const currentQuestion = questions[currentQuestionIndex];
    const isLastQuestion = currentQuestionIndex === questions.length - 1;
    const isResumeBased = currentQuestion.type === "resume-based";
    const progressPercentage =
        ((currentQuestionIndex + 1) / questions.length) * 100;
    const currentStepLabel = isResumeBased
        ? "3/3 이력서 기반"
        : "2/3 즉흥 질문";
    const progressLabel = `${currentQuestionIndex + 1} / ${
        questions.length
    } · 질문`;
    const quickTips = [
        {
            title: "STAR 구조",
            description: "상황-과제-행동-결과 순서로 핵심만 또렷하게 설명해요.",
        },
        {
            title: "감정 + 숫자",
            description:
                "느낀 점과 수치를 함께 말하면 설득력 있는 답변이 됩니다.",
        },
    ];

    // console.log('Render InterviewSession', { currentQuestion});

    const defaultAnswerPlaceholder = "여기에 답을 적어주세요";
    const placeholderText =
        currentQuestion.questionOrder % 2 === 1
            ? "이 질문은 음성 녹음으로 반드시 답변해야 합니다."
            : defaultAnswerPlaceholder;

    return (
        <div className="flex flex-col justify-start items-center pt-6 min-h-[calc(100vh-10rem)] animate-fadeIn">
            {isTimerVisible && !isTimerInView && (
                <div className="sm:top-20 right-2 sm:right-4 bottom-4 sm:bottom-auto z-50 fixed pb-[env(safe-area-inset-bottom)]">
                    <div
                        className={`backdrop-blur bg-white/90 border shadow-[0_12px_30px_rgba(103,0,230,0.15)] rounded-2xl px-3 py-2 sm:px-4 sm:py-3 flex items-center gap-3 sm:gap-4 transition-opacity duration-200 ${
                            isLowTime
                                ? "border-red-300 animate-pulse"
                                : "border-primary/30"
                        }`}
                    >
                        <ClockIcon
                            className={`w-5 h-5 sm:w-6 sm:h-6 ${
                                isLowTime ? "text-red-600" : "text-primary"
                            }`}
                        />
                        <div>
                            <p className="font-semibold text-[11px] text-slate-500 sm:text-xs uppercase tracking-widest">
                                남은 시간
                            </p>
                            <p
                                className={`text-lg sm:text-xl font-bold ${
                                    timeLeft <= 10
                                        ? "text-red-600"
                                        : isLowTime
                                        ? "text-amber-600"
                                        : "text-slate-800"
                                }`}
                            >
                                {formatTime(timeLeft)}
                            </p>
                        </div>
                    </div>
                </div>
            )}
            <div className="space-y-8 w-full max-w-9xl">
                <div className="gap-6 grid md:grid-cols-4">
                    <main className="flex flex-col gap-4 md:col-span-3 mx-4 my-auto">
                        <div>
                            {/* <p className="flex items-center gap-2 mb-4 font-semibold text-slate-500 text-sm uppercase tracking-wider">
                                AI 질문
                            </p> */}
                            <h2 className="font-bold text-slate-800 text-2xl text-center leading-tight">
                                Q
                                {currentQuestion?.questionOrder ??
                                    currentQuestionIndex + 1}
                                . {currentQuestion.text}
                            </h2>
                            {/* <p className="mt-2 text-slate-500 text-xs">
                                각 답변은 1~2분 안에 핵심만 정리해 주세요.
                            </p> */}
                        </div>

                        <div>
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
                                isRequestingMic={isRequestingMic}
                                answerPlaceholder={placeholderText}
                                isOddQuestion={
                                    currentQuestion.questionOrder % 2 === 1
                                }
                                isSoundDetected={isSoundDetected}
                                perQuestionSeconds={perQuestionSeconds}
                                questionKey={currentQuestion.id}
                            />

                            {(pauseEvents.length > 0 || sttSummary) && (
                                <div className="bg-slate-50 mt-3 p-3 border border-slate-200 rounded-[12px] text-slate-600 text-xs">
                                    {pauseEvents.length > 0 && (
                                        <p className="m-0">
                                            감지된 일시정지:{" "}
                                            {pauseEvents.length}회
                                        </p>
                                    )}
                                    {sttSummary && (
                                        <p className="m-0 mt-1">
                                            최종 요약 · 단어{" "}
                                            {sttSummary.wordCount ?? "-"}개 ·
                                            음성{" "}
                                            {sttSummary.audioDurationSeconds ??
                                                "-"}
                                            초 · 일시정지{" "}
                                            {sttSummary.totalPauseCount ?? "-"}
                                            회
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>
                    </main>

                    <aside className="md:top-20 z-20 md:sticky self-start md:col-span-1">
                        <div className="flex flex-col gap-4">
                            <Card>
                                <p className="mb-1 font-semibold text-slate-400 text-xs uppercase">
                                    TIP 1
                                </p>
                                <p className="font-semibold text-slate-800">
                                    {quickTips[0].title}
                                </p>
                                <p className="mt-1 text-slate-500 text-xs leading-relaxed">
                                    {quickTips[0].description}
                                </p>
                            </Card>

                            <Card>
                                <p className="mb-1 font-semibold text-slate-400 text-xs uppercase">
                                    TIP 2
                                </p>
                                <p className="font-semibold text-slate-800">
                                    {quickTips[1].title}
                                </p>
                                <p className="mt-1 text-slate-500 text-xs leading-relaxed">
                                    {quickTips[1].description}
                                </p>
                            </Card>

                            <div className="flex flex-col gap-2 mt-8">
                                <div className="flex flex-wrap justify-start items-center gap-3">
                                    <span className="text-slate-500 text-xs">
                                        모든 질문에 답변하지 않아도 필요하면
                                        건너뛸 수 있습니다.
                                    </span>
                                    <Button
                                        onClick={() => {
                                            handleSkipQuestion();
                                            console.log("Skip clicked");
                                        }}
                                        variant="secondary"
                                        className="bg-white px-6 border border-slate-200 hover:border-primary text-slate-700"
                                    >
                                        건너뛰기
                                    </Button>
                                    <Button
                                        onClick={() => {
                                            handleNext();
                                            console.log("Next clicked");
                                        }}
                                        className="flex-1 px-8"
                                    >
                                        {isLastQuestion
                                            ? "연습 마치고 결과 보기"
                                            : "다음 질문"}
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </aside>
                </div>
            </div>

            {showExitModal && (
                <div className="z-50 fixed inset-0 flex justify-center items-center bg-slate-900/50 backdrop-blur-sm px-4">
                    <div className="space-y-4 bg-white shadow-2xl p-6 border border-slate-200 rounded-2xl w-full max-w-md animate-softFadeUp">
                        <h3 className="font-bold text-slate-900 text-lg">
                            면접을 종료하시겠습니까?
                        </h3>
                        <p className="text-slate-600 text-sm">
                            진행 중인 답변이 사라질 수 있습니다. 저장 후
                            나가거나 계속 진행을 선택하세요.
                        </p>
                        <div className="flex flex-wrap justify-end gap-2">
                            <Button
                                type="button"
                                variant="secondary"
                                onClick={() => {
                                    setShowExitModal(false);
                                }}
                                className="bg-white border border-slate-200 text-slate-700"
                            >
                                계속 진행
                            </Button>
                            <Button
                                type="button"
                                onClick={() => {
                                    setShowExitModal(false);
                                    if (onExit) onExit();
                                }}
                            >
                                종료하기
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default InterviewSession;
