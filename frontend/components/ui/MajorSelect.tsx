import React, { useEffect, useRef, useState } from 'react';
import Input from './Input';
import Spinner from '../Spinner';
import { fetchMajors } from '../../services/studentService';
import type { Major } from '../../types';

interface Props {
    label?: string;
    value: string;
    onChange: (v: string) => void;
    required?: boolean;
    placeholder?: string;
    className?: string;
    spinnerPositionClassName?: string;
    dropdownPositionClassName?: string;
} 

const MajorSelect: React.FC<Props> = ({
    label,
    value,
    onChange,
    required = false,
    placeholder = '선택하거나 입력하세요',
    className = '',
    spinnerPositionClassName = 'absolute right-3 top-9',
    dropdownPositionClassName = 'absolute left-0 right-0 mt-1',
}) => {
    const [inputValue, setInputValue] = useState(value || '');
    const [suggestions, setSuggestions] = useState<Major[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [open, setOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement | null>(null);
    const debounceRef = useRef<number | null>(null);

    useEffect(() => {
        // keep in sync with controlled value
        setInputValue(value || '');
    }, [value]);

    useEffect(() => {
        // initial load
        let mounted = true;
        setLoading(true);
        fetchMajors(1, 50)
            .then((res) => {
                console.log(res)
                if (!mounted) return;
                const items = (res as any)?.data ?? (res as any)?.items ?? res ?? [];
                setSuggestions(items);
            })
            .catch((err) => {
                console.error(err);
                if (!mounted) return;
                setError('전공 목록을 불러오지 못했습니다.');
            })
            .finally(() => mounted && setLoading(false));
        return () => {
            mounted = false;
        };
    }, []);

    useEffect(() => {
        // outside click to close
        const onDocClick = (e: MouseEvent) => {
            if (!containerRef.current) return;
            if (!containerRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener('click', onDocClick);
        return () => document.removeEventListener('click', onDocClick);
    }, []);

    const doSearch = (q: string) => {
        setLoading(true);
        setError(null);
        // try backend search (fetchMajors supports search param); fallback to client filter
        fetchMajors(1, 50, q)
            .then((res) => {
                console.log(res)
                const items = (res as any)?.data ?? (res as any)?.items ?? res ?? [];
                setSuggestions(items);
            })
            .catch((err) => {
                console.error(err);
                // fallback: client-side filter
                setSuggestions((prev) => prev.filter((m) => m.name.toLowerCase().includes(q.toLowerCase())));
                setError('검색 중 오류가 발생했습니다.');
            })
            .finally(() => setLoading(false));
    };

    const onInputChange = (v: string) => {
        setInputValue(v);
        onChange(v);
        setOpen(true);
        if (debounceRef.current) window.clearTimeout(debounceRef.current);
        debounceRef.current = window.setTimeout(() => {
            doSearch(v);
        }, 300);
    };

    const onSelectSuggestion = (s: Major) => {
        setInputValue(s.name);
        onChange(s.name);
        setOpen(false);
    };

    return (
        <div className={`w-full relative ${className}`} ref={containerRef}>
            {label && (
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    {label}
                    {required && <span className="text-red-500 ml-1">*</span>}
                </label>
            )}
            <div>
                <Input
                    placeholder={placeholder}
                    value={inputValue}
                    onChange={(e) => onInputChange(e.target.value)}
                    className="mb-1"
                    aria-autocomplete="list"
                    required={required}
                />
            </div>

            {loading && (
                <div className={spinnerPositionClassName}>
                    <Spinner size="small" label="" />
                </div>
            )} 

            {error && <p className="text-xs text-red-600 mt-1">{error}</p>}

            {open && (suggestions.length > 0 || (!loading && inputValue)) && (
                <div className={`${dropdownPositionClassName} bg-white border rounded-lg shadow-lg z-50 max-h-60 overflow-auto`}>
                    {suggestions.map((s) => (
                        <button
                            key={s.id}
                            type="button"
                            onClick={() => onSelectSuggestion(s)}
                            className="w-full text-left py-2 px-4 hover:bg-slate-50 text-sm text-slate-800"
                        >
                            {s.name}
                        </button>
                    ))}

                    {!suggestions.some((s) => s.name === inputValue) && inputValue.trim() !== '' && (
                        <button
                            type="button"
                            onClick={() => {
                                setInputValue(inputValue);
                                onChange(inputValue);
                                setOpen(false);
                            }}
                            className="w-full text-left border-t px-2 py-2 text-sm text-slate-700 hover:bg-slate-50"
                            aria-label={`Use "${inputValue}" as a new major`}
                        >
                            "{inputValue}"로 새 전공 사용
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};

export default MajorSelect;
