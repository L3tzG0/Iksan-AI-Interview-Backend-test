import React, { useState, useCallback, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation, useParams } from 'react-router-dom';
import WelcomeScreen from './components/WelcomeScreen';
import InterviewSession from './components/InterviewSession';
import ResultsScreen from './components/ResultsScreen';
import TeacherDashboard from './components/TeacherDashboard';
import StudentDetailView from './components/StudentDetailView';
import TeacherHome from './components/TeacherHome';
import SignInScreen from './components/auth/SignInScreen';
import SignUpScreen from './components/auth/SignUpScreen';
import Navbar from './components/layout/Navbar';
import { InterviewReport, Question, Answer, User, InterviewStartPayload } from './types';
import { generateQuestions, evaluateAnswers, saveInterviewReportForStudent, getStudentDetails } from './services/geminiService';
import { GraduationCapIcon } from './components/icons';
import { clearStoredToken } from './services/authService';

interface AdminHeaderProps {
    user?: User | null;
}

const AdminHeader: React.FC<AdminHeaderProps> = ({ user }) => (
  <div className="bg-white/90 p-6 rounded-[24px] border border-white/70 shadow-soft mb-6 flex items-center justify-between animate-fadeIn">
    <div className="flex items-center gap-4">
      <div className="p-4 bg-primary-lightest rounded-2xl shadow-inner shadow-white/60">
        <GraduationCapIcon className="w-8 h-8 text-primary" />
      </div>
      <div>
        <h2 className="font-bold text-slate-800 text-lg">교사용 개요</h2>
        <p className="text-sm text-slate-600">
            {user?.grade ? `${user.grade}학년 ` : ''}{user?.major ? `${user.major} ` : ''}학생들의 AI 모의면접 성과를 한눈에 확인하세요.
        </p>
      </div>
    </div>
  </div>
);

