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
import { fetchStudentSessions } from './services/studentService';
import { initiateSession, submitSessionAnswers, fetchSessionStatus, fetchSessionDetail } from './services/sessionService';
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
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionStatusMessage, setSessionStatusMessage] = useState<string | null>(null);
  const [isWaitingForQuestions, setIsWaitingForQuestions] = useState(false);
  const [isWaitingForResults, setIsWaitingForResults] = useState(false);

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
          const sessions = await fetchStudentSessions();
          setStudentHistory([]);
        } catch {
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
    setSessionId(null);
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
    setQuestions([]);
    setReport(null);
    setSessionStatusMessage(null);
    setIsWaitingForResults(false);
    setIsWaitingForQuestions(true);
    setPerQuestionSeconds(input.perQuestionSeconds || 60);
    setSessionId(null);

    try {
      const session = await initiateSession(input);
      if (!session.sessionId) {
        throw new Error('Session ID missing');
      }
      setSessionId(session.sessionId);
      setSessionStatusMessage(session.message || 'Request queued. Generating questions...');
    } catch (err) {
      console.error('Failed to initiate interview session', err);
      setError('?? ??? ???? ? ??????. ?? ? ?? ??? ???.');
      setIsWaitingForQuestions(false);
      setIsLoading(false);
    }
  }, [clearDrafts]);

  const handleFinishInterview = useCallback(async (answers: Answer[]) => {
    if (!sessionId) {
      setError('??? ???? ? ??????. ??? ????.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const hasMeaningfulAnswer = answers.some((answer) => (answer.text || '').trim().length > 2 || answer.audioUrl);
      if (!hasMeaningfulAnswer) {
        setError('??? ?? ?? ??? ? ????. ?? ? ??? ??? ???.');
        setIsLoading(false);
        return;
      }

      await submitSessionAnswers(sessionId, answers);
      setIsWaitingForResults(true);
      setSessionStatusMessage('??? ?? ??. ?? ??? ?? ????.');
    } catch (err) {
      setError('?? ??? ?? ???? ??????. ??? ????.');
      console.error(err);
      setIsLoading(false);
    }
  }, [sessionId]);

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

  const mapQuestionsFromDetail = useCallback((detail: any): Question[] => {
    const feedback = Array.isArray(detail?.detailed_feedback) ? detail.detailed_feedback : [];
    return feedback
      .map((item: any, idx: number) => ({
        id: item?.question_order ?? idx + 1,
        text: item?.question || item?.question_text || '',
        type: 'general' as const,
      }))
      .filter((q: Question) => q.text);
  }, []);

  const mapReportFromDetail = useCallback((detail: any): InterviewReport => {
    const feedback = Array.isArray(detail?.detailed_feedback) ? detail.detailed_feedback : [];
    const overallScore = detail?.overall_score ?? detail?.overallScore;
    return {
      sessionId: detail?.session_id || detail?.sessionId,
      status: detail?.status,
      overallScore,
      strengthSummary: detail?.strength_summary,
      areasForGrowth: detail?.areas_for_growth,
      detailedFeedback: feedback,
      nextSteps: detail?.next_steps,
      scores: feedback.length
        ? {
            contentRelevance: feedback.reduce((sum: number, item: any) => sum + (item.content_relevance_score || 0), 0) / feedback.length || 0,
            structure: feedback.reduce((sum: number, item: any) => sum + (item.structure_score || 0), 0) / feedback.length || 0,
            fluency: feedback.reduce((sum: number, item: any) => sum + (item.fluency_score || 0), 0) / feedback.length || 0,
            confidence: feedback.reduce((sum: number, item: any) => sum + (item.confidence_score || 0), 0) / feedback.length || 0,
          }
        : undefined,
      totalScore: overallScore,
      summary: detail?.strength_summary || detail?.areas_for_growth
        ? { strengths: detail.strength_summary || '', areasForGrowth: detail.areas_for_growth || '' }
        : undefined,
      nextStepsDetailed: Array.isArray(detail?.next_steps)
        ? detail.next_steps.map((step: string) => ({ title: step, description: step }))
        : undefined,
    };
  }, []);

  useEffect(() => {
    if (!isWaitingForQuestions || !sessionId) return;
    let timer: any;
    const pollQuestions = async () => {
      try {
        const status = await fetchSessionStatus(sessionId);
        if (status.message) setSessionStatusMessage(status.message);
        if (status.isReady) {
          const detail = await fetchSessionDetail(sessionId);
          const fetchedQuestions = mapQuestionsFromDetail(detail);
          if (!fetchedQuestions.length) {
            throw new Error('No questions returned');
          }
          const limit = detail?.per_question_seconds || detail?.time_limit_seconds || detail?.time_limit;
          if (limit) setPerQuestionSeconds(limit);
          setQuestions(fetchedQuestions);
          setIsWaitingForQuestions(false);
          setIsLoading(false);
          navigate('/student/interview');
        }
      } catch (err) {
        console.error('Failed to poll questions', err);
        setError('??? ??? ??????. ??? ????.');
        setIsWaitingForQuestions(false);
        setIsLoading(false);
      }
    };
    pollQuestions();
    timer = setInterval(pollQuestions, 3000);
    return () => clearInterval(timer);
  }, [isWaitingForQuestions, sessionId, navigate, mapQuestionsFromDetail]);

  useEffect(() => {
    if (!isWaitingForResults || !sessionId) return;
    let timer: any;
    const pollResults = async () => {
      try {
        const status = await fetchSessionStatus(sessionId);
        if (status.message) setSessionStatusMessage(status.message);
        if (status.isReady || status.status === 'completed') {
          const detail = await fetchSessionDetail(sessionId);
          const mappedReport = mapReportFromDetail(detail);
          setReport(mappedReport as InterviewReport);
          setIsWaitingForResults(false);
          setIsLoading(false);
          const resultsPath = currentUser?.role === 'student' ? '/student/results' : '/teacher/dashboard';
          navigate(resultsPath);
        }
      } catch (err) {
        console.error('Failed to poll results', err);
        setError('?? ??? ?? ??????. ??? ????.');
        setIsWaitingForResults(false);
        setIsLoading(false);
      }
    };
    pollResults();
    timer = setInterval(pollResults, 5000);
    return () => clearInterval(timer);
  }, [isWaitingForResults, sessionId, navigate, currentUser?.role, mapReportFromDetail]);
const homePath = getHomePathForRole(currentUser?.role || 'teacher');

  const getSigninPath = () =>
    location.pathname.startsWith('/teacher') ? '/signin/teacher' : '/signin/student';

  const ProtectedRoute: React.FC<{
    allowed: Array<User['role']>;
    element: React.ReactElement;
    message?: string;
  }> = ({ allowed, element, message }) => {
    if (!isAuthenticated || !currentUser) {
      return <Navigate to={getSigninPath()} replace />;
    }
    if (allowed.includes(currentUser.role)) return element;
    return <AccessDenied onHome={() => navigate(homePath, { replace: true })} message={message} />;
  };

  const NotFound: React.FC = () => (
    <AccessDenied
      onHome={() => navigate(homePath, { replace: true })}
      message="요청한 페이지를 찾을 수 없습니다. 홈으로 돌아가 주세요."
    />
  );

    const renderError = () => (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/20 backdrop-blur-sm px-4">
      <div className="max-w-md w-full bg-white border border-slate-100 shadow-2xl rounded-2xl p-6 space-y-4 animate-fadeIn">
        <div className="w-12 h-12 rounded-full bg-amber-50 border border-amber-100 flex items-center justify-center mx-auto">
          <span className="text-amber-500 text-xl font-bold">!</span>
        </div>
        <div className="space-y-2 text-center">
          <h2 className="text-lg font-bold text-slate-900">잠시 멈췄어요</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            {error || '요청을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.'}
          </p>
          <p className="text-xs text-slate-500">
            네트워크가 잠시 불안정할 때 가끔 발생할 수 있어요.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <Button
            onClick={() => setError(null)}
            fullWidth
            className="justify-center bg-primary text-white hover:bg-primary-dark"
          >
            다시 시도
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              setError(null);
              navigate(homePath, { replace: true });
            }}
            fullWidth
            className="justify-center border border-slate-200 text-slate-700 hover:bg-slate-50"
          >
            홈으로 이동
          </Button>
        </div>
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

  const renderRestoringShell = () => (
    <div className="flex items-center justify-center min-h-screen text-slate-700">
      <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-primary"></div>
    </div>
  );

  if (isRestoring) {
    return renderRestoringShell();
  }

  if (!isAuthenticated) {
    const defaultSigninPath = location.pathname.startsWith('/teacher') ? '/signin/teacher' : '/signin/student';
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
                  <ProtectedRoute
                    allowed={['student', 'teacher', 'admin']}
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
                  <ProtectedRoute
                    allowed={['student', 'teacher', 'admin']}
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
                  <ProtectedRoute
                    allowed={['student', 'teacher', 'admin']}
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
                  <ProtectedRoute
                    allowed={['student', 'teacher', 'admin']}
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
                  <ProtectedRoute
                    allowed={['teacher', 'admin']}
                    element={
                      <Landing
                        user={currentUser!}
                        hasResults={!!latestReport}
                        latestReport={latestReport}
                        onStartInterview={() => navigate('/teacher/dashboard/2')}
                        onGoDashboard={() => navigate('/teacher/dashboard/1')}
                        onViewResults={handleOpenLatestReport}
                        onGoTeacherTab1={() => navigate('/teacher/dashboard/1')}
                        onGoTeacherTab2={() => navigate('/teacher/dashboard/2')}
                        onGoTeacherPreview={() => navigate('/teacher/interview/preview')}
                      />
                    }
                  />
                }
              />
              <Route path="/teacher/dashboard" element={<Navigate to="/teacher/dashboard/1" replace />} />
              <Route
                path="/teacher/dashboard/:tab"
                element={
                  <ProtectedRoute
                    allowed={['teacher', 'admin']}
                    element={<TeacherDashboard currentUser={currentUser!} onSelectStudent={handleViewStudent} />}
                  />
                }
              />
              <Route
                path="/teacher/interview/preview"
                element={
                  <ProtectedRoute
                    allowed={['teacher', 'admin']}
                    element={
                      <WelcomeScreen
                        onStart={() => {}}
                        history={[]}
                        onViewReport={() => {}}
                      />
                    }
                  />
                }
              />
              <Route
                path="/teacher/students/:id"
                element={
                  <ProtectedRoute allowed={['teacher', 'admin']} element={<InlineStudentDetail />} />
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





