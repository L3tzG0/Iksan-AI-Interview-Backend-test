import React from 'react';
import Button from './Button';

type ModalTone = 'success' | 'info' | 'error';

type ModalAction = {
  label: string;
  onClick: () => void;
  /** Optional button variant override. */
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
};

interface StatusModalProps {
  isOpen: boolean;
  type: ModalTone;
  title: string;
  description?: string;
  onClose: () => void;
  primaryAction?: ModalAction;
  secondaryAction?: ModalAction;
  children?: React.ReactNode;
}

const toneTokens: Record<ModalTone, { badge: string; border: string; text: string; iconBg: string; iconBorder: string }> = {
  success: {
    badge: 'text-emerald-700 bg-emerald-50',
    border: 'border-emerald-100',
    text: 'text-emerald-700',
    iconBg: 'bg-emerald-100',
    iconBorder: 'border-emerald-200',
  },
  info: {
    badge: 'text-blue-700 bg-blue-50',
    border: 'border-blue-100',
    text: 'text-blue-700',
    iconBg: 'bg-blue-100',
    iconBorder: 'border-blue-200',
  },
  error: {
    badge: 'text-rose-700 bg-rose-50',
    border: 'border-rose-100',
    text: 'text-rose-700',
    iconBg: 'bg-rose-100',
    iconBorder: 'border-rose-200',
  },
};

const ToneIcon: React.FC<{ type: ModalTone }> = ({ type }) => {
  const baseCircle = 'w-10 h-10 rounded-full border flex items-center justify-center';
  const basePath = 'stroke-current';

  if (type === 'success') {
    return (
      <div className={`${baseCircle} ${toneTokens.success.iconBg} ${toneTokens.success.iconBorder}`}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className={toneTokens.success.text} aria-hidden>
          <path className={basePath} d="M5 13l4 4L19 7" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    );
  }

  if (type === 'error') {
    return (
      <div className={`${baseCircle} ${toneTokens.error.iconBg} ${toneTokens.error.iconBorder}`}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className={toneTokens.error.text} aria-hidden>
          <path className={basePath} d="M12 8v5" strokeWidth="2.2" strokeLinecap="round" />
          <circle className={basePath} cx="12" cy="16" r="1.2" fill="currentColor" />
          <path className={basePath} d="M12 3l9 9-9 9-9-9 9-9z" strokeWidth="2" strokeLinejoin="round" />
        </svg>
      </div>
    );
  }

  return (
    <div className={`${baseCircle} ${toneTokens.info.iconBg} ${toneTokens.info.iconBorder}`}>
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className={toneTokens.info.text} aria-hidden>
        <circle className={basePath} cx="12" cy="12" r="9" strokeWidth="2" />
        <path className={basePath} d="M12 11v6" strokeWidth="2" strokeLinecap="round" />
        <circle className={basePath} cx="12" cy="8" r="1.1" fill="currentColor" />
      </svg>
    </div>
  );
};

const StatusModal: React.FC<StatusModalProps> = ({
  isOpen,
  type,
  title,
  description,
  onClose,
  primaryAction,
  secondaryAction,
  children,
}) => {
  if (!isOpen) return null;

  const tone = toneTokens[type];
  const primaryVariant = primaryAction?.variant || (type === 'error' ? 'danger' : 'primary');

  return (
    <div className="z-50 fixed inset-0 flex justify-center items-center bg-slate-900/40 backdrop-blur-sm px-4">
      <div className="relative space-y-5 bg-white shadow-2xl p-6 border border-white/80 rounded-2xl w-full max-w-lg animate-softFadeUp">
        <button
          type="button"
          onClick={onClose}
          className="top-3 right-3 absolute text-slate-400 hover:text-slate-600 transition-colors"
          aria-label="닫기"
        >
          ×
        </button>

        <div className="flex items-start gap-4">
          <ToneIcon type={type} />
          <div className="space-y-1">
            <span className={`inline-flex items-center px-2 py-1 text-[11px] font-semibold rounded-full uppercase tracking-[0.18em] ${tone.badge}`}>
              {type === 'success' ? 'Success' : type === 'error' ? 'Error' : 'Info'}
            </span>
            <h3 className="font-bold text-slate-900 text-xl">{title}</h3>
            {description && <p className="text-slate-600 text-sm leading-relaxed">{description}</p>}
          </div>
        </div>

        {children && <div className={`rounded-xl border ${tone.border} bg-slate-50/70 p-4 text-sm text-slate-700`}>{children}</div>}

        <div className="flex sm:flex-row flex-col sm:justify-end gap-3">
          {secondaryAction && (
            <Button
              type="button"
              variant={secondaryAction.variant || 'secondary'}
              className="w-full sm:w-auto"
              onClick={secondaryAction.onClick}
            >
              {secondaryAction.label}
            </Button>
          )}
          {primaryAction && (
            <Button
              type="button"
              variant={primaryVariant}
              className="w-full sm:w-auto"
              onClick={primaryAction.onClick}
            >
              {primaryAction.label}
            </Button>
          )}
          {!primaryAction && !secondaryAction && (
            <Button type="button" variant="secondary" className="w-full sm:w-auto" onClick={onClose}>
              닫기
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatusModal;
