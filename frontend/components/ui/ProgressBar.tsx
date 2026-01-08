import React from 'react';

type Tone = 'primary' | 'neutral' | 'success' | 'danger';

interface ProgressBarProps {
  value?: number; // 0-100; if undefined and indeterminate is true, show shimmer
  indeterminate?: boolean;
  label?: string;
  tone?: Tone;
  height?: 'xs' | 'sm' | 'md';
}

const toneClasses: Record<Tone, string> = {
  primary: 'from-primary to-primary/70',
  neutral: 'from-slate-400 to-slate-300',
  success: 'from-emerald-500 to-emerald-400',
  danger: 'from-rose-500 to-rose-400',
};

const heightClasses: Record<NonNullable<ProgressBarProps['height']>, string> = {
  xs: 'h-1.5',
  sm: 'h-2',
  md: 'h-3',
};

const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  indeterminate = false,
  label,
  tone = 'primary',
  height = 'sm',
}) => {
  const width = indeterminate ? '40%' : `${Math.min(Math.max(value ?? 0, 0), 100)}%`;

  return (
    <div className="w-full space-y-1">
      {label && <p className="text-[11px] font-semibold text-slate-500">{label}</p>}
      <div className={`w-full rounded-full bg-slate-100 overflow-hidden ${heightClasses[height]}`}>
        <div
          className={`h-full bg-gradient-to-r ${toneClasses[tone]} shadow-inner ${
            indeterminate ? 'animate-progressIndeterminate' : ''
          }`}
          style={{ width, transition: indeterminate ? undefined : 'width 200ms ease' }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
