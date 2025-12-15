import React from 'react';

const Spinner: React.FC<{ label?: string }> = ({ label = '로딩 중' }) => {
  return (
    <div className="flex flex-col items-center gap-2 text-primary">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-primary via-primary/60 to-white opacity-20 blur-sm"></div>
        <div className="absolute inset-0 rounded-full border-2 border-primary/20"></div>
        <div className="absolute inset-1 rounded-full border-4 border-transparent border-t-primary border-r-primary/60 animate-spin"></div>
        <div className="absolute inset-3 rounded-full bg-white shadow-inner shadow-primary/20"></div>
      </div>
      <span className="text-xs font-semibold tracking-wide text-primary/80">{label}</span>
    </div>
  );
};

export default Spinner;
