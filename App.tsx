import React, { useState, useCallback, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation, useParams } from 'react-router-dom';
import WelcomeScreen from './components/WelcomeScreen';
import Landing from './components/Landing';
import InterviewSession from './components/InterviewSession';
import ResultsScreen from './components/ResultsScreen';
import TeacherDashboard from './components/TeacherDashboard';
import StudentDetailView from './components/StudentDetailView';
import SignInScreen from './components/auth/SignInScreen';
import SignUpScreen from './components/auth/SignUpScreen';
import Navbar from './components/layout/Navbar';
import AddStudentModal from './components/AddStudentModal';
import { InterviewReport, Question, Answer, User, InterviewStartPayload } from './types';
import { evaluateAnswers, saveInterviewReportForStudent, getStudentDetails } from './services/geminiService';
import { initiateSession } from './services/sessionService';
import { GraduationCapIcon } from './components/icons';
import { clearStoredToken, fetchProfile } from './services/authService';
import Button from './components/ui/Button';

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

const AccessDenied: React.FC<{ onHome: () => void; message?: string }> = ({ onHome, message }) => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-700">
    <div className="max-w-md w-full bg-white border border-slate-200 shadow-2xl rounded-2xl p-8 space-y-4 text-center">
      <div className="w-12 h-12 rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center mx-auto">
        <span className="text-rose-500 text-xl font-bold">!</span>
      </div>
      <h2 className="text-xl font-bold text-slate-900">접근 권한이 없습니다</h2>
      <p className="text-sm text-slate-600">
        {message || '요청한 페이지를 볼 수 있는 권한이 없어요. 올바른 계정으로 로그인했는지 확인해주세요.'}
      </p>
      <Button onClick={onHome} fullWidth className="justify-center">
        홈으로 이동
      </Button>
    </div>
  </div>
);

