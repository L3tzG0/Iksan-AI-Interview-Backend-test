import React, { useState } from "react";
import AuthLayout from "./AuthLayout";
import Input from "../ui/Input";
import Button from "../ui/Button";
import {
    MailIcon,
    LockIcon,
    UserIcon,
    GraduationCapIcon,
    BrainIcon,
} from "../icons";
import { signUp } from "../../services/authService";
import { User } from "../../types";

interface SignUpScreenProps {
    onSignUp: (user: User) => void;
    onSwitchToSignIn: () => void;
    defaultRole?: "teacher" | "admin";
}

const SignUpScreen: React.FC<SignUpScreenProps> = ({
    onSignUp,
    onSwitchToSignIn,
    defaultRole = "teacher",
}) => {
    const [role, setRole] = useState<"teacher" | "admin">(defaultRole);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");

    const [schoolName, setSchoolName] = useState("");

    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (password !== confirmPassword) {
            alert("비밀번호가 일치하지 않습니다.");
            return;
        }
        if (role === "teacher" && !schoolName.trim()) {
            alert("학교를 선택하거나 입력해주세요.");
            return;
        }
        // if (role === 'admin' && !organization.trim()) {
        //   alert('기관/회사를 입력해주세요.');
        //   return;
        // }

        setIsLoading(true);
        let role_id;
        if (role === "teacher") {
            role_id = 2; // 교사
        } else if (role === "admin") {
            role_id = 1; // 관리자
        }

        try {
            const user = await signUp(
                name,
                email,
                role_id,
                { school_name: schoolName },
                password
            );
            onSignUp(user);
        } catch (error) {
            console.error(error);
            alert("회원가입에 실패했습니다.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <AuthLayout
            title="회원가입"
            subtitle="교사/관리자 계정을 만들고 학생을 관리하세요."
        >
            <div className="flex bg-slate-100 mb-6 p-1 rounded-xl">
                <button
                    type="button"
                    onClick={() => setRole("teacher")}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-bold transition-all ${
                        role === "teacher"
                            ? "bg-white text-primary shadow-sm"
                            : "text-slate-500 hover:text-slate-700"
                    }`}
                >
                    <GraduationCapIcon className="w-4 h-4" />
                    교사 가입
                </button>
                <button
                    type="button"
                    onClick={() => setRole("admin")}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-bold transition-all ${
                        role === "admin"
                            ? "bg-white text-primary shadow-sm"
                            : "text-slate-500 hover:text-slate-700"
                    }`}
                >
                    <BrainIcon className="w-4 h-4" />
                    관리자 가입
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

                {role === "teacher" && (
                    <Input
                        label="학교"
                        placeholder="예: 익산고등학교"
                        value={schoolName}
                        onChange={(e) => setSchoolName(e.target.value)}
                        required
                    />
                )}

                {/* {role === 'teacher' ? (
          <Input
            label="학교"
            placeholder="예: 익산고등학교"
            value={schoolName}
            onChange={(e) => setSchoolName(e.target.value)}
            required
          />
        ) : (
          <Input
            label="기관 / 회사"
            placeholder="예: 익산 교육청"
            value={organization}
            onChange={(e) => setOrganization(e.target.value)}
            required
          />
        )} */}

                <Input
                    label="업무용 이메일"
                    type="email"
                    placeholder="name@school.ac.kr"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    icon={<MailIcon className="w-5 h-5" />}
                    required
                />
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
                <Input
                    label="비밀번호 확인"
                    type="password"
                    allowReveal
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    icon={<LockIcon className="w-5 h-5" />}
                    required
                />

                <Button
                    type="submit"
                    fullWidth
                    isLoading={isLoading}
                    className="mt-4"
                >
                    계정 만들기
                </Button>
            </form>

            <div className="mt-6 text-slate-600 text-sm text-center">
                이미 계정이 있으신가요?{" "}
                <button
                    onClick={onSwitchToSignIn}
                    className="font-bold text-primary hover:text-primary-dark"
                >
                    로그인
                </button>
            </div>
        </AuthLayout>
    );
};

export default SignUpScreen;
