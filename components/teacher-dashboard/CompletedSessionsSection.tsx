import type { FC } from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CompletedSessionsSectionProps } from "../../types/teacherDashboard";
import type { StudentGoal, StudentSummary } from "../../types";
import FilterControls from "./FilterControls";
import SearchBar from "./SearchBar";
import Spinner from "../Spinner";
import Button from "../ui/Button";
import {
    fetchSessionsAll,
    type NormalizedSessionSummary,
} from "../../services/studentService";

const mapInterviewTypeToGoal = (value?: string): StudentGoal | undefined => {
    if (!value) return undefined;
    const normalized = value.toLowerCase();
    if (normalized === "job" || normalized === "work") return "work";
    if (normalized === "university") return "university";
    return undefined;
};

const normalizeSessionToSummary = (
    session: NormalizedSessionSummary
): StudentSummary | null => {
    const identifier = session.studentIdentifier || session.studentName || session.id;
    if (!identifier) return null;
    const grade = typeof session.gradeLevel === "number" ? session.gradeLevel : 0;
    const totalScore = typeof session.totalScore === "number" ? session.totalScore : 0;
    const statusValue = (session.status || "").toLowerCase();
    const completed = statusValue === "completed" || Boolean(session.completedAt);
    const sessionIdValue = session.id ?? (session as any).sessionId;

    return {
        id: String(identifier),
        name: session.studentName || "이름 없음",
        major: session.majorName || "",
        schoolName: session.schoolName || "",
        grade,
        latestScore: totalScore,
        improvement: 0,
        completed,
        status: completed ? "completed" : "in_progress",
        intent: mapInterviewTypeToGoal(session.interviewType),
        sessionId: sessionIdValue !== undefined ? String(sessionIdValue) : undefined,
        session_id: sessionIdValue !== undefined ? String(sessionIdValue) : undefined,
    };
};

