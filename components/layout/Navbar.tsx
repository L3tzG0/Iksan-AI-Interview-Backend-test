import React, { useState, useRef, useEffect, useMemo } from 'react';
import { User } from '../../types';
import { LogOutIcon, ChevronDownIcon, GraduationCapIcon, HomeIcon, SparklesIcon, ChartIcon, UsersIcon, FileTextIcon, HistoryIcon } from '../icons';

interface NavbarProps {
  user: User;
  onLogout: () => void;
  currentPath: string;
  onNavigate?: (path: string) => void;
}

type NavItem = {
  path: string;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  disabled?: boolean;
  matchCurrentPath?: (currentPath: string) => boolean;
};

const Navbar: React.FC<NavbarProps> = ({ user, onLogout, currentPath, onNavigate }) => {
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
    const base: NavItem[] = [
      { path: '/', label: '홈', icon: HomeIcon },
    ];

    if (user.role === 'teacher' || user.role === 'admin') {
      base.push({
        path: '/teacher/dashboard/1',
        label: '면접 결과 대시보드​',
        icon: ChartIcon,
        matchCurrentPath: (currentPath) => currentPath === '/teacher/dashboard' || currentPath.startsWith('/teacher/dashboard/1'),
      });
      base.push({
        path: '/teacher/dashboard/2',
        label: '구성원 관리',
        icon: GraduationCapIcon,
        matchCurrentPath: (currentPath) => currentPath.startsWith('/teacher/dashboard/2') || currentPath.startsWith('/teacher/students'),
      });
      base.push({ path: '/teacher/interview/preview', label: '학생 미리보기', icon: FileTextIcon });
      if (user.role === 'admin') {
        base.push({ path: '/admin/domains', label: '도메인 관리', icon: UsersIcon });
      }
    } else {
      base.push({ path: '/student/interview/start', label: '면접 준비​', icon: SparklesIcon });
      base.push({ path: '/student/history', label: '면접 결과 대시보드', icon: HistoryIcon, matchCurrentPath: (currentPath) => currentPath.startsWith('/student/history') });
    }

    return base;
  }, [user.role]);

  const accountId =
    user.role === 'student' ? user.studentId || user.id : user.email || user.id;
  const schoolLabel = user.schoolName || '학교 정보 없음';

  const isNavActive = (item: NavItem) => {
    if (item.matchCurrentPath) {
      return item.matchCurrentPath(currentPath);
    }
    if (item.path === '/' && (currentPath === '/' || currentPath === '/student/home' || currentPath === '/teacher/home')) {
      return true;
    }
    if (item.path === '/admin/domains' && currentPath.startsWith('/admin')) {
      return true;
    }
    return currentPath === item.path;
  };

  return (
    <nav className="top-0 z-50 sticky bg-white/80 shadow-sm backdrop-blur-xl border-white/70 border-b">
      <div className="px-4 sm:px-6 lg:px-8 w-full">
        <div className="flex justify-between items-center gap-4 h-16">
          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={() => onNavigate && onNavigate('/')}
              className="flex flex-shrink-0 items-center hover:opacity-90 p-0 transition-opacity"
            >
              <img src="/logo.png" alt="익산 AI 인터뷰" className="w-auto h-14 object-contain" />
            </button>
            <div className="hidden md:flex items-center gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isNavActive(item);
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
              <span className="hidden lg:flex items-center gap-2 bg-white shadow-inner shadow-white/40 px-3 py-1.5 border border-slate-100 rounded-full font-semibold text-slate-500 text-sm">
                <UsersIcon className="w-4 h-4 text-primary" />
                {user.schoolName}
              </span>
            )}

            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="flex items-center gap-3 bg-white hover:bg-primary-lightest/40 p-1 pr-3 border border-transparent hover:border-primary-light rounded-full focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 max-w-xs transition-colors"
              >
                <div className="flex justify-center items-center bg-primary-light rounded-full w-9 h-9 font-bold text-primary text-sm">
                  {user.name[0]}
                </div>
                <div className="hidden md:flex flex-col items-start">
                  <span className="font-semibold text-slate-700 text-sm">{user.name}</span>
                  <span className="text-slate-500 text-xs">
                    {user.role === 'teacher' ? '교사' : user.role === 'admin' ? '관리자' : '학생'}
                  </span>
                </div>
                <ChevronDownIcon className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {isMenuOpen && (
                <div className="right-0 z-50 absolute bg-white/95 shadow-soft mt-3 border border-white/70 rounded-2xl focus:outline-none w-64 overflow-hidden origin-top-right animate-fadeIn">
                  <div className="py-1 divide-y divide-slate-100">
                    <div className="bg-primary-lightest/60 px-5 py-4">
                      <p className="font-bold text-slate-900 text-sm">{user.name}</p>
                      <p className="mt-0.5 text-slate-600 text-xs">{schoolLabel}</p>
                      <p className="mt-1 text-slate-400 text-xs truncate">계정 ID: {accountId}</p>
                    </div>
                    {(user.role === 'teacher' || user.role === 'admin') && (
                      <div className="py-1">
                        <button
                          onClick={() => {
                            onNavigate && onNavigate('/teacher/dashboard/1');
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
                        className="flex items-center gap-2 hover:bg-red-50 px-4 py-3 w-full font-semibold text-red-600 text-sm text-left"
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
