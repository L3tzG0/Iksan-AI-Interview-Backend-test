import React, { useState, useCallback, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation, useParams } from 'react-router-dom';
import WelcomeScreen from './components/WelcomeScreen';
import Landing from './components/Landing';
import InterviewSession from './components/InterviewSession';
import ResultsScreen from './components/ResultsScreen';
import TeacherDashboard from './components/TeacherDashboard';
import StudentDetailView from './components/StudentDetailView';
import StudentHistory from './components/StudentHistory';
import AdminDomainManagement from './components/admin/AdminDomainManagement';
import SignInScreen from './components/auth/SignInScreen';
import SignUpScreen from './components/auth/SignUpScreen';
import Navbar from './components/layout/Navbar';
import Spinner from './components/Spinner';
import { InterviewReport, Question, Answer, User, InterviewStartPayload } from './types';
import { fetchStudentSessionsForStudentRole } from './services/studentService';
import { initiateSession, submitSessionAnswers, fetchSessionStatus, fetchSessionDetail } from './services/sessionService';
// GraduationCapIcon removed (was only used by AdminHeader which is removed)
import { clearStoredToken, fetchProfile, getStoredToken, getTokenExpiry, refreshAuthToken } from './services/authService';
import Button from './components/ui/Button';

// AdminHeader removed

