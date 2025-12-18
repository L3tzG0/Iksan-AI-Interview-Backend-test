
export interface School {
    id: string;
    name: string;
}

export interface Major {
    id: string;
    name: string;
    schoolId?: string;
    schoolName?: string;
}

export interface ClassRoom {
    id: string;
    name: string;
    gradeLevel?: number;
    schoolId?: string;
    schoolName?: string;
}

export type AppView = 'welcome' | 'session' | 'results' | 'teacherDashboard' | 'studentDetail' | 'studentPreview';

export interface Question {
  id: number;
  text: string;
  type: 'general' | 'resume-based';
}

export type StudentGoal = 'university' | 'work';

export interface InterviewStartPayload {
  resumeText?: string;
  fileData?: { data: string; mimeType: string };
  intent: StudentGoal;
  favoriteUniversities?: string[];
  major?: string;
  workIndustry?: string;
  workField?: string;
  perQuestionSeconds?: number;
}

export interface Answer {
  questionId: number;
  text: string;
  audioUrl?: string;
  questionOrder?: number;
  questionText?: string;
  audioDurationSeconds?: number;
  wordCount?: number;
  totalPauseDurationSeconds?: number;
  totalPauseCount?: number;
}

export interface QuestionFeedback {
  question: string;
  question_order?: number;
  answer?: string;
  evaluation?: string;
  content_relevance_score?: number;
  structure_score?: number;
  fluency_score?: number;
  confidence_score?: number;
  overall_score?: number;
  is_correct?: boolean;
  audio_duration_seconds?: number;
  word_count?: number;
  total_pause_duration_seconds?: number;
  total_pause_count?: number;
}

export interface InterviewReport {
  sessionId?: string;
  status?: string;
  overallScore?: number;
  strengthSummary?: string;
  areasForGrowth?: string;
  detailedFeedback?: QuestionFeedback[];
  nextSteps?: string[];
  date?: string; // legacy/history support
  scores?: {
    contentRelevance: number;
    structure: number;
    fluency: number;
    confidence: number;
  };
  totalScore?: number;
  summary?: {
    strengths: string;
    areasForGrowth: string;
  };
  nextStepsDetailed?: {
    title: string;
    description: string;
  }[];
}


export interface StudentSummary {
  id: string;
  name: string;
  major: string; 
  schoolName: string; 
  grade: number;       
  latestScore: number;
  improvement: number; // as a percentage
  completed: boolean;
  status?: 'in_progress' | 'completed';
  intent?: StudentGoal; // optional: university or work selection
  tempPassword?: string; // optional: temporary password for account
}

// StudentDetail now holds the history
export interface StudentDetail {
    id: string;
    name: string;
    major: string;
    schoolName: string;
    grade: number;
    report?: InterviewReport; // The latest report
    history: InterviewReport[]; // List of past reports
}

export interface StudentSession {
  id: string;
  startedAt?: string;
  completedAt?: string;
  totalScore?: number;
  status?: string;
  intent?: StudentGoal;
}

export interface StudentSessionDetail {
  id: string;
  report?: InterviewReport;
  startedAt?: string;
  completedAt?: string;
  totalScore?: number;
  status?: string;
  intent?: StudentGoal;
}

export interface User {
    id: string;
    name: string;
    email: string;
    role: 'student' | 'teacher' | 'admin';
    schoolName: string; 
    grade?: number;       
    major?: string;       
    avatarUrl?: string;
    authToken?: string;
  studentId?: string;
  tempPassword?: string;
}

export interface StudentAccountInput {
    name: string;
    school: string;
    gradeYear: 1 | 2 | 3;
    major: string;
    classLabel?: string;
}

export interface GeneratedStudentAccount extends StudentAccountInput {
    studentId: string;
    tempPassword: string;
}

export type AuthView = 'signin' | 'signup';
