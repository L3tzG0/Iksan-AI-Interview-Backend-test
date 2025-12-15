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
  isRequestingMic?: boolean;
  devices?: { deviceId: string; label: string }[];
  selectedDeviceId?: string;
  onSelectDevice?: (deviceId: string) => void;
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
  isRequestingMic = false,
  devices = [],
  selectedDeviceId,
  onSelectDevice,
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
            <span>{micPermission === 'granted' ? '마이크 허용' : micPermission === 'denied' ? '권한 차단됨' : '허용 대기'}</span>
          </div>
          <button
            onClick={onToggleRecording}
            disabled={!isSpeechSupported || micPermission === 'denied' || isRequestingMic}
            className={`relative mx-auto flex items-center justify-center w-24 h-24 rounded-full transition-all duration-300 border-4 ${
              isRecording ? 'bg-red-500/10 border-red-300' : 'bg-white border-primary-light hover:border-primary'
            } ${(!isSpeechSupported || micPermission === 'denied' || isRequestingMic) ? 'opacity-40 cursor-not-allowed' : ''}`}
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
            {isRecording ? '녹음 중...' : '음성 입력'}
          </p>
          <p className="text-sm text-slate-500 mt-1">
            {!isSpeechSupported
              ? '이 브라우저에서는 음성 입력이 지원되지 않습니다.'
              : isRecording
                ? '답변을 또렷하게 말해 주세요.'
                : '시작을 누르고 답변을 말씀해주세요.'}
          </p>
          <p className="text-[11px] text-slate-500 mt-2">음성 녹음이 어려우면 텍스트로 작성해도 괜찮습니다.</p>
          {devices.length > 0 && (
            <div className="mt-3 text-left">
              <label className="text-[11px] font-semibold text-slate-600 mb-1 block">마이크 선택</label>
              <select
                value={selectedDeviceId || ''}
                onChange={(e) => onSelectDevice && onSelectDevice(e.target.value)}
                className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                {devices.map((d, idx) => (
                  <option key={d.deviceId || idx} value={d.deviceId}>
                    {d.label || `마이크 ${idx + 1}`}
                  </option>
                ))}
              </select>
            </div>
          )}
          {micPermission !== 'granted' && (
            <button
              type="button"
              onClick={onRequestMicPermission}
              disabled={isRequestingMic}
              className="mt-3 text-xs font-semibold text-primary hover:text-primary-dark px-3 py-1.5 rounded-full bg-white border border-primary-light disabled:opacity-50"
            >
              {isRequestingMic ? '요청 중...' : '마이크 허용 요청'}
            </button>
          )}
        </div>
        {!isSpeechSupported && (
          <p className="text-xs text-slate-500 text-center px-4">
            음성 인식이 지원되지 않는 환경입니다. 텍스트로 입력을 마무리해주세요.
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
                ? 'AI가 자동으로 생성한 답변을 보고만 할 수 있습니다.'
                : '여기에 메모하거나 답변을 직접 작성해도 괜찮습니다.'
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
            <p className="text-sm font-semibold text-slate-700">작성/녹음 내용</p>
            <button
              type="button"
              onClick={handleRetry}
              className="text-xs font-semibold text-primary hover:text-primary-dark px-3 py-1 rounded-full bg-white border border-primary-light"
            >
              다시 쓰기
            </button>
          </div>
          <p className="text-xs text-slate-500 mt-1">작성한 텍스트와 녹음 내용을 함께 저장할 수 있습니다. 필요하면 다시 시도하세요.</p>
          <div className="mt-2 p-3 bg-white rounded-[10px] border border-slate-200 min-h-[64px] text-sm text-slate-700 whitespace-pre-wrap space-y-3">
            <p className="m-0">{currentAnswer || '작성한 답변이 여기에 표시됩니다.'}</p>
            {recordingUrl && (
              <div className="flex flex-col gap-1 bg-slate-50 border border-slate-200 rounded-[10px] p-2">
                <span className="text-xs text-slate-500 font-semibold">녹음 파일</span>
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
