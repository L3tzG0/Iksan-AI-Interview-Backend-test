
import React, { useState } from 'react';
import { EyeIcon, EyeOffIcon } from '../icons';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
  allowReveal?: boolean;
}

const Input: React.FC<InputProps> = ({ label, error, icon, className = '', required, allowReveal = false, type, ...props }) => {
  const [show, setShow] = useState(false);
  const isPasswordReveal = allowReveal && type === 'password';
  const inputType = isPasswordReveal ? (show ? 'text' : 'password') : type;

  const paddingClasses =
    icon && isPasswordReveal ? 'pl-10 pr-12' :
    icon ? 'pl-10 pr-4' :
    isPasswordReveal ? 'px-4 pr-12' : 'px-4';

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        {icon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                {icon}
            </div>
        )}
        <input
          className={`
            w-full rounded-lg border text-slate-800 placeholder-slate-400 
            focus:outline-none focus:ring-2 focus:ring-primary-focus focus:border-primary-focus 
            transition-colors py-3 bg-white
            ${paddingClasses}
            ${error ? 'border-red-500 focus:ring-red-200 focus:border-red-500' : 'border-slate-300'}
          `}
          required={required}
          type={inputType}
          {...props}
        />
        {isPasswordReveal && (
          <button
            type="button"
            onClick={() => setShow((prev) => !prev)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
            aria-label={show ? '비밀번호 숨기기' : '비밀번호 보기'}
          >
            {show ? <EyeOffIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
          </button>
        )}
      </div>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};

export default Input;