const AccessDenied: React.FC<{ onHome: () => void; message?: string }> = ({ onHome, message }) => (
  <div className="flex flex-col justify-center items-center min-h-[60vh] text-slate-700">
    <div className="space-y-4 bg-white shadow-2xl p-8 border border-slate-200 rounded-2xl w-full max-w-md text-center">
      <div className="flex justify-center items-center bg-rose-50 mx-auto border border-rose-200 rounded-full w-12 h-12">
        <span className="font-bold text-rose-500 text-xl">!</span>
      </div>
      <h2 className="font-bold text-slate-900 text-xl">접근 권한이 없습니다</h2>
      <p className="text-slate-600 text-sm">
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
  const [isWaitingForQuestions, setIsWaitingForQuestions] = useState(false);
  const [isWaitingForResults, setIsWaitingForResults] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const refreshTimerRef = React.useRef<number | null>(null);
  const progressTimerRef = React.useRef<number | null>(null);

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
          const sessions = await fetchStudentSessionsForStudentRole();
          const normalized = sessions
            .map((session, idx) => {
              const completedAt =
                (session as any)?.completed_at ||
                (session as any)?.completedAt ||
                (session as any)?.created_at ||
                (session as any)?.createdAt;
              const sortKey = completedAt ? Date.parse(completedAt) || 0 : 0;
              const totalScoreRaw = (session as any)?.total_score ?? (session as any)?.totalScore;
              const parsedScore = typeof totalScoreRaw === 'number' ? totalScoreRaw : Number(totalScoreRaw);
              const totalScore = Number.isFinite(parsedScore) ? parsedScore : 0;

              const report: InterviewReport = {
                sessionId: String(
                  (session as any)?.session_id ??
                    (session as any)?.sessionId ??
                    (session as any)?.id ??
                    `session-${idx + 1}`
                ),
                status: (session as any)?.status,
                totalScore: Number.isFinite(totalScore) ? totalScore : undefined,
                date: completedAt
                  ? new Date(completedAt).toLocaleDateString('ko-KR', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  : undefined,
              };

              return { sortKey, report };
            })
            .filter((item) => !!item.report.sessionId)
            .sort((a, b) => b.sortKey - a.sortKey)
            .map((item) => item.report);

          setStudentHistory(normalized);
        } catch (err) {
          console.error('Failed to fetch student history', err);
          setStudentHistory([]);
        }
      } else {
        setStudentHistory([]);
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

  const clearRefreshTimer = useCallback(() => {
    if (refreshTimerRef.current) {
      window.clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
  }, []);

  const clearProgressTimer = useCallback(() => {
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      clearRefreshTimer();
      return;
    }

    const token = getStoredToken();
    const expSeconds = getTokenExpiry(token);
    if (!expSeconds) return undefined;

    const expMs = expSeconds * 1000;
    const now = Date.now();
    const leadMs = 60 * 1000 * 3; // refresh 3 minutes before expiry
    const delay = Math.max(0, expMs - now - leadMs);

    refreshTimerRef.current = window.setTimeout(async () => {
      try {
        const result = await refreshAuthToken();
        const accessToken = result.accessToken || token;
        setCurrentUser((prev) => {
          if (!prev && result.user) {
            return { ...result.user, authToken: accessToken, refreshToken: result.refreshToken };
          }
          if (!prev) return prev;
          return {
            ...prev,
            ...result.user,
            authToken: accessToken || prev.authToken,
            refreshToken: result.refreshToken || prev.refreshToken,
          };
        });
        setIsAuthenticated(true);
      } catch (err) {
        console.error('Token refresh failed', err);
        handleLogout();
      }
    }, delay);

    return () => {
      clearRefreshTimer();
    };
  }, [clearRefreshTimer, currentUser?.authToken, handleLogout, isAuthenticated]);

  const handleStartInterview = useCallback(async (input: InterviewStartPayload) => {
    setIsLoading(true);
    setError(null);
    clearDrafts();
    setQuestions([]);
    setReport(null);
    setIsWaitingForResults(false);
    setIsWaitingForQuestions(true);
    setLoadingProgress(0);
    setPerQuestionSeconds(input.perQuestionSeconds || 60);
    setSessionId(null);

    try {
      const session = await initiateSession(input);
      if (!session.sessionId) {
        throw new Error('Session ID missing');
      }
      setSessionId(session.sessionId);
    } catch (err) {
      console.error('Failed to initiate interview session', err);
      setError('서버 오류로 인터뷰를 시작할 수 없습니다. 잠시 후 다시 시도해 주세요.');
      setIsWaitingForQuestions(false);
      setIsLoading(false);
      setLoadingProgress(0);
    }
  }, [clearDrafts]);

  const handleFinishInterview = useCallback(async (answers: Answer[]) => {
    if (!sessionId) {
      setError('세션 ID가 없습니다. 다시 시도해 주세요.');
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const answered = answers.filter(
        (answer) => !answer.isSkipped && (((answer.text || '').trim().length > 0) || answer.audioUrl)
      );
      const hasMeaningfulAnswer = answered.some((answer) => (answer.text || '').trim().length > 2 || answer.audioUrl);
      if (!hasMeaningfulAnswer) {
        setError('답변이 너무 짧습니다. 최소 3글자 이상 입력해 주세요.');
        setIsLoading(false);
        return;
      }

      await submitSessionAnswers(sessionId, answered);
      setIsWaitingForResults(true);
    } catch (err) {
      setError('답변 제출에 실패했습니다. 다시 시도해 주세요.');
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
    openReportBySessionId(historyReport.sessionId);
  };

  const mapQuestionsFromDetail = useCallback((detail: any): Question[] => {
    const feedback = Array.isArray(detail?.detailed_feedback) ? detail.detailed_feedback : [];
    return feedback
      .map((item: any, idx: number) => ({
        id: item?.question_order ?? idx + 1,
        questionOrder: item?.question_order ?? item.question_order,
        text: item?.question || item?.question_text || '',
        type: 'general' as const,
      }))
      .filter((q: Question) => q.text);
  }, []);

  const mapReportFromDetail = useCallback((detail: any): InterviewReport => {
    const feedback = Array.isArray(detail?.detailed_feedback) ? detail.detailed_feedback : [];
    const overallScore = detail?.overall_score ?? detail?.overallScore ?? detail?.total_score;
    const scoresFromFeedback = feedback.length
      ? {
          contentRelevance: feedback.reduce((sum: number, item: any) => sum + (item.content_relevance_score || 0), 0) / feedback.length || 0,
          structure: feedback.reduce((sum: number, item: any) => sum + (item.structure_score || 0), 0) / feedback.length || 0,
          fluency: feedback.reduce((sum: number, item: any) => sum + (item.fluency_score || 0), 0) / feedback.length || 0,
          confidence: feedback.reduce((sum: number, item: any) => sum + (item.confidence_score || 0), 0) / feedback.length || 0,
        }
      : undefined;

    const mapped: InterviewReport = {
      ...detail,
      sessionId: detail?.session_id || detail?.sessionId,
      status: detail?.status,
      overallScore,
      totalScore: detail?.total_score ?? overallScore,
      strengthSummary: detail?.strength_summary ?? detail?.strengthSummary,
      areasForGrowth: detail?.areas_for_growth ?? detail?.areasForGrowth,
      detailedFeedback: feedback,
      nextSteps: detail?.next_steps ?? detail?.nextSteps,
      scores: scoresFromFeedback,
      summary:
        detail?.strength_summary || detail?.areas_for_growth
          ? { strengths: detail.strength_summary || '', areasForGrowth: detail.areas_for_growth || '' }
          : undefined,
      nextStepsDetailed: Array.isArray(detail?.next_steps)
        ? detail.next_steps.map((step: any) =>
            typeof step === 'string'
              ? { title: step, description: step }
              : {
                  title: step?.title || step?.title_text || step?.label || '',
                  description: step?.description || step?.description_text || step?.body || '',
                }
          )
        : undefined,
    };

    return mapped;
  }, []);

  const openReportBySessionId = useCallback(
    async (sessionId: string | undefined) => {
      if (!sessionId) return;
      setIsLoading(true);
      setError(null);
      try {
        const detail = await fetchSessionDetail(sessionId);
        const mappedReport = mapReportFromDetail(detail);
        setReport(mappedReport as InterviewReport);
        const resultsPath = currentUser?.role === 'student' ? '/student/history/results' : '/teacher/dashboard';
        navigate(resultsPath);
      } catch (err) {
        console.error('Failed to load report from history', err);
        setError('이전 결과를 불러오지 못했습니다. 다시 시도해 주세요.');
      } finally {
        setIsLoading(false);
      }
    },
    [currentUser?.role, mapReportFromDetail, navigate]
  );

  useEffect(() => {
    if (!isWaitingForQuestions || !sessionId) return;
    let timer: any;
    const pollQuestions = async () => {
      try {
        const status = await fetchSessionStatus(sessionId);
        if (status.isReady) {
          clearProgressTimer();
          setLoadingProgress(100);
          const detail = await fetchSessionDetail(sessionId);
          console.log('Fetched session detail for questions', detail);
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
        setError('?? ??? ??????. ?? ??? ???.');
        setIsWaitingForQuestions(false);
        setIsLoading(false);
        setLoadingProgress(0);
      }
    };
    pollQuestions();
    timer = setInterval(pollQuestions, 3000);
    return () => clearInterval(timer);
  }, [isWaitingForQuestions, sessionId, navigate, mapQuestionsFromDetail, clearProgressTimer]);

  useEffect(() => {
    if (!isWaitingForQuestions) {
      clearProgressTimer();
      setLoadingProgress(0);
      return;
    }

    const tick = () => {
      setLoadingProgress((prev) => {
        if (prev >= 95) return prev;
        let increment = 0.2 + Math.random() * 0.6;
        if (prev < 70) increment = 0.8 + Math.random() * 1.6;
        else if (prev < 90) increment = 0.4 + Math.random() * 0.8;
        const next = Math.min(95, prev + increment);
        return Math.round(next);
      });
    };

    tick();
    progressTimerRef.current = window.setInterval(tick, 500);
    return () => clearProgressTimer();
  }, [isWaitingForQuestions, clearProgressTimer]);

  useEffect(() => {
    if (!isWaitingForResults || !sessionId) return;
    let timer: any;
    const pollResults = async () => {
      try {
        const status = await fetchSessionStatus(sessionId);
        if (status.isReady || status.status === 'completed') {
          const detail = await fetchSessionDetail(sessionId);
          const mappedReport = mapReportFromDetail(detail);
          setReport(mappedReport as InterviewReport);
          setIsWaitingForResults(false);
          setIsLoading(false);
          const resultsPath = currentUser?.role === 'student' ? '/student/history/results' : '/teacher/dashboard';
          navigate(resultsPath);
        }
      } catch (err) {
        console.error('Failed to poll results', err);
        setError('결과 생성에 실패했습니다. 다시 시도해 주세요.');
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
    <div className="z-40 fixed inset-0 flex justify-center items-center bg-slate-900/20 backdrop-blur-sm px-4">
      <div className="space-y-4 bg-white shadow-2xl p-6 border border-slate-100 rounded-2xl w-full max-w-md animate-fadeIn">
        <div className="flex justify-center items-center bg-amber-50 mx-auto border border-amber-100 rounded-full w-12 h-12">
          <span className="font-bold text-amber-500 text-xl">!</span>
        </div>
        <div className="space-y-2 text-center">
          <h2 className="font-bold text-slate-900 text-lg">잠시 멈췄어요</h2>
          <p className="text-slate-600 text-sm leading-relaxed">
            {error || '요청을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.'}
          </p>
          <p className="text-slate-500 text-xs">
            네트워크가 잠시 불안정할 때 가끔 발생할 수 있어요.
          </p>
        </div>
        <div className="flex sm:flex-row flex-col gap-2">
          <Button
            onClick={() => setError(null)}
            fullWidth
            className="justify-center bg-primary hover:bg-primary-dark text-white"
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
            className="justify-center hover:bg-slate-50 border border-slate-200 text-slate-700"
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
    const resultsPath = currentUser?.role === 'student' ? '/student/history/results' : '/teacher/dashboard';
    if (report) {
      navigate(resultsPath);
      return;
    }
    if (studentHistory.length > 0) {
      openReportBySessionId(studentHistory[0].sessionId);
    }
  };

  const InlineStudentDetail: React.FC = () => {
    const { id } = useParams();
    if (!id) return <Navigate to="/teacher/dashboard" replace />;
    return <StudentDetailView studentId={id} />;
  };

  const renderRestoringShell = () => (
    <div className="relative flex justify-center items-center min-h-screen overflow-hidden text-slate-700">
      <div className="-top-24 -right-16 absolute bg-primary/10 blur-3xl rounded-full w-72 h-72 animate-pulseSlow pointer-events-none"></div>
      <div className="top-32 -left-24 absolute bg-primary-light/40 blur-3xl rounded-full w-80 h-80 animate-pulseSlow pointer-events-none"></div>
      <Spinner label="로딩 중..." />
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
          element={<SignUpScreen defaultRole="teacher" onSwitchToSignIn={() => navigate('/signin/teacher')} />}
        />
        <Route
          path="/signup/admin"
          element={<SignUpScreen defaultRole="admin" onSwitchToSignIn={() => navigate('/signin/teacher')} />}
        />
        <Route path="*" element={<Navigate to={defaultSigninPath} replace />} />
      </Routes>
    );
  }

  return (
    <div className="relative bg-white min-h-screen overflow-visible font-elice text-slate-700">
      {/* <div className="-top-24 -right-16 absolute bg-primary/10 blur-3xl rounded-full w-72 h-72 animate-pulseSlow pointer-events-none"></div>
      <div className="top-24 -left-24 absolute bg-primary-light/40 blur-3xl rounded-full w-80 h-80 animate-pulseSlow pointer-events-none"></div> */}
      <div className="z-10 relative">
        <Navbar 
          user={currentUser!} 
          onLogout={handleLogout} 
          onToggleRole={handleRoleToggle}
          currentPath={location.pathname}
          onNavigate={(path) => navigate(path)}
        />
        <main className="mx-auto p-4 sm:p-6 lg:px-8 pt-8 pb-16 max-w-7xl">
          {/* AdminHeader removed */}
          {isLoading && (
            <div className="relative flex flex-col justify-center items-center bg-white/80 shadow-soft border border-white/70 rounded-3xl h-[60vh] overflow-hidden text-slate-700">
              <div className="-top-20 -right-12 absolute bg-primary/10 blur-3xl rounded-full w-64 h-64 animate-pulseSlow pointer-events-none"></div>
              <div className="top-16 -left-16 absolute bg-primary-light/40 blur-3xl rounded-full w-72 h-72 animate-pulseSlow pointer-events-none"></div>
              {isWaitingForQuestions ? (
                <div className="flex flex-col items-center gap-4">
                  <div className="scale-150 sm:scale-200">
                    <Spinner label="AI가 맞춤형 면접 질문을 준비하고 있어요" />
                  </div>
                  <p className="font-semibold text-primary text-sm">
                    {loadingProgress}%
                  </p>
                </div>
              ) : (
                <div className="scale-150 sm:scale-200">
                  <Spinner label="AI가 맞춤형 면접 질문을 준비하고 있어요" />
                </div>
              )}
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
                        onGoDashboard={() => navigate('/student/history/results')}
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
                        remainingAttempts={currentUser?.interviewSessionQuota ?? null}
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
                path="/student/history/results"
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
                path="/student/history"
                element={
                  <ProtectedRoute
                    allowed={['student']}
                    element={<StudentHistory history={studentHistory} onViewReport={handleViewHistoryReport} />}
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
                    element={<TeacherDashboard currentUser={currentUser!} />}
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
              <Route
                path="/admin/domains"
                element={
                  <ProtectedRoute allowed={['admin']} element={<AdminDomainManagement />} />
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
