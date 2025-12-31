import React, { useEffect, useState } from "react";
import { MicIcon, StopCircleIcon } from "../icons";

interface VoiceAnswerAreaProps {
    currentAnswer: string;
    onChangeAnswer: (text: string) => void;
    isRecording: boolean;
    onToggleRecording: () => void;
    isSpeechSupported: boolean;
    isReadOnly: boolean;
    recordingUrl?: string | null;
    onClearRecording?: () => void;
    inlineError?: string | null;
    micPermission?: "unknown" | "granted" | "denied";
    onRequestMicPermission?: () => void;
    isRequestingMic?: boolean;
    devices?: { deviceId: string; label: string }[];
    selectedDeviceId?: string;
    onSelectDevice?: (deviceId: string) => void;
    answerPlaceholder?: string;
    isSoundDetected?: boolean;
    isOddQuestion?: boolean;
    questionKey?: string | number;
    perQuestionSeconds: number;
}

const VoiceAnswerArea: React.FC<VoiceAnswerAreaProps> = ({
    currentAnswer,
    onChangeAnswer,
    isRecording,
    onToggleRecording,
    isSpeechSupported,
    isReadOnly,
    recordingUrl,
    onClearRecording,
    inlineError,
    micPermission = "unknown",
    onRequestMicPermission,
    isRequestingMic = false,
    devices = [],
    selectedDeviceId,
    onSelectDevice,
    answerPlaceholder = "여기에 답을 적어주세요",
    isSoundDetected = false,
    isOddQuestion = false,
    questionKey,
    perQuestionSeconds = 60,
}) => {
    const [inputMode, setInputMode] = useState<"voice" | "text">("voice");
    const [recordingSeconds, setRecordingSeconds] = useState(0);

    useEffect(() => {
        setInputMode("voice");
    }, [isOddQuestion, questionKey]);

    useEffect(() => {
        setRecordingSeconds(0);
    }, [questionKey]);

    useEffect(() => {
        let timerId: ReturnType<typeof window.setInterval> | null = null;
        if (isRecording) {
            setRecordingSeconds(0);
            timerId = window.setInterval(() => {
                setRecordingSeconds((prev) => prev + 1);
            }, 1000);
        }
        return () => {
            if (timerId) {
                window.clearInterval(timerId);
            }
        };
    }, [isRecording]);

    const formatRecordedTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, "0")}`;
    };

    const hasReachedLimit = recordingSeconds >= perQuestionSeconds;
    const timerColorClass = hasReachedLimit
        ? "text-red-500"
        : isRecording
        ? "text-slate-900"
        : "text-slate-400 opacity-70";

    const canToggleInput = !isOddQuestion;
    const isVoiceMode = isOddQuestion || inputMode === "voice";

    const handleRetry = () => {
        onChangeAnswer("");
        onClearRecording && onClearRecording();
    };

    return (
        <div className="z-10 relative flex flex-col md:justify-center items-center gap-6">
            {isVoiceMode && (
                <div className={`flex flex-col gap-4 md:w-1/2`}>
                    <div className="relative text-center">
                        {isRecording && (
                            <span
                                className={`absolute top-4 right-4 inline-flex items-center gap-1 text-xs font-semibold ${
                                    isRecording
                                        ? "text-red-500"
                                        : "text-slate-400"
                                }`}
                            >
                                <span
                                    className={`w-2 h-2 rounded-full ${
                                        isRecording
                                            ? "bg-red-500 animate-ping"
                                            : "bg-slate-300"
                                    }`}
                                ></span>
                                {isRecording && "REC"}
                            </span>
                        )}
                        <div className="inline-flex top-4 left-4 absolute items-center gap-2 font-semibold text-[11px] text-slate-600">
                            <span
                                className={`w-2 h-2 rounded-full ${
                                    micPermission === "granted"
                                        ? "bg-green-500"
                                        : micPermission === "denied"
                                        ? "bg-red-500"
                                        : "bg-amber-400"
                                }`}
                            ></span>
                            <span>
                                {micPermission === "granted"
                                    ? "마이크 허용"
                                    : micPermission === "denied"
                                    ? "권한 차단됨"
                                    : "허용 대기"}
                            </span>
                        </div>
                        <div className="flex flex-col items-center gap-1 mt-6">
                            <span
                                className={`text-2xl font-semibold tracking-wide transition-colors duration-200 ${timerColorClass}`}
                                aria-live="polite"
                            >
                                {formatRecordedTime(recordingSeconds)} /{" "}
                                {formatRecordedTime(perQuestionSeconds)}
                            </span>
                            {/* <span className="text-[10px] text-slate-400 uppercase tracking-[0.3em]">
                                녹음 시간
                            </span> */}
                        </div>
                        <button
                            onClick={onToggleRecording}
                            disabled={
                                !isSpeechSupported ||
                                micPermission === "denied" ||
                                isRequestingMic
                            }
                            className={`relative mx-auto flex items-center justify-center my-6 w-24 h-24 rounded-full transition-all duration-300 border-4 ${
                                isRecording
                                    ? "bg-red-500/10 border-red-300"
                                    : "bg-white border-primary-light hover:border-primary"
                            } ${
                                !isSpeechSupported ||
                                micPermission === "denied" ||
                                isRequestingMic
                                    ? "opacity-40 cursor-not-allowed"
                                    : ""
                            }`}
                            aria-label={isRecording ? "녹음 중지" : "녹음 시작"}
                            type="button"
                        >
                            {isRecording ? (
                                <StopCircleIcon className="w-10 h-10 text-red-500" />
                            ) : (
                                <MicIcon className="w-10 h-10 text-primary" />
                            )}
                            {isRecording && (
                                <span className="absolute inset-1 border border-red-400 rounded-full animate-pulseSlow"></span>
                            )}
                        </button>
                        {isRecording && isSoundDetected && (
                            <p className="mt-2 font-semibold text-emerald-600 text-xs">
                                귀하의 목소리가 녹음되고 있습니다
                            </p>
                        )}
                        <p className="mt-1 text-slate-500 text-sm">
                            {!isSpeechSupported &&
                                "이 브라우저에서는 음성 입력이 지원되지 않습니다."}
                        </p>
                        <p className="mt-2 text-[11px] text-slate-500">
                            다시 녹음하면 현재 답변이 대체됩니다.
                        </p>
                        {devices.length > 0 && (
                            <div className="mt-3 text-left">
                                <label className="block mb-1 font-semibold text-[11px] text-slate-600">
                                    마이크 선택
                                </label>
                                <select
                                    value={selectedDeviceId || ""}
                                    onChange={(e) =>
                                        onSelectDevice &&
                                        onSelectDevice(e.target.value)
                                    }
                                    className="bg-white px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30 w-full text-sm"
                                >
                                    {devices.map((d, idx) => (
                                        <option
                                            key={d.deviceId || idx}
                                            value={d.deviceId}
                                        >
                                            {d.label || `마이크 ${idx + 1}`}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}
                        {micPermission !== "granted" && (
                            <button
                                type="button"
                                onClick={onRequestMicPermission}
                                disabled={isRequestingMic}
                                className="bg-white disabled:opacity-50 mt-3 px-3 py-1.5 border border-primary-light rounded-full font-semibold text-primary hover:text-primary-dark text-xs"
                            >
                                {isRequestingMic
                                    ? "요청 중..."
                                    : "마이크 허용 요청"}
                            </button>
                        )}
                    </div>
                    {!isSpeechSupported && (
                        <p className="px-4 text-slate-500 text-xs text-center">
                            음성 인식이 지원되지 않는 환경입니다. 텍스트로
                            입력을 마무리해주세요.
                        </p>
                    )}
                </div>
            )}

            {!isOddQuestion && inputMode === "text" && (
                <div className={`flex flex-col gap-4 h-full md:w-1/2`}>
                    <div className="relative min-h-[260px] max-h-[440px]">
                        {/* {isOddQuestion && (
                        <>
                            <div className="z-10 absolute inset-0 bg-white shadow-inner shadow-slate-100 p-5 pr-24 border border-slate-200 rounded-[20px] w-full min-h-[260px] max-h-[400px]"></div>
                            <p className="top-5 left-5 z-20 absolute text-slate-400 text-sm pointer-events-none select-none">{answerPlaceholder}</p>
                        </>
                    )} */}

                        <textarea
                            value={currentAnswer}
                            onChange={(e) => onChangeAnswer(e.target.value)}
                            readOnly={isReadOnly}
                            placeholder={answerPlaceholder}
                            maxLength={800}
                            className={`w-full min-h-[260px] max-h-[400px] p-5 pr-24 border rounded-[20px] resize-none text-slate-800 leading-relaxed focus:outline-none focus:ring-2 transition-colors overflow-auto ${
                                isReadOnly
                                    ? "bg-slate-50 text-slate-600 border-slate-200 focus:ring-slate-200 cursor-not-allowed"
                                    : "bg-white border-slate-200 focus:ring-primary-focus focus:border-primary-focus shadow-inner shadow-slate-100"
                            }`}
                        />

                        <div className="top-5 right-5 absolute font-semibold text-slate-400 text-xs">
                            {currentAnswer.length}/800자
                        </div>
                        {isReadOnly && (
                            <div className="right-5 bottom-5 absolute bg-slate-100 px-3 py-1 rounded-full text-slate-500 text-xs">
                                읽기 전용
                            </div>
                        )}
                    </div>
                    {inlineError && (
                        <p className="mt-2 font-semibold text-red-600 text-sm">
                            {inlineError}
                        </p>
                    )}
                </div>
            )}

            {canToggleInput && (
                <button
                    type="button"
                    onClick={() =>
                        setInputMode((prev) =>
                            prev === "voice" ? "text" : "voice"
                        )
                    }
                    disabled={isRecording}
                    className="bg-white disabled:opacity-50 px-4 py-2 border border-primary-light rounded-full font-semibold text-primary hover:text-primary-dark text-xs"
                    aria-label={
                        inputMode === "voice"
                            ? "텍스트 입력으로 전환"
                            : "음성 입력으로 전환"
                    }
                >
                    {inputMode === "voice"
                        ? "텍스트 입력으로 답변"
                        : "음성 입력으로 답변"}
                </button>
            )}
        </div>
    );
};

export default VoiceAnswerArea;
