
import React, { useState } from 'react';
import AuthLayout from './AuthLayout';
import Input from '../ui/Input';
import Button from '../ui/Button';
import { MailIcon, LockIcon, UserIcon, GraduationCapIcon, BrainIcon } from '../icons';
import { signUp } from '../../services/authService';
import { User } from '../../types';

interface SignUpScreenProps {
  onSignUp: (user: User) => void;
  onSwitchToSignIn: () => void;
}

const SignUpScreen: React.FC<SignUpScreenProps> = ({ onSignUp, onSwitchToSignIn }) => {
  const [role, setRole] = useState<'student' | 'teacher'>('student');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // Simplified Organization State (Text Inputs)
  const [schoolName, setSchoolName] = useState('');
  const [grade, setGrade] = useState<number | ''>('');
  const [major, setMajor] = useState('');

  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if(password !== confirmPassword) {
        alert("비밀번호가 일치하지 않습니다.");
        return;
    }
    if (!schoolName.trim()) {
        alert("학교 이름을 입력해주세요.");
        return;
    }
    if (!grade) {
        alert("학년을 입력해주세요.");
        return;
    }
    if (role === 'student' && !major.trim()) {
        alert("전공을 입력해주세요.");
        return;
    }

    setIsLoading(true);
    try {
        const user = await signUp(
            name, 
            email, 
            role, 
            schoolName, 
            Number(grade), 
            major
        );
        onSignUp(user);
    } catch (error) {
        console.error(error);
        alert("회원가입 중 오류가 발생했습니다.");
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <AuthLayout 
      title="회원가입" 
      subtitle="정보를 입력하여 맞춤형 서비스를 이용하세요."
    >
      <div className="flex p-1 bg-slate-100 rounded-xl mb-6">
        <button
            type="button"
            onClick={() => setRole('student')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-bold transition-all ${role === 'student' ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
        >
            <GraduationCapIcon className="w-4 h-4" />
            학생용
        </button>
        <button
            type="button"
            onClick={() => setRole('teacher')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-bold transition-all ${role === 'teacher' ? 'bg-white text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
        >
            <BrainIcon className="w-4 h-4" />
            교사용
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="이름"
          type="text"
          placeholder="홍길동"
          value={name}
          onChange={(e) => setName(e.target.value)}
          icon={<UserIcon className="w-5 h-5" />}
          required
        />
        
        <div className="space-y-4">
             <Input
                label="학교명"
                placeholder="예: 이리공업고등학교"
                value={schoolName}
                onChange={(e) => setSchoolName(e.target.value)}
                required
            />
            
            <div className="grid grid-cols-2 gap-4">
                <Input
                    label="학년"
                    type="number"
                    placeholder="1"
                    min="1"
                    max="6"
                    value={grade}
                    onChange={(e) => setGrade(Number(e.target.value))}
                    required
                />
                
                <Input
                    label="전공"
                    type="text"
                    placeholder={role === 'teacher' ? "담당 과목/전공" : "예: 소프트웨어과"}
                    value={major}
                    onChange={(e) => setMajor(e.target.value)}
                    required={role === 'student'}
                />
            </div>
        </div>

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
        <Input
          label="비밀번호 확인"
          type="password"
          placeholder="••••••••"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          icon={<LockIcon className="w-5 h-5" />}
          required
        />

        <Button type="submit" fullWidth isLoading={isLoading} className="mt-4">
            가입하기
        </Button>
      </form>

      <div className="mt-6 text-center text-sm text-slate-600">
        이미 계정이 있으신가요?{' '}
        <button onClick={onSwitchToSignIn} className="text-primary font-bold hover:text-primary-dark">
          로그인
        </button>
      </div>
    </AuthLayout>
  );
};

export default SignUpScreen;