const CompletedSessionsSection: FC<CompletedSessionsSectionProps> = ({}) => {
    const [isLoading, setIsLoading] = useState(false);
    const [studentWithSessionList, setStudentWithSessionList] = useState<StudentSummary[]>([]);
    const [page, setPage] = useState<number>(1);
    const PAGE_SIZE = 20;
    const [totalCount, setTotalCount] = useState<number | undefined>(undefined);
    const [searchTerm, setSearchTerm] = useState<string>('');
    const [debouncedSearchTerm, setDebouncedSearchTerm] = useState<string>(searchTerm);
    const SEARCH_DEBOUNCE_MS = 300;
    const [goalFilter, setGoalFilter] = useState<'all' | 'work' | 'university'>('all');

    useEffect(() => {
        const id = setTimeout(() => setDebouncedSearchTerm(searchTerm), SEARCH_DEBOUNCE_MS);
        return () => clearTimeout(id);
    }, [searchTerm]);

    useEffect(() => {
        let isActive = true;

        const loadCompletedSessions = async () => {
            setIsLoading(true);
            try {
                const interviewTypeParam = goalFilter === 'work' ? 'job' : goalFilter === 'university' ? 'university' : undefined;
                const { sessions, totalCount: tc } = await fetchSessionsAll({
                    page,
                    pageSize: PAGE_SIZE,
                    interviewType: interviewTypeParam,
                    search: debouncedSearchTerm || undefined,
                });
                if (!isActive) return;
                const normalized = sessions
                    .map(normalizeSessionToSummary)
                    .filter((student): student is StudentSummary => Boolean(student));
                setStudentWithSessionList(normalized);
                setTotalCount(typeof tc === 'number' ? tc : undefined);
            } catch (error) {
                console.error("Failed to fetch completed sessions:", error);
                setStudentWithSessionList([]);
                setTotalCount(undefined);
            } finally {
                if (isActive) {
                    setIsLoading(false);
                }
            }
        };

        loadCompletedSessions();
        return () => {
            isActive = false;
        };
    }, [page, goalFilter, debouncedSearchTerm]);

    useEffect(() => {
        if (page !== 1) setPage(1);
    }, [goalFilter, debouncedSearchTerm]);

    const navigate = useNavigate();

    return (
        <div className="space-y-4">
            <div className="flex lg:flex-row flex-col lg:items-center gap-4">
                {/* <SearchBar value={searchTerm} onChange={setSearchTerm} placeholder="학생 이름 검색" /> */}
                <FilterControls
                    goalFilter={goalFilter}
                    onGoalChange={(v) => setGoalFilter(v as typeof goalFilter)}
                    compact
                    showGrade={false}
                />
            </div>

            {isLoading ? (
                <div className="bg-white shadow-soft border border-slate-100 rounded-[20px] overflow-hidden">
                    <div className="flex justify-center py-16">
                        <Spinner label="학생 목록을 불러오는 중..." />
                    </div>
                </div>
            ) : studentWithSessionList.length === 0 ? (
                <div className="py-16 text-slate-500 text-center">
                    <p className="font-semibold text-lg">
                        표시할 세션이 없습니다.
                    </p>
                    <p className="mt-2 text-slate-400 text-sm">
                        필터를 변경하거나 학생을 추가해 주세요.
                    </p>
                </div>
            ) : (
                <div className="bg-white shadow-soft border border-slate-100 rounded-[20px] overflow-hidden">
                    <div className="flex flex-wrap items-center gap-3 bg-slate-50/80 px-6 py-3 border-slate-100 border-b text-slate-500 text-xs">
                        <span className="inline-flex items-center gap-2">
                            <span className="bg-green-400 border border-green-600 rounded-full w-3 h-3"></span>
                            완료
                        </span>
                        <span className="inline-flex items-center gap-2">
                            <span className="bg-amber-300 border border-amber-600 rounded-full w-3 h-3"></span>
                            진행중
                        </span>
                        <span className="font-semibold text-slate-400">
                            학생을 클릭하면 상세로 이동합니다.
                        </span>
                        <span className="ml-auto text-slate-400">
                            총 {studentWithSessionList.length}명
                        </span>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="min-w-full text-slate-600 text-sm text-left">
                            <thead className="bg-slate-50 border-slate-200 border-b text-slate-500 text-xs uppercase">
                                <tr>
                                    <th className="px-6 py-4 font-bold">
                                        이름
                                    </th>
                                    <th className="px-6 py-4 font-bold">
                                        학년
                                    </th>
                                    <th className="px-6 py-4 font-bold">
                                        전공
                                    </th>
                                    <th className="px-6 py-4 font-bold text-center">
                                        인터뷰 유형
                                    </th>
                                    <th className="px-6 py-4 font-bold text-center">
                                        상태
                                    </th>
                                    <th className="px-6 py-4 font-bold text-center">
                                        점수
                                    </th>
                                    <th className="px-6 py-4 font-bold text-center">
                                        개선률
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {studentWithSessionList.map((student) => (
                                    <tr
                                        key={student.id}
                                        className={`group cursor-pointer transition-all border-primary text-primary hover:bg-primary-lightest/80 `}
                                        onClick={() => {
                                            const sessionId =
                                                student.session_id ||
                                                student.sessionId;
                                            const path = sessionId
                                                ? `/teacher/students/${
                                                      student.id
                                                  }?session_id=${encodeURIComponent(
                                                      sessionId
                                                  )}`
                                                : `/teacher/students/${student.id}`;
                                            navigate(path);
                                        }}
                                    >
                                        <td className="px-6 py-4 font-semibold text-slate-800 group-hover:text-primary">
                                            {student.name}
                                        </td>
                                        <td className="px-6 py-4">
                                            {student.grade}학년
                                        </td>
                                        <td className="px-6 py-4 font-medium text-slate-700">
                                            {student.major}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {student.intent
                                                ? student.intent === "work"
                                                    ? "취업"
                                                    : "대학"
                                                : "알 수 없음"}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span
                                                className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-semibold ${
                                                    student.status ===
                                                    "completed"
                                                        ? "bg-green-100 text-green-700 border border-green-200"
                                                        : "bg-amber-100 text-amber-700 border border-amber-200"
                                                }`}
                                            >
                                                {student.status === "completed"
                                                    ? "완료"
                                                    : "진행중"}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 font-mono font-bold text-slate-800 text-center">
                                            {`${Number((student.latestScore).toFixed(2))}/10`}
                                        </td>
                                        <td
                                            className={`px-6 py-4 text-center font-mono font-bold ${
                                                student.improvement >= 0
                                                    ? "text-green-600"
                                                    : "text-red-600"
                                            }`}
                                        >
                                            {student.improvement >= 0
                                                ? `+ ${student.improvement}%`
                                                : `- ${Math.abs(
                                                      student.improvement
                                                  )}%`}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {/* Pagination */}
                    <div className="px-4 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
                        <div className="text-slate-500 text-xs">
                            {typeof totalCount === 'number' ? (() => {
                                const start = totalCount === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
                                const end = Math.min(page * PAGE_SIZE, totalCount);
                                return `표시 ${start} - ${end} / ${totalCount}명`;
                            })() : `페이지 ${page}`}
                        </div>
                        <div className="flex items-center gap-2">
                            <Button variant="secondary" disabled={page <= 1 || isLoading} onClick={() => setPage((p) => Math.max(1, p - 1))}>이전</Button>
                            <Button variant="secondary" disabled={isLoading || (typeof totalCount === 'number' && page >= Math.ceil(totalCount / PAGE_SIZE))} onClick={() => setPage((p) => p + 1)}>다음</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CompletedSessionsSection;
