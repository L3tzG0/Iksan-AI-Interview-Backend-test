
import React from 'react';
import { ChevronDownIcon } from '../icons';

interface SelectOption {
    value: string | number;
    label: string;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
    label?: string;
    options: SelectOption[];
    error?: string;
    icon?: React.ReactNode;
    placeholder?: string;
}

const Select: React.FC<SelectProps> = ({ 
    label, 
    options, 
    error, 
    icon, 
    className = '', 
    placeholder = '선택하세요',
    required,
    ...props 
}) => {
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
                <select
                    className={`
                        w-full rounded-lg border text-slate-800 
                        focus:outline-none focus:ring-2 focus:ring-primary-focus focus:border-primary-focus 
                        transition-colors py-3 bg-white appearance-none
                        ${icon ? 'pl-10 pr-10' : 'px-4 pr-10'}
                        ${error ? 'border-red-500 focus:ring-red-200 focus:border-red-500' : 'border-slate-300'}
                        ${!props.value ? 'text-slate-400' : 'text-slate-800'}
                    `}
                    required={required}
                    {...props}
                >
                    <option value="" disabled>{placeholder}</option>
                    {options.map((option) => (
                        <option key={option.value} value={option.value} className="text-slate-800">
                            {option.label}
                        </option>
                    ))}
                </select>
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-slate-400">
                    <ChevronDownIcon className="w-4 h-4" />
                </div>
            </div>
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
        </div>
    );
};

export default Select;
