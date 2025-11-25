
export interface School {
    id: string;
    name: string;
}

export type AppView = 'welcome' | 'session' | 'results' | 'teacherDashboard' | 'studentDetail' | 'studentPreview';

export interface Question {
  id: number;
  text: string;
  type: 'general' | 'resume-based';
}

export interface Answer {
  questionId: number;
  text: string;
  audioUrl?: string;
}

export interface DetailedFeedback {
    question: string;
    answer: string;
    evaluation: string;
    isCorrect: boolean;
    score: number;
}

export interface InterviewReport {
  date?: string; // Added date for history
  scores: {
    contentRelevance: number; // 40%
    structure: number;        // 30%
    fluency: number;          // 20%
    confidence: number;       // 10%
  };
  totalScore: number;
  summary: {
    strengths: string;
    areasForGrowth: string;
  };
  detailedFeedback: DetailedFeedback[];
  nextSteps: {
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

export interface User {
    id: string;
    name: string;
    email: string;
    role: 'student' | 'teacher';
    schoolName: string; 
    grade?: number;       
    major?: string;       
    avatarUrl?: string;
}

export type AuthView = 'signin' | 'signup';