const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  // Auth State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  // App State
  const [questions, setQuestions] = useState<Question[]>([]);
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [studentHistory, setStudentHistory] = useState<InterviewReport[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [perQuestionSeconds, setPerQuestionSeconds] = useState(60);

  const clearDrafts = useCallback(() => {
    try {
      sessionStorage.removeItem('ai-interview-draft');
    } catch {
      // ignore
    }
  }, []);

  // Load student history if user is a student
  useEffect(() => {
      const fetchHistory = async () => {
          if (isAuthenticated && currentUser?.role === 'student') {
              try {
                  const details = await getStudentDetails(currentUser.id);
                  setStudentHistory(details.history || []);
              } catch (e) {
                  console.log("Fetching history failed (likely new user)", e);
                  setStudentHistory([]);
              }
          }
      };
      fetchHistory();
  }, [isAuthenticated, currentUser]);

  const handleAuthSuccess = (user: User) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
    navigate('/', { replace: true });
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setCurrentUser(null);
    setQuestions([]);
    setReport(null);
    setStudentHistory([]);
    clearDrafts();
    clearStoredToken();
    navigate('/signin', { replace: true });
  };

  const handleRoleToggle = () => {
    if (!currentUser) return;
    const newRole = currentUser.role === 'student' ? 'teacher' : 'student';
    setCurrentUser({ ...currentUser, role: newRole });
    navigate('/');
  };

  const handleStartInterview = useCallback(async (input: InterviewStartPayload) => {
    setIsLoading(true);
    setError(null);
    clearDrafts();
    setPerQuestionSeconds(input.perQuestionSeconds || 60);

    const goalLabel = input.intent === 'university' ? '대학교 진학' : '취업 준비';
    const targetDetail = input.intent === 'university'
      ? `희망 대학: ${(input.favoriteUniversities && input.favoriteUniversities.length > 0) ? input.favoriteUniversities.join(', ') : '미정'}, 전공: ${input.major || '미정'}`
      : `희망 분야: ${input.workField || '미정'}`;

    const mockQuestions: Question[] = [
      { id: 1, text: `${goalLabel} 관점에서 자신을 한 문장으로 소개해 주세요. (${targetDetail})`, type: "general" },
      { id: 2, text: input.intent === 'university'
          ? "선호하는 대학·전공에 지원하려는 동기와 준비한 활동을 STAR 구조로 설명해 주세요."
          : `${input.workField || '희망 분야'} 역할과 연관된 프로젝트 경험을 STAR 구조로 설명해 주세요.`, type: "resume-based" },
      { id: 3, text: "앞서 공유한 자료에서 본인이 가장 강점이라고 생각하는 역량을 구체적 사례와 함께 이야기해 주세요.", type: "general" },
    ];
    setQuestions(mockQuestions);
    setIsLoading(false);
    navigate('/interview');
    return;

    // For live generation, replace with backend AI calls
  }, [clearDrafts, navigate]);

  const handleFinishInterview = useCallback(async (answers: Answer[]) => {
    setIsLoading(true);
    setError(null);
    try {
      const hasMeaningfulAnswer = answers.some((answer) => answer.text && answer.text.trim().length > 2);
      if (!hasMeaningfulAnswer) {
        setError('답변이 비어 있어 평가할 수 없습니다. 최소 한 문장을 작성해 주세요.');
        setIsLoading(false);
        return;
      }

      const interviewReport = await evaluateAnswers(questions, answers);
      if (currentUser) {
        saveInterviewReportForStudent(currentUser.id, interviewReport);
        const details = await getStudentDetails(currentUser.id);
        setStudentHistory(details.history || []);
      }
      setReport(interviewReport);
      clearDrafts();
      navigate('/results');
    } catch (err) {
      setError('보고서 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [questions, currentUser, navigate, clearDrafts]);

  const handleTryAnotherTopic = () => {
    setQuestions([]);
    setReport(null);
    clearDrafts();
    navigate('/');
  };

  const handleViewHistoryReport = (historyReport: InterviewReport) => {
    setReport(historyReport);
    navigate('/results');
  };

  const handleViewStudent = (studentId: string) => {
    navigate(`/teacher/students/${studentId}`);
  };

  const renderError = () => (
    <div className="flex flex-col items-center justify-center h-[60vh] text-slate-700">
      <div className="bg-red-100 border border-red-400 p-6 rounded-lg text-center shadow-lg">
        <h2 className="text-xl font-bold mb-2 text-red-800">요청이 실패했어요</h2>
        <p className="text-red-700 leading-relaxed">{error}</p>
        <p className="text-sm text-red-600 mt-2">
          네트워크 상태를 확인하거나 잠시 후 다시 시도해 주세요. 계속 문제되면 관리자를 통해 문의해 주세요. 
        </p>
        <button 
            onClick={() => {
              setError(null);
              navigate('/');
            }} 
            className="mt-4 px-4 py-2 bg-primary text-white hover:bg-primary-dark rounded-md transition-colors"
        >
            다시 시도
        </button>
      </div>
    </div>
  );

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/signin" element={<SignInScreen onSignIn={handleAuthSuccess} onSwitchToSignUp={() => navigate('/signup')} />} />
        <Route path="/signup" element={<SignUpScreen onSignUp={handleAuthSuccess} onSwitchToSignIn={() => navigate('/signin')} />} />
        <Route path="*" element={<Navigate to="/signin" replace />} />
      </Routes>
    );
  }

  if (isAuthenticated && (location.pathname === '/signin' || location.pathname === '/signup')) {
    return <Navigate to="/" replace />;
  }

  const isTeacher = currentUser?.role === 'teacher';

  const TeacherRoute: React.FC<{ element: React.ReactElement }> = ({ element }) =>
    isTeacher ? element : <Navigate to="/" replace />;

  const InlineStudentDetail: React.FC = () => {
    const { id } = useParams();
    if (!id) return <Navigate to="/teacher/dashboard" replace />;
    return <StudentDetailView studentId={id} onBack={() => navigate('/teacher/dashboard')} />;
  };

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-[#f8f5ff] via-white to-[#f2eefe] text-slate-700 font-elice overflow-hidden">
      <div className="absolute -top-24 -right-16 w-72 h-72 bg-primary/10 rounded-full blur-3xl animate-pulseSlow pointer-events-none"></div>
      <div className="absolute top-24 -left-24 w-80 h-80 bg-primary-light/40 rounded-full blur-3xl animate-pulseSlow pointer-events-none"></div>
      <div className="relative z-10">
        <Navbar 
          user={currentUser!} 
          onLogout={handleLogout} 
          onToggleRole={handleRoleToggle}
          currentPath={location.pathname}
          onNavigate={(path) => navigate(path)}
          hasResults={!!report}
        />
        <main className="max-w-6xl mx-auto p-4 sm:p-6 lg:px-8 pt-8 pb-16">
          {isTeacher && location.pathname.startsWith('/teacher/dashboard') && <AdminHeader user={currentUser} />}
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-[60vh] text-slate-700">
              <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-primary"></div>
              <p className="mt-4 text-lg">AI가 준비를 마치고 있어요...</p>
            </div>
          )}
          {!isLoading && (
            <Routes>
              <Route
                path="/"
                element={
                  isTeacher ? (
                    <TeacherHome
                      user={currentUser!}
                      onGoDashboard={() => navigate('/teacher/dashboard')}
                      onPreviewStudent={() => navigate('/teacher/dashboard')}
                    />
                  ) : (
                    <WelcomeScreen 
                      onStart={handleStartInterview} 
                      history={studentHistory} 
                      onViewReport={handleViewHistoryReport}
                    />
                  )
                }
              />
              <Route
                path="/interview"
                element={
                  questions.length === 0 ? (
                    <Navigate to="/" replace />
                  ) : (
                    <InterviewSession
                      questions={questions}
                      onFinish={handleFinishInterview}
                      perQuestionSeconds={perQuestionSeconds}
                      onExit={() => navigate('/', { replace: true })}
                    />
                  )
                }
              />
              <Route
                path="/results"
                element={report ? <ResultsScreen report={report} onRetry={handleTryAnotherTopic} /> : <Navigate to="/" replace />}
              />
              <Route
                path="/teacher/dashboard"
                element={<TeacherRoute element={<TeacherDashboard currentUser={currentUser!} onSelectStudent={handleViewStudent} />} />}
              />
              <Route path="/teacher/students/:id" element={<TeacherRoute element={<InlineStudentDetail />} />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          )}
          {error && renderError()}
        </main>
      </div>
    </div>
  );
};

export default App;
