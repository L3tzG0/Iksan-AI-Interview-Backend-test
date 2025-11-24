
import React, { useState, useEffect } from 'react';
import { getStudentDetails } from '../services/geminiService';
import type { StudentDetail } from '../types';
import Spinner from './Spinner';
import Card from './Card';
import { ArrowLeftIcon } from './icons';
import InterviewReportView from './InterviewReportView';

interface StudentDetailViewProps {
  studentId: string;
  onBack: () => void;
}

const StudentDetailView: React.FC<StudentDetailViewProps> = ({ studentId, onBack }) => {
  const [student, setStudent] = useState<StudentDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const data = await getStudentDetails(studentId);
        setStudent(data);
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [studentId]);

  if (isLoading || !student) {
    return (
      <div className="flex justify-center items-center h-96">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="container mx-auto animate-fadeIn pb-12">
        <div className="flex items-center gap-4 mb-6">
            <button onClick={onBack} className="flex items-center gap-2 text-sm text-slate-500 hover:text-primary transition-colors font-medium">
                <ArrowLeftIcon className="w-4 h-4"/>
                대시보드로 돌아가기
            </button>
        </div>
      <div className="flex items-baseline justify-between mb-6">
        <div>
            <h1 className="text-3xl font-bold text-slate-800">{student.name}</h1>
            <p className="text-lg text-primary font-medium">{student.grade}학년 • {student.major}</p>
        </div>
      </div>

      {student.report ? (
        <InterviewReportView report={student.report} />
      ) : (
        <Card className="text-center py-12">
            <p className="text-slate-500 text-lg">이 학생은 아직 모의 면접을 완료하지 않았습니다.</p>
        </Card>
      )}
    </div>
  );
};

export default StudentDetailView;
