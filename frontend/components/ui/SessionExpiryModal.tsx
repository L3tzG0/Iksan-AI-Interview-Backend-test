import React from 'react';
import Button from './Button';

interface SessionExpiryModalProps {
  isOpen: boolean;
  secondsLeft: number;
  isExpired?: boolean;
  onRelogin: () => void;
  onDismiss: () => void;
}

const formatTimeLeft = (seconds: number) => {
  const safeSeconds = Math.max(0, seconds);
  const mins = Math.floor(safeSeconds / 60);
  const secs = safeSeconds % 60;
  if (mins <= 0) return `${secs}s`;
  return `${mins}m ${secs.toString().padStart(2, '0')}s`;
};

const SessionExpiryModal: React.FC<SessionExpiryModalProps> = ({ isOpen, secondsLeft, isExpired, onRelogin, onDismiss }) => {
  if (!isOpen) return null;

  const heading = isExpired ? '세션이 만료되었습니다' : '곧 세션이 만료됩니다';
  const description = isExpired
    ? '보안을 위해 다시 로그인해주세요.'
    : '1시간 후 자동 로그아웃됩니다. 계속 이용하려면 지금 다시 로그인해주세요.';

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl border border-slate-200 p-6 space-y-4 animate-softFadeUp">
        <div className="space-y-2">
          <p className="text-xs font-semibold tracking-[0.3em] uppercase text-primary">Session</p>
          <h2 className="text-2xl font-bold text-slate-900">{heading}</h2>
          <p className="text-slate-600 text-sm leading-relaxed">{description}</p>
          {!isExpired && (
            <p className="text-xs text-slate-500">
              남은 시간 <span className="font-semibold text-primary">{formatTimeLeft(secondsLeft)}</span>
            </p>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-3 sm:justify-end">
          {!isExpired && (
            <Button variant="secondary" className="w-full sm:w-auto" onClick={onDismiss}>
              잠시 후에
            </Button>
          )}
          <Button className="w-full sm:w-auto" onClick={onRelogin}>
            다시 로그인하기
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SessionExpiryModal;
