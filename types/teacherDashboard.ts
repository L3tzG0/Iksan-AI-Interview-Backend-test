import type { FormEvent, RefObject } from 'react';
import type { GeneratedStudentAccount, StudentGoal, StudentSummary, User } from '../types';
import type { BulkRowError } from '../services/studentService';

export type DashboardTab = 'completed' | 'manage';
export type SortOption = 'recent' | 'score' | 'growth';
export type GradeFilter = number | 'all';
export type GoalFilter = 'all' | StudentGoal;

export interface FilterControlsProps {
  gradeFilter: GradeFilter;
  gradeOptions?: number[];
  sortOption: SortOption;
  goalFilter: GoalFilter;
  onGradeChange: (grade: GradeFilter) => void;
  onSortChange: (option: SortOption) => void;
  onGoalChange: (goal: GoalFilter) => void;
  compact?: boolean;
  showGrade?: boolean;
  showGoal?: boolean;
}

export interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}

export interface DashboardHeroProps {
  currentUser: User;
  studentCount: number;
  completedCount: number;
  averageScore: number;
}

export interface TabSwitcherProps {
  activeTab: DashboardTab;
  onChange: (tab: DashboardTab) => void;
}

export type NewStudentInput = {
  name: string;
  school: string;
  gradeYear: 1 | 2 | 3;
  major: string;
  classLabel: string;
};

export interface CompletedSessionsSectionProps {
  searchTerm: string;
  onSearch: (value: string) => void;
  filterControlsProps: FilterControlsProps;
  processedCompleted: StudentSummary[];
  isLoadingStudents: boolean;
  activeStudentId: string | null;
  onSelectStudent: (studentId: string) => void;
  onHighlightStudent: (studentId: string) => void;
}

export interface AccountManagementSectionProps {
  newStudent: NewStudentInput;
  onUpdateNewStudent: (field: keyof NewStudentInput, value: string | number) => void;
  onCreateStudent: (e: FormEvent) => Promise<void>;
  isCreatingStudent: boolean;
  generatedAccount: GeneratedStudentAccount | null;
  bulkFileName: string;
  bulkErrors: string[];
  bulkPreview: GeneratedStudentAccount[];
  backendErrors: BulkRowError[];
  bulkUploadSummary: { total: number; created: number; failed: number } | null;
  isUploadingCsv: boolean;
  onBulkFileChange: (file?: File) => void;
  onBulkSubmit: () => Promise<void>;
  onTemplateDownload: () => void;
  onCsvPicker: () => void;
  onBackendErrorDownload: () => void;
  searchTerm: string;
  onSearch: (value: string) => void;
  filterControlsProps: FilterControlsProps;
  processedAll: StudentSummary[];
  isLoadingStudents: boolean;
  activeStudentId: string | null;
  onSelectStudent: (studentId: string) => void;
  onHighlightStudent: (studentId: string) => void;
  fileInputRef: RefObject<HTMLInputElement>;
  canSubmitBulkUpload: boolean;
}

export interface TeacherDashboardProps {
  currentUser: User;
  onSelectStudent: (studentId: string) => void;
}
