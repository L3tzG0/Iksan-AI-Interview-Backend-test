import React from 'react';
  import { MicIcon, StopCircleIcon } from '../icons';

  interface VoiceAnswerAreaProps {
    currentAnswer: string;
    onChangeAnswer: (text: string) => void;
    isRecording: boolean;
    onToggleRecording: () => void;
    isSpeechSupported: boolean;
    isReadOnly: boolean;
  }

  const VoiceAnswerArea: React.FC<VoiceAnswerAreaProps> = ({
    currentAnswer,
    onChangeAnswer,
    isRecording,
    onToggleRecording,
    isSpeechSupported,
    isReadOnly
  }) => {
    const handleRetry = () => {
      onChangeAnswer('');
      onToggleRecording(); // restart/stop depending on current state
    };

    return (
      <div className="flex flex-col md:flex-row gap-6">
        <div className="md:w-1/3 flex flex-col gap-4">
          <div className="relative rounded-[20px] border border-white/40 bg-gradient-to-b from-primary-lightest via-white to-white shadow-soft p-6 text-center">
            <span className={`absolute top-4 right-4 inline-flex items-center gap-1 text-xs font-semibold ${isRecording ? 'text-red-500' : 'text-slate-400'}`}>
              <span className={`w-2 h-2 rounded-full ${isRecording ? 'bg-red-500 animate-ping' : 'bg-slate-300'}`}></span>
              {isRecording ? 'REC' : 'STANDBY'}
            </span>
            <button
              onClick={onToggleRecording}
              disabled={!isSpeechSupported}
              className={`relative mx-auto flex items-center justify-center w-24 h-24 rounded-full transition-all duration-300 border-4 ${
                isRecording
                  ? 'bg-red-500/10 border-red-300'
                  : 'bg-white border-primary-light hover:border-primary'
              } ${!isSpeechSupported ? 'opacity-40 cursor-not-allowed' : ''}`}
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
              {isRecording ? '녹음 중...' : '마이크 준비 완료'}
            </p>
            <p className="text-sm text-slate-500 mt-1">
              {!isSpeechSupported
                ? '현재 브라우저에서는 음성 인식을 지원하지 않아요.'
                : isRecording
                  ? '또렷하게 말씀하시면 즉시 텍스트로 변환돼요.'
                  : '버튼을 눌러 내 목소리로 답변을 기록해 보세요.'}
            </p>
          </div>
          {!isSpeechSupported && (
            <p className="text-xs text-slate-500 text-center px-4">
              주변이 조용한 곳에서 이용하거나 유선 이어폰 마이크 사용을 권장합니다.
            </p>
          )}
        </div>

        <div className="md:w-2/3">
          <div className="relative h-full min-h-[220px]">
            <textarea
              value={currentAnswer}
              onChange={(e) => onChangeAnswer(e.target.value)}
              readOnly={isReadOnly}
              placeholder={
                isReadOnly
                  ? 'AI가 불러온 이력서/자소서를 참고하며 떠오르는 문장을 메모해 주세요.'
                  : '답변에 넣고 싶은 경험, 수치, 느낌을 간단히 정리해 두면 말하기가 쉬워집니다.'
              }
              className={`w-full h-full p-5 pr-24 border rounded-[20px] resize-none text-slate-800 leading-relaxed focus:outline-none focus:ring-2 transition-colors ${
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
                참고 텍스트
              </div>
            )}
          </div>
          <div className="mt-4 bg-slate-50 border border-slate-200 rounded-[14px] p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-700">녹음된 텍스트</p>
              <button
                type="button"
                onClick={handleRetry}
                className="text-xs font-semibold text-primary hover:text-primary-dark px-3 py-1 rounded-full bg-white border border-primary-light"
              >
                다시 녹음
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-1">배경 소음이 있으면 다시 녹음해 주세요.</p>
            <div className="mt-2 p-3 bg-white rounded-[10px] border border-slate-200 min-h-[64px] text-sm text-slate-700 whitespace-pre-wrap">
              {currentAnswer || '아직 텍스트가 기록되지 않았어요.'}
            </div>
          </div>
        </div>
      </div>
    );
  };

  export default VoiceAnswerArea