const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const getHomePathForRole = useCallback(
    (role: User['role']) => (role === 'student' ? '/student/home' : '/teacher/home'),
    []
  );
  // Auth State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loginRedirectPath, setLoginRedirectPath] = useState<string | null>(null);
  // App State
  const [questions, setQuestions] = useState<Question[]>([]);
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [studentHistory, setStudentHistory] = useState<InterviewReport[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [perQuestionSeconds, setPerQuestionSeconds] = useState(60);
  const [isAddStudentOpen, setIsAddStudentOpen] = useState(false);
  const [isRestoring, setIsRestoring] = useState(true);

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

  // Restore session from stored token on reload
  useEffect(() => {
    const restore = async () => {
      try {
        const user = await fetchProfile();
        if (user) {
          setCurrentUser(user);
          setIsAuthenticated(true);
          setLoginRedirectPath(getHomePathForRole(user.role));
        }
      } catch (err) {
        console.error('Failed to restore session', err);
        clearStoredToken();
      }
      setIsRestoring(false);
    };
    restore();
  }, [getHomePathForRole]);

  useEffect(() => {
    if (isAuthenticated || isRestoring) return;
    const hintedRole = location.pathname.startsWith('/teacher') ? 'teacher' : 'student';
    setLoginRedirectPath(getHomePathForRole(hintedRole as User['role']));
  }, [getHomePathForRole, isAuthenticated, isRestoring, location.pathname]);

  const handleAuthSuccess = (user: User) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
    const roleHome = getHomePathForRole(user.role);
    const hintedHome =
      loginRedirectPath && loginRedirectPath.startsWith('/teacher') && user.role !== 'student'
        ? loginRedirectPath
        : loginRedirectPath && loginRedirectPath.startsWith('/student') && user.role === 'student'
        ? loginRedirectPath
        : roleHome;
    navigate(hintedHome, { replace: true });
    setLoginRedirectPath(null);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setCurrentUser(null);
    setQuestions([]);
    setReport(null);
    setStudentHistory([]);
    clearDrafts();
    clearStoredToken();
    navigate('/', { replace: true });
  };

  const handleRoleToggle = () => {
    if (!currentUser) return;
    if (currentUser.role === 'admin') return;
    const newRole = currentUser.role === 'student' ? 'teacher' : 'student';
    setCurrentUser({ ...currentUser, role: newRole });
    navigate('/');
  };

  const handleStartInterview = useCallback(async (input: InterviewStartPayload) => {
    setIsLoading(true);
    setError(null);
    clearDrafts();
    setPerQuestionSeconds(input.perQuestionSeconds || 60);

    try {
      const session = await initiateSession(input);
      const fetchedQuestions = session.questions || [];
      if (fetchedQuestions.length === 0) {
        throw new Error('질문을 불러오지 못했습니다.');
      }
      setQuestions(fetchedQuestions);
      setPerQuestionSeconds(session.timeLimitSeconds || input.perQuestionSeconds || 60);
      navigate('/student/interview');
    } catch (err) {
      console.error('Failed to initiate interview session', err);
      setError('면접 질문을 불러오는 데 실패했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setIsLoading(false);
    }
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
      navigate(currentUser?.role === 'student' ? '/student/results' : '/teacher/dashboard');
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
    navigate(currentUser?.role === 'student' ? '/student/results' : '/teacher/dashboard');
  };

  const handleViewStudent = (studentId: string) => {
    navigate(`/teacher/students/${studentId}`);
  };

  const homePath = getHomePathForRole(currentUser?.role || 'teacher');

  const GuardedRoute: React.FC<{ allowed: Array<User['role']>; element: React.ReactElement; message?: string }> = ({ allowed, element, message }) => {
    if (currentUser && allowed.includes(currentUser.role)) return element;
    return <AccessDenied onHome={() => navigate(homePath, { replace: true })} message={message} />;
  };

  const NotFound: React.FC = () => (
    <AccessDenied
      onHome={() => navigate(homePath, { replace: true })}
      message="요청한 페이지를 찾을 수 없습니다. 홈으로 돌아가 주세요."
    />
  );

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

  const isStaff = currentUser?.role === 'teacher' || currentUser?.role === 'admin';
  const latestReport = report ?? (studentHistory.length > 0 ? studentHistory[0] : null);

  const handleOpenLatestReport = () => {
    const resultsPath = currentUser?.role === 'student' ? '/student/results' : '/teacher/dashboard';
    if (report) {
      navigate(resultsPath);
      return;
    }
    if (studentHistory.length > 0) {
      setReport(studentHistory[0]);
      navigate(resultsPath);
    }
  };

  const InlineStudentDetail: React.FC = () => {
    const { id } = useParams();
    if (!id) return <Navigate to="/teacher/dashboard" replace />;
    return <StudentDetailView studentId={id} onBack={() => navigate('/teacher/dashboard')} />;
  };

  if (!isAuthenticated) {
    const defaultSigninPath = location.pathname.startsWith('/teacher') ? '/signin/teacher' : '/signin/student';
    if (isRestoring) {
      return (
        <div className="flex items-center justify-center min-h-screen text-slate-700">
          <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-primary"></div>
        </div>
      );
    }
    return (
      <Routes>
        <Route path="/" element={<Navigate to={defaultSigninPath} replace />} />
        <Route
          path="/signin"
          element={
            <SignInScreen
              mode="student"
              onSignIn={handleAuthSuccess}
              onSwitchToSignUp={() => navigate('/signup/teacher')}
              onSwitchMode={() => navigate('/signin/teacher')}
            />
          }
        />
        <Route
          path="/signin/student"
          element={
            <SignInScreen
              mode="student"
              onSignIn={handleAuthSuccess}
              onSwitchToSignUp={() => navigate('/signup/teacher')}
              onSwitchMode={() => navigate('/signin/teacher')}
            />
          }
        />
        <Route
          path="/signin/teacher"
          element={
            <SignInScreen
              mode="staff"
              onSignIn={handleAuthSuccess}
              onSwitchToSignUp={() => navigate('/signup/teacher')}
              onSwitchMode={() => navigate('/signin/student')}
            />
          }
        />
        <Route
          path="/signup/teacher"
          element={<SignUpScreen defaultRole="teacher" onSignUp={handleAuthSuccess} onSwitchToSignIn={() => navigate('/signin/teacher')} />}
        />
        <Route
          path="/signup/admin"
          element={<SignUpScreen defaultRole="admin" onSignUp={handleAuthSuccess} onSwitchToSignIn={() => navigate('/signin/teacher')} />}
        />
        <Route path="*" element={<Navigate to={defaultSigninPath} replace />} />
      </Routes>
    );
  }

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
          onOpenAddStudent={isStaff ? () => setIsAddStudentOpen(true) : undefined}
        />
        {isStaff && (
          <AddStudentModal
            isOpen={isAddStudentOpen}
            onClose={() => setIsAddStudentOpen(false)}
            defaultSchool={currentUser?.schoolName}
          />
        )}
        <main className="max-w-6xl mx-auto p-4 sm:p-6 lg:px-8 pt-8 pb-16">
          {isStaff && location.pathname.startsWith('/teacher') && <AdminHeader user={currentUser} />}
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
          <Navigate
            to={currentUser?.role === 'student' ? '/student/home' : '/teacher/home'}
            replace
          />
          }
        />
              <Route
                path="/student/home"
                element={
                  <GuardedRoute
                    allowed={['student']}
                    element={
                      <Landing
                        user={currentUser!}
                        hasResults={!!latestReport}
                        latestReport={latestReport}
                        onStartInterview={() => navigate('/student/interview/start')}
                        onGoDashboard={() => navigate('/student/results')}
                        onViewResults={handleOpenLatestReport}
                      />
                    }
                  />
                }
              />
              <Route
                path="/student/interview/start"
                element={
                  <GuardedRoute
                    allowed={['student']}
                    element={
                      <WelcomeScreen
                        onStart={handleStartInterview}
                        history={studentHistory}
                        onViewReport={handleViewHistoryReport}
                      />
                    }
                  />
                }
              />
              <Route
                path="/student/interview"
                element={
                  <GuardedRoute
                    allowed={['student']}
                    element={
                      questions.length === 0 ? (
                        <Navigate to="/student/home" replace />
                      ) : (
                        <InterviewSession
                          questions={questions}
                          onFinish={handleFinishInterview}
                          perQuestionSeconds={perQuestionSeconds}
                          onExit={() => navigate('/student/home', { replace: true })}
                        />
                      )
                    }
                  />
                }
              />
              <Route
                path="/student/results"
                element={
                  <GuardedRoute
                    allowed={['student']}
                    element={
                      report ? (
                        <ResultsScreen
                          report={report}
                          onRetry={handleTryAnotherTopic}
                          studentMeta={{
                            name: currentUser!.name,
                            schoolName: currentUser!.schoolName,
                            grade: currentUser!.grade,
                            major: currentUser!.major,
                          }}
                        />
                      ) : (
                        <Navigate to="/student/home" replace />
                      )
                    }
                  />
                }
              />
              <Route
                path="/teacher/home"
                element={
                  <GuardedRoute
                    allowed={['teacher', 'admin']}
                    element={
                      <Landing
                        user={currentUser!}
                        hasResults={!!latestReport}
                        latestReport={latestReport}
                        onStartInterview={() => navigate('/teacher/dashboard')}
                        onGoDashboard={() => navigate('/teacher/dashboard')}
                        onViewResults={handleOpenLatestReport}
                      />
                    }
                  />
                }
              />
              <Route
                path="/teacher/dashboard"
                element={
                  <GuardedRoute
                    allowed={['teacher', 'admin']}
                    element={<TeacherDashboard currentUser={currentUser!} onSelectStudent={handleViewStudent} />}
                  />
                }
              />
              <Route
                path="/teacher/students/:id"
                element={
                  <GuardedRoute allowed={['teacher', 'admin']} element={<InlineStudentDetail />} />
                }
              />
              <Route path="*" element={<NotFound />} />
            </Routes>
          )}
          {error && renderError()}
        </main>
      </div>
    </div>
  );
};

export default App;
