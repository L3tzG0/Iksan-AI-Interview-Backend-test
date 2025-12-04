import React from 'react';
import { MicIcon, StopCircleIcon } from '../icons';

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
  micPermission?: 'unknown' | 'granted' | 'denied';
  onRequestMicPermission?: () => void;
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
  micPermission = 'unknown',
  onRequestMicPermission,
}) => {
  const handleRetry = () => {
    onChangeAnswer('');
    onClearRecording && onClearRecording();
  };

  return (
    <div className="relative z-10 flex flex-col md:flex-row gap-6">
      <div className="md:w-1/3 flex flex-col gap-4">
        <div className="relative rounded-[20px] border border-white/40 bg-gradient-to-b from-primary-lightest via-white to-white shadow-soft p-6 text-center">
          <span className={`absolute top-4 right-4 inline-flex items-center gap-1 text-xs font-semibold ${isRecording ? 'text-red-500' : 'text-slate-400'}`}>
            <span className={`w-2 h-2 rounded-full ${isRecording ? 'bg-red-500 animate-ping' : 'bg-slate-300'}`}></span>
            {isRecording ? 'REC' : 'STANDBY'}
          </span>
          <div className="absolute top-4 left-4 inline-flex items-center gap-2 text-[11px] font-semibold text-slate-600">
            <span className={`w-2 h-2 rounded-full ${micPermission === 'granted' ? 'bg-green-500' : micPermission === 'denied' ? 'bg-red-500' : 'bg-amber-400'}`}></span>
            <span>{micPermission === 'granted' ? '마이크 허용' : micPermission === 'denied' ? '마이크 거부됨' : '권한 확인 필요'}</span>
          </div>
          <button
            onClick={onToggleRecording}
            disabled={!isSpeechSupported || micPermission === 'denied'}
            className={`relative mx-auto flex items-center justify-center w-24 h-24 rounded-full transition-all duration-300 border-4 ${
              isRecording ? 'bg-red-500/10 border-red-300' : 'bg-white border-primary-light hover:border-primary'
            } ${(!isSpeechSupported || micPermission === 'denied') ? 'opacity-40 cursor-not-allowed' : ''}`}
            aria-label={isRecording ? '녹음 중지' : '녹음 시작'}
            type="button"
          >
            {isRecording ? (
              <StopCircleIcon className="w-10 h-10 text-red-500" />
            ) : (
              <MicIcon className="w-10 h-10 text-primary" />
            )}
            {isRecording && <span className="absolute inset-1 rounded-full border border-red-400 animate-pulseSlow"></span>}
          </button>

          <div className="mt-4 voice-wave">
            {Array.from({ length: 10 }).map((_, idx) => (
              <span
                key={idx}
                className={`voice-wave-bar ${!isRecording ? 'is-paused' : ''}`}
                style={{ animationDelay: `${idx * 0.08}s` }}
              />
            ))}
          </div>
          <p className={`font-bold text-lg ${isRecording ? 'text-red-500' : 'text-slate-700'}`}>
            {isRecording ? '녹음 중...' : '대기 중'}
          </p>
          <p className="text-sm text-slate-500 mt-1">
            {!isSpeechSupported
              ? '음성 인식이 지원되지 않는 브라우저입니다.'
              : isRecording
                ? '말씀을 멈추면 잠시 후 자동으로 저장돼요.'
                : '마이크를 켜거나 직접 입력할 수 있어요.'}
          </p>
          <p className="text-[11px] text-slate-500 mt-2">마이크 아이콘을 눌러 녹음을 시작하거나 텍스트로 작성하세요.</p>
          {micPermission !== 'granted' && (
            <button
              type="button"
              onClick={onRequestMicPermission}
              className="mt-3 text-xs font-semibold text-primary hover:text-primary-dark px-3 py-1.5 rounded-full bg-white border border-primary-light"
            >
              마이크 권한 요청
            </button>
          )}
        </div>
        {!isSpeechSupported && (
          <p className="text-xs text-slate-500 text-center px-4">
            음성 인식이 지원되지 않으면 다른 브라우저나 기기에서 다시 시도해 주세요.
          </p>
        )}
      </div>

      <div className="md:w-2/3 flex flex-col gap-4 h-full">
        <div className="relative min-h-[260px] max-h-[440px]">
          <textarea
            value={currentAnswer}
            onChange={(e) => onChangeAnswer(e.target.value)}
            readOnly={isReadOnly}
            placeholder={
              isReadOnly
                ? 'AI가 불러온 내용을 확인만 할 수 있습니다.'
                : '중요 포인트, 수치, 결과를 포함해 구체적으로 작성해 주세요.'
            }
            maxLength={800}
            className={`w-full min-h-[260px] max-h-[400px] p-5 pr-24 border rounded-[20px] resize-none text-slate-800 leading-relaxed focus:outline-none focus:ring-2 transition-colors overflow-auto ${
              isReadOnly
                ? 'bg-slate-50 text-slate-600 border-slate-200 focus:ring-slate-200 cursor-not-allowed'
                : 'bg-white border-slate-200 focus:ring-primary-focus focus:border-primary-focus shadow-inner shadow-slate-100'
            }`}
          />
            <div className="absolute top-5 right-5 text-xs font-semibold text-slate-400">
              {currentAnswer.length}/800자
            </div>
          {isReadOnly && (
            <div className="absolute bottom-5 right-5 bg-slate-100 text-slate-500 text-xs px-3 py-1 rounded-full">
              읽기 전용
            </div>
          )}
        </div>
        {inlineError && <p className="mt-2 text-sm text-red-600 font-semibold">{inlineError}</p>}
        <div className="mt-4 bg-slate-50 border border-slate-200 rounded-[14px] p-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-slate-700">실시간 전사 & 저장</p>
            <button
              type="button"
              onClick={handleRetry}
              className="text-xs font-semibold text-primary hover:text-primary-dark px-3 py-1 rounded-full bg-white border border-primary-light"
            >
              다시 작성
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-1">입력한 내용은 자동으로 저장돼요. 필요하면 다시 녹음하거나 수정할 수 있습니다.</p>
          <div className="mt-2 p-3 bg-white rounded-[10px] border border-slate-200 min-h-[64px] text-sm text-slate-700 whitespace-pre-wrap space-y-3">
            <p className="m-0">{currentAnswer || '아직 작성된 답변이 없습니다.'}</p>
            {recordingUrl && (
              <div className="flex flex-col gap-1 bg-slate-50 border border-slate-200 rounded-[10px] p-2">
                <span className="text-xs text-slate-500 font-semibold">녹음된 오디오</span>
                <audio src={recordingUrl} controls className="w-full" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceAnswerArea;
