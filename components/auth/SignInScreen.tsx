
import React, { useState } from 'react';
import AuthLayout from './AuthLayout';
import Input from '../ui/Input';
import Button from '../ui/Button';
import { MailIcon, LockIcon } from '../icons';
import { signIn } from '../../services/authService';
import { User } from '../../types';

interface SignInScreenProps {
  onSignIn: (user: User) => void;
  onSwitchToSignUp: () => void;
}

const SignInScreen: React.FC<SignInScreenProps> = ({ onSignIn, onSwitchToSignUp }) => {
  const [email, setEmail] = useState('student@elice.io');
  // Pre-filled password for easy login
  const [password, setPassword] = useState('password1234');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
        // Simulate auth via service
        const user = await signIn(email);
        onSignIn(user);
    } catch (e) {
        console.error(e);
        alert("로그인에 실패했습니다.");
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <AuthLayout 
      title="로그인" 
      subtitle="계정에 로그인하여 서비스를 이용하세요."
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        <Input
          label="이메일"
          type="email"
          placeholder="example@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          icon={<MailIcon className="w-5 h-5" />}
          required
        />
        <Input
          label="비밀번호"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          icon={<LockIcon className="w-5 h-5" />}
          required
        />
        
        <div className="flex items-center justify-between text-sm">
            <label className="flex items-center text-slate-600 cursor-pointer">
                <input type="checkbox" className="mr-2 rounded border-slate-300 text-primary focus:ring-primary bg-white" />
                로그인 유지
            </label>
            <button type="button" className="text-primary font-medium hover:text-primary-dark">
                비밀번호 찾기
            </button>
        </div>

        <Button type="submit" fullWidth isLoading={isLoading}>
            로그인
        </Button>
      </form>

      <div className="mt-6 text-center text-sm text-slate-600">
        계정이 없으신가요?{' '}
        <button onClick={onSwitchToSignUp} className="text-primary font-bold hover:text-primary-dark">
          회원가입
        </button>
      </div>
    </AuthLayout>
  );
};

export default SignInScreen;
