import React from "react";
import Button from "./ui/Button";
import {
    SparklesIcon,
    ChartIcon,
    UsersIcon,
    FileTextIcon,
    BrainIcon,
    LightbulbIcon,
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
        ? `${user.name}님, 반가워요! 학생들을 위한 연습 세션을 준비해볼까요?`
        : `${user.name}님, 나만의 AI 면접 코치​.`;
    const heroBody = isTeacher
        ? "대시보드에서 진행 상황을 확인하고, 학생 인터뷰를 관리할 수 있어요."
        : "내 서류를 기반으로 맞춤형 면접 질문을 생성하고 " +
          "즉각적인 모의면접과 피드백까지 제공하는 AI 기반 면접 플랫폼​";

    const teacherCards = [
        {
            icon: <FileTextIcon className="w-5 h-5" />,
            title: "맞춤 질문 세트",
            body: "자기소개서·이력서·생활기록부 기반 맞춤 질문 세트 제공.",
        },
        {
            icon: <BrainIcon className="w-5 h-5" />,
            title: "실전 면접 연습",
            body: "인적성·직무·산업 등 다양한 질문 유형으로 실제 면접 흐름 그대로 연습.",
        },
        {
            icon: <LightbulbIcon className="w-5 h-5" />,
            title: "피드백 & 팁",
            body: "정확도와 유창성 점검, 문장별 코멘트와 답변 팁까지.",
        },
    ];
    const studentCards = [
        {
            icon: <FileTextIcon className="w-5 h-5" />,
            title: "맞춤 질문 세트",
            body: "자기소개서·이력서·생활기록부 기반 맞춤 질문 세트 제공.",
        },
        {
            icon: <BrainIcon className="w-5 h-5" />,
            title: "실전 면접 연습",
            body: "인적성·직무·산업 등 다양한 질문 유형으로 실제 면접 흐름 그대로 연습.",
        },
        {
            icon: <LightbulbIcon className="w-5 h-5" />,
            title: "피드백 & 팁",
            body: "정확도와 유창성 점검, 문장별 코멘트와 답변 팁까지.",
        },
    ];
    const cards = isTeacher ? teacherCards : studentCards;

    const cardGridClass =
        cards.length === 1
            ? "grid grid-cols-1 gap-4"
            : cards.length === 2
            ? "grid grid-cols-1 md:grid-cols-2 gap-4"
            : "grid grid-cols-1 md:grid-cols-3 gap-4";

    return (
        <div className="space-y-8 animate-fadeIn">
            <section className="relative py-10 pl-3 md:pl-6">
                {/* <div className="-top-10 -right-10 hero-blob hero-blob--primary"></div> */}
                {/* <div className="bottom-0 -left-10 hero-blob hero-blob--secondary"></div> */}
                <div className="z-10 relative flex md:flex-row flex-col md:items-center gap-8">
                    <div className="space-y-4">
                        <p className="flex items-center gap-2 font-semibold text-primary-text text-sm uppercase tracking-[0.2em]">
                            환영합니다
                        </p>
                        <h1 className="font-bold text-slate-900 text-3xl md:text-4xl leading-tight">
                            {heroTitle}
                        </h1>
                        <p className="max-w-3xl text-slate-600 leading-relaxed">
                            {heroBody}
                        </p>
                        <div className="flex flex-wrap gap-3">
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
                        </div>
                    </div>
                    {!isTeacher && (
                        <div className="flex lg:flex-row md:flex-col gap-4 min-w-[260px] animate-softFadeUp">
                            {latestReport && (
                                <div className="flex-1 space-y-3 bg-white/90 shadow-soft p-6 border border-white/70 rounded-[24px]">
                                    <p className="font-semibold text-slate-500 text-xs uppercase">
                                        최근 점수
                                    </p>
                                    <div className="flex justify-center items-baseline gap-2">
                                        <span className="font-bold text-primary text-5xl">
                                            {latestReport.totalScore?.toFixed(1) ??
                                                "--"}
                                        </span>
                                        <span className="text-slate-500 text-sm">
                                            / 10
                                        </span>
                                    </div>
                                    <p className="text-slate-600 text-sm">
                                        {latestReport.summary?.strengths?.slice(
                                            0,
                                            60
                                        ) ?? ""}
                                    </p>
                                    <Button
                                        onClick={onViewResults}
                                        variant="secondary"
                                        fullWidth
                                        disabled={!hasResults}
                                    >
                                        결과 보기
                                    </Button>
                                </div>
                            )}
                            <div className="flex flex-col flex-1 justify-center items-center gap-2 shadow-soft p-6 border border-white/70 rounded-[24px]">
                                <p className="font-semibold text-slate-500 text-xs uppercase">
                                    남은 응시 횟수
                                </p>
                                <div className="flex justify-center items-baseline gap-2">
                                    <span className="font-bold text-slate-700 text-4xl">
                                        {typeof remainingAttempts === "number"
                                            ? remainingAttempts
                                            : "--"}
                                    </span>
                                    <span className="text-slate-500 text-sm">
                                        회
                                    </span>
                                </div>
                                <p className="text-slate-500 text-sm">
                                    계정 기준 잔여 횟수
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </section>

            <div className={cardGridClass}>
                {cards.map((card, index) => (
                    <div
                        key={card.title}
                        className={`bg-white rounded-[20px] border border-slate-100 shadow-soft p-5 flex flex-col gap-3 justify-between ${
                            index === 0
                                ? "animate-softFadeUp"
                                : "animate-softFadeUp-delayed"
                        }`}
                    >
                        <div className="flex items-center gap-3 font-bold text-primary text-lg">
                            {card.icon}
                            {card.title}
                        </div>
                        <p className="text-slate-600 text-sm">{card.body}</p>
                        {card.extra}
                        {card.button}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Landing;
