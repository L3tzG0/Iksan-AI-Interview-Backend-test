
import { User, School } from '../types';

// Mock Users Database
const MOCK_USERS: User[] = [
    { 
        id: 'u1', 
        name: '김교사', 
        email: 'teacher@elice.io', 
        role: 'teacher', 
        schoolName: '이리공업고등학교',
        grade: 3, // Teacher is in charge of 3rd grade
        major: '전기전자과'
    },
    { 
        id: 'u2', 
        name: '이학생', 
        email: 'student@elice.io', 
        role: 'student', 
        schoolName: '이리공업고등학교',
        grade: 3,
        major: '전기제어',
    }
];

export const getSchools = async (): Promise<School[]> => {
    // Keep for backward compatibility if needed, but unused in new signup
    await new Promise(resolve => setTimeout(resolve, 300));
    return [];
};

export const signIn = async (email: string): Promise<User> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Find existing mock user
    const user = MOCK_USERS.find(u => u.email === email);
    if (user) return user;

    // Fallback for demo purposes if email doesn't match mock data
    // Create a transient user based on email pattern
    const role = email.includes('teacher') ? 'teacher' : 'student';
    const name = email.split('@')[0];
    
    return {
        id: `temp-${Date.now()}`,
        name: name,
        email: email,
        role: role,
        schoolName: '이리공업고등학교',
        grade: 3,
        major: role === 'student' ? '소프트웨어과' : '정보컴퓨터',
    };
};

export const signUp = async (
    name: string, 
    email: string, 
    role: 'student' | 'teacher', 
    schoolName: string, 
    grade: number,
    major: string
): Promise<User> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const newUser: User = {
        id: `u-${Date.now()}`,
        name,
        email,
        role,
        schoolName,
        grade,
        major
    };
    
    // In a real app, we would add to MOCK_USERS or backend
    MOCK_USERS.push(newUser);
    
    return newUser;
};
