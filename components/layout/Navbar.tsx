import React, { useState, useRef, useEffect, useMemo } from 'react';
import { User } from '../../types';
import { LogOutIcon, ChevronDownIcon, GraduationCapIcon, HomeIcon, SparklesIcon, ChartIcon, UsersIcon, FileTextIcon, HistoryIcon } from '../icons';

interface NavbarProps {
  user: User;
  onLogout: () => void;
  currentPath: string;
  onNavigate?: (path: string) => void;
  hasResults?: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ user, onLogout, currentPath, onNavigate, hasResults }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems = useMemo(() => {
    const base: { path: string; label: string; disabled?: boolean; icon: React.ComponentType<React.SVGProps<SVGSVGElement>> }[] = [
      { path: '/', label: '홈', icon: HomeIcon },
    ];

    if (user.role === 'teacher' || user.role === 'admin') {
      base.push({ path: '/teacher/dashboard', label: '대시보드', icon: ChartIcon });
      base.push({ path: '/teacher/interview/preview', label: '학생 미리보기', icon: FileTextIcon });
      if (user.role === 'admin') {
        base.push({ path: '/admin/domains', label: '도메인 관리', icon: UsersIcon });
      }
    } else {
      base.push({ path: '/student/interview/start', label: '인터뷰 생성', icon: SparklesIcon });
      base.push({ path: '/student/history', label: '면접 기록', icon: HistoryIcon });
    }

    return base;
  }, [user.role, hasResults]);

  const isNavActive = (path: string) => {
    if (path === '/' && (currentPath === '/' || currentPath === '/student/home' || currentPath === '/teacher/home')) {
      return true;
    }
    if (path === '/teacher/dashboard' && (currentPath.startsWith('/teacher/students') || currentPath.startsWith('/teacher/dashboard'))) {
      return true;
    }
    if (path === '/admin/domains' && currentPath.startsWith('/admin')) {
      return true;
    }
    return currentPath === path;
  };

  return (
    <nav className="bg-white/80 backdrop-blur-xl border-b border-white/70 shadow-sm sticky top-0 z-50">
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center gap-4">
          <div className="flex items-center gap-8">
            <button
              type="button"
              onClick={() => onNavigate && onNavigate('/')}
              className="flex-shrink-0 flex items-center gap-3 hover:opacity-90 transition-opacity"
            >
              <img src="/logo.png" alt="익산 AI 인터뷰" className="h-14 w-auto object-contain" />
              <span className="text-xl font-bold text-slate-800 tracking-tight">AI 모의 면접</span>
            </button>
            <div className="hidden md:flex items-center gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isNavActive(item.path);
                return (
                  <button
                    key={item.path}
                    type="button"
                    disabled={item.disabled}
                    onClick={() => onNavigate && onNavigate(item.path)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${
                      active
                        ? 'bg-primary text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-700'
                    } ${item.disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
                  >
                    <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-primary'}`} />
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {(user.role === 'teacher' || user.role === 'admin') && user.schoolName && (
              <span className="hidden lg:flex items-center gap-2 text-sm text-slate-500 font-semibold bg-white px-3 py-1.5 rounded-full border border-slate-100 shadow-inner shadow-white/40">
                <UsersIcon className="w-4 h-4 text-primary" />
                {user.schoolName}
              </span>
            )}

            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="flex items-center gap-3 max-w-xs bg-white rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary p-1 pr-3 hover:bg-primary-lightest/40 transition-colors border border-transparent hover:border-primary-light"
              >
                <div className="h-9 w-9 rounded-full bg-primary-light flex items-center justify-center text-primary font-bold text-sm">
                  {user.name[0]}
                </div>
                <div className="hidden md:flex flex-col items-start">
                  <span className="text-sm font-semibold text-slate-700">{user.name}</span>
                  <span className="text-xs text-slate-500">
                    {user.role === 'teacher' ? '교사' : user.role === 'admin' ? '관리자' : '학생'}
                  </span>
                </div>
                <ChevronDownIcon className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {isMenuOpen && (
                <div className="origin-top-right absolute right-0 mt-3 w-64 rounded-2xl shadow-soft bg-white/95 border border-white/70 focus:outline-none animate-fadeIn overflow-hidden z-50">
                  <div className="py-1 divide-y divide-slate-100">
                    <div className="px-5 py-4 bg-primary-lightest/60">
                      <p className="text-sm text-slate-900 font-bold">{user.name}</p>
                      <p className="text-xs text-slate-600 mt-0.5">{user.schoolName}</p>
                      <p className="text-xs text-slate-400 mt-1 truncate">학번: {user.studentId || user.id}</p>
                    </div>
                    {(user.role === 'teacher' || user.role === 'admin') && (
                      <div className="py-1">
                        <button
                          onClick={() => {
                            onNavigate && onNavigate('/teacher/dashboard');
                            setIsMenuOpen(false);
                          }}
                          className={`w-full text-left px-4 py-3 text-sm hover:bg-primary-lightest/60 flex items-center gap-2 font-semibold ${
                            currentPath.startsWith('/teacher') ? 'text-primary' : 'text-slate-700'
                          }`}
                        >
                          <HomeIcon className="w-4 h-4 text-primary" />
                          교사 페이지로 이동
                        </button>
                      </div>
                    )}
                    <div className="py-1">
                      <button
                        onClick={onLogout}
                        className="w-full text-left px-4 py-3 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 font-semibold"
                      >
                        <LogOutIcon className="w-4 h-4" />
                        로그아웃
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
