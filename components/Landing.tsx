import React from "react";
import Button from "./ui/Button";
import {
    SparklesIcon,
    ChartIcon,
    UsersIcon,
    FileTextIcon,
    BrainIcon,
    LightbulbIcon,
    BriefcaseIcon
} from "./icons";
import type { InterviewReport, User } from "../types";

interface LandingProps {
    user: User;
    hasResults: boolean;
    latestReport?: InterviewReport | null;
    onStartInterview: () => void;
    onGoDashboard: () => void;
    onViewResults: () => void;
    onGoTeacherTab1?: () => void;
    onGoTeacherTab2?: () => void;
    onGoTeacherPreview?: () => void;
}

const Landing: React.FC<LandingProps> = ({
    user,
    hasResults,
    latestReport,
    onStartInterview,
    onGoDashboard,
    onViewResults,
    onGoTeacherTab1,
    onGoTeacherTab2,
    onGoTeacherPreview,
}) => {
    const isTeacher = user.role === "teacher" || user.role === "admin";
    const remainingAttempts = user.interviewSessionQuota;
    const heroTitle = isTeacher
        ? `나만의 AI 면접 코치`
        : `나만의 AI 면접 코치​`;
    const heroBody = isTeacher
    ? (
        <>
            내 서류를 기반으로 맞춤형 면접 질문을 생성하고 <br />
            즉각적인 모의면접과 피드백까지 제공하는 AI 기반 면접 플랫폼​
        </>
      )
    : (
        <>
            내 서류를 기반으로 맞춤형 면접 질문을 생성하고 <br />
            즉각적인 모의면접과 피드백까지 제공하는 AI 기반 면접 플랫폼​
        </>
      );

    const features = [
        {
            icon: <FileTextIcon className="w-5 h-5 text-primary" />,
            text: "자기소개서·이력서·생활기록부 기반 맞춤 질문 세트 제공",
        },
        {
            icon: <BriefcaseIcon className="w-5 h-5 text-primary" />,
            text: "인적성·직무·산업 등 다양한 질문 유형으로 실제 면접 흐름 그대로 연습",
        },
        {
            icon: <LightbulbIcon className="w-5 h-5 text-primary" />,
            text: "정확도와 유창성 점검, 문장별 코멘트와 답변 팁까지",
        },
    ];

    return (
        <div className="space-y-8 animate-fadeIn">
            <div className="relative left-1/2 right-1/2 ml-[-50vw] mr-[-50vw] w-screen -mt-6">
                <section className="relative bg-[#F2F0FF] py-8 md:py-16">
                    {/* <div className="-top-10 -right-10 hero-blob hero-blob--primary"></div> */}
                    {/* <div className="bottom-0 -left-10 hero-blob hero-blob--secondary"></div> */}
                    <div className="px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
                        <div className="z-10 relative flex md:flex-row flex-col md:items-center justify-between gap-10 md:gap-16 lg:gap-24 w-full">
                    <div className="space-y-4 max-w-3xl">
                        {/* <p className="flex items-center gap-2 font-semibold text-primary-text text-sm uppercase tracking-[0.2em]">
                            환영합니다
                        </p> */}
                        <h1 className="font-bold text-slate-900 text-2xl md:text-4xl lg:text-5xl leading-tight">
                            {heroTitle}
                        </h1>
                        <p className="max-w-3xl text-slate-600 md:text-2xl leading-relaxed">
                            {heroBody}
                        </p>
                        {/* <div className="flex flex-wrap gap-3">
                            {isTeacher ? (
                                <Button
                                    onClick={onGoTeacherTab1 || onGoDashboard}
                                    className="px-6 py-3"
                                >
                                    면접 결과표 확인하기​
                                </Button>
                            ) : (
                                <Button
                                    onClick={onStartInterview}
                                    className="px-6 py-3"
                                >
                                    결과표 확인하기
                                </Button>
                            )}
                        </div> */}
                    </div>
                    <div className="flex flex-col gap-3 w-full sm:w-[320px] md:w-[280px] animate-softFadeUp">
                        {isTeacher ? (
                            <Button
                                onClick={onGoTeacherTab1 || onGoDashboard}
                                variant="secondary"
                                className="w-full px-6 py-3"
                            >
                                면접 결과표 확인하기​
                            </Button>
                        ) : (
                            <div className="w-full text-center text-sm font-semibold text-slate-700 bg-white/90 px-6 py-2 rounded-lg border border-slate-200">
                                면접 준비하기 <br />(남은 횟수: {typeof remainingAttempts === "number" ? remainingAttempts : "--"}회)
                            </div>
                        )}
                        {!isTeacher && (
                            <Button
                                onClick={onStartInterview}
                                className="w-full px-6 py-2"
                                disabled={!hasResults}
                            >
                                결과표 확인하기
                            </Button>
                        )}
                    </div>
                        </div>
                    </div>
                </section>
            </div>

            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="space-y-3 mt-6">
                    {features.map((f) => (
                        <div key={f.text} className="flex items-start gap-3 text-slate-700 text-xl">
                            <div className="mt-1 text-primary">{f.icon}</div>
                            <p className="leading-relaxed">{f.text}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Landing;
