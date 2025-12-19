import React, { useState } from 'react';
import AuthLayout from './AuthLayout';
import Input from '../ui/Input';
import Button from '../ui/Button';
import { MailIcon, LockIcon, IdBadgeIcon } from '../icons';
import { signIn } from '../../services/authService';
import { User } from '../../types';

interface SignInScreenProps {
  onSignIn: (user: User) => void;
  onSwitchToSignUp: () => void;
  mode?: 'staff' | 'student';
  onSwitchMode?: () => void;
}

const SignInScreen: React.FC<SignInScreenProps> = ({ onSignIn, onSwitchToSignUp, onSwitchMode, mode: initialMode = 'student' }) => {
  const [mode, setMode] = useState<'staff' | 'student'>(initialMode);
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);

  const handleLoginIdChange = (value: string) => {
    if (mode === 'student') {
      const sanitized = value.replace(/[@\s]/g, '');
      if (value !== sanitized) {
        setInlineError('학생 ID에 이메일은 사용할 수 없어요.');
      } else {
        setInlineError(null);
      }
      setLoginId(sanitized);
      return;
    }
    setInlineError(null);
    setLoginId(value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === 'student' && loginId.includes('@')) {
      setInlineError('학생 ID에 이메일은 사용할 수 없어요.');
      return;
    }
    setIsLoading(true);
    try {
      const user = await signIn(loginId, password, mode === 'student' ? 'student' : 'staff');
      onSignIn(user);
    } catch (e) {
      console.error(e);
      alert('로그인에 실패했습니다. 계정을 확인해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="로그인"
      subtitle="학생은 발급받은 ID, 교사/관리자는 업무용 이메일을 사용하세요."
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <Input
          label={mode === 'student' ? '학생 ID' : '업무용 이메일'}
          type={mode === 'student' ? 'text' : 'email'}
          placeholder={mode === 'student' ? '예: 001000100001' : 'name@school.ac.kr'}
          value={loginId}
          onChange={(e) => handleLoginIdChange(e.target.value)}
          icon={mode === 'student' ? <IdBadgeIcon className="w-6 h-6" /> : <MailIcon className="w-5 h-5" />}
          required
        />
        {inlineError && <p className="text-xs text-rose-500">{inlineError}</p>}
        <Input
          label="비밀번호"
          type="password"
          allowReveal
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          icon={<LockIcon className="w-5 h-5" />}
          required
        />

        <div className="flex items-center justify-between text-sm">
            <label className="flex items-center text-slate-600 cursor-pointer">
                <input type="checkbox" className="mr-2 rounded border-slate-300 text-primary focus:ring-primary bg-white" />
                로그인 상태 유지
            </label>
            <button type="button" className="text-primary font-medium hover:text-primary-dark">
                비밀번호 찾기
            </button>
        </div>

        <Button type="submit" fullWidth isLoading={isLoading}>
            로그인
        </Button>

        <div className="pt-4 text-center">
          <button
            type="button"
              onClick={() => {
              const next = mode === 'student' ? 'staff' : 'student';
                setMode(next);
                setInlineError(null);
                setLoginId('');
                onSwitchMode && onSwitchMode();
              }}
            className="text-sm text-primary font-semibold hover:text-primary-dark"
          >
            {mode === 'student' ? '교사/관리자 로그인으로 전환' : '학생 로그인으로 전환'}
          </button>
        </div>
      </form>

      {mode === 'staff' && (
        <div className="mt-6 text-center text-sm text-slate-600">
          교사/관리자 신규 계정이 필요하신가요?{' '}
          <button onClick={onSwitchToSignUp} className="text-primary font-bold hover:text-primary-dark">
            회원가입
          </button>
        </div>
      )}
    </AuthLayout>
  );
};

export default SignInScreen;
