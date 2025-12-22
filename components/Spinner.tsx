import React from 'react';

type Size = "small" | "medium" | "large";

const Spinner: React.FC<{ label?: string, size?: Size }> = ({ label = '로딩 중', size = "medium" }) => {
  const sizeMap: Record<Size, { wrapper: string; gradient: string; ring: string; spinner: string; inner: string; label: string }> = {
    small: {
      wrapper: 'w-6 h-6',
      gradient: 'absolute inset-0 rounded-full bg-gradient-to-tr from-primary via-primary/60 to-white opacity-20 blur-sm',
      ring: 'absolute inset-0 rounded-full border border-primary/20',
      spinner: 'absolute inset-0 rounded-full border-2 border-transparent border-t-primary border-r-primary/60 animate-spin',
      inner: 'absolute inset-1 rounded-full bg-white shadow-inner shadow-primary/20',
      label: 'text-[10px] font-semibold tracking-wide text-primary/80'
    },
    medium: {
      wrapper: 'w-12 h-12',
      gradient: 'absolute inset-0 rounded-full bg-gradient-to-tr from-primary via-primary/60 to-white opacity-20 blur-sm',
      ring: 'absolute inset-0 rounded-full border-2 border-primary/20',
      spinner: 'absolute inset-1 rounded-full border-4 border-transparent border-t-primary border-r-primary/60 animate-spin',
      inner: 'absolute inset-3 rounded-full bg-white shadow-inner shadow-primary/20',
      label: 'text-xs font-semibold tracking-wide text-primary/80'
    },
    large: {
      wrapper: 'w-16 h-16',
      gradient: 'absolute inset-0 rounded-full bg-gradient-to-tr from-primary via-primary/60 to-white opacity-20 blur-sm',
      ring: 'absolute inset-0 rounded-full border-2 border-primary/20',
      spinner: 'absolute inset-1 rounded-full border-6 border-transparent border-t-primary border-r-primary/60 animate-spin',
      inner: 'absolute inset-4 rounded-full bg-white shadow-inner shadow-primary/20',
      label: 'text-sm font-semibold tracking-wide text-primary/80'
    }
  };

  const v = sizeMap[size];

  return (
    <div className="flex flex-col items-center gap-2 text-primary" role="status" aria-live="polite">
      <div className={`relative ${v.wrapper}`}>
        <div className={v.gradient}></div>
        <div className={v.ring}></div>
        <div className={v.spinner}></div>
        <div className={v.inner}></div>
      </div>
      {label ? <span className={v.label}>{label}</span> : null}
    </div>
  );
};

export default Spinner;
