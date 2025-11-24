
import React, { useState, useCallback, useEffect } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import InterviewSession from './components/InterviewSession';
import ResultsScreen from './components/ResultsScreen';
import TeacherDashboard from './components/TeacherDashboard';
import StudentDetailView from './components/StudentDetailView';
import SignInScreen from './components/auth/SignInScreen';
import SignUpScreen from './components/auth/SignUpScreen';
import Navbar from './components/layout/Navbar';
import { InterviewReport, Question, Answer, User, AuthView, AppView } from './types';
import { generateQuestions, evaluateAnswers, saveInterviewReportForStudent, getStudentDetails } from './services/geminiService';
import { GraduationCapIcon } from './components/icons';

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
        <h2 className="font-bold text-slate-800 text-lg">오늘의 학급 현황</h2>
        <p className="text-sm text-slate-600">
            {user?.grade ? `${user.grade}학년 ` : ''}{user?.major ? `${user.major} ` : ''}학생들의 AI 면접 데이터를 한눈에 확인해 보세요.
        </p>
      </div>
    </div>
  </div>
);

const App: React.FC = () => {
  // Auth State
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authView, setAuthView] = useState<AuthView>('signin');

  // App State
  const [view, setView] = useState<AppView>('welcome');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [studentHistory, setStudentHistory] = useState<InterviewReport[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    
    if (user.role === 'teacher') {
        setView('teacherDashboard');
    } else {
        setView('welcome');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setCurrentUser(null);
    setAuthView('signin');
    setView('welcome');
    setQuestions([]);
    setReport(null);
    setStudentHistory([]);
  };

  const handleRoleToggle = () => {
    if (!currentUser) return;
    // Demo feature: toggle role but keep user data for simplicity in this mock
    const newRole = currentUser.role === 'student' ? 'teacher' : 'student';
    setCurrentUser({ ...currentUser, role: newRole });
    
    if (newRole === 'teacher') {
        setView('teacherDashboard');
    } else {
        setView('welcome');
    }
  };

  const handleStartInterview = useCallback(async (input: string | { data: string; mimeType: string }) => {
    setIsLoading(true);
    setError(null);

    // Prototype: bypass API calls so UI can be previewed instantly
    const mockQuestions: Question[] = [
      { id: 1, text: "최근 학교 프로젝트에서 가장 기억에 남는 경험은 무엇인가요?", type: "general" },
      { id: 2, text: "이력서에 적힌 동아리/동아리 활동 중 가장 도전적이었던 순간을 이야기해 주세요.", type: "resume-based" },
      { id: 3, text: "졸업 후 진로 목표와 그 이유를 구체적으로 설명해 주세요.", type: "general" },
    ];
    setQuestions(mockQuestions);
    setView('session');
    setIsLoading(false);
    return;

    // If you want live generation later, remove the return above and re-enable below.
    // try {
    //   const generatedQuestions = await generateQuestions(input);
    //   setQuestions(generatedQuestions);
    //   setView('session');
    // } catch (err) {
    //   setError('질문 생성 중 오류가 발생했어요. 다시 시도해 주세요.');
    //   console.error(err);
    // } finally {
    //   setIsLoading(false);
    // }
  }, []);

  const handleFinishInterview = useCallback(async (answers: Answer[]) => {
    setIsLoading(true);
    setError(null);
    try {
      const interviewReport = await evaluateAnswers(questions, answers);
      if (currentUser) {
        saveInterviewReportForStudent(currentUser.id, interviewReport);
        // Refresh history
        const details = await getStudentDetails(currentUser.id);
        setStudentHistory(details.history || []);
      }
      setReport(interviewReport);
      setView('results');
    } catch (err)
     {
      setError('답변 평가에 실패했습니다. 다시 시도해주세요.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [questions, currentUser]);

  const handleTryAnotherTopic = () => {
    setQuestions([]);
    setReport(null);
    setView('welcome');
  };

  const handleNavigate = useCallback((targetView: AppView) => {
    if (targetView === 'results' && !report) {
        setView('welcome');
        return;
    }
    if (targetView === 'session' && questions.length === 0) {
        setView('welcome');
        return;
    }
    if (targetView === 'teacherDashboard' && currentUser?.role !== 'teacher') {
        setView('welcome');
        return;
    }
    setView(targetView);
  }, [report, questions, currentUser]);

  const handleViewStudent = (studentId: string) => {
    setSelectedStudentId(studentId);
    setView('studentDetail');
  };

  const handleBackToDashboard = () => {
    setSelectedStudentId(null);
    setView('teacherDashboard');
  };
  
  const handleViewHistoryReport = (historyReport: InterviewReport) => {
      setReport(historyReport);
      setView('results');
  };

  const renderMainContent = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-[60vh] text-slate-700">
          <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-primary"></div>
          <p className="mt-4 text-lg">AI가 작업 중입니다...</p>
        </div>
      );
    }

    if (error) {
       return (
        <div className="flex flex-col items-center justify-center h-[60vh] text-slate-700">
            <div className="bg-red-100 border border-red-400 p-6 rounded-lg text-center shadow-lg">
                <h2 className="text-xl font-bold mb-2 text-red-800">오류가 발생했습니다</h2>
                <p className="text-red-700">{error}</p>
                <button 
                    onClick={() => {
                      setError(null);
                      setView('welcome');
                    }} 
                    className="mt-4 px-4 py-2 bg-primary text-white hover:bg-primary-dark rounded-md transition-colors"
                >
                    처음으로 돌아가기
                </button>
            </div>
        </div>
       );
    }

    switch (view) {
      case 'session':
        return <InterviewSession questions={questions} onFinish={handleFinishInterview} />;
      case 'results':
        return report && <ResultsScreen report={report} onRetry={handleTryAnotherTopic} />;
      case 'teacherDashboard':
        return currentUser && <TeacherDashboard currentUser={currentUser} onSelectStudent={handleViewStudent} />;
      case 'studentDetail':
        return selectedStudentId && <StudentDetailView studentId={selectedStudentId} onBack={handleBackToDashboard} />;
      case 'welcome':
      default:
        return (
            <WelcomeScreen 
                onStart={handleStartInterview} 
                history={studentHistory} 
                onViewReport={handleViewHistoryReport}
            />
        );
    }
  };

  // Authentication Flow
  if (!isAuthenticated) {
    if (authView === 'signin') {
        return <SignInScreen onSignIn={handleAuthSuccess} onSwitchToSignUp={() => setAuthView('signup')} />;
    } else {
        return <SignUpScreen onSignUp={handleAuthSuccess} onSwitchToSignIn={() => setAuthView('signin')} />;
    }
  }

  // Main App Flow
  return (
    <div className="relative min-h-screen bg-gradient-to-b from-[#f8f5ff] via-white to-[#f2eefe] text-slate-700 font-elice overflow-hidden">
      <div className="absolute -top-24 -right-16 w-72 h-72 bg-primary/10 rounded-full blur-3xl animate-pulseSlow pointer-events-none"></div>
      <div className="absolute top-24 -left-24 w-80 h-80 bg-primary-light/40 rounded-full blur-3xl animate-pulseSlow pointer-events-none"></div>
      <div className="relative z-10">
        <Navbar 
          user={currentUser!} 
          onLogout={handleLogout} 
          onToggleRole={handleRoleToggle}
          currentView={view}
          onNavigate={handleNavigate}
          hasResults={!!report}
        />
        <main className="max-w-6xl mx-auto p-4 sm:p-6 lg:px-8 pt-8 pb-16">
          {currentUser?.role === 'teacher' && view === 'teacherDashboard' && <AdminHeader user={currentUser} />}
          {renderMainContent()}
        </main>
      </div>
    </div>
  );
};

export default App;







